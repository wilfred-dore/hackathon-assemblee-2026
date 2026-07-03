"""Pipeline « IA de confiance » (fusion RAG + vérification post-hoc).

Flux : question -> (ancrage retrieval) -> génération LLM -> extraction des
citations -> vérification de CHAQUE citation contre les sources -> réponse
SOURCÉE ou REFUS explicite.

Règle d'or : **pas de citation vérifiable, pas de réponse**. Défense en
profondeur : on ancre la génération dans les sources récupérées (RAG) ET on
fact-checke a posteriori chaque article cité (héritage POC « Le Rapporteur »).
Au moindre article introuvable — ou en l'absence totale de citation vérifiée —
on refuse plutôt que d'inventer.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .citations import extract_citations
from .data import canutes
from .llm.client import LLMClient
from .mcp.client import moulineuse, parlement
from .verify import default_verifier


@dataclass
class Source:
    """Une source d'ancrage (retrieval). `ref` permet de retrouver l'original."""
    ref: str          # ex : "LEGIARTI000...", "PROJET-LOI-2025-42"
    title: str
    snippet: str
    origin: str       # "moulineuse" | "parlement" | "canutes" | ...


@dataclass
class Answer:
    question: str
    text: str
    status: str = "refus"                 # "ok" | "refus"
    citations: list[dict] = field(default_factory=list)  # {label, exists, url, source}
    grounding: list[Source] = field(default_factory=list)
    detail: str = ""
    validation: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    @property
    def refused(self) -> bool:
        return self.status != "ok"


# --- 1. Ancrage (retrieval, optionnel) -----------------------------------

def retrieve(question: str, notes: list[str] | None = None) -> list[Source]:
    """Récupère des passages sourcés pour ancrer la génération. [] si rien.

    Tolérant aux pannes (fail-closed) : toute erreur réseau/protocole est
    traitée comme une ABSENCE de source, jamais comme un crash. Diagnostics
    ajoutés à `notes`. Branche ici les vrais appels (moulineuse().call_tool,
    canutes.rest_get) selon le défi.
    """
    from .config import CONFIG
    notes = notes if notes is not None else []
    sources: list[Source] = []

    mcp = moulineuse()
    if CONFIG.is_live and mcp.ready:
        try:
            # TODO : adapter au nom réel de l'outil de recherche du serveur.
            res = mcp.call_tool("search", {"query": question})
            for item in _as_items(res):
                sources.append(Source(
                    ref=item.get("ref", "?"),
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    origin="moulineuse",
                ))
        except Exception as e:  # noqa: BLE001 — fail-closed volontaire
            notes.append(f"moulineuse: ancrage indisponible ({type(e).__name__}) -> ignoré")

    _ = parlement, canutes  # pointeurs pour brancher plus tard selon le défi
    return sources


def _as_items(res) -> list[dict]:
    if isinstance(res, dict):
        return res.get("items") or res.get("results") or []
    if isinstance(res, list):
        return res
    return []


# --- Orchestration --------------------------------------------------------

REFUSAL = "Je ne trouve pas de texte applicable."


def answer_question(question: str, llm: LLMClient | None = None, verifier=None) -> Answer:
    llm = llm or LLMClient()
    verifier = verifier or default_verifier()

    notes: list[str] = []
    grounding = retrieve(question, notes)
    context = "\n\n".join(f"[{s.ref}] {s.title}\n{s.snippet}" for s in grounding)

    draft = llm.complete(question, context)
    citations = extract_citations(draft)
    results = [verifier.verify(c) for c in citations]

    payload = [
        {
            "label": r.citation.label,
            "exists": r.exists,
            "url": r.citation.legifrance_url if r.exists else None,
            "source": r.source,
        }
        for r in results
    ]

    all_verified = bool(results) and all(r.exists for r in results)
    invented = [r.citation.label for r in results if not r.exists]
    validation = {
        "has_grounding": bool(grounding),
        "cited": [r.citation.label for r in results],
        "invented": invented,
        "no_invented_citation": not invented,
        "retrieval_notes": notes,
    }

    if all_verified:
        return Answer(question=question, text=draft, status="ok", citations=payload,
                      grounding=grounding, validation=validation)

    detail = (
        "Références introuvables dans les sources : " + " ; ".join(invented)
        if invented else "La réponse générée ne citait aucune source vérifiable."
    )
    return Answer(question=question, text=REFUSAL, status="refus", citations=payload,
                  grounding=grounding, detail=detail, validation=validation)
