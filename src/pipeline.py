"""Pipeline « IA de confiance » : question -> retrieval -> réponse SOURCÉE -> validation.

Règle d'or : **pas de source, pas de réponse**. Si le retrieval ne ramène
aucune source, on refuse explicitement plutôt que d'inventer.

Le flux est volontairement simple et lisible (hackathon). Chaque étape est
remplaçable selon le défi choisi.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .data import canutes
from .llm.client import LLMClient
from .mcp.client import moulineuse, parlement


@dataclass
class Source:
    """Une source citable. `ref` doit permettre de retrouver l'original."""
    ref: str          # ex : "LEGIARTI000...", "PROJET-LOI-2025-42"
    title: str
    snippet: str
    origin: str       # "moulineuse" | "parlement" | "canutes" | ...


@dataclass
class Answer:
    question: str
    text: str
    sources: list[Source] = field(default_factory=list)
    refused: bool = False
    validation: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.refused and bool(self.sources)


# --- 1. Retrieval ---------------------------------------------------------

def retrieve(question: str, notes: list[str] | None = None) -> list[Source]:
    """Interroge les sources disponibles. Renvoie [] si rien trouvé.

    En mode mock (URLs/clés absentes), renvoie [] : le pipeline doit alors
    REFUSER — c'est le comportement de confiance qu'on veut démontrer.
    Branche ici les vrais appels (moulineuse().call_tool(...),
    canutes.rest_get(...)) une fois les endpoints/tokens disponibles.

    Tolérant aux pannes (fail-closed) : toute erreur réseau/protocole est
    traitée comme une ABSENCE de source (-> refus), jamais comme un crash.
    Les diagnostics sont ajoutés à `notes` pour affichage.
    """
    notes = notes if notes is not None else []
    sources: list[Source] = []

    mcp = moulineuse()
    if mcp.ready:
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
            notes.append(f"moulineuse: retrieval indisponible ({type(e).__name__}) -> ignoré")

    # Idem pour parlement() et canutes.rest_get(...) selon le défi.
    _ = parlement, canutes  # pointeurs pour brancher plus tard

    return sources


def _as_items(res) -> list[dict]:
    if isinstance(res, dict):
        return res.get("items") or res.get("results") or []
    if isinstance(res, list):
        return res
    return []


# --- 2. Génération sourcée -----------------------------------------------

SYSTEM_PROMPT = (
    "Tu es un assistant juridique de confiance. Tu ne réponds QU'À PARTIR des "
    "sources fournies. Tu cites chaque affirmation avec [ref]. Si les sources "
    "ne suffisent pas, tu le dis explicitement. Tu n'inventes JAMAIS de citation."
)


def generate(question: str, sources: list[Source], llm: LLMClient) -> str:
    bloc = "\n\n".join(f"[{s.ref}] {s.title}\n{s.snippet}" for s in sources)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Question : {question}\n\nSources :\n{bloc}"},
    ]
    return llm.chat(messages)


# --- 3. Validation --------------------------------------------------------

def validate(answer_text: str, sources: list[Source]) -> dict:
    """Garde-fous simples : toute [ref] citée doit exister dans les sources."""
    known = {s.ref for s in sources}
    cited = _extract_refs(answer_text)
    invented = sorted(cited - known)
    return {
        "cited_refs": sorted(cited),
        "invented_refs": invented,
        "no_invented_citation": not invented,
        "has_sources": bool(sources),
    }


def _extract_refs(text: str) -> set[str]:
    import re
    return set(re.findall(r"\[([^\[\]]+)\]", text))


# --- Orchestration --------------------------------------------------------

REFUSAL = (
    "Je ne peux pas répondre : aucune source vérifiable n'a été trouvée pour "
    "cette question. (Refus volontaire — pas de source, pas de réponse.)"
)


def answer_question(question: str, llm: LLMClient | None = None) -> Answer:
    llm = llm or LLMClient()
    notes: list[str] = []
    sources = retrieve(question, notes)

    if not sources:
        return Answer(question=question, text=REFUSAL, refused=True,
                      validation={"has_sources": False, "no_invented_citation": True,
                                  "retrieval_notes": notes})

    text = generate(question, sources, llm)
    validation = validate(text, sources)
    validation["retrieval_notes"] = notes
    return Answer(question=question, text=text, sources=sources, validation=validation)
