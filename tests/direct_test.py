#!/usr/bin/env python3
"""
Purpose: Manual browser automation test bypassing AI agent - demonstrates direct WebAutomation API usage
LLM-Note:
  Dependencies: imports from [web_automation.WebAutomation, time, sys] | not imported by other files (standalone test) | manual test (not run in test suite)
  Data flow: receives search_term from CLI args → calls web.* methods sequentially (open_browser→go_to→type_text→submit_form→take_screenshot→close) → prints status strings to stdout → saves 3 screenshots to screenshots/*.png
  State/Effects: creates WebAutomation() instance with headless=False (visible browser) | mutates browser: navigates to google.com, types search, submits form | writes 3 PNG files: google_homepage.png, google_search_typed.png, google_search_results.png | time.sleep(1) for UI stability
  Integration: demonstrates low-level web.* API without agent orchestration | useful for debugging WebAutomation methods directly | contrasts with tests/test_all.py which uses agent.input()
  Performance: synchronous execution with explicit time.sleep(1) delays | visible browser (headless=False) slower than headless mode
  Errors: no exception handling - will crash on WebAutomation failures | prints web.* return strings (errors included)
"""

from web_automation import WebAutomation
import time

def test_google_search(search_term="Playwright"):
    """Test Google search with screenshots at each step."""
    web = WebAutomation()

    print(f"🔍 Testing Google search for: {search_term}")
    print("=" * 60)

    # Step 1: Open browser
    print("1. Opening browser...")
    print(web.open_browser(headless=False))

    # Step 2: Go to Google
    print("2. Navigating to Google...")
    print(web.go_to("https://www.google.com"))

    # Step 3: Take screenshot of homepage
    print("3. Taking screenshot of Google homepage...")
    print(web.take_screenshot("google_homepage.png"))

    # Step 4: Type search term
    print(f"4. Typing '{search_term}' in search box...")
    print(web.type_text("search box", search_term))

    # Step 5: Wait a moment
    time.sleep(1)

    # Step 6: Take screenshot after typing
    print("5. Taking screenshot after typing...")
    print(web.take_screenshot("google_search_typed.png"))

    # Step 7: Submit search (press Enter)
    print("6. Submitting search...")
    print(web.submit_form())

    # Step 8: Wait for results
    print("7. Waiting for results...")
    print(web.wait_for_text(search_term, timeout=5))

    # Step 9: Take screenshot of results
    print("8. Taking screenshot of search results...")
    print(web.take_screenshot("google_search_results.png"))

    # Step 10: Close browser
    print("9. Closing browser...")
    print(web.close())

    print("=" * 60)
    print("✅ Test complete! Check for screenshots:")
    print("  - google_homepage.png")
    print("  - google_search_typed.png")
    print("  - google_search_results.png")

if __name__ == "__main__":
    import sys
    search = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Playwright"
    test_google_search(search)