"""Chargement centralisé de la config depuis .env (jamais de secret en dur)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()  # charge .env s'il existe ; sinon on reste en mode mock


def _get(key: str) -> str | None:
    val = os.environ.get(key, "").strip()
    return val or None


@dataclass(frozen=True)
class Config:
    # LLM
    llm_base_url: str | None = _get("LLM_BASE_URL")
    llm_api_key: str | None = _get("LLM_API_KEY")
    llm_model: str | None = _get("LLM_MODEL")
    # MCP
    mcp_moulineuse_url: str | None = _get("MCP_MOULINEUSE_URL")
    mcp_parlement_url: str | None = _get("MCP_PARLEMENT_URL")
    mcp_token: str | None = _get("MCP_TOKEN")
    # Canutes
    canutes_rest_url: str | None = _get("CANUTES_REST_URL")
    canutes_db_host: str | None = _get("CANUTES_DB_HOST")
    canutes_db_port: str | None = _get("CANUTES_DB_PORT")
    canutes_db_user: str | None = _get("CANUTES_DB_USER")
    canutes_db_password: str | None = _get("CANUTES_DB_PASSWORD")

    @property
    def llm_ready(self) -> bool:
        return bool(self.llm_base_url and self.llm_api_key and self.llm_model)

    @property
    def canutes_db_ready(self) -> bool:
        return bool(self.canutes_db_host and self.canutes_db_password)


CONFIG = Config()
