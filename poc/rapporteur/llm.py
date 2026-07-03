"""Génération : LLM local OpenAI-compatible (Modular MAX) ou démo hors-ligne."""

from __future__ import annotations

import os

import httpx

SYSTEM_PROMPT = """Tu es un assistant juridique pour les citoyens français.
Réponds brièvement et cite TOUJOURS tes sources sous la forme exacte
« article <numéro> du <nom du code> » (ex. : article L. 3121-27 du Code du travail).
Ne cite jamais un article dont tu n'es pas certain de l'existence."""


class MaxLLM:
    """Client d'un serveur OpenAI-compatible (docker modular/max-openai-api)."""

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get(
            "RAPPORTEUR_LLM_BASE_URL", "http://localhost:8000/v1"
        )).rstrip("/")
        self.model = model or os.environ.get("RAPPORTEUR_LLM_MODEL", "default")

    def complete(self, question: str) -> str:
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                ],
                "temperature": 0.2,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


class DemoLLM:
    """Modèle simulé pour la démo hors-ligne.

    Reproduit les deux comportements types d'un LLM généraliste :
    des citations exactes… et des citations inventées avec aplomb.
    """

    _CANNED: list[tuple[tuple[str, ...], str]] = [
        (
            ("durée légale", "35 heures", "temps de travail"),
            "La durée légale de travail effectif des salariés à temps complet est "
            "fixée à trente-cinq heures par semaine, conformément à l'article "
            "L. 3121-27 du Code du travail.",
        ),
        (
            ("cdd", "durée déterminée"),
            "Un CDD ne peut être conclu que pour l'exécution d'une tâche précise et "
            "temporaire, dans les cas prévus par l'article L. 1242-2 du Code du travail.",
        ),
        (
            ("vie privée", "photo", "image"),
            "Chacun a droit au respect de sa vie privée, comme le garantit "
            "l'article 9 du Code civil.",
        ),
        (
            ("licenciement", "licencié"),
            "Tout licenciement pour motif personnel doit être justifié par une cause "
            "réelle et sérieuse, en application de l'article L. 1232-1 du Code du travail.",
        ),
        (
            ("prime de noël",),
            # Citation INVENTÉE volontairement : démontre le refus du Rapporteur.
            "La prime de Noël est un droit garanti à tous les salariés par l'article "
            "L. 4321-7 du Code du travail, qui oblige l'employeur à la verser.",
        ),
    ]

    _DEFAULT = (
        # Citation INVENTÉE volontairement (article fantaisiste).
        "Votre situation est couverte par l'article L. 9999-1 du Code de la "
        "consommation, qui vous donne entièrement raison."
    )

    def complete(self, question: str) -> str:
        q = question.lower()
        for keywords, answer in self._CANNED:
            if any(k in q for k in keywords):
                return answer
        return self._DEFAULT


def default_llm():
    if os.environ.get("RAPPORTEUR_MODE", "demo") == "live":
        return MaxLLM()
    return DemoLLM()
