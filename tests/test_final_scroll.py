"""
Test the final unified scroll() method with modular architecture.

scroll() uses scroll_strategies.py module with:
1. AI strategy (first, default)
2. Element strategy (fallback)
3. Page strategy (last fallback)
4. Screenshot verification
"""

from web_automation import WebAutomation
import time

def test_unified_scroll():
    print("=== Testing Unified scroll() Method ===\n")
    print("Architecture:")
    print("  web_automation.py - Main class with scroll() method")
    print("  scroll_strategies.py - All scroll logic with auto-fallback")
    print()

    web = WebAutomation(use_chrome_profile=True)
    web.open_browser(headless=False)
    web.go_to("https://gmail.com")
    time.sleep(3)

    print("Calling simple: web.scroll(5, 'the email list')")
    print("This will:")
    print("  1. Try AI-generated strategy")
    print("  2. Compare screenshots to verify")
    print("  3. Auto-fallback if needed\n")

    result = web.scroll(times=5, description="the email list")

    print(f"\n✅ Result: {result}\n")

    web.close()

    print("✅ Test complete!")
    print("\nCode organization:")
    print("  ✓ web_automation.py - clean, focused on browser automation")
    print("  ✓ scroll_strategies.py - all scroll logic separated")
    print("  ✓ One simple method: web.scroll()")

if __name__ == "__main__":
    test_unified_scroll()
