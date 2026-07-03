"""Accès à la base Canutes.

Deux voies :
  1. PostgREST (REST filtré) via `rest_get()` — voie par défaut, juste du HTTP.
  2. Accès PostgreSQL direct via `db_query()` — OPTIONNEL, nécessite psycopg
     (`uv sync --extra db`) et CANUTES_DB_PASSWORD dans .env.

Sans config, `rest_get()` renvoie une réponse mock.
"""
from __future__ import annotations

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
        f"dbname={CONFIG.canutes_db_user}"
    )
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall()
