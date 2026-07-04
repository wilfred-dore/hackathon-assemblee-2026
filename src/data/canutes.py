"""Accès à la base Canutes.

Deux voies :
  1. PostgREST (REST filtré) via `rest_get()` — voie par défaut, juste du HTTP.
  2. Accès PostgreSQL direct via `db_query()` — OPTIONNEL, nécessite psycopg
     (`uv sync --extra db`) et CANUTES_DB_PASSWORD dans .env.

Sans config, `rest_get()` renvoie une réponse mock.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

import httpx

from ..config import CONFIG


def rest_get(table: str, params: dict | None = None) -> Any:
    """GET filtré sur PostgREST. Ex : rest_get("lois", {"annee": "eq.2025"})."""
    if not CONFIG.canutes_rest_url:
        return {"_mock": True, "table": table, "params": params or {}}

    url = CONFIG.canutes_rest_url.rstrip("/") + "/" + table.lstrip("/")
    with httpx.Client(timeout=30) as client:
        r = client.get(url, params=params or {})
        r.raise_for_status()
        return r.json()


def db_query(sql: str, args: tuple = ()) -> list[tuple]:
    """Requête SQL directe (optionnel). Nécessite psycopg + mot de passe DB.

    TODO : n'utiliser que si l'accès REST ne suffit pas (jointures lourdes...).
    """
    if not CONFIG.canutes_db_ready:
        raise RuntimeError(
            "Accès DB direct non configuré : renseigne CANUTES_DB_* dans .env "
            "et installe psycopg (`uv sync --extra db`)."
        )
    try:
        import psycopg
    except ImportError as e:
        raise RuntimeError("psycopg absent — lance `uv sync --extra db`.") from e

    dsn = (
        f"host={CONFIG.canutes_db_host} port={CONFIG.canutes_db_port} "
        f"user={CONFIG.canutes_db_user} password={CONFIG.canutes_db_password} "
        f"dbname={CONFIG.canutes_db_name} connect_timeout=15"
    )
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall()


# --- Vérification d'article Légifrance (table legifrance.article) -----------

def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", _strip_accents(s).lower()).strip()


def verify_article(num: str, code: str) -> dict:
    """Vérifie qu'un article existe dans un code donné, via Canutes (legifrance.article).

    Stratégie : num normalisé (SQL) + nom du code présent dans le JSON de l'article
    (ILIKE) + on préfère la version EN VIGUEUR. Renvoie l'ID LEGIARTI réel (→ URL
    Légifrance) et un extrait. `exists=False` si aucun match code n'est trouvé.
    """
    # Variantes exactes de `num` (index-friendly) plutôt qu'un regexp sur toute
    # la table (scan complet -> statement timeout). Légifrance encode ex.
    # "L3121-27" ou "L. 3121-27".
    compact = re.sub(r"\s+", "", num.strip())        # "L.3121-27"
    nodot = compact.replace(".", "")                  # "L3121-27"
    variants = {num.strip(), compact, nodot}
    m = re.match(r"^([LRD])\.?\s*(.+)$", nodot, re.I)
    if m:
        letter, rest = m.group(1).upper(), m.group(2)
        variants |= {f"{letter}{rest}", f"{letter}. {rest}", f"{letter}.{rest}"}
    like = f"%{code.strip()}%"
    rows = db_query(
        "select id, num, data from legifrance.article "
        "where num = any(%s) and data::text ilike %s limit 200",
        (list(variants), like),
    )
    nc = _norm(code)
    candidates = []  # (etat, id, data)
    for id_, _rnum, data in rows:
        etat = (
            data.get("META", {}).get("META_SPEC", {}).get("META_ARTICLE", {}).get("ETAT")
        )
        # double-check accent-insensible côté Python (ILIKE ne gère pas les accents)
        import json as _json
        if nc in _norm(_json.dumps(data, ensure_ascii=False)):
            candidates.append((etat, id_, data))

    if not candidates:
        return {"exists": False, "etat": None, "id": None, "url": None, "excerpt": None}

    vigueur = [c for c in candidates if c[0] == "VIGUEUR"]
    etat, id_, data = (vigueur or candidates)[0]
    contenu = (data.get("BLOC_TEXTUEL", {}) or {}).get("CONTENU", "") or ""
    excerpt = re.sub(r"<[^>]+>", " ", contenu)
    excerpt = re.sub(r"\s+", " ", excerpt).strip()[:1200] or None
    return {
        "exists": True,
        "etat": etat,
        "id": id_,
        "url": f"https://www.legifrance.gouv.fr/codes/article_lc/{id_}",
        "excerpt": excerpt,
    }
