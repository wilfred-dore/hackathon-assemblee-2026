"""Stub de client MCP (JSON-RPC 2.0) pour Moulineuse / Parlement.

Fournit `describe_tools()` (liste les outils exposés par le serveur) et
`call_tool(name, arguments)` (appel d'un outil). Transport HTTP POST vers
l'endpoint MCP.

Sans URL/token configurés, on renvoie des réponses mock pour le smoke test.

TODO(auth) : l'orga fournit MCP_TOKEN sur place. Brancher l'en-tête
d'authentification exact attendu par le serveur (Bearer ? header custom ?)
une fois la doc reçue. Vérifier aussi la négociation de session MCP
(initialize + notifications) si le serveur l'exige — ce stub fait un POST
JSON-RPC simple, suffisant pour un premier test.
"""
from __future__ import annotations

from typing import Any

import httpx

from ..config import CONFIG


class MCPClient:
    def __init__(self, url: str | None, token: str | None = None, name: str = "mcp"):
        self.url = url
        self.token = token or CONFIG.mcp_token
        self.name = name
        self._id = 0

    @property
    def ready(self) -> bool:
        return bool(self.url)

    def _headers(self) -> dict[str, str]:
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        # TODO(auth) : confirmer le schéma d'auth avec l'orga.
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _rpc(self, method: str, params: dict | None = None) -> dict[str, Any]:
        if not self.ready:
            return {"_mock": True, "method": method, "params": params or {}}

        self._id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._id,
            "method": method,
            "params": params or {},
        }
        with httpx.Client(timeout=30) as client:
            r = client.post(self.url, json=payload, headers=self._headers())
            r.raise_for_status()
            data = r.json()
        if "error" in data:
            raise RuntimeError(f"MCP error ({self.name}): {data['error']}")
        return data.get("result", {})

    def describe_tools(self) -> list[dict]:
        """Liste les outils exposés (MCP `tools/list`)."""
        if not self.ready:
            return [{"name": f"{self.name}.mock_tool", "description": "stub (URL manquante)"}]
        return self._rpc("tools/list").get("tools", [])

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        """Appelle un outil (MCP `tools/call`)."""
        if not self.ready:
            return {"_mock": True, "tool": name, "arguments": arguments or {}}
        return self._rpc("tools/call", {"name": name, "arguments": arguments or {}})


def moulineuse() -> MCPClient:
    return MCPClient(CONFIG.mcp_moulineuse_url, name="moulineuse")


def parlement() -> MCPClient:
    return MCPClient(CONFIG.mcp_parlement_url, name="parlement")
