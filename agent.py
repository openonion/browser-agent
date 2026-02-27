"""
Browser Agent Initialization Module.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from connectonion import Agent
from connectonion.useful_plugins import image_result_formatter, ui_stream

from tools.browser import web
from tools.deep_research import perform_deep_research

# Load environment variables
load_dotenv()

def create_agent():
    """Create a fresh browser agent instance.

    Returns a new Agent instance for each request to ensure proper isolation.
    Used by host() to create agents per request.
    """
    system_prompt_path = Path(__file__).parent / "prompts" / "agent.md"

    return Agent(
        name="browser_agent",
        model="co/gemini-2.5-pro",
        system_prompt=system_prompt_path,
        tools=[web, perform_deep_research],
        plugins=[image_result_formatter, ui_stream],
        max_iterations=200
    )

if __name__ == "__main__":
    agent = create_agent()
    agent.input("""pls use this user name and passwd to login nsw.gov.au aaronplus1996@gmail.com passwd is @HZERn5W65z$-Ez
    the url is https://driver-knowledge-test.service.nsw.gov.au/
    then try to click and learning all the learning part
    if any page need auth code, pls let use to use login thing to login
      """)