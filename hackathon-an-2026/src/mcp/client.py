"""Client MCP (JSON-RPC 2.0, streamable HTTP) pour Moulineuse / Parlement.

Implémente le protocole MCP réel : négociation de session (`initialize` +
`notifications/initialized`), en-tête `mcp-session-id`, et parsing des réponses
`text/event-stream` (SSE). Fournit `describe_tools()` (MCP `tools/list`) et
`call_tool()` (MCP `tools/call`).

Sans URL configurée, renvoie des réponses mock pour le smoke test hors-ligne.

TODO(auth) : si le serveur exige un jeton (MCP_TOKEN, fourni par l'orga), il est
envoyé en `Authorization: Bearer`. Confirmer le schéma exact sur place.
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from ..config import CONFIG


class MCPClient:
    PROTOCOL_VERSION = "2024-11-05"

    def __init__(self, url: str | None, token: str | None = None, name: str = "mcp"):
        self.url = url
        self.token = token or CONFIG.mcp_token
        self.name = name
        self._id = 0
        self._session_id: str | None = None
        self._client: httpx.Client | None = None

    @property
    def ready(self) -> bool:
        return bool(self.url)

    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30)
        return self._client

    def _headers(self) -> dict[str, str]:
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.token:  # TODO(auth) : confirmer le schéma avec l'orga.
            h["Authorization"] = f"Bearer {self.token}"
        if self._session_id:
            h["mcp-session-id"] = self._session_id
        return h

    def _rpc(self, method: str, params: dict | None = None, notify: bool = False) -> dict[str, Any] | None:
        """Un appel JSON-RPC. `notify=True` pour une notification (sans réponse)."""
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        if not notify:
            self._id += 1
            payload["id"] = self._id

        r = self._http().post(self.url, json=payload, headers=self._headers())
        r.raise_for_status()
        if sid := r.headers.get("mcp-session-id"):
            self._session_id = sid
        if notify:
            return None

        body = r.text
        if "text/event-stream" in r.headers.get("content-type", ""):
            # SSE : on prend le premier événement `data: {...}`.
            for line in body.splitlines():
                if line.startswith("data:"):
                    body = line[5:].strip()
                    break
        data = json.loads(body)
        if "error" in data:
            raise RuntimeError(f"MCP error ({self.name}): {data['error']}")
        return data.get("result", {})

    def _ensure_session(self) -> None:
        if self._session_id is not None:
            return
        self._rpc(
            "initialize",
            {
                "protocolVersion": self.PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "hackathon-assemblee-2026", "version": "0.1.0"},
            },
        )
        self._rpc("notifications/initialized", {}, notify=True)

    def describe_tools(self) -> list[dict]:
        """Liste les outils exposés (MCP `tools/list`)."""
        if not self.ready:
            return [{"name": f"{self.name}.mock_tool", "description": "stub (URL manquante)"}]
        self._ensure_session()
        return (self._rpc("tools/list", {}) or {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        """Appelle un outil (MCP `tools/call`)."""
        if not self.ready:
            return {"_mock": True, "tool": name, "arguments": arguments or {}}
        self._ensure_session()
        return self._rpc("tools/call", {"name": name, "arguments": arguments or {}}) or {}


def moulineuse() -> MCPClient:
    return MCPClient(CONFIG.mcp_moulineuse_url, name="moulineuse")


def parlement() -> MCPClient:
    return MCPClient(CONFIG.mcp_parlement_url, name="parlement")
