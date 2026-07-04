"""API HTTP « integration-ready » — Le Rapporteur.

Expose la couche de confiance comme un service réutilisable (AN, CiviqHub, tout
front citoyen) :

  GET  /health          -> mode + état du câblage
  POST /answer          -> {question} -> réponse sourcée ou refus (+ citations vérifiées)
  POST /verify          -> {text}     -> fact-check des articles cités dans un texte

FUSION : sert aussi l'UI institutionnelle de François (poc/static) branchée sur
NOTRE moteur live (Qualcomm + vérif Canutes) via les routes qu'attend son front :
  GET  /  /details  /sources        -> pages
  POST /api/ask                      -> = /answer (format attendu par son UI)
  GET  /api/article?ref=  /api/articles

Le endpoint `/verify` est le point d'intégration clé : n'importe quelle plateforme
envoie la sortie d'un LLM, on renvoie quelles citations sont réelles.

Lancer :  uv sync --extra api && uv run uvicorn src.api:app --port 8080
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .citations import extract_citations
from .config import CONFIG
from .data import canutes
from .llm.client import LLMClient
from .pipeline import answer_question
from .verify import default_verifier

app = FastAPI(title="Le Rapporteur — API de confiance", version="0.1.0")

# UI de François (best-of-both : son front + notre moteur)
_STATIC = Path(__file__).resolve().parent.parent / "poc" / "static"


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
        "guarantees": ans.guarantees,   # garanties de confiance (affichables)
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


# --- UI de François, branchée sur NOTRE moteur (best-of-both) ---------------

@app.post("/api/ask")
def api_ask(q: Question) -> dict:
    """Route attendue par le front de François -> notre moteur live."""
    return answer(q)


@app.get("/api/articles")
def api_articles() -> dict:
    """Petite liste d'articles de démo (labels reconnus hors-ligne)."""
    demo = [
        ("L. 3121-27", "Code du travail"), ("L. 1242-2", "Code du travail"),
        ("L. 1232-1", "Code du travail"), ("9", "Code civil"), ("1240", "Code civil"),
    ]
    return {"articles": [{"ref": f"article {n} du {c}", "num": n, "code": c} for n, c in demo]}


@app.get("/api/article")
def api_article(ref: str) -> dict:
    """Charge un article depuis Canutes (Légifrance). Fail-closed."""
    cits = extract_citations(ref)
    if not cits:
        return {"found": False, "query": ref}
    c = cits[0]
    try:
        res = canutes.verify_article(c.num, c.code)
    except Exception:
        res = {"exists": False}
    if not res.get("exists"):
        return {"found": False, "query": ref}
    return {
        "found": True, "num": c.num, "code": c.code,
        "text": res.get("excerpt"), "excerpt": res.get("excerpt"),
        "url": res.get("url"), "source": f"canutes-db ({res.get('etat')})",
    }


def _page(name: str) -> FileResponse:
    return FileResponse(_STATIC / name)


@app.get("/")
def ui_index() -> FileResponse:
    return _page("landing.html")   # hall d'accueil


@app.get("/demo")
def ui_demo() -> FileResponse:
    return _page("index.html")     # app « Poser une question » de François


@app.get("/details")
def ui_details() -> FileResponse:
    return _page("details.html")


@app.get("/sources")
def ui_sources() -> FileResponse:
    return _page("sources.html")


@app.get("/app.css")
def ui_css() -> FileResponse:
    return FileResponse(_STATIC / "app.css", media_type="text/css")


@app.get("/api.js")
def ui_js() -> FileResponse:
    return FileResponse(_STATIC / "api.js", media_type="text/javascript")


@app.get("/favicon.svg")
def ui_favicon() -> FileResponse:
    return FileResponse(_STATIC / "favicon.svg", media_type="image/svg+xml")


# Notre doc schéma (cartographie Canutes) servie aussi en live sous /schema
_SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema-site"
if _SCHEMA_DIR.exists():
    app.mount("/schema", StaticFiles(directory=str(_SCHEMA_DIR), html=True), name="schema")
