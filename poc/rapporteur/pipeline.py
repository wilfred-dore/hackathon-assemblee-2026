"""Pipeline du Rapporteur : générer → extraire → vérifier → répondre ou refuser."""

from __future__ import annotations

from typing import Any

from .citations import extract_citations
from .llm import default_llm
from .verifier import default_verifier

REFUSAL = "Je ne trouve pas de texte applicable."


class Rapporteur:
    def __init__(self, llm=None, verifier=None) -> None:
        self.llm = llm or default_llm()
        self.verifier = verifier or default_verifier()

    def answer(self, question: str) -> dict[str, Any]:
        """Répond à une question citoyenne. Chaque citation est vérifiée ;
        au moindre article introuvable (ou en l'absence de source), la réponse
        est un refus explicite."""
        draft = self.llm.complete(question)
        citations = extract_citations(draft)
        results = [self.verifier.verify(c) for c in citations]

        payload_citations = [
            {
                "label": r.citation.label,
                "exists": r.exists,
                "url": r.citation.legifrance_url if r.exists else None,
                "source": r.source,
            }
            for r in results
        ]

        all_verified = bool(results) and all(r.exists for r in results)
        if all_verified:
            return {
                "status": "ok",
                "answer": draft,
                "citations": payload_citations,
            }

        invented = [r.citation.label for r in results if not r.exists]
        return {
            "status": "refus",
            "answer": REFUSAL,
            "citations": payload_citations,
            "detail": (
                "Références introuvables dans les sources : " + " ; ".join(invented)
                if invented
                else "La réponse générée ne citait aucune source vérifiable."
            ),
        }
