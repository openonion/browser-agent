"""
Browser Agent Initialization Module.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from connectonion import Agent
from connectonion.useful_plugins import image_result_formatter, ui_stream

from tools.web_automation import WebAutomation
from agents.deep_research import DeepResearch

# Load environment variables
load_dotenv()

# Initialize the web automation instance (default to headless)
web = WebAutomation(headless=True)

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