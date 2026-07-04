"""Vérification des citations contre les sources (Canutes/Légifrance via MCP Moulineuse)."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

import httpx

from .citations import Citation


@dataclass
class VerificationResult:
    citation: Citation
    exists: bool
    source: str          # « canutes », « moulineuse », « mock »…
    excerpt: str | None = None


class MockVerifier:
    """Vérificateur hors-ligne : base locale d'articles réellement en vigueur.

    Sert au mode démo et aux tests Gherkin (aucun réseau requis).
    """

    SOURCE = "mock (base locale)"

    # Clés normalisées (cf. Citation.key) d'articles qui existent vraiment.
    KNOWN = {
        "l3121-27|code du travail",   # durée légale 35 h
        "l1242-2|code du travail",    # cas de recours au CDD
        "l1232-1|code du travail",    # licenciement pour motif personnel
        "9|code civil",               # respect de la vie privée
        "1240|code civil",            # responsabilité du fait personnel
        "l121-1|code de la consommation",  # pratiques commerciales déloyales
    }

    def verify(self, citation: Citation) -> VerificationResult:
        return VerificationResult(
            citation=citation,
            exists=citation.key in self.KNOWN,
            source=self.SOURCE,
        )


class MoulineuseVerifier:
    """Vérificateur branché sur le MCP Moulineuse (JSON-RPC streamable HTTP).

    Découvre les outils exposés puis interroge celui qui permet de résoudre
    une référence d'article. La réponse est jugée positive si l'outil renvoie
    un contenu mentionnant le numéro d'article demandé.
    """

    SOURCE = "mcp-moulineuse"

    def __init__(self, url: str | None = None, tool: str | None = None) -> None:
        self.url = url or os.environ.get(
            "RAPPORTEUR_MCP_URL", "https://mcp.hackathon2026.leximpact.dev/mcp"
        )
        self.tool = tool or os.environ.get("RAPPORTEUR_MCP_TOOL")
        self._session_id: str | None = None
        self._client = httpx.Client(timeout=20)

    # --- protocole MCP minimal -------------------------------------------
    def _rpc(self, method: str, params: dict | None = None, id_: int | None = 1) -> dict | None:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["mcp-session-id"] = self._session_id
        payload: dict = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        if id_ is not None:
            payload["id"] = id_
        resp = self._client.post(self.url, headers=headers, json=payload)
        resp.raise_for_status()
        if sid := resp.headers.get("mcp-session-id"):
            self._session_id = sid
        if id_ is None:  # notification
            return None
        body = resp.text
        if "text/event-stream" in resp.headers.get("content-type", ""):
            # extraire le premier événement data: {...}
            for line in body.splitlines():
                if line.startswith("data:"):
                    body = line[5:].strip()
                    break
        return json.loads(body)

    def _ensure_session(self) -> None:
        if self._session_id is not None:
            return
        self._rpc(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "le-rapporteur-poc", "version": "0.1.0"},
            },
        )
        self._rpc("notifications/initialized", {}, id_=None)

    def _pick_tool(self) -> str:
        if self.tool:
            return self.tool
        result = self._rpc("tools/list", {}, id_=2) or {}
        tools = result.get("result", {}).get("tools", [])
        for pattern in (r"article", r"legifrance|canutes", r"search|recherche"):
            for t in tools:
                if re.search(pattern, t.get("name", ""), re.IGNORECASE):
                    self.tool = t["name"]
                    return self.tool
        raise RuntimeError(
            "Aucun outil MCP pertinent trouvé ; fixez RAPPORTEUR_MCP_TOOL. "
            f"Outils disponibles : {[t.get('name') for t in tools]}"
        )

    # ----------------------------------------------------------------------
    def verify(self, citation: Citation) -> VerificationResult:
        try:
            self._ensure_session()
            tool = self._pick_tool()
            result = self._rpc(
                "tools/call",
                {"name": tool, "arguments": {"query": citation.label}},
                id_=3,
            ) or {}
            contents = result.get("result", {}).get("content", [])
            text = " ".join(c.get("text", "") for c in contents if c.get("type") == "text")
            num_compact = re.sub(r"[.\s]", "", citation.num).lower()
            exists = num_compact in re.sub(r"[.\s]", "", text).lower()
            return VerificationResult(
                citation=citation,
                exists=exists,
                source=f"{self.SOURCE}:{tool}",
                excerpt=text[:280] or None,
            )
        except Exception as exc:  # réseau indisponible → on NE valide PAS
            return VerificationResult(
                citation=citation,
                exists=False,
                source=f"{self.SOURCE} (erreur: {exc})",
            )


def default_verifier():
    if os.environ.get("RAPPORTEUR_MODE", "demo") == "live":
        return MoulineuseVerifier()
    return MockVerifier()
