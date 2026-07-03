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
from .mcp.client import moulineuse


@dataclass
class VerificationResult:
    citation: Citation
    exists: bool
    source: str               # « mock », « mcp-moulineuse:<tool> », …
    excerpt: str | None = None


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


# TODO : repli Canutes direct (PostgREST) via src/data/canutes.py une fois le
# schéma réel connu (ne pas inventer la forme des tables — cf. CLAUDE.md).


def default_verifier():
    """Live (MCP Moulineuse) si MODE=live et URL câblée, sinon Mock (hors-ligne)."""
    if CONFIG.is_live and CONFIG.mcp_moulineuse_url:
        return MoulineuseVerifier()
    return MockVerifier()
