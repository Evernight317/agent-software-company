"""CLI entry point — run the agent software company."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

from company.llm.client import LLMClient
from company.pipeline.orchestrator import Orchestrator

app = typer.Typer(help="Agent Software Company — autonomous multi-agent development")
console = Console()


@app.command()
def run(
    requirement: str = typer.Option(..., "--requirement", "-r", help="Project requirement description"),
    name: str = typer.Option("project", "--name", "-n", help="Project name"),
):
    """Run the full development pipeline for a given requirement."""
    console.print(Panel(
        f"[bold cyan]Agent Software Company[/bold cyan]\n"
        f"Project: {name}\nRequirement: {requirement}",
        border_style="cyan",
    ))

    try:
        llm = LLMClient()
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print("\n[yellow]Please configure your .env file first.[/yellow]")
        console.print("See .env.example for reference.")
        raise typer.Exit(1)

    orchestrator = Orchestrator(llm=llm, project_name=name)
    results = orchestrator.run(requirement)

    console.print("\n[bold green]Pipeline complete![/bold green]")
    console.print(f"Artifacts: {results.get('summary', {})}")


@app.command()
def status():
    """Show current configuration status."""
    from company.llm.client import LLMConfig
    config = LLMConfig.from_env()

    console.print(Panel("[bold]Configuration Status[/bold]", border_style="cyan"))
    console.print(f"  API Key: {'✓ set' if config.api_key else '✗ not set'}")
    console.print(f"  Base URL: {config.base_url}")
    console.print(f"  Primary Model: {config.primary_model}")
    console.print(f"  Fast Model: {config.fast_model}")

    if not config.api_key:
        console.print("\n[yellow]⚠ LLM_API_KEY not configured.[/yellow]")
        console.print("Create a .env file based on .env.example")


if __name__ == "__main__":
    app()
