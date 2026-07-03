"""Extraction des citations juridiques d'un texte libre.

Le LLM répond en français naturel (« ... article L. 3121-27 du Code du
travail »). On en extrait des `Citation` normalisées, vérifiables ensuite
contre les sources (voir [src/verify.py]). Origine : POC « Le Rapporteur ».
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import quote_plus

# « article L. 4321-7 du Code du travail », « l'article 9 du Code civil »,
# « article R. 123-4 du code de commerce »…
_CITATION_RE = re.compile(
    r"article\s+"
    r"(?P<num>(?:[LRD]\.?\s*)?\d+(?:-\d+)*)"
    r"\s+du\s+"
    r"(?P<code>[Cc]ode(?:\s+(?:de\s+la|de\s+l['’]|du|des|de))?\s+[\w'’àâäéèêëîïôöùûüç-]+(?:\s+[\w'’àâäéèêëîïôöùûüç-]+)*?)"
    r"(?=[.,;:!?)»\n]|\s+(?:et|ou|qui|que|dont|,)\s|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Citation:
    """Une référence à un article de code, telle que citée par le modèle."""

    num: str      # ex. « L. 4321-7 »
    code: str     # ex. « Code du travail »
    raw: str      # texte exact trouvé

    @property
    def key(self) -> str:
        """Clé normalisée pour comparaison : « l4321-7|code du travail »."""
        num = re.sub(r"[.\s]", "", self.num).lower()
        code = _strip_accents(self.code.lower())
        code = re.sub(r"[’']", "'", code)
        code = re.sub(r"\s+", " ", code).strip()
        return f"{num}|{code}"

    @property
    def label(self) -> str:
        return f"article {self.num} du {self.code}"

    @property
    def legifrance_url(self) -> str:
        return (
            "https://www.legifrance.gouv.fr/search/all?query="
            + quote_plus(f"article {self.num} {self.code}")
        )


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def extract_citations(text: str) -> list[Citation]:
    """Extrait toutes les citations d'articles de codes du texte (dédupliquées)."""
    seen: set[str] = set()
    citations: list[Citation] = []
    for m in _CITATION_RE.finditer(text):
        citation = Citation(num=m.group("num").strip(), code=m.group("code").strip(), raw=m.group(0))
        if citation.key not in seen:
            seen.add(citation.key)
            citations.append(citation)
    return citations
