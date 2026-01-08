"""
Initialization module for the specialized Deep Research sub-agent.
"""
import os
from pathlib import Path
from connectonion import Agent
from connectonion.useful_plugins import image_result_formatter
from tools.web_automation import web
from tools.file_tools import FileTools
from tools.deep_research import perform_deep_research

# Initialize the Deep Research agent at module level
deep_research_agent = Agent(
    name="deep_researcher",
    model=os.getenv("BROWSER_AGENT_MODEL", "co/gemini-2.5-flash"),
    system_prompt=Path(__file__).parent.parent / "prompts" / "deep_research.md",
    # Added perform_deep_research as a tool so the sub-agent can also trigger research
    tools=[web, FileTools(), perform_deep_research],
    plugins=[image_result_formatter],
    max_iterations=50
)
