#!/usr/bin/env python3
"""
Test selector caching mechanism across browser sessions.
Uses Stack Overflow to test finding legal/footer links with natural language descriptions.

CACHE EXPLANATION:
==================
The browser agent uses an LLM to convert natural language descriptions
(like "the privacy policy link") into CSS selectors. This is expensive, so we cache results.

HOW IT WORKS:
1. First call: LLM analyzes HTML and generates CSS selector → saved to .selector_cache.json
2. Second call: Same description on same URL → retrieves cached selector (no LLM call)
3. Cache file persists across browser sessions → future runs are faster

CACHE KEY FORMAT:
{
  "normalized_url": {
    "description": "css_selector",
    "the privacy policy link": "a[href='/privacy']"
  }
}

EXPECTED BEHAVIOR:
- Run 1: Slower (calls LLM, builds cache)
- Run 2: Much faster (uses cache, no LLM calls)
- Performance improvement: typically 60-90% faster
"""
import time
import json
from pathlib import Path
import pytest
from web_automation import WebAutomation


@pytest.mark.integration
@pytest.mark.screenshot
def test_selector_cache():
    """Test that CSS selectors are cached and reused across browser sessions."""

    cache_file = Path(".selector_cache.json")

    # Clean slate - remove cache if exists
    # This ensures we test the full cycle: no cache → build cache → use cache
    if cache_file.exists():
        cache_file.unlink()
        print("[SETUP] Removed existing cache for clean test")

    print("\n[TEST] Run 1: Building cache with Stack Overflow")
    print("-" * 60)
    print("[INFO] This run will call LLM to generate CSS selectors")

    # === RUN 1: Build Cache ===
    web1 = WebAutomation(cache_persistent=True)

    try:
        web1.open_browser(headless=True)
        web1.go_to("https://stackoverflow.com")
        time.sleep(2)  # Let page load

        # Find legal/footer elements - these should trigger LLM calls and cache
        # Each call to find_element_by_description() will:
        # 1. Get pruned HTML from the page
        # 2. Send to LLM: "Find CSS selector for 'the privacy policy link'"
        # 3. LLM returns selector like "a[href*='privacy']"
        # 4. Selector is cached with key: (url, description)
        print("[RUN 1] Finding elements (should call LLM and cache)...")
        start_time = time.time()

        result1 = web1.find_element_by_description("the privacy policy link")
        print(f"  - Privacy Policy: {result1[:80]}")

        result2 = web1.find_element_by_description("the terms of service link")
        print(f"  - Terms of Service: {result2[:80]}")

        result3 = web1.find_element_by_description("the legal link in the footer")
        print(f"  - Legal link: {result3[:80]}")

        first_run_time = time.time() - start_time
        print(f"\n[RUN 1] Time taken: {first_run_time:.2f}s")

        # Take screenshot
        web1.take_screenshot("stackoverflow_run1.png")

        # Verify cache was created
        # Cache file should now contain mappings like:
        # {"stackoverflow.com": {"the privacy policy link": "a.some-selector"}}
        assert cache_file.exists(), "Cache file should be created after first run"

        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        initial_cache_size = len(cache_data)
        print(f"[RUN 1] Cache entries created: {initial_cache_size}")
        print(f"[INFO] Cache file location: {cache_file.absolute()}")
        assert initial_cache_size > 0, "Cache should have entries after first run"

    finally:
        web1.close()

    print("\n[TEST] Run 2: Using cached selectors")
    print("-" * 60)
    print("[INFO] This run should use cached selectors (no LLM calls)")

    # === RUN 2: Use Cache ===
    # Important: Create new WebAutomation instance to simulate new browser session
    # Cache persists because it's stored in .selector_cache.json file
    web2 = WebAutomation(cache_persistent=True)

    try:
        web2.open_browser(headless=True)
        web2.go_to("https://stackoverflow.com")
        time.sleep(2)  # Let page load

        # Find same elements - should use cache, no LLM calls
        # For each call, the system will:
        # 1. Check cache for (url, description) key
        # 2. Find cached selector
        # 3. Validate selector still works on page
        # 4. Return cached selector (no LLM call needed!)
        print("[RUN 2] Finding elements (should use cache)...")
        start_time = time.time()

        result1 = web2.find_element_by_description("the privacy policy link")
        print(f"  - Privacy Policy: {result1[:80]}")

        result2 = web2.find_element_by_description("the terms of service link")
        print(f"  - Terms of Service: {result2[:80]}")

        result3 = web2.find_element_by_description("the legal link in the footer")
        print(f"  - Legal link: {result3[:80]}")

        second_run_time = time.time() - start_time
        print(f"\n[RUN 2] Time taken: {second_run_time:.2f}s")

        # Take screenshot
        web2.take_screenshot("stackoverflow_run2.png")

        # Verify cache wasn't modified (no new entries)
        # If cache is working correctly:
        # - No new entries should be added
        # - Cache size should remain the same
        # - No LLM calls should have been made
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        final_cache_size = len(cache_data)
        print(f"[RUN 2] Cache entries: {final_cache_size}")
        print(f"[VERIFY] Cache reused: {initial_cache_size == final_cache_size}")

        assert final_cache_size == initial_cache_size, \
            f"Cache should not grow (reused existing). Was {initial_cache_size}, now {final_cache_size}"

        # Verify cache made it faster
        time_improvement = first_run_time - second_run_time
        improvement_percent = (time_improvement / first_run_time) * 100

        print(f"\n[RESULTS] Performance comparison:")
        print(f"  First run:  {first_run_time:.2f}s (with LLM calls)")
        print(f"  Second run: {second_run_time:.2f}s (cached)")
        print(f"  Improvement: {time_improvement:.2f}s ({improvement_percent:.1f}% faster)")

        # Second run should be faster (cached lookups)
        # Allow some variance, but should be noticeably faster
        assert second_run_time < first_run_time, \
            f"Cached run should be faster. First: {first_run_time:.2f}s, Second: {second_run_time:.2f}s"

        # Verify screenshots exist
        screenshot1 = Path("screenshots/stackoverflow_run1.png")
        screenshot2 = Path("screenshots/stackoverflow_run2.png")
        assert screenshot1.exists(), "First screenshot should exist"
        assert screenshot2.exists(), "Second screenshot should exist"

        print(f"\n[SUCCESS] Cache test passed!")
        print(f"  - Cache entries: {final_cache_size}")
        print(f"  - Speed improvement: {improvement_percent:.1f}%")
        print(f"  - Screenshots saved to screenshots/")

    finally:
        web2.close()


if __name__ == "__main__":
    # Run directly for quick testing
    test_selector_cache()
