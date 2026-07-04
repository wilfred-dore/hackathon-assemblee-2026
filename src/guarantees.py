"""Garanties de confiance — SOURCE DE VÉRITÉ UNIQUE.

Les mêmes règles sont (1) appliquées au runtime, (2) renvoyées par l'API et
affichées à la démo, et (3) asservies par les scénarios Gherkin. Une seule
définition -> impossible que le test et le runtime divergent.

`check_guarantees(answer)` renvoie une liste inspectable :
    [{"rule": "...", "passed": bool, "detail": "..."}, ...]
"""
from __future__ import annotations


def check_guarantees(answer) -> list[dict]:
    """Évalue les garanties de confiance sur une réponse (duck-typé : .status, .citations)."""
    cits = answer.citations or []
    ok = answer.status == "ok"
    invented = [c["label"] for c in cits if not c["exists"]]
    verified = [c for c in cits if c["exists"]]
    sourced_linkable = all(c.get("url") for c in cits) if cits else True

    return [
        {
            "rule": "Zéro citation inventée présentée comme vérifiée",
            "passed": (not ok) or not invented,
            "detail": "aucune" if (not ok or not invented) else "inventées : " + ", ".join(invented),
        },
        {
            "rule": "Refus si aucune source vérifiable",
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
