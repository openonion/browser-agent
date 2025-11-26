"""
Purpose: Provides natural language browser automation primitives via Playwright
LLM-Note:
  Dependencies: imports from [typing, connectonion.xray/llm_do, playwright.sync_api, base64, json, logging, pydantic] | imported by [agent.py, tests/direct_test.py, tests/test_all.py] | tested by [tests/test_all.py, tests/direct_test.py]
  Data flow: agent.py creates web=WebAutomation() → exposes 15+ @xray decorated methods as tools → methods receive natural language descriptions → find_element_by_description() uses llm_do(HTML→CSS selector) with gpt-4o → playwright.sync_api executes browser actions → returns descriptive status strings
  State/Effects: maintains self.playwright/browser/page/current_url/form_data state | playwright.chromium.launch() creates browser process | page.goto()/click()/fill() mutate DOM | take_screenshot() writes to screenshots/*.png | close() terminates browser process
  Integration: exposes 15 tools (open_browser, go_to, click, type_text, take_screenshot, find_forms, fill_form, submit_form, select_option, check_checkbox, wait_for_element, wait_for_text, extract_data, get_text, close) | all methods return str (success/error messages, not exceptions) | @xray decorator logs behavior to ~/.connectonion/ | llm_do() calls for AI-powered element finding and form filling
  Performance: AI element finder uses llm_do() with gpt-4o (100-500ms) | HTML analysis limited to first 15000 chars | find_element_by_description() has text-matching fallback if AI fails | browser operations are synchronous playwright.sync_api | screenshots auto-create screenshots/ directory
  Errors: methods return error strings (not raise) - "Browser not open", "Could not find element", "Navigation failed" | AI selector may fail on dynamic sites → falls back to text matching | form submission tries 6 button patterns before failing
  ⚠️ Performance: find_element_by_description() calls LLM for every element lookup - cache results in calling code if reusing selectors
  ⚠️ Security: llm_do() sends page HTML to external API (gpt-4o) - avoid on pages with sensitive data
"""

from typing import Optional, List, Dict, Any, Literal
from connectonion import xray, llm_do
from playwright.sync_api import sync_playwright, Page, Browser, Playwright
import base64
import json
import logging
from pydantic import BaseModel, Field
import scroll_strategies

logger = logging.getLogger(__name__)


# Simple, clear data models
class FormField(BaseModel):
    """A form field on a web page."""
    name: str = Field(..., description="Field name or identifier")
    label: str = Field(..., description="User-facing label")
    type: str = Field(..., description="Input type (text, email, select, etc.)")
    value: Optional[str] = Field(None, description="Current value")
    required: bool = Field(False, description="Is this field required?")
    options: List[str] = Field(default_factory=list, description="Available options for select/radio")


