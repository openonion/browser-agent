"""
Purpose: Test ConnectOnion auto_debug feature with browser automation
pytest-compatible version with fixtures
"""
from pathlib import Path
import pytest
from connectonion import Agent
import sys

# Ensure tools can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.browser import Browser


@pytest.mark.manual
@pytest.mark.integration
def test_auto_debug_hacker_news():
    """Test auto_debug feature with browser automation - requires user interaction."""
    # Create the web automation instance
    web = Browser()

    # Get correct path to prompt.md
    prompt_path = Path(__file__).parent.parent / "prompts" / "agent.md"
    assert prompt_path.exists(), f"agent.md should exist at {prompt_path}"

    # Create the agent with browser tools
    agent = Agent(
        name="playwright_agent",
        model="co/gpt-5",
        system_prompt=prompt_path,
        tools=web,
        max_iterations=20
    )

    # Test with a simple task that will trigger breakpoints
    result = agent.auto_debug("""
    Open browser and go to news.ycombinator.com
    Take a screenshot of the homepage
    """)

    assert result, "auto_debug should return a result"
    assert len(result) > 0, "Result should not be empty"

    # Cleanup
    if web.page:
        web.close()


# For manual testing
if __name__ == "__main__":
    import sys
    pytest.main([__file__, "-v", "-s"])  # -s to show print output
