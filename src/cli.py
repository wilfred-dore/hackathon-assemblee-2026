"""Smoke test end-to-end. Tourne SANS vraies clés (mock/dry-run).

Affiche clairement ce qui est CÂBLÉ (config présente) vs STUBBÉ (mock), puis
exécute une question à travers le pipeline pour montrer le comportement de
refus quand il n'y a pas de source.

Usage :
    uv run python -m src.cli
    uv run python -m src.cli "Ma question juridique ?"
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
    t.add_row("LLM", _status(llm.ready), llm.model or "LLM_MODEL vide")
    t.add_row("MCP Moulineuse", _status(moulineuse().ready), CONFIG.mcp_moulineuse_url or "URL vide")
    t.add_row("MCP Parlement", _status(parlement().ready), CONFIG.mcp_parlement_url or "URL vide")
    t.add_row("Canutes REST", _status(bool(CONFIG.canutes_rest_url)), CONFIG.canutes_rest_url or "URL vide")
    t.add_row("Canutes DB directe", _status(CONFIG.canutes_db_ready), "psycopg + mot de passe requis")
    console.print(t)


def main() -> None:
    question = sys.argv[1] if len(sys.argv) > 1 else "Quelles sont les conditions d'application de cette loi ?"

    console.print(Panel.fit("[bold]Smoke test — IA de confiance[/bold]\nAucune vraie clé requise.", border_style="cyan"))
    wiring_report()

    console.print(f"\n[bold]Question :[/bold] {question}")
    ans = answer_question(question)

    style = "green" if ans.ok else "yellow"
    verdict = "RÉPONSE SOURCÉE" if ans.ok else "REFUS (pas de source)"
    console.print(Panel(ans.text, title=f"[{style}]{verdict}[/{style}]", border_style=style))

    console.print("[bold]Sources :[/bold]", f"{len(ans.sources)} trouvée(s)")
    console.print("[bold]Validation :[/bold]", ans.validation)

    console.print(
        "\n[dim]Note : en mock, retrieve() ne ramène aucune source -> le pipeline "
        "REFUSE. C'est le comportement de confiance attendu. Renseigne .env pour "
        "câbler les vraies sources.[/dim]"
    )


if __name__ == "__main__":
    main()