class WebAutomation:
    """Web browser automation with form handling capabilities.

    Simple interface for complex web interactions.
    """

    def __init__(
        self,
        use_chrome_profile: bool = False,
        cache_selectors: bool = True,
        cache_persistent: bool = False
    ):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.current_url: str = ""
        self.form_data: Dict[str, Any] = {}
        self.use_chrome_profile = use_chrome_profile

        # Selector caching configuration
        self.cache_selectors = cache_selectors
        self.cache_persistent = cache_persistent
        self._selector_cache: Dict[str, Dict[str, str]] = {}  # {url: {description: selector}}
        self._cache_hits = 0
        self._cache_misses = 0

        # Multi-tab management
        self.pages: Dict[str, Page] = {}  # {name: page}
        self.active_page_name: Optional[str] = None
        self._page_counter = 0  # For auto-naming tabs

        # Load persistent cache if enabled
        if self.cache_persistent:
            self._load_cache_from_file()

    def _get_cache_file_path(self) -> str:
        """Get the path to the cache file in project root."""
        from pathlib import Path
        return str(Path.cwd() / ".selector_cache.json")

    def _register_page(self, page: Page, name: str = None) -> str:
        """Register a page in the tabs dictionary and set as active."""
        if name is None:
            name = f"tab_{self._page_counter}"
            self._page_counter += 1

        self.pages[name] = page
        self.active_page_name = name
        self.page = page  # Keep backward compatibility
        return name

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent cache keys.

        - Convert to lowercase
        - Strip trailing slashes
        - Keep query parameters (different params might mean different layouts)
        """
        normalized = url.lower().rstrip('/')
        return normalized

    def _load_cache_from_file(self) -> None:
        """Load cache from disk if it exists."""
        cache_path = self._get_cache_file_path()
        try:
            import os
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    self._selector_cache = json.load(f)
                logger.info(f"Loaded selector cache from {cache_path} ({len(self._selector_cache)} URLs)")
        except Exception as e:
            logger.warning(f"Could not load cache file: {e}. Starting with empty cache.")
            self._selector_cache = {}

    def _save_cache_to_file(self) -> None:
        """Save cache to disk."""
        if not self.cache_persistent:
            return

        cache_path = self._get_cache_file_path()
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(self._selector_cache, f, indent=2)
            logger.debug(f"Saved selector cache to {cache_path}")
        except Exception as e:
            logger.warning(f"Could not save cache file: {e}")

    def open_browser(self, headless: bool = False) -> str:
        """Open a new browser wiFalse

        Note: If use_chrome_profile=True, Chrome must be completely closed before running.
        """
        if self.browser:
            return "Browser already open"

        import os
        from pathlib import Path

        self.playwright = sync_playwright().start()

        if self.use_chrome_profile:
            # Use Chromium with Chrome profile copy (avoids Chrome 136 restrictions)
            chromium_profile = Path.cwd() / "chromium_automation_profile"

            # If profile doesn't exist, copy it from user's Chrome
            if not chromium_profile.exists():
                import shutil

                # Determine source Chrome profile path
                home = Path.home()
                if os.name == 'nt':  # Windows
                    source_profile = home / "AppData/Local/Google/Chrome/User Data"
                elif os.uname().sysname == 'Darwin':  # macOS
                    source_profile = home / "Library/Application Support/Google/Chrome"
                else:  # Linux
                    source_profile = home / ".config/google-chrome"

                if source_profile.exists():
                    # Copy profile (exclude caches for speed)
                    shutil.copytree(
                        source_profile,
                        chromium_profile,
                        ignore=shutil.ignore_patterns('*Cache*', '*cache*', 'Service Worker', 'ShaderCache'),
                        dirs_exist_ok=True
                    )

            # Launch Chromium with persistent context using copied Chrome profile
            self.browser = self.playwright.chromium.launch_persistent_context(
                str(chromium_profile),
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                ],
                ignore_default_args=['--enable-automation'],
                timeout=120000,  # 120 seconds timeout
            )
            self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()

            # Hide webdriver property
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            # Register initial page as main tab
            self._register_page(self.page, "main")

            return f"Browser opened with Chromium using Chrome profile: {chromium_profile}"
        else:
            # Default behavior: launch without profile
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.page = self.browser.new_page()

            # Register initial page as main tab
            self._register_page(self.page, "main")

            return "Browser opened successfully"

    def go_to(self, url: str) -> str:
        """Navigate to a URL."""
        if not self.page:
            return "Browser not open. Call open_browser() first"

        self.page.goto(url, wait_until="load")
        self.current_url = self.page.url
        return f"Navigated to {self.current_url}"

    def get_pruned_html(self, max_chars: int = 15000) -> str:
        """Get pruned HTML optimized for LLM analysis.

        Removes noise (scripts, styles, images) and unnecessary attributes
        to reduce token usage while preserving element-finding capability.

        Args:
            max_chars: Maximum characters to return

        Returns:
            Pruned HTML string
        """
        if not self.page:
            return ""

        pruned_html = self.page.evaluate("""
            (() => {
                // Clone the body to avoid modifying the actual page
                const clone = document.body.cloneNode(true);

                // Remove noise tags that don't help with element finding
                clone.querySelectorAll('script, style, img, svg, noscript, iframe, video, audio').forEach(el => el.remove());

                // Remove hidden elements (optional - can be disabled if needed)
                clone.querySelectorAll('[style*="display: none"], [style*="visibility: hidden"]').forEach(el => {
                    // Keep hidden inputs as they might be important for forms
                    if (el.tagName !== 'INPUT') {
                        el.remove();
                    }
                });

                // Simplify attributes - keep only what's useful for finding elements
                const simplify = (el) => {
                    Array.from(el.children).forEach(child => {
                        const attrs = Array.from(child.attributes);
                        attrs.forEach(attr => {
                            // Keep only useful attributes for element finding
                            if (!['class', 'id', 'role', 'type', 'name', 'placeholder', 'aria-label', 'aria-labelledby', 'href', 'value'].includes(attr.name)) {
                                child.removeAttribute(attr.name);
                            }
                        });
                        simplify(child);
                    });
                };

                simplify(clone);
                return clone.innerHTML;
            })()
        """)

        # Truncate to max_chars
        return pruned_html[:max_chars]

    def find_element_by_description(self, description: str) -> str:
        """Find an element on the page using natural language description.

        Uses AI to analyze the HTML and find the best matching element for your description.
        Results are cached to avoid expensive LLM calls for repeated lookups.

        Args:
            description: Natural language description of what you're looking for
                        e.g., "the submit button", "email input field", "main navigation menu"

        Returns:
            CSS selector for the found element, or error message
        """
        if not self.page:
            return "Browser not open"

        # Check cache if enabled
        if self.cache_selectors:
            normalized_url = self._normalize_url(self.page.url)

            # Check if we have a cached selector for this URL and description
            if normalized_url in self._selector_cache:
                if description in self._selector_cache[normalized_url]:
                    cached_selector = self._selector_cache[normalized_url][description]

                    # Validate cached selector still works
                    if self.page.locator(cached_selector).count() > 0:
                        self._cache_hits += 1
                        logger.info(f"✓ Cache hit: '{description}' → {cached_selector}")
                        return cached_selector
                    else:
                        # Cached selector is stale, regenerate
                        logger.warning(f"Cache stale for '{description}', regenerating...")

        # Cache miss or disabled - call LLM
        self._cache_misses += 1
        logger.info(f"✗ Cache miss: '{description}' - calling LLM...")

        # Get pruned HTML for analysis (optimized for LLM)
        html = self.get_pruned_html(max_chars=15000)

        # Use AI to find the best selector
        class ElementSelector(BaseModel):
            selector: str = Field(..., description="CSS selector for the element")
            confidence: float = Field(..., description="Confidence score 0-1")
            explanation: str = Field(..., description="Why this element matches")

        result = llm_do(
            f"""Analyze this HTML and find the CSS selector for: "{description}"

            HTML (pruned, up to 15000 chars): {html}

            Return the most specific CSS selector that uniquely identifies this element.
            Consider id, class, type, attributes, and position in DOM.
            """,
            output=ElementSelector,
            model="co/gpt-4o",  # Use ConnectOnion managed API key
            temperature=0.1
        )

        # Verify the selector works
        if self.page.locator(result.selector).count() > 0:
            # Store in cache if enabled
            if self.cache_selectors:
                normalized_url = self._normalize_url(self.page.url)
                if normalized_url not in self._selector_cache:
                    self._selector_cache[normalized_url] = {}
                self._selector_cache[normalized_url][description] = result.selector

                # Save to file if persistent caching enabled
                self._save_cache_to_file()

                logger.info(f"Cached selector for '{description}' on {normalized_url}")

            return result.selector
        else:
            return f"Found selector {result.selector} but element not on page"

    def click(self, description: str) -> str:
        """Click on an element using natural language description.

        Args:
            description: Natural language description like "the blue submit button"
                        or "the email field" or "link to contact page"
        """
        if not self.page:
            return "Browser not open"

        # First find the element using natural language
        selector = self.find_element_by_description(description)

        if selector.startswith("Could not") or selector.startswith("Found selector"):
            # Fallback to simple text matching
            if self.page.locator(f"text='{description}'").count() > 0:
                self.page.click(f"text='{description}'")
                return f"Clicked on '{description}' (by text)"
            return selector  # Return the error

        # Click the found element
        self.page.click(selector)
        return f"Clicked on '{description}' (selector: {selector})"


    def type_text(self, field_description: str, text: str) -> str:
        """Type text into a form field using natural language description.

        Args:
            field_description: Natural language description of the field
                              e.g., "email field", "password input", "comment box"
            text: The text to type into the field
        """
        if not self.page:
            return "Browser not open"

        # Find the field using natural language
        selector = self.find_element_by_description(field_description)

        if selector.startswith("Could not") or selector.startswith("Found selector"):
            # Fallback to simple matching
            for fallback in [
                f"input[placeholder*='{field_description}' i]",
                f"[aria-label*='{field_description}' i]",
                f"input[name*='{field_description}' i]"
            ]:
                if self.page.locator(fallback).count() > 0:
                    self.page.fill(fallback, text)
                    self.form_data[field_description] = text
                    return f"Typed into {field_description}"
            return f"Could not find field '{field_description}'"

        # Fill the found field
        self.page.fill(selector, text)
        self.form_data[field_description] = text
        return f"Typed into {field_description} (selector: {selector})"


    def get_text(self) -> str:
        """Get all visible text from the page."""
        if not self.page:
            return "Browser not open"

        text = self.page.inner_text("body")
        return text

    @xray
    def take_screenshot(self, filename: str = None) -> str:
        """Take a screenshot of the current page and return base64 encoded image."""
        if not self.page:
            return "Browser not open"

        import os
        from datetime import datetime

        # Create screenshots directory if it doesn't exist
        os.makedirs("screenshots", exist_ok=True)

        # Auto-generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"step_{timestamp}.png"

        # Always save in screenshots folder unless full path provided
        if not "/" in filename:
            filename = f"screenshots/{filename}"

        # Take screenshot and get bytes
        screenshot_bytes = self.page.screenshot(path=filename)

        # Encode to base64 for LLM vision
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

        # Return in data URL format so image_result_formatter plugin can process it
        return f"data:image/png;base64,{screenshot_base64}"

    def find_forms(self) -> List[FormField]:
        """Find all form fields on the current page."""
        if not self.page:
            return []

        # Get all form inputs using JavaScript
        fields_data = self.page.evaluate("""
            () => {
                const fields = [];
                const inputs = document.querySelectorAll('input, textarea, select');

                inputs.forEach(input => {
                    const label = input.labels?.[0]?.textContent ||
                                input.placeholder ||
                                input.name ||
                                input.id ||
                                'Unknown';

                    fields.push({
                        name: input.name || input.id || label,
                        label: label.trim(),
                        type: input.type || input.tagName.toLowerCase(),
                        value: input.value || '',
                        required: input.required || false,
                        options: input.tagName === 'SELECT' ?
                                Array.from(input.options).map(o => o.text) : []
                    });
                });

                return fields;
            }
        """)

        return [FormField(**field) for field in fields_data]

    def fill_form(self, data: Dict[str, str]) -> str:
        """Fill multiple form fields at once."""
        if not self.page:
            return "Browser not open"

        results = []
        for field_name, value in data.items():
            result = self.type_text(field_name, value)
            results.append(f"{field_name}: {result}")

        return "\n".join(results)

    def submit_form(self) -> str:
        """Submit the current form."""
        if not self.page:
            return "Browser not open"

        # Try common submit buttons
        for selector in [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit')",
            "button:has-text('Send')",
            "button:has-text('Continue')",
            "button:has-text('Next')"
        ]:
            if self.page.locator(selector).count() > 0:
                self.page.click(selector)
                return "Form submitted"

        # Try pressing Enter in the last form field
        if self.form_data:
            last_field = list(self.form_data.keys())[-1]
            self.page.press(f"input[name='{last_field}']", "Enter")
            return "Form submitted with Enter key"

        return "Could not find submit button"

    def select_option(self, field_description: str, option: str) -> str:
        """Select an option from a dropdown using natural language.

        Args:
            field_description: Natural description of the dropdown
            option: The option text to select
        """
        if not self.page:
            return "Browser not open"

        selector = self.find_element_by_description(field_description)

        if selector.startswith("Could not"):
            return selector

        # Select the option
        self.page.select_option(selector, label=option)
        return f"Selected '{option}' in {field_description}"


    def check_checkbox(self, description: str, checked: bool = True) -> str:
        """Check or uncheck a checkbox using natural language.

        Args:
            description: Natural description of the checkbox
            checked: True to check, False to uncheck
        """
        if not self.page:
            return "Browser not open"

        selector = self.find_element_by_description(description)

        if selector.startswith("Could not"):
            return selector

        if checked:
            self.page.check(selector)
            return f"Checked {description}"
        else:
            self.page.uncheck(selector)
            return f"Unchecked {description}"


    def wait_for_element(self, description: str, timeout: int = 30) -> str:
        """Wait for an element described in natural language to appear.

        Args:
            description: Natural language description of the element
            timeout: Maximum wait time in seconds
        """
        if not self.page:
            return "Browser not open"

        # Find the selector first
        selector = self.find_element_by_description(description)

        if selector.startswith("Could not"):
            # Try waiting for text instead
            self.page.wait_for_selector(f"text='{description}'", timeout=timeout * 1000)
            return f"Found text: '{description}'"

        self.page.wait_for_selector(selector, timeout=timeout * 1000)
        return f"Element appeared: {description}"


    def wait_for_text(self, text: str, timeout: int = 30) -> str:
        """Wait for specific text to appear on the page."""
        if not self.page:
            return "Browser not open"

        self.page.wait_for_selector(f"text='{text}'", timeout=timeout * 1000)
        return f"Found text: '{text}'"

    @xray
    def analyze_page(self, question: str) -> str:
        """Ask a question about the current page content using AI.

        Uses pruned HTML for efficient token usage.

        Args:
            question: Natural language question about the page
                     e.g., "What are the main navigation items?", "Is there a login form?"

        Returns:
            AI-generated answer based on page content
        """
        if not self.page:
            return "Browser not open"

        # Get pruned HTML (optimized for LLM)
        html = self.get_pruned_html(max_chars=20000)  # Larger limit for analysis

        return llm_do(
            f"Based on this HTML content, {question}\n\n{html}",
            model="co/gpt-4o",  # Use ConnectOnion managed API key
            temperature=0.3
        )

    def extract_data(self, selector: str) -> List[str]:
        """Extract data from elements matching a selector."""
        if not self.page:
            return []

        elements = self.page.locator(selector)
        count = elements.count()

        data = []
        for i in range(count):
            text = elements.nth(i).inner_text()
            data.append(text)

        return data

    @xray
    def scroll(self, times: int = 5, description: str = "the main content area") -> str:
        """Universal scroll with automatic strategy selection and verification.

        This is the MAIN scroll method you should use. It:
        1. Tries AI-generated strategy first (analyzes page, creates custom JS)
        2. Falls back to element scrolling if AI fails
        3. Falls back to page scrolling if element fails
        4. Verifies success by comparing screenshots

        Args:
            times: Number of scroll iterations
            description: What to scroll (e.g., "the email list", "the news feed")

        Returns:
            Status message with successful strategy

        Example:
            web.scroll(5, "the email inbox")
            web.scroll(10, "the product list")
        """
        return scroll_strategies.scroll_with_verification(
            page=self.page,
            take_screenshot=self.take_screenshot,
            times=times,
            description=description
        )

    def scroll_page(self, direction: str = "down", amount: int = 1000) -> str:
        """Scroll the page up or down.

        Args:
            direction: "down" or "up" or "bottom" or "top"
            amount: Number of pixels to scroll (ignored for "bottom"/"top")

        Returns:
            Confirmation message
        """
        if not self.page:
            return "Browser not open"

        if direction == "bottom":
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            return "Scrolled to bottom of page"
        elif direction == "top":
            self.page.evaluate("window.scrollTo(0, 0)")
            return "Scrolled to top of page"
        elif direction == "down":
            self.page.evaluate(f"window.scrollBy(0, {amount})")
            return f"Scrolled down {amount} pixels"
        elif direction == "up":
            self.page.evaluate(f"window.scrollBy(0, -{amount})")
            return f"Scrolled up {amount} pixels"
        else:
            return f"Unknown direction: {direction}. Use 'up', 'down', 'top', or 'bottom'"

    def scroll_element(self, selector: str, amount: int = 1000) -> str:
        """Scroll a specific element (useful for Gmail's email list container).

        This tries multiple methods to scroll an element:
        1. Find the element by selector
        2. Try scrolling it with JavaScript
        3. Try keyboard navigation if JS fails

        Args:
            selector: CSS selector for the element to scroll (e.g., '[role="main"]' for Gmail)
            amount: Pixels to scroll down

        Returns:
            Status message
        """
        if not self.page:
            return "Browser not open"

        # Method 1: Try direct element scrolling with JavaScript
        result = self.page.evaluate(f"""
            (() => {{
                const element = document.querySelector('{selector}');
                if (!element) return 'Element not found: {selector}';

                // Get scroll position before
                const beforeScroll = element.scrollTop;

                // Scroll the element
                element.scrollTop += {amount};

                // Get scroll position after
                const afterScroll = element.scrollTop;

                return `Scrolled element from ${{beforeScroll}}px to ${{afterScroll}}px (delta: ${{afterScroll - beforeScroll}}px)`;
            }})()
        """)

        return result

    def scroll_with_ai_strategy(self, times: int = 5, description: str = "the main content area") -> str:
        """Scroll ANY website using AI-generated strategy based on page analysis.

        This method:
        1. Analyzes the page to find scrollable elements
        2. Uses AI to determine the best scrolling strategy
        3. Tests scrolling and verifies with screenshots
        4. Works for any website, not just Gmail

        Args:
            times: Number of times to scroll
            description: Natural language description of what to scroll (e.g., "the email list", "the feed")

        Returns:
            Status message with results and verification
        """
        if not self.page:
            return "Browser not open"

        print(f"\n🔍 Investigating page structure to determine scroll strategy...")

        # Step 1: Find all scrollable elements on the page
        scrollable_elements = self.page.evaluate("""
            (() => {
                const allElements = Array.from(document.querySelectorAll('*'));
                const scrollable = [];

                allElements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    const hasOverflow = style.overflow === 'auto' || style.overflow === 'scroll' ||
                                       style.overflowY === 'auto' || style.overflowY === 'scroll';

                    if (hasOverflow && el.scrollHeight > el.clientHeight) {
                        scrollable.push({
                            tag: el.tagName,
                            classes: el.className,
                            id: el.id,
                            role: el.getAttribute('role'),
                            scrollHeight: el.scrollHeight,
                            clientHeight: el.clientHeight,
                            scrollTop: el.scrollTop,
                            canScroll: el.scrollHeight > el.clientHeight
                        });
                    }
                });

                return scrollable;
            })()
        """)

        print(f"  Found {len(scrollable_elements)} scrollable elements")

        # Step 2: Get simplified HTML structure (using pruned HTML)
        simplified_html = self.get_pruned_html(max_chars=5000)

        # Step 3: Use AI to determine scroll strategy
        from pydantic import BaseModel

        class ScrollStrategy(BaseModel):
            method: str  # "window", "element", "container"
            selector: str  # CSS selector if method is "element" or "container"
            javascript: str  # JavaScript code to execute for scrolling
            explanation: str

        strategy = llm_do(
            f"""Analyze this webpage and determine the BEST way to scroll "{description}".

