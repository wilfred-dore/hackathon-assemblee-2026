"""API HTTP « integration-ready » — Le Rapporteur.

Expose la couche de confiance comme un service réutilisable (AN, CiviqHub, tout
front citoyen) :

  GET  /health          -> mode + état du câblage
  POST /answer          -> {question} -> réponse sourcée ou refus (+ citations vérifiées)
  POST /verify          -> {text}     -> fact-check des articles cités dans un texte

Le endpoint `/verify` est le point d'intégration clé : n'importe quelle plateforme
envoie la sortie d'un LLM, on renvoie quelles citations sont réelles (vérifiées
dans Canutes/Légifrance) et lesquelles sont inventées.

Lancer :  uv sync --extra api && uv run uvicorn src.api:app --port 8080
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from .citations import extract_citations
from .config import CONFIG
from .llm.client import LLMClient
from .pipeline import answer_question
from .verify import default_verifier

app = FastAPI(title="Le Rapporteur — API de confiance", version="0.1.0")


class Question(BaseModel):
    question: str


class TextIn(BaseModel):
    text: str


def _citation_dict(r) -> dict:
    return {
        "label": r.citation.label,
        "num": r.citation.num,
        "code": r.citation.code,
        "exists": r.exists,
        "url": (r.url or r.citation.legifrance_url) if r.exists else None,
        "source": r.source,
        "excerpt": r.excerpt,
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "mode": CONFIG.mode,
        "llm_configured": LLMClient().ready,
        "canutes_db": CONFIG.canutes_db_ready,
        "mcp_moulineuse": bool(CONFIG.mcp_moulineuse_url),
    }


@app.post("/answer")
def answer(q: Question) -> dict:
    """Pose une question -> réponse SOURCÉE (citations vérifiées) ou REFUS."""
    llm = LLMClient()
    ans = answer_question(q.question, llm=llm)
    return {
        "question": ans.question,
        "status": ans.status,           # "ok" | "refus"
        "answer": ans.text,
        "detail": ans.detail or None,
        "citations": ans.citations,
        "metrics": llm.last_metrics,    # latence/tokens/s si backend live
    }


@app.post("/verify")
def verify(inp: TextIn) -> dict:
    """Fact-check : extrait les articles cités dans `text` et vérifie chacun.

    Point d'intégration réutilisable (ex. CiviqHub) : détecte les citations
    juridiques inventées dans n'importe quelle sortie de LLM.
    """
    verifier = default_verifier()
    results = [verifier.verify(c) for c in extract_citations(inp.text)]
    citations = [_citation_dict(r) for r in results]
    invented = [c["label"] for c in citations if not c["exists"]]
    return {
        "citations": citations,
        "n_citations": len(citations),
        "n_invented": len(invented),
        "invented": invented,
        "no_invented_citation": not invented,
        "trustworthy": bool(citations) and not invented,
    }
