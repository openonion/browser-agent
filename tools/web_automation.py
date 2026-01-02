"""
Purpose: Provides natural language browser automation primitives via Playwright
LLM-Note:
  Dependencies: imports from [typing, connectonion.xray/llm_do, playwright.sync_api, base64, json, logging, pydantic] | imported by [agent.py, tests/direct_test.py, tests/test_all.py] | tested by [tests/test_all.py, tests/direct_test.py]
  Data flow: agent.py creates web=WebAutomation() → exposes 15+ @xray decorated methods as tools → methods receive natural language descriptions → find_element_by_description() uses llm_do(HTML→CSS selector) with gpt-4o → playwright.sync_api executes browser actions → returns descriptive status strings
  State/Effects: maintains self.playwright/browser/page/current_url/form_data state | playwright.chromium.launch() creates browser process | page.goto()/click()/fill() mutate DOM | take_screenshot() writes to screenshots/*.png | close() terminates browser process
  Integration: exposes 15 tools (open_browser, go_to, click, type_text, take_screenshot, find_forms, fill_form, submit_form, select_option, check_checkbox, wait_for_element, wait_for_text, extract_data, get_text, close) | all methods return str (success/error messages, not exceptions) | @xray decorator logs behavior to ~/.connectonion/ | llm_do() calls for AI-powered element finding and form filling
  Performance: AI element finder uses llm_do() with gpt-4o (100-500ms) | HTML analysis limited to first 15000 chars | find_element_by_description() has text-matching fallback if AI fails | browser operations are synchronous playwright.sync_api | screenshots auto-create screenshots/ directory
  Errors: methods return error strings (not exceptions) - "Browser not open", "Could not find element", "Navigation failed" | AI selector may fail on dynamic sites → falls back to text matching | form submission tries 6 button patterns before failing
  ⚠️ Performance: find_element_by_description() calls LLM for every element lookup - cache results in calling code if reusing selectors
  ⚠️ Security: llm_do() sends page HTML to external API (gpt-4o) - avoid on pages with sensitive data
"""