Scrollable elements found:
{scrollable_elements[:3]}

Simplified HTML (first 5000 chars):
{simplified_html}

Determine the scrolling strategy. Return:
1. method: "window" (scroll whole page), "element" (scroll specific element), or "container" (scroll a container)
2. selector: CSS selector for the scrollable element (if method is element/container)
3. javascript: Complete IIFE JavaScript code to scroll, like:
   (() => {{
     const el = document.querySelector('.selector');
     if (el) el.scrollTop += 1000;
     return {{success: true, scrolled: el.scrollTop}};
   }})()
4. explanation: Why this method will work

User wants to scroll: "{description}"
""",
            output=ScrollStrategy,
            model="co/gpt-4o",  # Use ConnectOnion managed API key
            temperature=0.1
        )

        print(f"\n📋 AI Strategy: {strategy.method}")
        print(f"   Selector: {strategy.selector}")
        print(f"   Explanation: {strategy.explanation}")

        # Step 4: Take BEFORE screenshot
        self.take_screenshot("smart_scroll_before.png")

        # Step 5: Test the scroll
        results = []
        for i in range(times):
            result = self.page.evaluate(strategy.javascript)
            results.append(result)
            print(f"   Scroll {i+1}/{times}: {result}")

            import time
            time.sleep(1.2)

        # Step 6: Take AFTER screenshot
        self.take_screenshot("smart_scroll_after.png")

        # Step 7: Verify scrolling worked
        print(f"\n✅ Scroll complete. Check screenshots:")
        print(f"   - smart_scroll_before.png")
        print(f"   - smart_scroll_after.png")
        print(f"   If content is different, scrolling WORKS!")

        return f"AI-strategy scroll completed using method: {strategy.method}. Results: {results}. Check screenshots for verification."

    def wait_for_manual_login(self, site_name: str = "the website") -> str:
        """Pause automation and wait for user to login manually.

        Args:
            site_name: Name of the site user needs to login to (e.g., "Gmail")

        Returns:
            Confirmation message when user is ready to continue
        """
        if not self.page:
            return "Browser not open"

        print(f"\n{'='*60}")
        print(f"[PAUSE] MANUAL LOGIN REQUIRED")
        print(f"{'='*60}")
        print(f"Please login to {site_name} in the browser window.")
        print(f"Once you're logged in and ready to continue:")
        print(f"  Type 'yes' or 'Y' and press Enter")
        print(f"{'='*60}\n")

        while True:
            response = input("Ready to continue? (yes/Y): ").strip().lower()
            if response in ['yes', 'y']:
                print("[OK] Continuing automation...\n")
                return f"User confirmed login to {site_name} - continuing automation"
            else:
                print("Please type 'yes' or 'Y' when ready.")

    @xray
    def get_cache_stats(self) -> str:
        """Get statistics about selector cache usage.

        Returns:
            Human-readable cache statistics including hits, misses, and hit rate
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0

        # Count total cached selectors
        total_cached = sum(len(selectors) for selectors in self._selector_cache.values())

        stats = f"""Selector Cache Statistics:
  Cache enabled: {self.cache_selectors}
  Persistent cache: {self.cache_persistent}
  Cache file: {self._get_cache_file_path() if self.cache_persistent else 'N/A'}

  Total requests: {total_requests}
  Cache hits: {self._cache_hits}
  Cache misses: {self._cache_misses}
  Hit rate: {hit_rate:.1f}%

  Cached selectors: {total_cached} across {len(self._selector_cache)} URLs"""

        return stats

    def close(self) -> str:
        """Close the browser and all tabs."""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

        self.page = None
        self.browser = None
        self.playwright = None
        self.pages = {}
        self.active_page_name = None

        return "Browser closed"

    @xray
    def new_tab(self, url: str = None, name: str = None) -> str:
        """Open a new tab, optionally navigate to URL.

        Args:
            url: Optional URL to navigate to
            name: Optional name for the tab (auto-generated if not provided)

        Returns:
            Success message with tab name
        """
        if not self.browser:
            return "Browser not open. Call open_browser() first"

        # Create new page
        new_page = self.browser.new_page()

        # Register the page
        tab_name = self._register_page(new_page, name)

        # Navigate if URL provided
        if url:
            new_page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return f"Opened new tab '{tab_name}' and navigated to {url}"
        else:
            return f"Opened new tab '{tab_name}'"

    @xray
    def switch_to_tab(self, name: str) -> str:
        """Switch active context to a named tab.

        Args:
            name: Name of the tab to switch to

        Returns:
            Success message with tab info
        """
        if name not in self.pages:
            available = ", ".join(self.pages.keys())
            return f"Tab '{name}' not found. Available tabs: {available}"

        self.page = self.pages[name]
        self.active_page_name = name
        current_url = self.page.url

        return f"Switched to tab '{name}' (currently at: {current_url})"

    @xray
    def list_tabs(self) -> str:
        """List all open tabs with their URLs.

        Returns:
            Formatted list of tabs
        """
        if not self.pages:
            return "No tabs open"

        tab_list = []
        for name, page in self.pages.items():
            active_marker = "[ACTIVE]" if name == self.active_page_name else ""
            tab_list.append(f"  {active_marker} {name}: {page.url}")

        return "Open tabs:\n" + "\n".join(tab_list)

    @xray
    def close_tab(self, name: str) -> str:
        """Close a specific tab by name.

        Args:
            name: Name of the tab to close

        Returns:
            Success message
        """
        if name not in self.pages:
            available = ", ".join(self.pages.keys())
            return f"Tab '{name}' not found. Available tabs: {available}"

        # Don't allow closing the last tab
        if len(self.pages) == 1:
            return "Cannot close the last tab. Use close() to close the browser instead"

        # Close the page
        page_to_close = self.pages[name]
        page_to_close.close()
        del self.pages[name]

        # If we closed the active tab, switch to another
        if name == self.active_page_name:
            # Switch to first available tab
            new_active = next(iter(self.pages.keys()))
            self.page = self.pages[new_active]
            self.active_page_name = new_active
            return f"Closed tab '{name}' and switched to '{new_active}'"
        else:
            return f"Closed tab '{name}'"


