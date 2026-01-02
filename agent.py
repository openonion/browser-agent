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
from connectonion.useful_plugins import image_result_formatter, ui_stream
from tools.web_automation import WebAutomation
from agents.deep_research import DeepResearch

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

    # Create the web automation instance
    web = WebAutomation(headless=headless)
    
    # Initialize the Deep Research capability (sharing the browser)
    deep_researcher = DeepResearch(web)
    
    # Create the agent
    system_prompt_path = Path(__file__).parent / "prompts" / "agent.md"
    
    agent = Agent(
        name="browser_agent",
        model=os.getenv("BROWSER_AGENT_MODEL", "co/gemini-3-flash-preview"),
        system_prompt=system_prompt_path,
        # We pass the web instance (for direct tools) AND the deep_research method
        tools=[web, deep_researcher.perform_deep_research], 
        plugins=[image_result_formatter, ui_stream],
        max_iterations=50
    )

    # Pre-open browser for ALL tasks to ensure sub-agents have a shared session
    web.open_browser()
    if headless:
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