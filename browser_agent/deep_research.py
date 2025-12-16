"""
Purpose: Specialized deep research capability spawning a sub-agent
LLM-Note:
  Dependencies: imports from [typing, pathlib, connectonion.Agent, connectonion.useful_plugins.image_result_formatter, web_automation.WebAutomation] | imported by [agent.py]
  Data flow: perform_deep_research(topic) ">→" spawns new Agent("deep_researcher") ">→" shares EXISTING WebAutomation instance ">→" sub-agent executes browser tools ">→" returns summarized research
  State/Effects: REUSES parent agent's browser window/session (critical for efficiency) | navigates independently within that window
"""

from typing import Optional
import os
from pathlib import Path
from connectonion import Agent
from connectonion.useful_plugins import image_result_formatter
from .web_automation import WebAutomation


class DeepResearch:
    """
    A tool that allows the agent to spawn a sub-agent for deep research tasks.
    This helps in breaking down complex research goals into manageable sub-tasks.
    """

    def __init__(self, web_automation: WebAutomation):
        self.web = web_automation

    def perform_deep_research(self, topic: str) -> str:
        """
        Conducts deep, multi-step research on a specific topic.
        
        This tool spawns a specialized sub-agent that will take control of the browser
        to exhaustively research the given topic, navigate multiple pages, 
        and synthesize a detailed report.

        Args:
            topic: The research goal or question (e.g. "Find top 10 marketing subreddits for AI tools")
            
        Returns:
            A comprehensive summary of the research findings.
        """
        print(f"\nLaunching Deep Research Sub-Agent for: {topic}")
        
        # Initialize the sub-agent
        # We pass the SAME web_automation instance, so it shares the browser state/window.
        researcher = Agent(
            name="deep_researcher",
            model=os.getenv("BROWSER_AGENT_MODEL", "co/gemini-2.5-flash"),
            system_prompt=Path(__file__).parent / "resources" / "deep_research_prompt.md",
            tools=self.web,  # Share the browser tools
            plugins=[image_result_formatter],
            max_iterations=50  # Give it plenty of steps to browse around
        )

        # Run the sub-agent
        # This blocks until the researcher is done
        result = researcher.input(topic)
        
        print(f"\nDeep Research Complete.")
        return result
