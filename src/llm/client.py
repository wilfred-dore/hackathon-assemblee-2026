"""Wrapper LLM OpenAI-compatible.

Base URL / clé / modèle lus dans .env. Facilement swappable entre le backend
principal (Mistral via Modular MAX sur AMD) et le fallback (playground Qualcomm) :
il suffit de changer LLM_BASE_URL / LLM_API_KEY / LLM_MODEL.

Sans clé configurée, `chat()` renvoie une réponse mock déterministe pour que le
smoke test tourne hors-ligne.
"""
from __future__ import annotations

from ..config import CONFIG


class LLMClient:
    def __init__(self, base_url=None, api_key=None, model=None):
        self.base_url = base_url or CONFIG.llm_base_url
        self.api_key = api_key or CONFIG.llm_api_key
        self.model = model or CONFIG.llm_model
        self._client = None

    @property
    def ready(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)

    def _ensure_client(self):
        if self._client is None:
            from openai import OpenAI  # import paresseux

            self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        return self._client

    def chat(self, messages: list[dict], temperature: float = 0.0) -> str:
        """Renvoie le texte de la réponse. Mode mock si non configuré."""
        if not self.ready:
            last = messages[-1]["content"] if messages else ""
            return f"[MOCK LLM] (aucune clé LLM configurée) — reçu : {last[:120]}"

        resp = self._ensure_client().chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""
