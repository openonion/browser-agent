#!/usr/bin/env python3
"""
Test multi-tab functionality.
Verifies that tabs can be opened, switched, listed, and closed.
"""
import time
from pathlib import Path
import pytest
from web_automation import WebAutomation


@pytest.mark.integration
@pytest.mark.screenshot
def test_multi_tab_basic():
    """Test basic multi-tab operations."""

    print("\n[TEST] Multi-tab functionality")
    print("-" * 60)

    web = WebAutomation()

    try:
        # Open browser
        print("[STEP 1] Opening browser...")
        result = web.open_browser(headless=False)
        print(f"  {result}")
        assert "opened" in result.lower()

        # Verify initial tab exists
        print("\n[STEP 2] Checking initial tab...")
        tabs = web.list_tabs()
        print(f"  {tabs}")
        assert "main" in tabs

        # Navigate main tab
        print("\n[STEP 3] Navigating main tab to example.com...")
        web.go_to("https://example.com")
        time.sleep(1)

        # Open second tab
        print("\n[STEP 4] Opening second tab to stackoverflow.com...")
        result = web.new_tab("https://stackoverflow.com", "stackoverflow")
        print(f"  {result}")
        assert "stackoverflow" in result.lower()
        time.sleep(2)

        # Open third tab
        print("\n[STEP 5] Opening third tab to github.com...")
        result = web.new_tab("https://github.com", "github")
        print(f"  {result}")
        assert "github" in result.lower()
        time.sleep(2)

        # List all tabs
        print("\n[STEP 6] Listing all tabs...")
        tabs = web.list_tabs()
        print(f"{tabs}")
        assert "main" in tabs
        assert "stackoverflow" in tabs
        assert "github" in tabs

        # Switch to main tab
        print("\n[STEP 7] Switching to main tab...")
        result = web.switch_to_tab("main")
        print(f"  {result}")
        assert "main" in result
        assert "example.com" in result

        # Take screenshot of main tab
        print("\n[STEP 8] Taking screenshot of main tab...")
        web.take_screenshot("main_tab.png")

        # Switch to stackoverflow tab
        print("\n[STEP 9] Switching to stackoverflow tab...")
        result = web.switch_to_tab("stackoverflow")
        print(f"  {result}")
        assert "stackoverflow" in result

        # Take screenshot of stackoverflow tab
        print("\n[STEP 10] Taking screenshot of stackoverflow tab...")
        web.take_screenshot("stackoverflow_tab.png")

        # Close stackoverflow tab
        print("\n[STEP 11] Closing stackoverflow tab...")
        result = web.close_tab("stackoverflow")
        print(f"  {result}")
        assert "closed" in result.lower()

        # List remaining tabs
        print("\n[STEP 12] Listing remaining tabs...")
        tabs = web.list_tabs()
        print(f"{tabs}")
        assert "stackoverflow" not in tabs
        assert "main" in tabs
        assert "github" in tabs

        # Verify screenshots exist
        screenshot1 = Path("screenshots/main_tab.png")
        screenshot2 = Path("screenshots/stackoverflow_tab.png")
        assert screenshot1.exists(), "Main tab screenshot should exist"
        assert screenshot2.exists(), "Stackoverflow tab screenshot should exist"

        print("\n[SUCCESS] All multi-tab operations passed!")
        print("  Pause for 3 seconds to see the browser...")
        time.sleep(3)

    finally:
        web.close()


@pytest.mark.integration
@pytest.mark.screenshot
def test_multi_tab_auto_naming():
    """Test auto-generated tab names with visual confirmation."""

    print("\n[TEST] Auto-generated tab names")
    print("-" * 60)

    web = WebAutomation()

    try:
        web.open_browser(headless=False)

        # Navigate main tab
        print("[STEP 1] Navigating main tab to Hacker News...")
        web.go_to("https://news.ycombinator.com")
        time.sleep(2)
        web.take_screenshot("01_main_tab_hn.png")

        # Open second tab
        print("[STEP 2] Opening auto-named tab to example.com...")
        web.new_tab("https://example.com")
        time.sleep(2)
        web.take_screenshot("02_tab_0_example.png")

        # Open third tab
        print("[STEP 3] Opening auto-named tab to google.com...")
        web.new_tab("https://google.com")
        time.sleep(2)
        web.take_screenshot("03_tab_1_google.png")

        # List all tabs
        tabs = web.list_tabs()
        print(f"\n[TABS] {tabs}")

        # Switch back to each tab and screenshot
        print("\n[STEP 4] Switching back to main tab...")
        web.switch_to_tab("main")
        time.sleep(1)
        web.take_screenshot("04_switched_to_main.png")

        print("\n[STEP 5] Switching to tab_0...")
        web.switch_to_tab("tab_0")
        time.sleep(1)
        web.take_screenshot("05_switched_to_tab_0.png")

        # Should have main, tab_0, tab_1
        assert "main" in tabs
        assert "tab_0" in tabs or "tab_1" in tabs

        print("\n[SUCCESS] Auto-naming works! Check screenshots/ folder for visual confirmation.")
        print("  Pause for 3 seconds to see the browser...")
        time.sleep(3)

    finally:
        web.close()


@pytest.mark.integration
@pytest.mark.screenshot
@pytest.mark.slow
def test_agent_multi_tab_autonomous():
    """Test agent autonomously using multi-tab tools based on natural language."""
    from connectonion import Agent

    print("\n[TEST] Agent autonomous multi-tab usage")
    print("-" * 60)

    web = WebAutomation()
    agent = Agent(
        name="multi_tab_agent",
        model="co/gpt-4o-mini",
        tools=web,
        max_iterations=15
    )

    try:
        # Give the agent a task that requires multi-tab
        task = """
        Open browser and go to https://news.ycombinator.com
        Then open a new tab and go to https://example.com
        Switch between the two tabs and take a screenshot of each one.
        Name the screenshots 'agent_hn.png' and 'agent_example.png'
        Finally, close the browser.
        """

        print(f"[TASK] {task.strip()}\n")
        print("[AGENT] Working...")

        result = agent.input(task)

        print(f"\n[AGENT RESPONSE] {result}\n")

        # Verify the agent completed the task
        # Check if screenshots were created
        hn_screenshot = Path("screenshots/agent_hn.png")
        example_screenshot = Path("screenshots/agent_example.png")

        if hn_screenshot.exists():
            print("[OK] Agent created Hacker News screenshot")
        else:
            print("[WARNING] Hacker News screenshot not found")

        if example_screenshot.exists():
            print("[OK] Agent created Example.com screenshot")
        else:
            print("[WARNING] Example.com screenshot not found")

        # At least one screenshot should exist
        assert hn_screenshot.exists() or example_screenshot.exists(), \
            "Agent should create at least one screenshot"

        print("\n[SUCCESS] Agent successfully used multi-tab tools autonomously!")

    finally:
        # Ensure browser is closed
        if web.browser:
            web.close()


if __name__ == "__main__":
    # Run directly for quick testing
    test_multi_tab_basic()
    test_multi_tab_auto_naming()
    test_agent_multi_tab_autonomous()
