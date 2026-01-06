"""
Unified scroll module - AI-powered with fallback strategies.

"""
import os
import time
from pathlib import Path
from pydantic import BaseModel
from connectonion import llm_do

# Locate the prompt file (one level up from tools/)
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "scroll_strategy.md"
_PROMPT = _PROMPT_PATH.read_text()

class ScrollStrategy(BaseModel):
    method: str  # "window", "element", "container"
    selector: str
    javascript: str
    explanation: str

def scroll(page, take_screenshot, times: int = 5, description: str = "the main content area") -> str:
    """Universal scroll with AI strategy and fallback."""
    if not page:
        return "Browser not open"

    timestamp = int(time.time())
    before = f"scroll_before_{timestamp}.png"
    take_screenshot(filename=before)

    strategies = [
        ("AI strategy", lambda: _ai_scroll(page, times, description)),
        ("Element scroll", lambda: _element_scroll(page, times)),
        ("Page scroll", lambda: _page_scroll(page, times)),
    ]

    for name, execute in strategies:
        print(f"  Trying: {name}...")
        execute()
        time.sleep(0.5)
        after = f"scroll_after_{timestamp}.png"
        take_screenshot(filename=after)

        if _screenshots_different(before, after):
            print(f"  ✅ {name} worked")
            return f"Scrolled using {name}"
        
        print(f"  ⚠️ {name} didn't change content")
        before = after

    return "All scroll strategies failed"

def _ai_scroll(page, times: int, description: str):
    """AI-generated scroll strategy."""
    scrollable = page.evaluate("""
        (() => {
            return Array.from(document.querySelectorAll('*'))
                .filter(el => {
                    const s = window.getComputedStyle(el);
                    return (s.overflow === 'auto' || s.overflowY === 'scroll') &&
                           el.scrollHeight > el.clientHeight;
                })
                .slice(0, 3)
                .map(el => ({tag: el.tagName, classes: el.className, id: el.id}));
        })()
    """)

    html = page.evaluate("""
        (() => {
            const c = document.body.cloneNode(true);
            c.querySelectorAll('script,style,img,svg').forEach(e => e.remove());
            return c.innerHTML.substring(0, 5000);
        })()
    """)

    strategy = llm_do(
        _PROMPT.format(description=description, scrollable_elements=scrollable, simplified_html=html),
        output=ScrollStrategy,
        model="co/gemini-2.5-flash",
        temperature=0.1
    )
    print(f"    AI: {strategy.explanation}")

    for _ in range(times):
        page.evaluate(strategy.javascript)
        time.sleep(1)

def _element_scroll(page, times: int):
    """Scroll first scrollable element found."""
    for _ in range(times):
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
        time.sleep(0.8)

def _page_scroll(page, times: int):
    """Scroll window."""
    for _ in range(times):
        page.evaluate("window.scrollBy(0, 1000)")
        time.sleep(0.8)

def _screenshots_different(file1: str, file2: str) -> bool:
    """Compare screenshots using PIL pixel difference."""
    from PIL import Image
    path1 = os.path.join("screenshots", file1)
    path2 = os.path.join("screenshots", file2)
    
    if not os.path.exists(path1) or not os.path.exists(path2):
        return True

    img1 = Image.open(path1).convert('RGB')
    img2 = Image.open(path2).convert('RGB')

    diff = sum(
        abs(a - b)
        for p1, p2 in zip(img1.getdata(), img2.getdata())
        for a, b in zip(p1, p2)
    )
    threshold = img1.size[0] * img1.size[1] * 3 * 0.01
    return diff > threshold

# Maintain compatibility with web_automation.py
scroll_with_verification = scroll
