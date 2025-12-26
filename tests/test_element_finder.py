"""Test element_finder extraction and click functionality.

Tests:
1. Extract all interactive elements with injected IDs
2. Take highlighted screenshot showing bounding boxes + indices
3. Click on conversations in LinkedIn messaging

Run: python tests/test_element_finder.py (from browser-agent directory)
Output: screenshots/highlighted_{timestamp}.png
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import element_finder
import highlight_screenshot
from web_automation import WebAutomation
import time

# Open browser and go to LinkedIn messaging
print("=== Opening LinkedIn Messaging ===")
web = WebAutomation(use_chrome_profile=True)
web.open_browser(headless=False)
web.go_to("https://www.linkedin.com/messaging/")
time.sleep(3)

# Extract elements
print("\n=== Extracting interactive elements ===")
elements = element_finder.extract_elements(web.page)
print(f"Found {len(elements)} interactive elements\n")

# Take highlighted screenshot
print("=== Taking highlighted screenshot ===")
path = highlight_screenshot.highlight_current_page(web.page)
print(f"Saved: {path}")

# Show first 20 elements
print("\nFirst 20 elements:")
for el in elements[:20]:
    text = el.text[:40] if el.text else (el.placeholder or el.aria_label or "")
    print(f"  [{el.index}] {el.tag} text='{text}' pos=({el.x},{el.y})")

# Test clicking on conversations
print("\n=== Testing Click Functionality ===")

# Click first 3 conversations
for i in range(1, 4):
    description = f"the conversation number {i}" if i > 1 else "the first conversation"
    print(f"\nClicking: {description}")
    result = web.click(description)
    print(f"  Result: {result}")
    time.sleep(2)

    # Take screenshot after each click
    path = highlight_screenshot.highlight_current_page(web.page)
    print(f"  Screenshot: {path}")

print("\n=== Test Complete ===")
web.close()
