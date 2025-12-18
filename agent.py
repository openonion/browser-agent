#!/usr/bin/env python3
"""
Main CLI entry point for the browser agent using Typer and Rich.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

import typer
from rich import print
from rich.console import Console
from rich.panel import Panel

# Load environment variables
load_dotenv()

from connectonion import Agent
from connectonion.useful_plugins import image_result_formatter
from tools.web_automation import WebAutomation

app = typer.Typer(help="Natural language browser automation agent")
console = Console()

@app.command()
def run(
    prompt: str = typer.Argument(..., help="The natural language task to perform"),
    headless: bool = typer.Option(False, "--headless", help="Run browser in headless mode"),
    deep_research: bool = typer.Option(False, "--deep-research", help="Enable deep research mode with sub-agent"),
):
    """
    Run the browser agent with a natural language prompt.
    """
    console.print(Panel(f"[bold blue]Task:[/bold blue] {prompt}", title="🚀 Browser Agent Starting"))

    # Create the web automation instance
    web = WebAutomation(headless=headless)
    
    # Prepare tools
    tools = [web]

    # Handle Deep Research Mode
    if deep_research:
        from agents.deep_research import DeepResearch
        deep_research_tool = DeepResearch(web)
        tools.append(deep_research_tool)
        console.print("[yellow]🧠 Deep Research mode enabled[/yellow]")

    # Create the agent
    # Note: Adjusting path to resources relative to this file (at root)
    system_prompt_path = Path(__file__).parent / "prompts" / "browser_agent.md"
    
    agent = Agent(
        name="playwright_agent",
        model=os.getenv("BROWSER_AGENT_MODEL", "co/gemini-2.5-flash"),
        system_prompt=system_prompt_path,
        tools=tools, 
        plugins=[image_result_formatter],
        max_iterations=50
    )

    if headless:
        # Pre-initialize browser in headless mode if requested
        # The agent tools will use this existing instance
        web.open_browser()
        console.print("[dim]Browser initialized in headless mode[/dim]")

    # Run the agent
    try:
        result = agent.input(prompt)
        console.print(Panel(result, title="✅ Task Completed", border_style="green"))
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    app()