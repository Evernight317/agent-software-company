"""CLI entry point — run the agent software company."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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

    _print_results(results)


@app.command()
def plan(
    requirement: str = typer.Option(..., "--requirement", "-r", help="Project requirement description"),
    name: str = typer.Option("project", "--name", "-n", help="Project name"),
):
    """Run PM + Architect only — generate PRD and design (Phase 1-2)."""
    console.print(Panel(
        f"[bold cyan]Agent Software Company — Planning[/bold cyan]\n"
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
    results = orchestrator.run_phases_1_2(requirement)

    _print_results(results)


@app.command()
def status():
    """Show current configuration status."""
    from company.llm.client import LLMConfig
    config = LLMConfig.from_env()

    console.print(Panel("[bold]Configuration Status[/bold]", border_style="cyan"))

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Setting")
    table.add_column("Value")
    table.add_row("API Key", "[green]✓ set[/green]" if config.api_key else "[red]✗ not set[/red]")
    table.add_row("Base URL", config.base_url)
    table.add_row("Primary Model", config.primary_model)
    table.add_row("Fast Model", config.fast_model)
    table.add_row("Temperature", str(config.temperature))
    console.print(table)

    if not config.api_key:
        console.print("\n[yellow]⚠ LLM_API_KEY not configured.[/yellow]")
        console.print("Create a .env file based on .env.example")


def _print_results(results: dict) -> None:
    """Print pipeline results summary."""
    console.print()
    console.print(Panel("[bold green]Pipeline Results[/bold green]", border_style="green"))

    summary = results.get("summary", {})
    if summary:
        table = Table(show_header=True, header_style="bold cyan", title="Summary")
        table.add_column("Metric")
        table.add_column("Value", justify="right")
        for key, value in summary.items():
            if isinstance(value, dict):
                value = ", ".join(f"{k}={v}" for k, v in value.items())
            table.add_row(key.replace("_", " ").title(), str(value))
        console.print(table)

    artifacts = summary.get("artifacts", {})
    if artifacts:
        console.print("\n[bold]Artifacts Generated:[/bold]")
        for atype, count in artifacts.items():
            if count:
                console.print(f"  • {atype}: {count}")


if __name__ == "__main__":
    app()
