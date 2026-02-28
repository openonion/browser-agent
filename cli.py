#!/usr/bin/env python3
"""
Main CLI entry point for the browser agent using Typer and Rich.
"""
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from agent import create_agent, web

app = typer.Typer(help="Natural language browser automation agent")
console = Console()
EXIT_COMMANDS = {"exit", "quit", "q"}


def _ensure_browser(headless: bool) -> None:
    if web.page is not None:
        return

    web.open_browser(headless=headless)
    if headless:
        console.print("[dim]Browser initialized in headless mode[/dim]")


def _run_prompt(prompt: str) -> None:
    console.print(Panel(f"[bold blue]Task:[/bold blue] {prompt}", title="🚀 Browser Agent Starting"))
    agent = create_agent()
    result = agent.input(prompt)
    console.print(Panel(result, title="✅ Task Completed", border_style="green"))


def _interactive_loop(headless: bool) -> None:
    console.print(
        Panel(
            "Type a task and press Enter. Type 'exit' to quit.",
            title="Interactive Mode",
            border_style="cyan",
        )
    )

    while True:
        try:
            prompt = Prompt.ask("[bold blue]task[/bold blue]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Exiting interactive mode[/dim]")
            break

        if not prompt:
            continue
        if prompt.lower() in EXIT_COMMANDS:
            console.print("[dim]Goodbye[/dim]")
            break

        _ensure_browser(headless=headless)
        _run_prompt(prompt)

@app.command()
def run(
    prompt: Optional[str] = typer.Argument(None, help="The natural language task to perform"),
    headless: bool = typer.Option(False, "--headless", help="Run browser in headless mode"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Start an interactive session"),
):
    """
    Run the browser agent with a natural language prompt or interactive session.
    """
    if prompt is None and not interactive:
        raise typer.BadParameter("Provide a prompt or use --interactive.")

    if prompt:
        # Pre-open browser for ALL tasks to ensure sub-agents have a shared session
        _ensure_browser(headless=headless)
        _run_prompt(prompt)

    if interactive:
        _interactive_loop(headless=headless)


@app.command()
def interactive(
    headless: bool = typer.Option(False, "--headless", help="Run browser in headless mode"),
):
    """
    Start an interactive chat session.
    """
    _interactive_loop(headless=headless)

if __name__ == "__main__":
    app()
