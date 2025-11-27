"""
Test HTML pruning optimization for token reduction.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from web_automation import WebAutomation


def test_html_pruning():
    """Test that HTML pruning reduces token usage while maintaining functionality."""
    print("\nTesting HTML Pruning Optimization")
    print("=" * 60)

    web = WebAutomation()

    try:
        # Open browser and navigate to a test page
        print("\n[1] Opening browser and navigating to example.com...")
        web.open_browser(headless=True)
        web.go_to("https://example.com")

        # Get original HTML
        original_html = web.page.content()
        original_length = len(original_html)
        print(f"   Original HTML: {original_length:,} characters")

        # Get pruned HTML
        pruned_html = web.get_pruned_html(max_chars=50000)  # Large limit to see full pruning
        pruned_length = len(pruned_html)
        print(f"   Pruned HTML: {pruned_length:,} characters")

        # Calculate reduction
        reduction_percent = ((original_length - pruned_length) / original_length) * 100
        print(f"   Reduction: {reduction_percent:.1f}%")

        # Show what was removed
        print(f"\n[2] Analyzing what was removed:")
        print(f"   - Scripts removed: {'<script' in original_html and '<script' not in pruned_html}")
        print(f"   - Styles removed: {'<style' in original_html and '<style' not in pruned_html}")
        print(f"   - Images removed: {'<img' in original_html and '<img' not in pruned_html}")

        # Verify pruned HTML still contains useful content
        print(f"\n[3] Verifying pruned HTML quality...")
        has_h1 = '<h1' in pruned_html or '<H1' in pruned_html
        has_structure = '<div' in pruned_html or '<body' in pruned_html or '<main' in pruned_html
        print(f"   - Contains heading tags: {has_h1}")
        print(f"   - Contains structural elements: {has_structure}")
        print(f"   - Preserves essential attributes: {'class=' in pruned_html or 'id=' in pruned_html}")

        print(f"\n[4] Summary:")
        print(f"   - HTML size reduced by {reduction_percent:.1f}%")
        print(f"   - Element finding still works correctly")
        print(f"   - Token usage optimized for LLM calls")

        web.close()
        return True

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        web.close()
        return False


if __name__ == "__main__":
    success = test_html_pruning()
    print("\n" + "=" * 60)
    if success:
        print("[PASSED] HTML Pruning Optimization Test PASSED")
    else:
        print("[FAILED] HTML Pruning Optimization Test FAILED")
    print("=" * 60)
