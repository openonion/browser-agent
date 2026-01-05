"""
Purpose: Specialized deep research capability spawning a sub-agent
LLM-Note:
  Dependencies: imports from [typing, pathlib, connectonion.Agent, connectonion.useful_plugins.image_result_formatter, tools.web_automation.WebAutomation] | imported by [agent.py]
  Data flow: perform_deep_research(topic) ">→" spawns new Agent("deep_researcher") ">→" shares EXISTING WebAutomation instance ">→" sub-agent executes browser tools ">→" returns summarized research
  State/Effects: REUSES parent agent's browser window/session (critical for efficiency) | navigates independently within that window
"""

from typing import Optional
import os
from pathlib import Path
from connectonion import Agent, xray
from connectonion.useful_plugins import image_result_formatter
from tools.web_automation import WebAutomation
from tools.file_tools import FileTools


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
        
        This tool uses a specialized sub-agent that shares the browser session
        to exhaustively research the given topic, navigate multiple pages, 
        and synthesize a detailed report.

        Args:
            topic: The full research request or question.
            
        Returns:
            A comprehensive summary of the research findings.
        """
        # Ensure a clean slate for the new research task
        self._cleanup_files()

        # Initialize the sub-agent for this specific task to ensure fresh context/memory
        # We pass the SAME web_automation instance, so it shares the browser state/window.
        research_agent = Agent(
            name="deep_researcher",
            model=os.getenv("BROWSER_AGENT_MODEL", "co/gemini-2.5-flash"),
            system_prompt=Path(__file__).parent.parent / "prompts" / "deep_research.md",
            tools=[self.web, FileTools()],
            plugins=[image_result_formatter],
            max_iterations=50
        )

        print(f"\nLaunching Deep Research Sub-Agent for: {topic}")
        
        # Run the sub-agent (blocking)
        result = research_agent.input(topic)
        
        # Safety cleanup: Ensure notes are deleted even if the agent forgot
        if os.path.exists("research_notes.md"):
            try:
                os.remove("research_notes.md")
            except OSError:
                pass

        print(f"\nDeep Research Complete.")
        return result

    def _cleanup_files(self):
        """Clean up previous research artifacts to prevent context leakage."""
        for filename in ["research_notes.md", "research_results.md"]:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except OSError:
                    pass
