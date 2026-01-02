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
        
        # Initialize the sub-agent once
        # We pass the SAME web_automation instance, so it shares the browser state/window.
        # We also pass the file tools explicitly here.
        self.research_agent = Agent(
            name="deep_researcher",
            model=os.getenv("BROWSER_AGENT_MODEL", "co/gemini-2.5-flash"),
            system_prompt=Path(__file__).parent.parent / "prompts" / "deep_research.md",
            tools=[self.web, FileTools],  # Browser tools + File tools
            plugins=[image_result_formatter],
            max_iterations=50
        )

    def perform_deep_research(self, topic: str) -> str:
        """
        Conducts deep, multi-step research on a specific topic.
        
        This tool uses a specialized sub-agent that shares the browser session
        to exhaustively research the given topic, navigate multiple pages, 
        and synthesize a detailed report.

        Args:
            topic: The research goal or question (e.g. "Find top 10 marketing subreddits for AI tools")
            
        Returns:
            A comprehensive summary of the research findings.
        """
        print(f"\nLaunching Deep Research Sub-Agent for: {topic}")
        
        # Run the sub-agent (blocking)
        result = self.research_agent.input(topic)
        
        print(f"\nDeep Research Complete.")
        return result
