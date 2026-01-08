"""
Purpose: Provides natural language browser automation primitives via Playwright.
"""

from typing import Optional, List, Dict, Any, Union
import os
from pathlib import Path
import base64
from pydantic import BaseModel, Field

from connectonion import xray, llm_do
from playwright.sync_api import sync_playwright, Page, Playwright

from . import scroll_strategies
from .element_finder import find_element



class WebAutomation:
    """Web browser automation with form handling capabilities.

    Simple interface for complex web interactions.
    """

    def __init__(self, headless: bool = False, profile_path: str = None):
        self.playwright: Optional[Playwright] = None
        self.context: Optional[Any] = None
        self.page: Optional[Page] = None
        self.current_url: str = ""
        self.form_data: Dict[str, Any] = {}
        self.headless = headless
        
        self.screenshots_dir = "screenshots"
        self.DEFAULT_AI_MODEL = os.getenv("BROWSER_AGENT_MODEL", "co/gemini-2.5-flash")
        
        # Session storage path
        self.session_file = Path.cwd() / ".co" / "browser_session.json"
        
        # Chrome profile path
        if profile_path:
            self.chrome_profile_path = str(profile_path)
        else:
            self.chrome_profile_path = str(Path.cwd() / ".co" / "chrome_profile")

    def open_browser(self, headless: Union[bool, str, None] = None) -> str:
        """Open a new browser window."""
        if isinstance(headless, str):
            headless = headless.lower() == 'true'

        if headless is None:
            headless = self.headless

        self.playwright = sync_playwright().start()

        self.context = self.playwright.chromium.launch_persistent_context(
                self.chrome_profile_path,
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                ],
                ignore_default_args=['--enable-automation'],
                timeout=120000,
            )
        
        self.page = self.context.new_page()
        self.page.set_default_navigation_timeout(60000)

        self.page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
        )

        return "Browser opened successfully"

    def go_to(self, url: str) -> str:
        """Navigate to a URL."""
        self.page.goto(url, wait_until="load")
        self.current_url = self.page.url
        return f"Navigated to {self.current_url}"

    def find_element_by_description(self, description: str) -> str:
        """Find an element on the page using natural language description."""
        element = find_element(self.page, description)

        if element:
            return element.locator
        
        return f"Could not find element for '{description}'"

    def click(self, description: str) -> str:
        """Click on an element using natural language description."""
        element = find_element(self.page, description)
        if not element:
            # Fallback to simple text matching
            self.page.click(f"text={description}", timeout=5000)
            return f"Clicked on '{description}' (by text)"

        # Click the found element
        self.page.click(element.locator)
        return f"Clicked on '{description}'"

    def type_text(self, field_description: str, text: str) -> str:
        """Type text into a form field using natural language description."""
        element = find_element(self.page, field_description)
        if not element:
             self.page.fill(f"text={field_description}", text)
             return f"Typed into {field_description} (by text)"

        self.page.fill(element.locator, text)
        self.form_data[field_description] = text
        return f"Typed into {field_description}"


    def get_text(self) -> str:
        """Get all visible text from the page."""
        return self.page.inner_text("body")

    @xray
    def take_screenshot(self, filename: str = None) -> str:
        """Take a screenshot of the current page and return base64 encoded image."""
        from datetime import datetime

        os.makedirs(self.screenshots_dir, exist_ok=True)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"step_{timestamp}.png"

        if not "/" in filename:
            filename = f"{self.screenshots_dir}/{filename}"

        screenshot_bytes = self.page.screenshot(path=filename)
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

        return f"data:image/png;base64,{screenshot_base64}"



    def select_option(self, field_description: str, option: str) -> str:
        """Select an option from a dropdown using natural language."""
        selector = self.find_element_by_description(field_description)
        self.page.select_option(selector, label=option)
        return f"Selected '{option}' in {field_description}"


    def check_checkbox(self, description: str, checked: bool = True) -> str:
        """Check or uncheck a checkbox using natural language."""
        selector = self.find_element_by_description(description)

        if checked:
            self.page.check(selector)
            return f"Checked {description}"
        else:
            self.page.uncheck(selector)
            return f"Unchecked {description}"


    def wait_for_element(self, description: str, timeout: int = 30) -> str:
        """Wait for an element described in natural language to appear."""
        selector = self.find_element_by_description(description)
        self.page.wait_for_selector(selector, timeout=timeout * 1000)
        return f"Element appeared: {description}"


    def wait_for_text(self, text: str, timeout: int = 30) -> str:
        """Wait for specific text to appear on the page."""
        self.page.wait_for_selector(f"text='{text}'", timeout=timeout * 1000)
        return f"Found text: '{text}'"

    def extract_data(self, selector: str) -> List[str]:
        """Extract data from elements matching a selector."""
        elements = self.page.locator(selector)
        count = elements.count()

        data = []
        for i in range(count):
            text = elements.nth(i).inner_text()
            data.append(text)

        return data

    @xray
    def analyze_html(self, html_content: str, objective: str) -> str:
        """Analyzes the provided HTML content based on a given objective."""
        class AnalysisResult(BaseModel):
            analysis: str = Field(..., description="The result of the HTML analysis based on the objective.")

        result = llm_do(
            f"Analyze the following HTML content based on the objective: \"{objective}\"\n\nHTML content:\n{html_content}",
            output=AnalysisResult,
            model=self.DEFAULT_AI_MODEL,
            temperature=0.2
        )

        return result.analysis

    @xray
    def explore(self, url: str, objective: str) -> str:
        """Navigates to a URL and analyzes it."""
        self.go_to(url)
        return self.analyze_html(self.page.content(), objective)

    @xray
    def scroll(self, times: int = 5, description: str = "the main content area") -> str:
        """Universal scroll."""
        return scroll_strategies.scroll(
            page=self.page,
            take_screenshot=self.take_screenshot,
            times=times,
            description=description
        )

    def wait_for_manual_login(self, site_name: str = "the website") -> str:
        """Pause automation and wait for user to login manually."""
        print(f"\n{'='*60}\n⏸️  MANUAL LOGIN REQUIRED\n{'='*60}")
        print(f"Please login to {site_name} in the browser window.")
        input("Press Enter to continue...")
        return f"User confirmed login to {site_name}"

    @xray
    def google_search(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Performs a web search on Google and extracts results."""
        self.go_to(f"https://www.google.com/search?q={query}")
        self.page.wait_for_load_state('networkidle')

        h3_elements = self.page.locator("h3").all()
        results = []
        for h3_element in h3_elements[:max_results]:
            parent_link = h3_element.locator("xpath=./ancestor::a").first
            if parent_link.count() > 0:
                title = h3_element.inner_text()
                url = parent_link.get_attribute("href")
                if title and url and url.startswith("http"):
                    results.append({"title": title, "url": url})

        return results

    def close(self, keep_browser_open: bool = False) -> str:
        """Close the browser."""
        if keep_browser_open:
            return "Browser kept open"

        if self.page: self.page.close()
        if self.context: self.context.close()
        if self.playwright: self.playwright.stop()

        self.page = None
        self.context = None
        self.playwright = None

        return "Browser closed"

    def analyze_page(self, question: str) -> str:
        """Ask a question about page content using AI."""
        return llm_do(
            f"Based on this HTML content, {question}\n\n {self.page.content()}",
            model=self.DEFAULT_AI_MODEL,
            temperature=0.3
        )

# Default shared instance
web = WebAutomation(headless=True)