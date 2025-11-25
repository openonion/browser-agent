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
from connectonion.useful_plugins import image_result_formatter
from web_automation import WebAutomation

# Create the web automation instance
# Cache configuration options:
#   cache_selectors=True: Enable selector caching (default: True)
#   cache_persistent=True: Save cache to disk for reuse across script runs (default: False)
#
# For daily scripts that visit the same sites repeatedly, use cache_persistent=True
# to avoid expensive LLM calls on subsequent runs
web = WebAutomation(
    use_chrome_profile=True,
    cache_selectors=True,      # Enable caching
    cache_persistent=True      # Changed to True to test persistent cache
)

# Create the agent with browser tools and image_result_formatter plugin
# image_result_formatter converts base64 screenshots to vision format for LLM to see
# Note: react plugin temporarily disabled - it conflicts with batched tool calls
agent = Agent(
    name="playwright_agent",
    model="co/gpt-4o-mini",  # Use ConnectOnion managed model
    system_prompt=Path(__file__).parent / "prompt.md",
    tools=web,
    plugins=[image_result_formatter],  # Just vision formatting for now
    max_iterations=50  # Increased for scrolling through all emails
)

if __name__ == "__main__":
    # Gmail analysis task - Get ALL emails and extract contacts
    result = agent.input("""
    1. Go to gmail.com
    2. Take a screenshot to check what page we're on
    3. Based on what you SEE in the screenshot, determine if we need to login or if we're already logged in
    4. If you need to login, call the manually login tool and wait for me to login manually

    Then after login:
    5. Scroll down repeatedly to load MORE emails (at least 5-10 times) to get as many emails as possible
    6. After scrolling, extract ALL visible email senders and subjects
    7. Create a comprehensive summary with:
       a) Total number of emails found
       b) List of ALL unique contacts (people who sent emails) with their email addresses if visible
       c) Most frequent senders (top 10)
       d) Main topics/categories across all emails

    Take screenshots before and after scrolling.
    Close the browser when done.
    """)
    print(f"\n[OK] Task completed: {result}")
 