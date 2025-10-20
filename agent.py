"""
Purpose: Main entry point for natural language browser automation agent
LLM-Note:
  Dependencies: imports from [pathlib, dotenv, connectonion.Agent, web_automation.WebAutomation] | imported by [README.md examples] | tested by [tests/test_all.py]
  Data flow: receives natural language command string from __main__ → agent.input() routes to LLM (gemini-2.5-flash) → LLM calls web.* tools → returns execution result string
  State/Effects: creates global web=WebAutomation() instance | loads .env with OPENONION_API_KEY | reads prompt.md system instructions | web tools mutate browser state (open/navigate/click/close)
  Integration: exposes agent.input(str) → str API | uses ConnectOnion Agent with tools=web (all WebAutomation methods become callable tools) | max_iterations=20 for complex multi-step workflows
  Performance: agent orchestrates sequential tool calls based on LLM decisions | browser operations are synchronous (blocking) | screenshot I/O writes to screenshots/ folder
  Errors: raises if .env missing OPENONION_API_KEY | playwright install required or import fails | web tools return error strings (not exceptions) for LLM to handle
"""

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
    model="co/gpt-4o",
    system_prompt=Path(__file__).parent / "prompt.md",
    tools=web,
    max_iterations=20
)

if __name__ == "__main__":
    # Test with a more complex task
    result = agent.auto_debug("""
    Open browser and go to news.ycombinator.com
    Take a screenshot of the homepage
    Find the first article and click on it
    Take another screenshot
    Then close the browser
    """)
    print(result)