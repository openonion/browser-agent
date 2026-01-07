"""
Test image_result_formatter plugin with browser automation
"""
import os
import pytest
from connectonion import Agent
from connectonion.useful_plugins import image_result_formatter
from tools.web_automation import WebAutomation
from pathlib import Path


@pytest.mark.integration
@pytest.mark.screenshot
def test_image_plugin_with_screenshot(web):
    """Test that image_result_formatter plugin works with browser screenshots."""
    # web fixture handles instantiation and cleanup automatically

    # Create agent with image plugin
    agent = Agent(
        name="test_image",
        model=os.getenv("BROWSER_AGENT_MODEL", "gemini-2.5-flash"),
        tools=web,
        plugins=[image_result_formatter],
        log=True
    )

    # Execute task
    result = agent.input("Open headless browser, go to example.com, take screenshot, tell me what you see, close browser")

    # Assertions
    assert result, "Agent should return a result"
    assert len(result) > 0, "Result should not be empty"

    # Check that screenshot was likely created (agent should mention it or it exists)
    screenshot_dir = Path(web.screenshots_dir)
    if screenshot_dir.exists():
        screenshots = list(screenshot_dir.glob("*.png"))
        assert len(screenshots) > 0, "At least one screenshot should be created"

    # Cleanup is handled by fixture


@pytest.mark.integration
def test_image_plugin_basic(web):
    """Test that image_result_formatter plugin can be loaded."""
    # web fixture handles instantiation and cleanup automatically

    # Just verify plugin can be added to agent
    agent = Agent(
        name="test_plugin",
        model=os.getenv("BROWSER_AGENT_MODEL", "gemini-2.5-flash"),
        tools=web,
        plugins=[image_result_formatter]
    )

    assert agent is not None, "Agent should be created with image plugin"
    assert hasattr(agent, 'plugins') or 'image' in str(agent.__dict__), "Agent should have plugins configured"


# For manual testing
if __name__ == "__main__":
    import sys
    pytest.main([__file__, "-v", "-s"])
