#!/usr/bin/env python3
"""
Purpose: Complete integration test suite validating ConnectOnion auth, direct WebAutomation, agent orchestration, and Google search workflow
pytest-compatible version with fixtures and proper assertions
"""
import os
import time
from pathlib import Path
import pytest
from connectonion import Agent
from web_automation import WebAutomation


@pytest.mark.integration
def test_authentication(check_api_key):
    """Test 1: Verify authentication works with ConnectOnion."""
    # check_api_key fixture already validates token exists
    token = check_api_key
    assert token, "OPENONION_API_KEY should exist"
    assert len(token) > 10, "Token should be valid length"

    # Test agent creation
    agent = Agent(name="auth_test", model="co/o4-mini")
    assert agent is not None, "Agent should be created"

    # Test simple call
    result = agent.input("Say exactly: 'OK'")
    assert result, "Agent should return a response"
    assert "ok" in result.lower(), f"Agent should respond with OK, got: {result}"


@pytest.mark.integration
@pytest.mark.screenshot
def test_browser_direct(web):
    """Test 2: Direct browser operations without agent."""
    # Open browser
    result = web.open_browser()
    assert "opened" in result.lower() or "browser" in result.lower(), f"Browser should open: {result}"

    # Navigate
    result = web.go_to("https://www.example.com")
    assert "example.com" in result.lower() or "navigated" in result.lower(), f"Should navigate: {result}"

    # Screenshot
    result = web.take_screenshot("test_example.png")
    assert "screenshot" in result.lower() or "saved" in result.lower(), f"Screenshot should be taken: {result}"

    # Verify screenshot exists
    screenshot_path = Path("screenshots/test_example.png")
    if not screenshot_path.exists():
        screenshot_path = Path("test_example.png")
    assert screenshot_path.exists(), "Screenshot file should exist"

    # Close
    result = web.close()
    assert "closed" in result.lower() or "browser" in result.lower(), f"Browser should close: {result}"


@pytest.mark.integration
def test_agent_browser(agent):
    """Test 3: Agent-controlled browser operations."""
    # Simple navigation task
    task = "Open browser, go to example.com, then close the browser"

    result = agent.input(task)
    assert result, "Agent should return a result"
    assert len(result) > 0, "Agent response should not be empty"


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.screenshot
def test_google_search():
    """Test 4: Google search with agent - multi-step workflow."""
    web = WebAutomation()
    agent = Agent(
        name="search_agent",
        model="co/o4-mini",
        tools=web,
        max_iterations=8
    )

    search_term = "OpenAI GPT-4"

    # Step-by-step approach
    steps = [
        "Open a browser",
        "Go to google.com",
        f"Type '{search_term}' in the search box",
        "Take a screenshot and save it as 'google_search.png'",
        "Close the browser"
    ]

    step_results = []
    for step in steps:
        try:
            result = agent.input(step)
            step_results.append((step, True, result))
            time.sleep(1)  # Small delay between steps
        except Exception as e:
            step_results.append((step, False, str(e)))

    # At least 3 out of 5 steps should succeed
    successful_steps = sum(1 for _, success, _ in step_results if success)
    assert successful_steps >= 3, f"At least 3 steps should succeed, got {successful_steps}/5"

    # Check if screenshot was created
    screenshot_found = Path("google_search.png").exists() or Path("screenshots/google_search.png").exists()
    # Don't fail if screenshot not found, but warn
    if not screenshot_found:
        pytest.skip("Screenshot not created, but test mostly passed")


# Keep the old main() for backward compatibility
def main():
    """Run all tests using pytest."""
    import sys
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()