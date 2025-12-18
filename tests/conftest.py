"""
pytest configuration and fixtures for browser automation tests
"""
import os
import sys
import asyncio
import warnings
from pathlib import Path
import pytest
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# Disable anyio for these tests to avoid conflicts with Playwright sync API
def pytest_configure(config):
    """Disable anyio plugin if present to avoid conflicts with Playwright."""
    if hasattr(config, 'pluginmanager'):
        # Try to unregister anyio plugin if it exists
        try:
            anyio_plugin = config.pluginmanager.get_plugin('anyio')
            if anyio_plugin:
                config.pluginmanager.unregister(anyio_plugin)
        except Exception:
            pass


@pytest.fixture(scope="function", autouse=True)
def cleanup_async_loop():
    """Clean up any asyncio event loops before each test to avoid conflicts with Playwright."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.stop()
        loop.close()
    except RuntimeError:
        pass
    yield
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.stop()
        loop.close()
    except RuntimeError:
        pass


@pytest.fixture(autouse=True)
def cleanup_asyncio():
    """Clear asyncio loop after each test to prevent pollution"""
    yield
    try:
        # Suppress deprecation warning for get_event_loop()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            loop = asyncio.get_event_loop()
            
        if not loop.is_closed():
            loop.close()
    except RuntimeError:
        # No event loop set, which is fine
        pass
    finally:
        # Always clear the global reference
        asyncio.set_event_loop(None)


@pytest.fixture(scope="function")
def web(tmp_path):
    """Create WebAutomation instance for each test using temp dir for screenshots"""
    from tools.web_automation import WebAutomation
    web_instance = WebAutomation()
    # Redirect screenshots to temp directory
    web_instance.screenshots_dir = str(tmp_path / "screenshots")
    yield web_instance
    # Cleanup: close browser if still open
    if web_instance.page:
        web_instance.close()


@pytest.fixture(scope="function")
def agent(web):
    """Create Agent with WebAutomation tools"""
    from connectonion import Agent
    agent_instance = Agent(
        name="test_agent",
        model="gemini-2.5-flash",
        tools=web,
        max_iterations=10
    )
    return agent_instance


@pytest.fixture(scope="function")
def agent_with_prompt(web):
    """Create Agent with prompt.md system prompt"""
    from connectonion import Agent
    prompt_path = Path(__file__).parent.parent / "prompts/browser_agent.md"
    agent_instance = Agent(
        name="playwright_agent",
        model="gemini-2.5-flash",
        system_prompt=prompt_path,
        tools=web,
        max_iterations=20
    )
    return agent_instance


@pytest.fixture(scope="session", autouse=True)
def setup_screenshots_dir():
    """Ensure screenshots directory exists"""
    # Kept for backward compatibility or manual runs not using the web fixture
    screenshots_dir = Path(__file__).parent.parent / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def check_api_key():
    """Verify OPENONION_API_KEY is set"""
    token = os.getenv("OPENONION_API_KEY")
    if not token:
        pytest.skip("OPENONION_API_KEY not found. Run 'co auth' to authenticate")
    return token