"""Build d'un site 100 % statique pour GitHub Pages (aucun backend requis).

GitHub Pages ne sert que des fichiers : impossible d'y faire tourner FastAPI.
Ce script génère `site/` en remplaçant les appels backend par des données
**pré-calculées par le vrai pipeline Python** (canned LLM + MockVerifier +
fond documentaire Légifrance) — donc fidèles, sans réimplémenter la logique en JS.

Usage : `python poc/build_static.py` -> ./site/
"""
from __future__ import annotations

import json
import shutil
import sys
import unicodedata
from pathlib import Path

POC = Path(__file__).resolve().parent
sys.path.insert(0, str(POC))  # pour importer `rapporteur` quel que soit le cwd

from rapporteur import legifrance          # noqa: E402
from rapporteur.pipeline import Rapporteur  # noqa: E402

STATIC = POC / "static"
OUT = POC.parent / "site"

# Questions de démonstration (celles proposées dans l'UI + variantes proches).
DEMO_QUESTIONS = [
    "Quelle est la durée légale du travail ?",
    "Dans quels cas puis-je être embauché en CDD ?",
    "On a publié une photo de moi sans mon accord",
    "Ai-je droit à la prime de Noël ?",
    "Mon voisin peut-il peindre sa clôture en rose ?",
]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.split())


def build_answers() -> dict:
    rapporteur = Rapporteur()
    return {_norm(q): rapporteur.answer(q) for q in DEMO_QUESTIONS}


def build_articles() -> tuple[list, dict]:
    articles = legifrance.available()
    by_key: dict[str, dict] = {}
    for a in articles:
        art = legifrance.get_article(a["label"])
        if art is None:
            continue
        payload = {
            "found": True,
            "num": art.num,
            "code": art.code,
            "text": art.text,
            "url": art.url,
            "source": art.source,
            "excerpt": art.excerpt,
        }
        aliases = {
            a["label"],
            a["label"].replace("article ", ""),
            f"{art.num} {art.code}",
            f"article {art.num} {art.code}",
        }
        for alias in aliases:
            by_key[_norm(alias)] = payload
    return articles, by_key


def render_api_js(answers: dict, articles: list, article_map: dict) -> str:
    return (
        "// GÉNÉRÉ par poc/build_static.py — NE PAS ÉDITER.\n"
        "// Moteur statique : réponses pré-calculées par le pipeline Python (canned LLM +\n"
        "// MockVerifier + fond documentaire Légifrance). Aucune logique n'est devinée côté JS.\n"
        f"const _ANSWERS = {json.dumps(answers, ensure_ascii=False)};\n"
        f"const _ARTICLES = {json.dumps(articles, ensure_ascii=False)};\n"
        f"const _ARTICLE_MAP = {json.dumps(article_map, ensure_ascii=False)};\n"
        "function _norm(s){return s.toLowerCase().normalize('NFD')"
        ".replace(/[\\u0300-\\u036f]/g,'').replace(/\\s+/g,' ').trim();}\n"
        "async function askApi(question){\n"
        "  const hit = _ANSWERS[_norm(question)];\n"
        "  if (hit) return hit;\n"
        "  return {status:'refus', answer:\"Je ne trouve pas de texte applicable.\","
        " citations:[], detail:\"Démo statique hors-ligne : essayez une question d'exemple. \"+\n"
        "    \"Le LLM souverain complet tourne côté serveur (mode live).\"};\n"
        "}\n"
        "async function articlesApi(){ return {articles:_ARTICLES}; }\n"
        "async function articleApi(ref){ return _ARTICLE_MAP[_norm(ref)] || {found:false, query:ref}; }\n"
    )


def adapt_html(html: str) -> str:
    """Réécrit les chemins absolus (routes FastAPI) en chemins statiques relatifs."""
    repl = {
        'href="/app.css"': 'href="app.css"',
        'href="/favicon.svg"': 'href="favicon.svg"',
        'src="/favicon.svg"': 'src="favicon.svg"',
        'src="/api.js"': 'src="api.js"',
        'href="/schema/"': 'href="schema/index.html"',
        'href="/demo"': 'href="demo.html"',
        'href="/sources"': 'href="sources.html"',
        'href="/details"': 'href="details.html"',
        'href="/pitch"': 'href="pitch.html"',
        'href="/"': 'href="index.html"',  # brand -> hall d'accueil
    }
    for old, new in repl.items():
        html = html.replace(old, new)
    return html


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    answers = build_answers()
    articles, article_map = build_articles()
    (OUT / "api.js").write_text(render_api_js(answers, articles, article_map), encoding="utf-8")

    for name in ("app.css", "favicon.svg", "404.html"):
        shutil.copyfile(STATIC / name, OUT / name)

    # landing.html = hall d'accueil (racine) ; index.html de François = /demo
    pages = {
        "landing.html": "index.html",
        "index.html": "demo.html",
        "sources.html": "sources.html",
        "details.html": "details.html",
        "pitch.html": "pitch.html",
    }
    for src, dst in pages.items():
        (OUT / dst).write_text(adapt_html((STATIC / src).read_text(encoding="utf-8")), encoding="utf-8")

    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    # Notre asset : cartographie du schéma Canutes (SchemaSpy + JSON/DBML) -> /schema
    schema_src = POC.parent / "schema-site"
    if schema_src.exists():
        shutil.copytree(schema_src, OUT / "schema", dirs_exist_ok=True)
        print(f"  + doc schéma copiée depuis {schema_src.name}/ -> site/schema/")

    print(f"Site statique généré dans {OUT}")
    print(f"  {len(answers)} réponses pré-calculées, {len(articles)} articles.")
    print("  Test local : python -m http.server -d site 8000")


if __name__ == "__main__":
    main()