# Standalone helper functions for AI-powered analysis
def analyze_page(html_content: str, question: str) -> str:
    """Ask a question about page content using AI."""
    return llm_do(
        f"Based on this HTML content, {question}\n\n {html_content}",
        model="co/gpt-4o",  # Use ConnectOnion managed API key
        temperature=0.3
    )


def smart_fill_form(fields: List[FormField], user_info: str) -> Dict[str, str]:
    """Generate smart form values based on user information."""

    class FormData(BaseModel):
        values: Dict[str, str]

    field_descriptions = "\n".join([
        f"- {f.name}: {f.label} ({f.type}, required: {f.required})"
        for f in fields
    ])

    result = llm_do(
        f"""Generate appropriate form values based on this user info:

        {user_info}

        Form fields:
        {field_descriptions}

        Return a dictionary with field names as keys and appropriate values.""",
        output=FormData,
        model="co/gpt-4o",  # Use ConnectOnion managed API key
        temperature=0.7
    )

    return result.values


def detect_page_type(url: str, text: str) -> str:
    """Detect what type of page we're on (login, signup, application, etc)."""

    # Simple heuristic detection
    text_lower = text.lower()

    if "sign in" in text_lower or "log in" in text_lower:
        return "login"
    elif "sign up" in text_lower or "create account" in text_lower:
        return "signup"
    elif "application" in text_lower or "apply" in text_lower:
        return "application"
    elif "checkout" in text_lower or "payment" in text_lower:
        return "checkout"
    elif "profile" in text_lower or "settings" in text_lower:
        return "profile"
    else:
        return "general"


def validate_form_data(fields: List[FormField]) -> Dict[str, bool]:
    """Check which required fields are filled."""
    validation = {}

    for field in fields:
        if field.required:
            validation[field.name] = bool(field.value and field.value.strip())

    return validation