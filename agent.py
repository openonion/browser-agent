"""
Browser Agent Initialization Module.
"""
import os
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv
from connectonion import Agent
from connectonion.useful_plugins import image_result_formatter, ui_stream

from tools.web_automation import WebAutomation
from agents.deep_research import DeepResearch

# Load environment variables
load_dotenv()

def create_agent(headless: bool = False) -> Tuple[Agent, WebAutomation]:
    """
    Initialize and return the browser agent and web automation instance.

    Args:
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        Tuple[Agent, WebAutomation]: The configured agent and web instance.
    """
    # Create the web automation instance
    web = WebAutomation(headless=headless)
    
    # Initialize the Deep Research capability (sharing the browser)
    deep_researcher = DeepResearch(web)
    
    # Create the agent
    system_prompt_path = Path(__file__).parent / "prompts" / "agent.md"
    
    agent = Agent(
        name="browser_agent",
        model=os.getenv("BROWSER_AGENT_MODEL", "co/gemini-2.5-flash"),
        system_prompt=system_prompt_path,
        # We pass the web instance (for direct tools) AND the deep_research method
        tools=[web, deep_researcher.perform_deep_research], 
        plugins=[image_result_formatter, ui_stream],
        max_iterations=50
    )
    
    return agent, web

# Create a default instance for main.py (hosting)
agent, _ = create_agent(headless=True)
