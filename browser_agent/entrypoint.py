"""
Purpose: Main entry point for natural language browser automation agent
LLM-Note:
  Dependencies: imports from [pathlib, dotenv, connectonion.Agent, web_automation.WebAutomation, argparse, sys] | imported by [README.md examples] | tested by [tests/test_all.py]
  Data flow: receives CLI arguments via argparse → agent.input() routes to LLM (gemini-2.5-flash) → LLM calls web.* tools (and optional DeepResearch tool) → returns execution result string
  State/Effects: creates global web=WebAutomation() instance | loads .env with OPENONION_API_KEY | reads prompt.md system instructions | web tools mutate browser state (open/navigate/click/close)
  Integration: exposes agent.input(str) → str API | uses ConnectOnion Agent with tools=web (all WebAutomation methods become callable tools) | max_iterations=50 | Supports --mode deep-research
  Performance: agent orchestrates sequential tool calls based on LLM decisions | browser operations are synchronous (blocking) | screenshot I/O writes to screenshots/ folder
  Errors: raises if .env missing OPENONION_API_KEY | playwright install required or import fails | web tools return error strings (not exceptions) for LLM to handle
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from connectonion import Agent
from connectonion.useful_plugins import image_result_formatter
from .web_automation import WebAutomation


def main():
    parser = argparse.ArgumentParser(description="Natural language browser automation agent")
    parser.add_argument("prompt", nargs="?", help="The natural language task to perform")
    parser.add_argument("--mode", choices=["standard", "deep-research"], default="standard", help="Operation mode")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--no-profile", action="store_true", help="Do not use Chrome profile")
    
    args = parser.parse_args()

    # Create the web automation instance
    use_profile = not args.no_profile
    web = WebAutomation(use_chrome_profile=use_profile)

    # Prepare tools
    tools = [web]
    
    # Handle Deep Research Mode
    if args.mode == "deep-research":
        from .deep_research import DeepResearch
        deep_research_tool = DeepResearch(web)
        tools.append(deep_research_tool)
        print("Deep Research mode enabled")

    # Create the agent
    agent = Agent(
        name="playwright_agent",
        model=os.getenv("BROWSER_AGENT_MODEL", "co/gemini-2.5-flash"),
        system_prompt=Path(__file__).parent / "resources" / "prompt.md",
        tools=tools, # Pass list of tools (web + potentially others)
        plugins=[image_result_formatter],
        max_iterations=50
    )

    # Determine prompt
    prompt = args.prompt
    if not prompt:
        raise ValueError("No prompt provided. Please provide a prompt as a command line argument.")

    print(f"\nAgent starting with mode: {args.mode}")
    print(f"Task: {prompt}\n")

    result = agent.input(prompt)
    print(f"\n✅ Task completed: {result}")


if __name__ == "__main__":
    main()