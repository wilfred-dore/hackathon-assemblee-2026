"""Micro-benchmark d'inférence, vendor-agnostique.

Tape le backend LLM configuré dans .env (MODE=live) avec un jeu de prompts, et
mesure **latence** et **débit (tokens/s)**. Sert à comparer les backends
souverains (Qualcomm Cloud AI 100, AMD/MAX, NVIDIA/MAX) : on relance le même
script en pointant `LLM_BASE_URL` ailleurs.

⚠️ Les **watts** ne sont pas mesurables via un endpoint OpenAI-compatible : pour
l'énergie, citer les specs constructeur / l'étude UCSD (arXiv 2507.00418).

Usage :
    MODE=live uv run python -m src.bench                 # backend du .env
    MODE=live uv run python -m src.bench --label "AMD MI300X · Mistral-7B"
    MODE=live uv run python -m src.bench --runs 5
"""
from __future__ import annotations

import argparse
import statistics
import sys

from rich.console import Console
from rich.table import Table

from .llm.client import LLMClient

console = Console()

PROMPTS = [
    "Quelle est la durée légale du travail en France ? Cite l'article.",
    "Dans quels cas peut-on conclure un CDD ?",
    "Ai-je droit à la prime de Noël ?",
    "Que dit le Code civil sur le respect de la vie privée ?",
    "Un licenciement doit-il être motivé ?",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default=None, help="nom du backend (sinon host/modèle)")
    ap.add_argument("--runs", type=int, default=3, help="répétitions par prompt (médiane)")
    args = ap.parse_args()

    llm = LLMClient()
    if not llm.live:
        console.print("[red]Backend non actif.[/red] Lance avec MODE=live et LLM_* renseignés dans .env.")
        sys.exit(1)

    host = (llm.base_url or "").split("//")[-1].split("/")[0]
    label = args.label or f"{host} · {llm.model}"
    console.print(f"[bold]Benchmark[/bold] : {label}  ({args.runs} run(s)/prompt)\n")

    t = Table(show_header=True, header_style="bold")
    t.add_column("Prompt", style="dim", max_width=42)
    t.add_column("Latence (s)", justify="right")
    t.add_column("tokens", justify="right")
    t.add_column("tok/s", justify="right")

    lat_all: list[float] = []
    tps_all: list[float] = []
    for p in PROMPTS:
        lats, tpss, toks = [], [], []
        for _ in range(args.runs):
            llm.complete(p)
            m = llm.last_metrics or {}
            if m.get("latency_s"):
                lats.append(m["latency_s"])
            if m.get("tokens_per_s"):
                tpss.append(m["tokens_per_s"])
            if m.get("completion_tokens"):
                toks.append(m["completion_tokens"])
        lat = statistics.median(lats) if lats else 0.0
        tps = statistics.median(tpss) if tpss else 0.0
        tok = statistics.median(toks) if toks else 0
        lat_all.append(lat); tps_all.append(tps)
        t.add_row(p, f"{lat:.2f}", f"{int(tok)}", f"{tps:.1f}")

    console.print(t)
    if lat_all:
        console.print(
            f"\n[bold]Médianes[/bold] — latence : {statistics.median(lat_all):.2f} s · "
            f"débit : {statistics.median(tps_all):.1f} tok/s"
        )
    console.print("[dim]Énergie (W) non mesurable ici -> citer specs constructeur / étude UCSD.[/dim]")


if __name__ == "__main__":
    main()
