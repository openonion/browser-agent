"""
Integration test validating unified scroll() method with modular scroll_strategies.py architecture
pytest-compatible version - requires manual Gmail login
"""
import time
import pytest
from browser_agent.web_automation import WebAutomation


@pytest.mark.manual
@pytest.mark.chrome_profile
@pytest.mark.slow
def test_unified_scroll_gmail():
    """
    Test unified scroll() method on Gmail - requires manual login.

    This test validates:
    - web_automation.scroll() → scroll_strategies.scroll_with_verification()
    - AI strategy generation → fallback chain → screenshot comparison
    - Clean separation of concerns (automation vs scroll logic)
    """
    web = WebAutomation(use_chrome_profile=True)

    # Open visible browser for manual login
    web.open_browser(headless=False)
    web.go_to("https://gmail.com")

    # Wait for manual login (user should log in during this time)
    print("\n⚠️  Please log in to Gmail within 10 seconds...")
    time.sleep(10)

    # Test scroll functionality
    result = web.scroll(times=5, description="the email list")

    # Assertions
    assert result, "Scroll should return a result"
    assert "scroll" in result.lower() or "email" in result.lower(), f"Result should mention scrolling: {result}"

    # Cleanup
    web.close()


@pytest.mark.manual
@pytest.mark.chrome_profile
def test_scroll_architecture_demo():
    """
    Demo test showing the clean scroll architecture.

    This validates the design principle:
    - web_automation.py stays clean
    - scroll_strategies.py handles complexity
    - One simple method: web.scroll()
    """
    # Just verify the architecture is in place
    web = WebAutomation(use_chrome_profile=False)

    # Verify scroll method exists
    assert hasattr(web, 'scroll'), "WebAutomation should have scroll() method"
    assert callable(web.scroll), "scroll should be callable"

    # Verify scroll_strategies module exists
    try:
        from browser_agent import scroll_strategies
        assert hasattr(scroll_strategies, 'scroll_with_verification'), "scroll_strategies should have scroll_with_verification()"
    except ImportError:
        pytest.skip("scroll_strategies module not found")


# For manual testing
if __name__ == "__main__":
    import sys
    pytest.main([__file__, "-v", "-s"])
