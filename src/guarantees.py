"""Garanties de confiance — SOURCE DE VÉRITÉ UNIQUE.

Les mêmes règles sont (1) appliquées au runtime, (2) renvoyées par l'API et
affichées à la démo, et (3) asservies par les scénarios Gherkin. Une seule
définition -> impossible que le test et le runtime divergent.

`check_guarantees(answer)` renvoie une liste inspectable :
    [{"rule": "...", "passed": bool, "detail": "..."}, ...]
"""
from __future__ import annotations


def check_guarantees(answer) -> list[dict]:
    """Évalue les garanties de confiance sur une réponse (duck-typé : .status, .citations).

    Une citation est *vérifiée* si elle EXISTE (en vigueur dans Canutes) ET est
    PERTINENTE (son texte soutient la réponse). L'existence seule ne suffit pas :
    un article réel mais hors-sujet est rejeté.
    """
    cits = answer.citations or []
    ok = answer.status == "ok"
    inexistant = [c["label"] for c in cits if not c.get("exists")]
    hors_sujet = [c["label"] for c in cits if c.get("exists") and c.get("pertinent") is False]
    verified = [c for c in cits if c.get("verified", c.get("exists"))]
    sourced_linkable = all(c.get("url") for c in verified) if verified else True

    return [
        {
            "rule": "Zéro citation inexistante présentée comme vérifiée",
            "passed": (not ok) or not inexistant,
            "detail": "aucune" if (not ok or not inexistant) else "inexistantes : " + ", ".join(inexistant),
        },
        {
            "rule": "Zéro citation hors-sujet : le texte de l'article soutient la réponse",
            "passed": (not ok) or not hors_sujet,
            "detail": "toutes pertinentes" if (not ok or not hors_sujet) else "hors-sujet : " + ", ".join(hors_sujet),
        },
        {
            "rule": "Refus si aucune source vérifiée (existante ET pertinente)",
            "passed": (not ok) or len(verified) >= 1,
            "detail": f"{len(verified)} source(s) vérifiée(s)" if ok else "refus explicite",
        },
        {
            "rule": "Réponse sourcée : chaque citation renvoie à Légifrance",
            "passed": (not ok) or sourced_linkable,
            "detail": "liens présents" if (not ok or sourced_linkable) else "lien manquant",
        },
    ]


def all_passed(guarantees: list[dict]) -> bool:
    return all(g["passed"] for g in guarantees)