from typing import Optional, List, Dict, Any, Union
import os
import shutil
from connectonion import xray, llm_do
from playwright.sync_api import sync_playwright, Page, Browser, Playwright
import base64
import logging
from pydantic import BaseModel, Field
from . import scroll_strategies
from .element_finder import find_element, extract_elements, format_elements_for_llm

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

    def __init__(self, headless: bool = False):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.current_url: str = ""
        self.form_data: Dict[str, Any] = {}
        self.headless = headless
        
        self.screenshots_dir = "screenshots"
        self.DEFAULT_AI_MODEL = os.getenv("BROWSER_AGENT_MODEL", "co/gemini-3-flash-preview")

    def open_browser(self, headless: Union[bool, str, None] = None) -> str:
        """Open a new browser window.

        Note: If use_chrome_profile=True, Chrome must be completely closed before running.
        """
        if self.browser:
            return "Browser already open"

        # Handle string arguments (common from LLMs)
        if isinstance(headless, str):
            headless = headless.lower() == 'true'

        # Use instance default if argument not provided
        if headless is None:
            headless = self.headless

        from pathlib import Path

        self.playwright = sync_playwright().start()

        # Always launch a new browser instance without a persistent profile
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
            ],
            ignore_default_args=['--enable-automation'],
            timeout=120000,  # 120 seconds timeout
        )
        self.page = self.browser.new_page()
        self.page.set_default_navigation_timeout(60000)  # 60s timeout for heavy sites

        # Hide webdriver property
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
        if not self.page:
            return "Browser not open. Call open_browser() first"

        self.page.goto(url, wait_until="load")
        self.current_url = self.page.url
        return f"Navigated to {self.current_url}"

    def find_element_by_description(self, description: str) -> str:
        """Find an element on the page using natural language description.

        Uses AI to select from pre-extracted interactive elements.

        Args:
            description: Natural language description of what you're looking for
                        e.g., "the submit button", "email input field", "main navigation menu"

        Returns:
            CSS selector for the found element, or error message
        """
        if not self.page:
            return "Browser not open"

        # Use new element finder (injects IDs, selects best match)
        element = find_element(self.page, description)

        if element:
            return element.locator
        
        return f"Could not find element for '{description}'"

    def click(self, description: str) -> str:
        """Click on an element using natural language description."""
        if not self.page:
            return "Browser not open"

        element = find_element(self.page, description)
        if not element:
            # Fallback to simple text matching in main frame
            if self.page.locator(f"text='{description}'").count() > 0:
                self.page.click(f"text='{description}'", timeout=5000)
                return f"Clicked on '{description}' (by text)"
            return f"Could not find element: {description}"

        # Get the correct frame
        target_frame = self.page.frames[element.frame_index]
        target_frame.click(element.locator)
        return f"Clicked on '{description}'"

    def type_text(self, field_description: str, text: str) -> str:
        """Type text into a form field using natural language description."""
        if not self.page:
            return "Browser not open"

        element = find_element(self.page, field_description)
        if not element:
            return f"Could not find field: {field_description}"

        target_frame = self.page.frames[element.frame_index]
        target_frame.fill(element.locator, text)
        self.form_data[field_description] = text
        return f"Typed into {field_description}"


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

        from datetime import datetime

        # Create screenshots directory if it doesn't exist
        os.makedirs(self.screenshots_dir, exist_ok=True)

        # Auto-generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"step_{timestamp}.png"

        # Always save in screenshots folder unless full path provided
        if not "/" in filename:
            filename = f"{self.screenshots_dir}/{filename}"

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
        fields_data = self.page.evaluate(
            """
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
        """
        )

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
    def analyze_html(self, html_content: str, objective: str) -> str:
        """
        Analyzes the provided HTML content based on a given objective.

        This method uses an LLM to process the HTML and extract relevant information
        according to the specified objective. It is useful for summarizing content,
        extracting specific data points, or getting an overview of a page's structure
        and purpose without manual inspection.

        Args:
            html_content (str): The raw HTML content of a web page to be analyzed.
            objective (str): The specific goal of the analysis. For example:
                             "Summarize the key points of the article",
                             "Extract all the links and their text",
                             "Identify the main products and their prices".

        Returns:
            str: The result of the analysis as a string. This could be a summary,
                 a list of extracted data, or a description of the page's content,
                 depending on the objective.
        """
        if not self.page:
            return "Browser not open"

        # Define the Pydantic model for structured output
        class AnalysisResult(BaseModel):
            analysis: str = Field(..., description="The result of the HTML analysis based on the objective.")

        # Use llm_do for the analysis
        result = llm_do(
            f"""Analyze the following HTML content based on the objective: "{objective}"\n
            HTML content:\n{html_content}""",
            output=AnalysisResult,
            model=self.DEFAULT_AI_MODEL,
            temperature=0.2
        )

        return result.analysis

    @xray
    def explore(self, url: str, objective: str) -> str:
        """
        Navigates to a URL, retrieves its HTML content, and analyzes it based on a given objective.

        This method combines navigation and analysis into a single step. It first navigates to the
        specified URL, then captures the full HTML of the page. This HTML is then passed to the
        `analyze_html` method along with the provided objective to perform a detailed analysis.

        Args:
            url (str): The URL of the web page to explore.
            objective (str): The objective of the exploration and analysis. This is passed directly
                             to the `analyze_html` method. Examples include:
                             "Summarize the main article",
                             "Extract the contact information from the page",
                             "List all the job openings mentioned".

        Returns:
            str: A string containing the analysis of the page's HTML content, based on the
                 specified objective. If navigation or analysis fails, an error message is returned.
        """
        if not self.page:
            return "Browser not open. Call open_browser() first"

        # Navigate to the URL
        navigation_result = self.go_to(url)
        if "Navigated to" not in navigation_result:
            return f"Failed to navigate to {url}: {navigation_result}"

        # Get the raw HTML content of the page
        html_content = self.page.content()
        if not html_content:
            return f"Could not retrieve content from {url}"

        # Analyze the HTML content with the given objective
        analysis_result = self.analyze_html(html_content, objective)

        return analysis_result

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
        return scroll_strategies.scroll_page(self.page, direction, amount)

    def scroll_element(self, selector: str, amount: int = 1000) -> str:
        """Scroll a specific element (useful for Gmail's email list container).

        Args:
            selector: CSS selector for the element to scroll
            amount: Pixels to scroll down

        Returns:
            Status message
        """
        return scroll_strategies.scroll_element(self.page, selector, amount)

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
        print(f"⏸️  MANUAL LOGIN REQUIRED")
        print(f"{ '='*60}")
        print(f"Please login to {site_name} in the browser window.")
        print(f"Once you're logged in and ready to continue:")
        print(f"  Type 'yes' or 'Y' and press Enter")
        print(f"{ '='*60}\n")

        while True:
            response = input("Ready to continue? (yes/Y): ").strip().lower()
            if response in ['yes', 'y']:
                print("✅ Continuing automation...\n")
                return f"User confirmed login to {site_name} - continuing automation"
            else:
                print("Please type 'yes' or 'Y' when ready.")

    @xray
    def get_search_results(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Performs a web search on Google and extracts the top search results using DOM traversal.
        
        This is more robust than a single CSS selector as it finds titles (h3) and walks up to the link.
        """
        if not self.page:
            raise ValueError("Browser not open.")

        search_url = f"https://www.google.com/search?q={query}"
        self.go_to(search_url)
        self.page.wait_for_load_state('networkidle')

        # Find all h3 elements, which are the titles of search results
        h3_elements = self.page.locator("h3").all()
        
        results = []
        for h3_element in h3_elements:
            if len(results) >= max_results:
                break
            
            # Find the parent link (a tag) of the h3 element
            # Search results are usually <a><h3>Title</h3></a> or <a><div><h3>Title</h3></div></a>
            # We look for the first anchor ancestor
            parent_link = h3_element.locator("xpath=./ancestor::a").first
            
            if parent_link.count() > 0:
                title = h3_element.inner_text()
                url = parent_link.get_attribute("href")
                
                if title and url and url.startswith("http"):
                    results.append({"title": title, "url": url})

        return results

    def close(self, keep_browser_open: bool = False) -> str:
        """Close the browser unless instructed to keep it open.

        Args:
            keep_browser_open (bool): If True, the browser will not be closed.

        Returns:
            str: A message indicating whether the browser was closed or kept open.
        """
        if keep_browser_open:
            return "Browser kept open for user interaction."

        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

        self.page = None
        self.browser = None
        self.playwright = None

        return "Browser closed"

    def analyze_page(self, question: str) -> str:
        """Ask a question about page content using AI. 
        
        Args:
            question: The question to ask about the current page content
            
        Returns:
            The AI's answer based on the page HTML
        """
        if not self.page:
            return "Browser not open"
            
        html_content = self.page.content()
        # Limit content to avoid token limits
        return llm_do(
            f"Based on this HTML content, {question}\n\n {html_content}",
            model=self.DEFAULT_AI_MODEL,
            temperature=0.3
        )

    def smart_fill_form(self, user_info: str) -> str:
        """Generate smart form values based on user information and fill the form.
        
        Args:
            user_info: Natural language description of the user/data (e.g., "User is John Doe, email john@example.com")
            
        Returns:
            Status message describing what fields were filled
        """
        if not self.page:
            return "Browser not open"

        fields = self.find_forms()
        if not fields:
            return "No form fields found on page"

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
            model=self.DEFAULT_AI_MODEL,
            temperature=0.7
        )
        
        return self.fill_form(result.values)