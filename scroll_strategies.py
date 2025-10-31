"""
Scroll strategies for browser automation.

This module contains all scroll-related functions with automatic strategy selection
and verification using screenshot comparison.
"""

from typing import Callable, List, Tuple
from pydantic import BaseModel
from connectonion import llm_do


class ScrollStrategy(BaseModel):
    """AI-generated scroll strategy."""
    javascript: str
    explanation: str


def scroll_with_verification(
    page,
    take_screenshot: Callable,
    times: int = 5,
    description: str = "the main content area"
) -> str:
    """Universal scroll with automatic strategy selection and fallback.

    Tries multiple strategies in order until one works:
    1. AI-generated strategy (default)
    2. Element scrolling
    3. Page scrolling

    Args:
        page: Playwright page object
        take_screenshot: Function to take screenshots
        times: Number of scroll iterations
        description: What to scroll (natural language)

    Returns:
        Status message with successful strategy
    """
    if not page:
        return "Browser not open"

    print(f"\n📜 Starting universal scroll for: '{description}'")

    import time
    timestamp = int(time.time())
    before_file = f"scroll_before_{timestamp}.png"
    after_file = f"scroll_after_{timestamp}.png"

    # Take before screenshot
    take_screenshot(before_file)

    strategies = [
        ("AI-generated strategy", lambda: ai_scroll_strategy(page, times, description)),
        ("Element scrolling", lambda: element_scroll_strategy(page, times)),
        ("Page scrolling", lambda: page_scroll_strategy(page, times))
    ]

    for strategy_name, strategy_func in strategies:
        print(f"\n  Trying: {strategy_name}...")

        try:
            strategy_func()
            time.sleep(1)

            # Take after screenshot
            take_screenshot(after_file)

            # Verify scroll worked
            if screenshots_are_different(before_file, after_file):
                print(f"  ✅ {strategy_name} WORKED! Content changed.")
                return f"Scroll successful using {strategy_name}. Check {before_file} vs {after_file}"
            else:
                print(f"  ⚠️  {strategy_name} didn't change content. Trying next...")
                before_file = after_file
                after_file = f"scroll_after_{timestamp}_next.png"

        except Exception as e:
            print(f"  ❌ {strategy_name} failed: {e}")
            continue

    return "All scroll strategies failed. No visible content change."


def screenshots_are_different(file1: str, file2: str) -> bool:
    """Compare screenshots to verify content changed.

    Args:
        file1: First screenshot filename
        file2: Second screenshot filename

    Returns:
        True if screenshots are different
    """
    try:
        from PIL import Image
        import os

        path1 = os.path.join("screenshots", file1)
        path2 = os.path.join("screenshots", file2)

        img1 = Image.open(path1).convert('RGB')
        img2 = Image.open(path2).convert('RGB')

        # Calculate pixel difference
        diff = sum(
            abs(a - b)
            for pixel1, pixel2 in zip(img1.getdata(), img2.getdata())
            for a, b in zip(pixel1, pixel2)
        )

        # 1% threshold
        threshold = img1.size[0] * img1.size[1] * 3 * 0.01

        is_different = diff > threshold
        print(f"    Screenshot diff: {diff:.0f} (threshold: {threshold:.0f}) - {'DIFFERENT' if is_different else 'SAME'}")

        return is_different

    except Exception as e:
        print(f"    Warning: Screenshot comparison failed: {e}")
        return True  # Assume different if comparison fails


def ai_scroll_strategy(page, times: int, description: str):
    """AI-generated scroll strategy.

    Analyzes page structure and generates custom JavaScript.
    """
    # Find scrollable elements
    scrollable_elements = page.evaluate("""
        (() => {
            const scrollable = [];
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                if ((style.overflow === 'auto' || style.overflowY === 'scroll') &&
                    el.scrollHeight > el.clientHeight) {
                    scrollable.push({
                        tag: el.tagName,
                        classes: el.className,
                        id: el.id
                    });
                }
            });
            return scrollable;
        })()
    """)

    # Get simplified HTML
    simplified_html = page.evaluate("""
        (() => {
            const clone = document.body.cloneNode(true);
            clone.querySelectorAll('script, style, img, svg').forEach(el => el.remove());
            return clone.innerHTML.substring(0, 5000);
        })()
    """)

    # Generate scroll strategy using AI
    strategy = llm_do(
        f"""Generate JavaScript to scroll "{description}".

Scrollable elements: {scrollable_elements[:3]}
HTML structure: {simplified_html}

Return IIFE that scrolls the correct element:
(() => {{
  const el = document.querySelector('.selector');
  if (el) el.scrollTop += 1000;
  return {{success: true}};
}})()
""",
        output=ScrollStrategy,
        model="gpt-4o",
        temperature=0.1
    )

    print(f"    AI generated: {strategy.explanation}")

    # Execute scroll
    import time
    for i in range(times):
        page.evaluate(strategy.javascript)
        time.sleep(1.2)


def element_scroll_strategy(page, times: int):
    """Scroll first scrollable element found."""
    import time
    for i in range(times):
        page.evaluate("""
            (() => {
                const el = Array.from(document.querySelectorAll('*')).find(e => {
                    const s = window.getComputedStyle(e);
                    return (s.overflow === 'auto' || s.overflowY === 'scroll') &&
                           e.scrollHeight > e.clientHeight;
                });
                if (el) el.scrollTop += 1000;
            })()
        """)
        time.sleep(1)


def page_scroll_strategy(page, times: int):
    """Scroll the page window."""
    import time
    for i in range(times):
        page.evaluate("window.scrollBy(0, 1000)")
        time.sleep(1)


# Additional scroll helpers that can be called directly
def scroll_page(page, direction: str = "down", amount: int = 1000) -> str:
    """Scroll the page in a specific direction.

    Args:
        page: Playwright page object
        direction: "down", "up", "top", or "bottom"
        amount: Pixels to scroll

    Returns:
        Status message
    """
    if not page:
        return "Browser not open"

    if direction == "bottom":
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        return "Scrolled to bottom of page"
    elif direction == "top":
        page.evaluate("window.scrollTo(0, 0)")
        return "Scrolled to top of page"
    elif direction == "down":
        page.evaluate(f"window.scrollBy(0, {amount})")
        return f"Scrolled down {amount} pixels"
    elif direction == "up":
        page.evaluate(f"window.scrollBy(0, -{amount})")
        return f"Scrolled up {amount} pixels"
    else:
        return f"Unknown direction: {direction}"


def scroll_element(page, selector: str, amount: int = 1000) -> str:
    """Scroll a specific element by CSS selector.

    Args:
        page: Playwright page object
        selector: CSS selector for the element
        amount: Pixels to scroll

    Returns:
        Status message
    """
    if not page:
        return "Browser not open"

    result = page.evaluate(f"""
        (() => {{
            const element = document.querySelector('{selector}');
            if (!element) return 'Element not found: {selector}';

            const beforeScroll = element.scrollTop;
            element.scrollTop += {amount};
            const afterScroll = element.scrollTop;

            return `Scrolled from ${{beforeScroll}}px to ${{afterScroll}}px (delta: ${{afterScroll - beforeScroll}}px)`;
        }})()
    """)

    return result
