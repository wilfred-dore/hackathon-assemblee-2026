"""API HTTP du Rapporteur (FastAPI) + interface de démo."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .pipeline import Rapporteur

app = FastAPI(title="Le Rapporteur", version="0.1.0")
_rapporteur = Rapporteur()
_STATIC = Path(__file__).resolve().parent.parent / "static"


class Question(BaseModel):
    question: str


@app.post("/api/ask")
def ask(q: Question) -> dict:
    return _rapporteur.answer(q.question)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC / "index.html")
