"""
Initialization module for the specialized Deep Research sub-agent.
"""
import os
from pathlib import Path
from connectonion import Agent
from connectonion.useful_plugins import image_result_formatter
from tools.browser import BrowserAutomation
from tools.file_tools import FileTools
from tools.deep_research import perform_deep_research

_agent = None
_web = None

def _get_browser():
    """Lazy-load browser automation instance."""
    global _web
    if _web is None:
        _web = BrowserAutomation(use_chrome_profile=False, headless=True)
    return _web

def _get_agent():
    """Lazy-load the deep research agent."""
    global _agent
    if _agent is None:
        _agent = Agent(
            name="deep_researcher",
            model=os.getenv("BROWSER_AGENT_MODEL", "co/gemini-2.5-flash"),
            system_prompt=Path(__file__).parent.parent / "prompts" / "deep_research.md",
            tools=[_get_browser(), FileTools(), perform_deep_research],
            plugins=[image_result_formatter],
            max_iterations=50
        )
    return _agent

# Expose as module-level attribute for backward compatibility
class _AgentProxy:
    def __getattr__(self, name):
        return getattr(_get_agent(), name)

deep_research_agent = _AgentProxy()
