#!/usr/bin/env python3
"""
Entry point for the browser agent.
Wraps browser_agent.entrypoint.main()
"""
<<<<<<< HEAD
from browser_agent.entrypoint import main
=======

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from connectonion import Agent
from connectonion.useful_plugins import image_result_formatter
from web_automation import WebAutomation

# Create the web automation instance
# Set use_chrome_profile=True to use a copy of your Chrome profile (cookies, sessions, etc)
web = WebAutomation(use_chrome_profile=True)

# Create the agent with browser tools and image_result_formatter plugin
# image_result_formatter converts base64 screenshots to vision format for LLM to see
# Note: react plugin temporarily disabled - it conflicts with batched tool calls
agent = Agent(
    name="playwright_agent",
    model="co/gemini-2.5-flash",
    system_prompt=Path(__file__).parent / "prompt.md",
    tools=web,
    plugins=[image_result_formatter],  # Just vision formatting for now
    max_iterations=50  # Increased for scrolling through all emails
)
>>>>>>> 04a7f6d61460ee9cc35205e615f1d66388a02955

if __name__ == "__main__":
    main()
