"""Wrapper LLM OpenAI-compatible + LLM démo hors-ligne.

Base URL / clé / modèle lus dans .env. Facilement swappable entre le backend
principal (Mistral via Modular MAX sur AMD) et le fallback (playground Qualcomm
Cloud AI 100) : il suffit de changer LLM_BASE_URL / LLM_API_KEY / LLM_MODEL.

Sans clé configurée, on bascule sur un LLM démo déterministe qui reproduit les
deux comportements d'un LLM généraliste : des citations exactes… ET des
citations inventées avec aplomb (pour démontrer le refus du pipeline hors-ligne).
"""
from __future__ import annotations

from ..config import CONFIG

SYSTEM_PROMPT = """Tu es un assistant juridique pour les citoyens français.
Réponds brièvement et cite TOUJOURS tes sources sous la forme exacte
« article <numéro> du <nom du code> » (ex. : article L. 3121-27 du Code du travail).
Ne cite jamais un article dont tu n'es pas certain de l'existence."""

# Réponses canned pour la démo hors-ligne : keywords -> réponse.
# Certaines citent des articles réels, une cite un article INVENTÉ (prime de
# Noël) pour prouver que le pipeline refuse.
_CANNED: list[tuple[tuple[str, ...], str]] = [
    (("durée légale", "35 heures", "temps de travail"),
     "La durée légale de travail effectif des salariés à temps complet est fixée "
     "à trente-cinq heures par semaine, conformément à l'article L. 3121-27 du "
     "Code du travail."),
    (("cdd", "durée déterminée"),
     "Un CDD ne peut être conclu que pour l'exécution d'une tâche précise et "
     "temporaire, dans les cas prévus par l'article L. 1242-2 du Code du travail."),
    (("vie privée", "photo", "image"),
     "Chacun a droit au respect de sa vie privée, comme le garantit l'article 9 "
     "du Code civil."),
    (("licenciement", "licencié"),
     "Tout licenciement pour motif personnel doit être justifié par une cause "
     "réelle et sérieuse, en application de l'article L. 1232-1 du Code du travail."),
    (("prime de noël",),
     # Citation INVENTÉE volontairement.
     "La prime de Noël est un droit garanti à tous les salariés par l'article "
     "L. 4321-7 du Code du travail, qui oblige l'employeur à la verser."),
]
# Par défaut, le LLM généraliste « invente avec aplomb » (article fantaisiste).
_DEFAULT_CANNED = (
    "Votre situation est couverte par l'article L. 9999-1 du Code de la "
    "consommation, qui vous donne entièrement raison."
)


def _demo_answer(question: str) -> str:
    q = question.lower()
    for keywords, answer in _CANNED:
        if any(k in q for k in keywords):
            return answer
    return _DEFAULT_CANNED


class LLMClient:
    def __init__(self, base_url=None, api_key=None, model=None):
        self.base_url = base_url or CONFIG.llm_base_url
        self.api_key = api_key or CONFIG.llm_api_key
        self.model = model or CONFIG.llm_model
        self._client = None

    @property
    def ready(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)

    def _ensure_client(self):
        if self._client is None:
            from openai import OpenAI  # import paresseux

            self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        return self._client

    def complete(self, question: str, context: str = "") -> str:
        """Réponse à une question citoyenne (éventuellement ancrée par `context`).

        Mode démo déterministe si aucune clé LLM n'est configurée.
        """
        if not self.ready:
            return _demo_answer(question)

        user = question if not context else f"{question}\n\nContexte sourcé :\n{context}"
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ]
        return self.chat(messages)

    def chat(self, messages: list[dict], temperature: float = 0.2) -> str:
        """Appel bas niveau OpenAI-compatible. Mode démo si non configuré."""
        if not self.ready:
            last = messages[-1]["content"] if messages else ""
            return _demo_answer(last)

        resp = self._ensure_client().chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""
