"""Vérification des citations contre les sources (Canutes/Légifrance via MCP Moulineuse).

Chaque `Citation` extraite de la réponse du LLM est confrontée à une source :
- hors-ligne (`MockVerifier`) : base locale d'articles réellement en vigueur,
  pour la démo et les tests Gherkin sans réseau ;
- en ligne (`MoulineuseVerifier`) : MCP Moulineuse (vrai protocole, cf.
  [src/mcp/client.py]) contre Canutes/Légifrance.

`default_verifier()` choisit selon `.env` : Moulineuse si l'URL MCP est câblée,
sinon Mock. Toute erreur réseau = citation NON validée (fail-closed).
Origine du design : POC « Le Rapporteur ».
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .citations import Citation
from .config import CONFIG
from .data import canutes
from .mcp.client import moulineuse


@dataclass
class VerificationResult:
    citation: Citation
    exists: bool
    source: str               # « mock », « canutes-db:… », « mcp-moulineuse:<tool> »
    excerpt: str | None = None
    url: str | None = None     # URL Légifrance réelle (ID LEGIARTI) si dispo


class MockVerifier:
    """Vérificateur hors-ligne : base locale d'articles réellement en vigueur."""

    SOURCE = "mock (base locale)"

    # Clés normalisées (cf. Citation.key) d'articles qui existent vraiment.
    KNOWN = {
        "l3121-27|code du travail",         # durée légale 35 h
        "l1242-2|code du travail",          # cas de recours au CDD
        "l1232-1|code du travail",          # licenciement pour motif personnel
        "9|code civil",                     # respect de la vie privée
        "1240|code civil",                  # responsabilité du fait personnel
        "l121-1|code de la consommation",   # pratiques commerciales déloyales
    }

    def verify(self, citation: Citation) -> VerificationResult:
        return VerificationResult(
            citation=citation,
            exists=citation.key in self.KNOWN,
            source=self.SOURCE,
        )


class MoulineuseVerifier:
    """Vérificateur branché sur le MCP Moulineuse.

    Découvre l'outil de résolution d'article (par motif de nom), l'appelle, et
    valide si la réponse mentionne le numéro d'article demandé.
    """

    SOURCE = "mcp-moulineuse"

    def __init__(self, mcp=None, tool: str | None = None):
        self.mcp = mcp or moulineuse()
        self.tool = tool  # forçable via CONFIG plus tard si besoin

    def _pick_tool(self) -> str:
        if self.tool:
            return self.tool
        tools = self.mcp.describe_tools()
        for pattern in (r"article", r"legifrance|canutes", r"search|recherche"):
            for t in tools:
                if re.search(pattern, t.get("name", ""), re.IGNORECASE):
                    self.tool = t["name"]
                    return self.tool
        raise RuntimeError(
            f"Aucun outil MCP pertinent trouvé. Outils : {[t.get('name') for t in tools]}"
        )

    def verify(self, citation: Citation) -> VerificationResult:
        try:
            tool = self._pick_tool()
            result = self.mcp.call_tool(tool, {"query": citation.label})
            contents = result.get("content", []) if isinstance(result, dict) else []
            text = " ".join(c.get("text", "") for c in contents if c.get("type") == "text")
            num_compact = re.sub(r"[.\s]", "", citation.num).lower()
            exists = num_compact in re.sub(r"[.\s]", "", text).lower()
            return VerificationResult(
                citation=citation,
                exists=exists,
                source=f"{self.SOURCE}:{tool}",
                excerpt=text[:280] or None,
            )
        except Exception as exc:  # noqa: BLE001 — fail-closed : réseau KO -> non validé
            return VerificationResult(
                citation=citation, exists=False, source=f"{self.SOURCE} (erreur: {type(exc).__name__})",
            )


class CanutesDBVerifier:
    """Vérificateur branché sur Canutes en direct (PostgreSQL, table
    legifrance.article). Schéma introspecté (cf. docs/canutes-schema.md) :
    on vérifie num + code + version EN VIGUEUR, et on renvoie la vraie URL
    Légifrance (ID LEGIARTI). Fail-closed sur erreur réseau/DB."""

    SOURCE = "canutes-db:legifrance.article"

    def verify(self, citation: Citation) -> VerificationResult:
        try:
            res = canutes.verify_article(citation.num, citation.code)
            return VerificationResult(
                citation=citation,
                exists=res["exists"],
                source=f"{self.SOURCE}" + (f" ({res['etat']})" if res.get("etat") else ""),
                excerpt=res.get("excerpt"),
                url=res.get("url"),
            )
        except Exception as exc:  # noqa: BLE001 — fail-closed
            return VerificationResult(
                citation=citation, exists=False, source=f"{self.SOURCE} (erreur: {type(exc).__name__})",
            )


def default_verifier():
    """Choix du vérificateur :
    - MODE=live + accès DB Canutes  -> CanutesDBVerifier (vérif réelle, URL Légifrance)
    - MODE=live + MCP Moulineuse    -> MoulineuseVerifier (SQL/JS via MCP)
    - sinon                         -> MockVerifier (hors-ligne déterministe)
    """
    if CONFIG.is_live and CONFIG.canutes_db_ready:
        return CanutesDBVerifier()
    if CONFIG.is_live and CONFIG.mcp_moulineuse_url:
        return MoulineuseVerifier()
    return MockVerifier()
