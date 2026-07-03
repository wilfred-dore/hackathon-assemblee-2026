"""API HTTP du Rapporteur (FastAPI) + interface de démo + serveur MCP.

Le Rapporteur est aussi un **serveur MCP** (`POST /mcp`, JSON-RPC 2.0,
streamable HTTP) : n'importe quel agent peut appeler `repondre_question`
(pipeline complet, refus si source introuvable) ou `verifier_article`
(fact-check d'une référence). Symétrique du client MCP de src/mcp/client.py.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .citations import extract_citations
from .pipeline import Rapporteur

app = FastAPI(title="Le Rapporteur", version="0.1.0")
_rapporteur = Rapporteur()
_STATIC = Path(__file__).resolve().parent.parent / "static"


class Question(BaseModel):
    question: str


@app.post("/api/ask")
def ask(q: Question) -> dict:
    return _rapporteur.answer(q.question)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


# --- Serveur MCP (JSON-RPC 2.0, streamable HTTP) ---------------------------

MCP_PROTOCOL_VERSION = "2024-11-05"

MCP_TOOLS = [
    {
        "name": "repondre_question",
        "description": (
            "Répond à une question de droit français avec des citations "
            "vérifiées contre les sources. Refuse explicitement si un article "
            "cité est introuvable ou si aucune source n'est vérifiable."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"question": {"type": "string", "description": "Question citoyenne en français"}},
            "required": ["question"],
        },
    },
    {
        "name": "verifier_article",
        "description": (
            "Vérifie qu'une référence d'article existe dans les sources. "
            "Format attendu : « article L. 3121-27 du Code du travail »."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"reference": {"type": "string", "description": "ex. « article L. 3121-27 du Code du travail »"}},
            "required": ["reference"],
        },
    },
]


def _tool_call(name: str, arguments: dict) -> dict:
    """Exécute un outil MCP -> résultat `tools/call` (content + structuredContent)."""
    if name == "repondre_question":
        payload = _rapporteur.answer(str(arguments.get("question", "")))
    elif name == "verifier_article":
        citations = extract_citations(str(arguments.get("reference", "")))
        if not citations:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "Référence non reconnue. Format : « article L. 3121-27 du Code du travail »."}],
            }
        results = [_rapporteur.verifier.verify(c) for c in citations]
        payload = {
            "verifications": [
                {
                    "label": r.citation.label,
                    "exists": r.exists,
                    "url": r.citation.legifrance_url if r.exists else None,
                    "source": r.source,
                }
                for r in results
            ]
        }
    else:
        raise KeyError(name)
    return {
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}],
        "structuredContent": payload,
    }


def _rpc_error(req_id, code: int, message: str) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


@app.post("/mcp")
async def mcp(request: Request) -> Response:
    try:
        msg = await request.json()
    except Exception:
        return _rpc_error(None, -32700, "Parse error")

    method, req_id, params = msg.get("method", ""), msg.get("id"), msg.get("params") or {}

    # Notifications : accusé sans corps.
    if method.startswith("notifications/"):
        return Response(status_code=202)

    if method == "initialize":
        result = {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "le-rapporteur", "version": "0.1.0"},
        }
        return JSONResponse(
            {"jsonrpc": "2.0", "id": req_id, "result": result},
            headers={"mcp-session-id": uuid.uuid4().hex},
        )

    if method == "tools/list":
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {"tools": MCP_TOOLS}})

    if method == "tools/call":
        try:
            result = _tool_call(params.get("name", ""), params.get("arguments") or {})
        except KeyError as exc:
            return _rpc_error(req_id, -32602, f"Outil inconnu : {exc}")
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": result})

    return _rpc_error(req_id, -32601, f"Méthode non supportée : {method}")
