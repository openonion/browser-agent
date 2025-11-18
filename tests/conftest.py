"""
pytest configuration and fixtures for browser automation tests
"""
import os
import sys
from pathlib import Path
import pytest
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")


@pytest.fixture(scope="function")
def web():
    """Create WebAutomation instance for each test"""
    from web_automation import WebAutomation
    web_instance = WebAutomation()
    yield web_instance
    # Cleanup: close browser if still open
    if web_instance.page:
        web_instance.close()


@pytest.fixture(scope="function")
def web_with_chrome():
    """Create WebAutomation instance with Chrome profile"""
    from web_automation import WebAutomation
    web_instance = WebAutomation(use_chrome_profile=True)
    yield web_instance
    if web_instance.page:
        web_instance.close()


@pytest.fixture(scope="function")
def agent(web):
    """Create Agent with WebAutomation tools"""
    from connectonion import Agent
    agent_instance = Agent(
        name="test_agent",
        model="co/o4-mini",
        tools=web,
        max_iterations=10
    )
    return agent_instance


@pytest.fixture(scope="function")
def agent_with_prompt(web):
    """Create Agent with prompt.md system prompt"""
    from connectonion import Agent
    prompt_path = Path(__file__).parent.parent / "prompt.md"
    agent_instance = Agent(
        name="playwright_agent",
        model="co/gpt-4o-mini",
        system_prompt=prompt_path,
        tools=web,
        max_iterations=20
    )
    return agent_instance


@pytest.fixture(scope="session", autouse=True)
def setup_screenshots_dir():
    """Ensure screenshots directory exists"""
    screenshots_dir = Path(__file__).parent.parent / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def check_api_key():
    """Verify OPENONION_API_KEY is set"""
    token = os.getenv("OPENONION_API_KEY")
    if not token:
        pytest.skip("OPENONION_API_KEY not found. Run 'co auth' to authenticate")
    return token