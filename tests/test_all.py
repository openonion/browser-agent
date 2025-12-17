#!/usr/bin/env python3
"""
Purpose: Complete integration test suite validating ConnectOnion auth, direct WebAutomation, agent orchestration, and Google search workflow
pytest-compatible version with fixtures and proper assertions
"""
import time
from pathlib import Path
import pytest
from connectonion import Agent


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
    result = web.open_browser(headless=True)
    assert "opened" in result.lower() or "browser" in result.lower(), f"Browser should open: {result}"

    # Navigate
    result = web.go_to("https://www.example.com")
    assert "example.com" in result.lower() or "navigated" in result.lower(), f"Should navigate: {result}"

    # Screenshot
    result = web.take_screenshot("test_example.png")
    assert result.startswith("data:image/png;base64,"), f"Screenshot should return base64 data: {result[:100]}..."

    # Verify screenshot exists
    # Use web.SCREENSHOTS_DIR which is set by the fixture (temp dir or default)
    screenshot_path = Path(web.SCREENSHOTS_DIR) / "test_example.png"
    assert screenshot_path.exists(), "Screenshot file should exist"

    # Close
    result = web.close()
    assert "closed" in result.lower() or "browser" in result.lower(), f"Browser should close: {result}"


@pytest.mark.integration
def test_agent_browser(agent):
    """Test 3: Agent-controlled browser operations."""
    # Simple navigation task - explicitly request headless
    task = "Open headless browser, go to example.com, then close the browser"

    result = agent.input(task)
    assert result, "Agent should return a result"
    assert len(result) > 0, "Agent response should not be empty"


# Keep the old main() for backward compatibility
def main():
    """Run all tests using pytest."""
    import sys
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
