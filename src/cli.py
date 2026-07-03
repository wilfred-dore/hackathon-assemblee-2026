"""Smoke test end-to-end. Tourne SANS vraies clés (mock/dry-run).

Affiche ce qui est CÂBLÉ (config présente) vs STUBBÉ (mock), puis exécute une
question à travers le pipeline pour montrer :
- soit une réponse SOURCÉE avec citations vérifiées (liens Légifrance),
- soit un REFUS explicite (article inventé détecté, ou aucune source).

Usage :
    uv run python -m src.cli
    uv run python -m src.cli "Ai-je droit à la prime de Noël ?"
"""
from __future__ import annotations

import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import CONFIG
from .llm.client import LLMClient
from .mcp.client import moulineuse, parlement
from .pipeline import answer_question

console = Console()


def _status(ready: bool) -> str:
    return "[green]CÂBLÉ[/green]" if ready else "[yellow]STUBBÉ (mock)[/yellow]"


def wiring_report() -> None:
    t = Table(title="État du câblage", show_header=True, header_style="bold")
    t.add_column("Composant")
    t.add_column("Statut")
    t.add_column("Détail", style="dim")

    llm = LLMClient()
    t.add_row("LLM", _status(llm.ready), llm.model or "LLM démo hors-ligne")
    t.add_row("MCP Moulineuse", _status(moulineuse().ready), CONFIG.mcp_moulineuse_url or "URL vide")
    t.add_row("MCP Parlement", _status(parlement().ready), CONFIG.mcp_parlement_url or "URL vide")
    t.add_row("Canutes REST", _status(bool(CONFIG.canutes_rest_url)), CONFIG.canutes_rest_url or "URL vide")
    t.add_row("Canutes DB directe", _status(CONFIG.canutes_db_ready), "psycopg + mot de passe requis")
    console.print(t)


def main() -> None:
    question = sys.argv[1] if len(sys.argv) > 1 else "Quelle est la durée légale du travail ?"

    console.print(Panel.fit("[bold]Smoke test — IA de confiance[/bold]\nAucune vraie clé requise.", border_style="cyan"))
    wiring_report()

    console.print(f"\n[bold]Question :[/bold] {question}")
    ans = answer_question(question)

    style = "green" if ans.ok else "yellow"
    verdict = "RÉPONSE SOURCÉE" if ans.ok else "REFUS EXPLICITE"
    console.print(Panel(ans.text, title=f"[{style}]{verdict}[/{style}]", border_style=style))

    if ans.citations:
        tc = Table(title="Citations", show_header=True, header_style="bold")
        tc.add_column("Article")
        tc.add_column("Vérifié")
        tc.add_column("Lien / source", style="dim")
        for c in ans.citations:
            ok = "[green]✓[/green]" if c["exists"] else "[red]✗ introuvable[/red]"
            tc.add_row(c["label"], ok, c["url"] or c["source"])
        console.print(tc)

    if ans.detail:
        console.print(f"[dim]{ans.detail}[/dim]")
    for note in ans.validation.get("retrieval_notes", []):
        console.print(f"  [dim]· {note}[/dim]")

    console.print(
        "\n[dim]Note : hors-ligne, un LLM démo répond (dont des citations "
        "inventées volontaires). Chaque article est vérifié ; au moindre article "
        "introuvable -> REFUS. Renseigne .env pour brancher MAX/MCP réels.[/dim]"
    )


if __name__ == "__main__":
    main()
