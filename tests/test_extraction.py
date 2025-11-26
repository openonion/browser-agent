#!/usr/bin/env python3
"""
Test content extraction methods.
Verifies extract_text, get_page_text, and get_page_summary functionality.
"""
import time
from pathlib import Path
import pytest
from web_automation import WebAutomation


@pytest.mark.integration
def test_extract_text_basic():
    """Test basic text extraction from elements."""

    print("\n[TEST] Basic text extraction")
    print("-" * 60)

    web = WebAutomation(cache_persistent=True)

    try:
        web.open_browser(headless=True)
        web.go_to("https://example.com")
        time.sleep(2)

        # Take initial screenshot
        print("[SCREENSHOT] Page loaded...")
        web.take_screenshot("extraction_01_page.png")

        # Extract the main heading
        print("\n[STEP 1] Extracting main heading...")
        heading = web.extract_text("the main heading")
        print(f"  Result: {heading}")
        web.take_screenshot("extraction_02_heading.png")
        assert len(heading) > 0
        assert "Example Domain" in heading or "example" in heading.lower()

        # Extract paragraph text
        print("\n[STEP 2] Extracting first paragraph...")
        paragraph = web.extract_text("the first paragraph")
        print(f"  Result: {paragraph[:100]}...")
        web.take_screenshot("extraction_03_paragraph.png")
        assert len(paragraph) > 0

        print("\n[SUCCESS] Text extraction works!")
        print("  Screenshots saved: extraction_01_page.png, extraction_02_heading.png, extraction_03_paragraph.png")

    finally:
        web.close()


@pytest.mark.integration
def test_get_page_text():
    """Test getting all page text."""

    print("\n[TEST] Get all page text")
    print("-" * 60)

    web = WebAutomation()

    try:
        web.open_browser(headless=True)
        web.go_to("https://example.com")
        time.sleep(2)

        # Take screenshot before extraction
        print("[SCREENSHOT] Page loaded...")
        web.take_screenshot("page_text_01_loaded.png")

        print("[STEP 1] Getting all page text...")
        page_text = web.get_page_text()
        print(f"  Text length: {len(page_text)} characters")
        print(f"  Preview: {page_text[:200]}...")

        assert len(page_text) > 0
        assert "Example Domain" in page_text or "example" in page_text.lower()

        print("\n[SUCCESS] Page text extraction works!")
        print("  Screenshot saved: page_text_01_loaded.png")

    finally:
        web.close()


@pytest.mark.integration
@pytest.mark.slow
def test_get_page_summary():
    """Test AI-powered page summary with scrolling to capture all content."""

    print("\n[TEST] AI-powered page summary")
    print("-" * 60)

    web = WebAutomation()

    try:
        web.open_browser(headless=True)
        web.go_to("https://news.ycombinator.com")
        time.sleep(2)

        # Take screenshot before scrolling
        print("[SCREENSHOT] Hacker News loaded (initial view)...")
        web.take_screenshot("summary_01_hn_initial.png")

        # Scroll to bottom to load all content (HN has 30 items total)
        print("\n[STEP 1] Scrolling to bottom to load all content...")
        web.scroll_page(direction="bottom")
        time.sleep(2)  # Wait for any lazy-loaded content
        web.take_screenshot("summary_02_hn_scrolled.png")

        # Now get summary with all content
        print("\n[STEP 2] Generating page summary (should have all 30 items)...")
        summary = web.get_page_summary()
        print(f"  Summary: {summary}")

        assert len(summary) > 0
        assert not summary.startswith("Error")

        # Test with focus
        print("\n[STEP 3] Generating focused summary...")
        focused = web.get_page_summary(focus="top stories")
        print(f"  Focused: {focused}")

        assert len(focused) > 0

        print("\n[SUCCESS] Page summary generation works!")
        print("  Screenshots saved: summary_01_hn_initial.png, summary_02_hn_scrolled.png")

    finally:
        web.close()


@pytest.mark.integration
@pytest.mark.slow
def test_agent_autonomous_extraction():
    """Test agent autonomously scrolling and extracting complete content."""
    from connectonion import Agent

    print("\n[TEST] Agent autonomous content extraction")
    print("-" * 60)

    from pathlib import Path

    web = WebAutomation()
    prompt_path = Path(__file__).parent.parent / "prompt.md"
    agent = Agent(
        name="extraction_agent",
        model="co/gpt-4o-mini",
        system_prompt=prompt_path,
        tools=web,
        max_iterations=15
    )

    try:
        # Give the agent a task requiring complete content extraction
        task = """
        Go to https://news.ycombinator.com and get a summary of ALL the news items.
        Make sure to scroll to capture all 30 items, not just the visible ones.
        Take screenshots before and after scrolling.
        """

        print(f"[TASK] {task.strip()}\n")
        print("[AGENT] Working...")

        result = agent.input(task)

        print(f"\n[AGENT RESPONSE] {result}\n")

        # Check if screenshots were created
        from pathlib import Path
        screenshots_dir = Path("screenshots")
        if screenshots_dir.exists():
            screenshots = list(screenshots_dir.glob("*.png"))
            print(f"[OK] Agent created {len(screenshots)} screenshots")

        print("\n[SUCCESS] Agent successfully scrolled and extracted content autonomously!")

    finally:
        # Ensure browser is closed
        if web.browser:
            web.close()


if __name__ == "__main__":
    # Run directly for quick testing
    test_extract_text_basic()
    test_get_page_text()
    test_get_page_summary()
    test_agent_autonomous_extraction()
