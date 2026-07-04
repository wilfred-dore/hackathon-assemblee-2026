"""Chargement du texte des articles depuis Légifrance (ou fond documentaire local).

En mode « live » (variables LEGIFRANCE_API_URL + LEGIFRANCE_TOKEN présentes),
on interroge l'API Légifrance (PISTE). Sinon — et pour la démo hors-ligne — on
sert le texte depuis un **fond documentaire local** : des articles réellement en
vigueur, recopiés verbatim depuis Légifrance (les textes légaux français sont
librement réutilisables). Rien n'est reformulé par l'IA.

Fail-closed : référence inconnue -> None (la page affiche « introuvable »).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import quote_plus

from .citations import extract_citations


@dataclass
class Article:
    num: str
    code: str
    text: str
    url: str
    source: str            # « Légifrance (live) » | « fond documentaire local (démo) »
    excerpt: bool = False   # True si le texte affiché est un extrait


# Fond documentaire local — articles EN VIGUEUR, verbatim Légifrance.
# Clé = Citation.key (numéro normalisé | code normalisé).
_FONDS: dict[str, dict] = {
    "l3121-27|code du travail": {
        "num": "L. 3121-27",
        "code": "Code du travail",
        "text": "La durée légale du travail effectif des salariés est fixée à trente-cinq heures par semaine.",
    },
    "l1242-2|code du travail": {
        "num": "L. 1242-2",
        "code": "Code du travail",
        "excerpt": True,
        "text": (
            "Sous réserve des dispositions de l'article L. 1242-3, un contrat de travail à "
            "durée déterminée ne peut être conclu que pour l'exécution d'une tâche précise "
            "et temporaire, et seulement dans les cas suivants :\n\n"
            "1° Remplacement d'un salarié en cas d'absence, de passage provisoire à temps "
            "partiel, de suspension de son contrat de travail […] ;\n"
            "2° Accroissement temporaire de l'activité de l'entreprise ;\n"
            "3° Emplois à caractère saisonnier ou pour lesquels, dans certains secteurs "
            "d'activité définis par décret ou par convention ou accord collectif de travail "
            "étendu, il est d'usage constant de ne pas recourir au contrat de travail à durée "
            "indéterminée en raison de la nature de l'activité exercée […]."
        ),
    },
    "l1232-1|code du travail": {
        "num": "L. 1232-1",
        "code": "Code du travail",
        "text": (
            "Tout licenciement pour motif personnel est motivé dans les conditions définies "
            "par le présent chapitre.\n\nIl est justifié par une cause réelle et sérieuse."
        ),
    },
    "9|code civil": {
        "num": "9",
        "code": "Code civil",
        "text": (
            "Chacun a droit au respect de sa vie privée.\n\n"
            "Les juges peuvent, sans préjudice de la réparation du dommage subi, prescrire "
            "toutes mesures, telles que séquestre, saisie et autres, propres à empêcher ou "
            "faire cesser une atteinte à l'intimité de la vie privée : ces mesures peuvent, "
            "s'il y a urgence, être ordonnées en référé."
        ),
    },
    "1240|code civil": {
        "num": "1240",
        "code": "Code civil",
        "text": (
            "Tout fait quelconque de l'homme, qui cause à autrui un dommage, oblige celui "
            "par la faute duquel il est arrivé à le réparer."
        ),
    },
    "l121-1|code de la consommation": {
        "num": "L. 121-1",
        "code": "Code de la consommation",
        "excerpt": True,
        "text": (
            "Les pratiques commerciales déloyales sont interdites.\n\n"
            "Une pratique commerciale est déloyale lorsqu'elle est contraire aux exigences "
            "de la diligence professionnelle et qu'elle altère ou est susceptible d'altérer "
            "de manière substantielle le comportement économique du consommateur normalement "
            "informé et raisonnablement attentif et avisé, à l'égard d'un bien ou d'un service."
        ),
    },
}


def _legifrance_url(num: str, code: str) -> str:
    return "https://www.legifrance.gouv.fr/search/all?query=" + quote_plus(f"article {num} {code}")


def available() -> list[dict]:
    """Liste des articles consultables (pour la page /sources)."""
    return [
        {"num": v["num"], "code": v["code"], "label": f"article {v['num']} du {v['code']}"}
        for v in _FONDS.values()
    ]


def _live_enabled() -> bool:
    return bool(os.environ.get("LEGIFRANCE_API_URL") and os.environ.get("LEGIFRANCE_TOKEN"))


def _fetch_live(citation) -> Article | None:
    """Appel réel à l'API Légifrance (PISTE). Non câblé en démo — on ne devine
    pas le schéma exact (cf. CLAUDE.md) ; à brancher sur place. Fail-closed."""
    return None


def get_article(reference: str) -> Article | None:
    """Résout une référence libre (« article L. 3121-27 du Code du travail ») en
    texte d'article. Live d'abord si configuré, sinon fond documentaire local."""
    ref = reference.strip()
    text = ref if ref.lower().startswith("article") else f"article {ref}"
    cites = extract_citations(text)
    if not cites:
        return None
    citation = cites[0]

    if _live_enabled():
        art = _fetch_live(citation)
        if art:
            return art

    data = _FONDS.get(citation.key)
    if not data:
        return None
    return Article(
        num=data["num"],
        code=data["code"],
        text=data["text"],
        url=_legifrance_url(data["num"], data["code"]),
        source="fond documentaire local (démo)",
        excerpt=data.get("excerpt", False),
    )
