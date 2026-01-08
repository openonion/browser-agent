#!/usr/bin/env python3
"""
Main CLI entry point for the browser agent using Typer and Rich.
"""
import sys
import typer
from rich.console import Console
from rich.panel import Panel
from agent import agent, web

app = typer.Typer(help="Natural language browser automation agent")
console = Console()

@app.command()
def run(
    prompt: str = typer.Argument(..., help="The natural language task to perform"),
    headless: bool = typer.Option(False, "--headless", help="Run browser in headless mode"),
):
    """
    Run the browser agent with a natural language prompt.
    """
    console.print(Panel(f"[bold blue]Task:[/bold blue] {prompt}", title="🚀 Browser Agent Starting"))

    # Pre-open browser for ALL tasks to ensure sub-agents have a shared session
    web.open_browser(headless=headless)
    if headless:
        console.print("[dim]Browser initialized in headless mode[/dim]")

    # Run the agent
    result = agent.input(prompt)
    console.print(Panel(result, title="✅ Task Completed", border_style="green"))

if __name__ == "__main__":
    app()