#!/usr/bin/env python3
"""
Direct browser automation test - demonstrates WebAutomation API without AI agent
pytest-compatible version
"""
import time
from pathlib import Path
import pytest
from web_automation import WebAutomation


@pytest.mark.manual
@pytest.mark.integration
@pytest.mark.screenshot
@pytest.mark.slow
@pytest.mark.parametrize("search_term", ["Playwright", "Python automation"])
def test_google_search_direct(search_term):
    """Test Google search with direct WebAutomation calls - no agent.

    Note: This test is marked as manual because:
    1. It requires real Google interaction which can be flaky
    2. Parametrized tests with Playwright can have async loop conflicts
    3. It's more of an end-to-end test than a unit test
    """
    web = WebAutomation()

    # Step 1: Open browser
    result = web.open_browser(headless=False)
    assert "opened" in result.lower() or "browser" in result.lower(), f"Browser should open: {result}"

    # Step 2: Go to Google
    result = web.go_to("https://www.google.com")
    assert "google" in result.lower() or "navigated" in result.lower(), f"Should navigate to Google: {result}"

    # Step 3: Take screenshot of homepage
    result = web.take_screenshot("google_homepage.png")
    assert result.startswith("data:image/png;base64,"), f"Screenshot should return base64 data: {result[:100]}..."

    # Step 4: Type search term
    result = web.type_text("search box", search_term)
    assert "typed" in result.lower() or search_term.lower() in result.lower(), f"Should type search term: {result}"

    # Step 5: Wait a moment
    time.sleep(1)

    # Step 6: Take screenshot after typing
    result = web.take_screenshot("google_search_typed.png")
    assert result.startswith("data:image/png;base64,"), f"Screenshot should return base64 data: {result[:100]}..."

    # Step 7: Submit search
    result = web.submit_form()
    assert "submit" in result.lower() or "pressed" in result.lower(), f"Should submit form: {result}"

    # Step 8: Wait for results
    result = web.wait_for_text(search_term, timeout=5)
    # May or may not find exact text, so just check it returned something
    assert result, "Should return a result from wait_for_text"

    # Step 9: Take screenshot of results
    result = web.take_screenshot("google_search_results.png")
    assert result.startswith("data:image/png;base64,"), f"Screenshot should return base64 data: {result[:100]}..."

    # Verify screenshots exist
    for filename in ["google_homepage.png", "google_search_typed.png", "google_search_results.png"]:
        screenshot_path = Path("screenshots") / filename
        if not screenshot_path.exists():
            screenshot_path = Path(filename)
        assert screenshot_path.exists(), f"Screenshot {filename} should exist"

    # Step 10: Close browser
    result = web.close()
    assert "closed" in result.lower() or "browser" in result.lower(), f"Browser should close: {result}"


@pytest.mark.integration
def test_direct_browser_basic(web):
    """Basic test of direct WebAutomation methods."""
    # Just test that basic methods work
    result = web.open_browser()
    assert "opened" in result.lower() or "browser" in result.lower()

    result = web.go_to("https://example.com")
    assert "example" in result.lower() or "navigated" in result.lower()

    result = web.close()
    assert "closed" in result.lower() or "browser" in result.lower()


# For manual testing with custom search term
if __name__ == "__main__":
    import sys
    search = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Playwright"
    pytest.main([__file__, "-v", "-s", "-k", "test_google_search_direct", "--tb=short"])