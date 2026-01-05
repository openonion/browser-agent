"""Test element_finder extraction and click functionality."""
import sys
from pathlib import Path
import pytest
import time

# Ensure tools can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import element_finder
from tools import highlight_screenshot

@pytest.mark.integration
@pytest.mark.screenshot
def test_element_extraction_and_click(web):
    """Test extracting elements and clicking using element finder."""
    
    # Open browser (headless for CI)
    print("=== Opening Browser ===")
    web.open_browser(headless=True)
    
    # Use a public site for testing
    web.go_to("https://example.com") 
    time.sleep(1)

    # Extract elements
    print("\n=== Extracting interactive elements ===")
    elements = element_finder.extract_elements(web.page)
    print(f"Found {len(elements)} interactive elements\n")
    
    assert len(elements) > 0, "Should find some elements on example.com"

    # Take highlighted screenshot
    print("=== Taking highlighted screenshot ===")
    path = highlight_screenshot.highlight_current_page(web.page)
    print(f"Saved: {path}")

    # Show first 20 elements (logging)
    print("\nFirst 20 elements:")
    for el in elements[:20]:
        text = el.text[:40] if el.text else (el.placeholder or el.aria_label or "")
        print(f"  [{el.index}] {el.tag} text='{text}' pos=({el.x},{el.y})")

    # Test clicking (using example.com 'More information...')
    print("\n=== Testing Click Functionality ===")
    description = "More information"
    print(f"\nClicking: {description}")
    
    # We expect this to work
    result = web.click(description)
    print(f"  Result: {result}")
    
    assert "Clicked" in result or "navigated" in result.lower(), f"Should click successfully: {result}"
    
    time.sleep(1)

    # Take screenshot after click
    path = highlight_screenshot.highlight_current_page(web.page)
    print(f"  Screenshot: {path}")

    print("\n=== Test Complete ===")
    # Web fixture handles closing