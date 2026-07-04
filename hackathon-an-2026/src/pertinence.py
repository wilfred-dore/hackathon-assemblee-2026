"""Vérification de PERTINENCE d'une citation.

Exister ne suffit pas : un article réel mais hors-sujet (p. ex. citer L. 3121-1
« champ d'application » au lieu de L. 3121-27 « durée légale ») est une
hallucination que la vérification d'EXISTENCE laisse passer — avec, pire, un vrai
lien Légifrance qui la rend crédible.

On vérifie donc que le **texte officiel de l'article** (récupéré dans Canutes)
soutient réellement la question posée. Deux voies :
  - ancrée LLM (live) : un vérificateur lit le texte réel et répond OUI/NON ;
  - déterministe (hors-ligne) : recouvrement lexical texte-article / question.

Si on n'a pas le texte de l'article (vérificateur mock sans extrait), on ne peut
pas juger la pertinence -> on retombe sur l'existence seule (pertinent=True).
"""
from __future__ import annotations

import re
import unicodedata

_PERT_PROMPT = (
    "Tu es un vérificateur juridique STRICT. Voici le texte officiel d'un article "
    "de loi français :\n---\n{excerpt}\n---\n"
    "La question d'un citoyen était : « {question} »\n\n"
    "Ce texte d'article traite-t-il RÉELLEMENT du sujet de la question et peut-il "
    "servir de fondement à la réponse ? Un article qui existe mais parle d'autre "
    "chose doit être rejeté. Réponds STRICTEMENT par un seul mot : OUI ou NON."
)

# mots vides à ignorer dans le recouvrement lexical
_STOP = {
    "quelle", "quel", "quels", "quelles", "cite", "citez", "article", "code",
    "france", "droit", "legal", "legale", "phrase", "reponds", "quelle", "cas",
    "dans", "pour", "avec", "sans", "leur", "leurs", "elle", "elles", "être",
    "sont", "doit", "doivent", "peut", "peuvent", "combien", "quelles",
}


def _toks(s: str) -> set[str]:
    s = "".join(
        c for c in unicodedata.normalize("NFD", (s or "").lower())
        if unicodedata.category(c) != "Mn"
    )
    return {w for w in re.findall(r"[a-z]{4,}", s) if w not in _STOP}


def lexical_pertinent(question: str, excerpt: str, threshold: float = 0.20) -> bool:
    """Recouvrement des mots-clés de la question présents dans le texte de l'article."""
    q, e = _toks(question), _toks(excerpt)
    if not q or not e:
        return False
    return (len(q & e) / len(q)) >= threshold


def check_pertinence(question: str, excerpt: str | None, llm=None) -> bool:
    """True si le texte de l'article soutient la question. Sans texte -> True
    (on ne peut pas juger, on ne bloque pas sur la seule existence)."""
    if not excerpt:
        return True  # pas de texte -> pas de jugement de pertinence possible
    if llm is not None and getattr(llm, "live", False):
        try:
            out = llm.chat(
                [{"role": "user", "content": _PERT_PROMPT.format(
                    excerpt=excerpt[:1500], question=question)}],
                temperature=0.0,
            )
            return out.strip().lower().startswith("oui")
        except Exception:
            # fail-closed côté confiance : si le vérificateur échoue, on retombe
            # sur le lexical plutôt que d'accepter aveuglément.
            return lexical_pertinent(question, excerpt)
    return lexical_pertinent(question, excerpt)
