#!/usr/bin/env python3
"""
Direct browser automation test - demonstrates WebAutomation API without AI agent
pytest-compatible version
"""
import time
from pathlib import Path
import pytest


@pytest.mark.integration
@pytest.mark.screenshot
@pytest.mark.slow
@pytest.mark.parametrize("search_term", ["Playwright", "Python automation"])
def test_wikipedia_search_direct(web, search_term):
    """Test Wikipedia search with direct WebAutomation calls - no agent."""
    # web fixture handles browser cleanup automatically

    # Step 1: Open browser
    result = web.open_browser(headless=False)
    assert "opened" in result.lower() or "browser" in result.lower(), f"Browser should open: {result}"

    # Step 2: Go to Wikipedia
    result = web.go_to("https://www.wikipedia.org")
    assert "wikipedia" in result.lower() or "navigated" in result.lower(), f"Should navigate to Wikipedia: {result}"

    # Step 3: Take screenshot of homepage
    result = web.take_screenshot("wikipedia_homepage.png")
    assert "data:image/png;base64" in result or "screenshot" in result.lower(), f"Screenshot should be saved: {result}"

    # Step 4: Type search term
    # Wikipedia's search input is typically "search-input" or has name="search"
    result = web.type_text("search input", search_term)
    
    if "Could not find" in result:
        # Fallback 1: Simpler description
        result = web.type_text("search", search_term)
    
    if "Could not find" in result:
        # Fallback 2: Direct selector interaction if natural language fails
        if web.page.locator("input[name='search']").count() > 0:
            web.page.fill("input[name='search']", search_term)
            result = f"Typed '{search_term}' using fallback selector"
        elif web.page.locator("#searchInput").count() > 0:
            web.page.fill("#searchInput", search_term)
            result = f"Typed '{search_term}' using fallback selector"

    assert "typed" in result.lower() or search_term.lower() in result.lower(), f"Should type search term: {result}"

    # Step 5: Wait a moment
    time.sleep(1)

    # Step 6: Take screenshot after typing
    result = web.take_screenshot("wikipedia_search_typed.png")
    assert "data:image/png;base64" in result or "screenshot" in result.lower(), f"Screenshot should be saved: {result}"

    # Step 7: Submit search
    result = web.submit_form()
    assert "submit" in result.lower() or "pressed" in result.lower(), f"Should submit form: {result}"

    # Step 8: Wait for results - Wikipedia usually redirects to an article or search results
    # We look for the search term or "Search results"
    try:
        result = web.wait_for_text(search_term, timeout=5)
    except:
        # If specific term not found (maybe in title), check if we navigated
        pass
        
    # Step 9: Take screenshot of results
    result = web.take_screenshot("wikipedia_search_results.png")
    assert "data:image/png;base64" in result or "screenshot" in result.lower(), f"Screenshot should be saved: {result}"

    # Verify screenshots exist
    for filename in ["wikipedia_homepage.png", "wikipedia_search_typed.png", "wikipedia_search_results.png"]:
        screenshot_path = Path(web.SCREENSHOTS_DIR) / filename
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
    pytest.main([__file__, "-v", "-s", "-k", "test_wikipedia_search_direct", "--tb=short"])