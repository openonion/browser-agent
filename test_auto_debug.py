"""Test auto_debug feature with REPL editing"""
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from connectonion import Agent
from web_automation import WebAutomation

# Create the web automation instance
web = WebAutomation()

# Create the agent with browser tools
agent = Agent(
    name="playwright_agent",
    model="co/gpt-5",
    system_prompt=Path(__file__).parent / "prompt.md",
    tools=web,
    max_iterations=20
)

if __name__ == "__main__":
    # Test with a simple task that will trigger breakpoints
    result = agent.auto_debug("""
    Open browser and go to news.ycombinator.com
    Take a screenshot of the homepage
    """)
    print(result)
