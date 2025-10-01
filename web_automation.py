"""
Purpose: Provides natural language browser automation primitives via Playwright
LLM-Note:
  Dependencies: imports from [typing, connectonion.xray/llm_do, playwright.sync_api, base64, json, logging, pydantic] | imported by [agent.py, tests/direct_test.py, tests/test_all.py] | tested by [tests/test_all.py, tests/direct_test.py]
  Data flow: agent.py creates web=WebAutomation() → exposes 15+ @xray decorated methods as tools → methods receive natural language descriptions → find_element_by_description() uses llm_do(HTML→CSS selector) with co/gpt-4o → playwright.sync_api executes browser actions → returns descriptive status strings
  State/Effects: maintains self.playwright/browser/page/current_url/form_data state | playwright.chromium.launch() creates browser process | page.goto()/click()/fill() mutate DOM | take_screenshot() writes to screenshots/*.png | close() terminates browser process
  Integration: exposes 15 tools (open_browser, go_to, click, type_text, take_screenshot, find_forms, fill_form, submit_form, select_option, check_checkbox, wait_for_element, wait_for_text, extract_data, get_text, close) | all methods return str (success/error messages, not exceptions) | @xray decorator logs behavior to ~/.connectonion/ | llm_do() calls for AI-powered element finding and form filling
  Performance: AI element finder uses llm_do() with co/gpt-4o (100-500ms) | HTML analysis limited to first 15000 chars | find_element_by_description() has text-matching fallback if AI fails | browser operations are synchronous playwright.sync_api | screenshots auto-create screenshots/ directory
  Errors: methods return error strings (not raise) - "Browser not open", "Could not find element", "Navigation failed" | AI selector may fail on dynamic sites → falls back to text matching | form submission tries 6 button patterns before failing
  ⚠️ Performance: find_element_by_description() calls LLM for every element lookup - cache results in calling code if reusing selectors
  ⚠️ Security: llm_do() sends page HTML to external API (co/gpt-4o) - avoid on pages with sensitive data
"""

from typing import Optional, List, Dict, Any, Literal
from connectonion import xray, llm_do
from playwright.sync_api import sync_playwright, Page, Browser, Playwright
import base64
import json
import logging
from pydantic import BaseModel, Field

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

    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.current_url: str = ""
        self.form_data: Dict[str, Any] = {}

    @xray
    def open_browser(self, headless: bool = True) -> str:
        """Open a new browser window."""
        if self.browser:
            return "Browser already open"

        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.page = self.browser.new_page()
            return "Browser opened successfully"
        except Exception as e:
            return f"Failed to open browser: {str(e)}"

    @xray
    def go_to(self, url: str) -> str:
        """Navigate to a URL."""
        if not self.page:
            return "Browser not open. Call open_browser() first"

        try:
            self.page.goto(url, wait_until="load")
            self.current_url = self.page.url
            xray.trace()
            return f"Navigated to {self.current_url}"
        except Exception as e:
            return f"Navigation failed: {str(e)}"

    @xray
    def find_element_by_description(self, description: str) -> str:
        xray.trace()
        """Find an element on the page using natural language description.

        Uses AI to analyze the HTML and find the best matching element for your description.

        Args:
            description: Natural language description of what you're looking for
                        e.g., "the submit button", "email input field", "main navigation menu"

        Returns:
            CSS selector for the found element, or error message
        """
        if not self.page:
            return "Browser not open"

        try:
            # Get page HTML for analysis
            html = self.page.content()

            # Use AI to find the best selector
            class ElementSelector(BaseModel):
                selector: str = Field(..., description="CSS selector for the element")
                confidence: float = Field(..., description="Confidence score 0-1")
                explanation: str = Field(..., description="Why this element matches")

            result = llm_do(
                f"""Analyze this HTML and find the CSS selector for: "{description}"

                HTML (first 15000 chars): {html[:15000]}

                Return the most specific CSS selector that uniquely identifies this element.
                Consider id, class, type, attributes, and position in DOM.
                """,
                output=ElementSelector,
                model="co/gpt-4o",
                temperature=0.1
            )

            # Verify the selector works
            if self.page.locator(result.selector).count() > 0:
                return result.selector
            else:
                return f"Found selector {result.selector} but element not on page"

        except Exception as e:
            return f"Could not find element: {str(e)}"

    @xray
    def click(self, description: str) -> str:
        """Click on an element using natural language description.

        Args:
            description: Natural language description like "the blue submit button"
                        or "the email field" or "link to contact page"
        """
        if not self.page:
            return "Browser not open"

        try:
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

        except Exception as e:
            return f"Click failed: {str(e)}"

    @xray
    def type_text(self, field_description: str, text: str) -> str:
        """Type text into a form field using natural language description.

        Args:
            field_description: Natural language description of the field
                              e.g., "email field", "password input", "comment box"
            text: The text to type into the field
        """
        if not self.page:
            return "Browser not open"

        try:
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

        except Exception as e:
            return f"Type failed: {str(e)}"

    @xray
    def get_text(self) -> str:
        """Get all visible text from the page."""
        if not self.page:
            return "Browser not open"

        try:
            text = self.page.inner_text("body")
            return text
        except Exception as e:
            return f"Failed to get text: {str(e)}"

    @xray
    def take_screenshot(self, filename: str = None) -> str:
        """Take a screenshot of the current page."""
        if not self.page:
            return "Browser not open"

        try:
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

            self.page.screenshot(path=filename)
            return f"Screenshot saved: {filename}"
        except Exception as e:
            return f"Screenshot failed: {str(e)}"

    @xray
    def find_forms(self) -> List[FormField]:
        """Find all form fields on the current page."""
        if not self.page:
            return []

        try:
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
        except Exception as e:
            logger.error(f"Failed to find forms: {e}")
            return []

    @xray
    def fill_form(self, data: Dict[str, str]) -> str:
        """Fill multiple form fields at once."""
        if not self.page:
            return "Browser not open"

        results = []
        for field_name, value in data.items():
            result = self.type_text(field_name, value)
            results.append(f"{field_name}: {result}")

        return "\n".join(results)

    @xray
    def submit_form(self) -> str:
        """Submit the current form."""
        if not self.page:
            return "Browser not open"

        try:
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
        except Exception as e:
            return f"Submit failed: {str(e)}"

    @xray
    def select_option(self, field_description: str, option: str) -> str:
        """Select an option from a dropdown using natural language.

        Args:
            field_description: Natural description of the dropdown
            option: The option text to select
        """
        if not self.page:
            return "Browser not open"

        try:
            selector = self.find_element_by_description(field_description)

            if selector.startswith("Could not"):
                return selector

            # Select the option
            self.page.select_option(selector, label=option)
            return f"Selected '{option}' in {field_description}"

        except Exception as e:
            return f"Select failed: {str(e)}"

    @xray
    def check_checkbox(self, description: str, checked: bool = True) -> str:
        """Check or uncheck a checkbox using natural language.

        Args:
            description: Natural description of the checkbox
            checked: True to check, False to uncheck
        """
        if not self.page:
            return "Browser not open"

        try:
            selector = self.find_element_by_description(description)

            if selector.startswith("Could not"):
                return selector

            if checked:
                self.page.check(selector)
                return f"Checked {description}"
            else:
                self.page.uncheck(selector)
                return f"Unchecked {description}"

        except Exception as e:
            return f"Checkbox operation failed: {str(e)}"

    @xray
    def wait_for_element(self, description: str, timeout: int = 30) -> str:
        """Wait for an element described in natural language to appear.

        Args:
            description: Natural language description of the element
            timeout: Maximum wait time in seconds
        """
        if not self.page:
            return "Browser not open"

        try:
            # Find the selector first
            selector = self.find_element_by_description(description)

            if selector.startswith("Could not"):
                # Try waiting for text instead
                self.page.wait_for_selector(f"text='{description}'", timeout=timeout * 1000)
                return f"Found text: '{description}'"

            self.page.wait_for_selector(selector, timeout=timeout * 1000)
            return f"Element appeared: {description}"

        except Exception as e:
            return f"Element '{description}' did not appear after {timeout} seconds"

    @xray
    def wait_for_text(self, text: str, timeout: int = 30) -> str:
        """Wait for specific text to appear on the page."""
        if not self.page:
            return "Browser not open"

        try:
            self.page.wait_for_selector(f"text='{text}'", timeout=timeout * 1000)
            return f"Found text: '{text}'"
        except Exception as e:
            return f"Text '{text}' not found after {timeout} seconds"

    @xray
    def extract_data(self, selector: str) -> List[str]:
        """Extract data from elements matching a selector."""
        if not self.page:
            return []

        try:
            elements = self.page.locator(selector)
            count = elements.count()

            data = []
            for i in range(count):
                text = elements.nth(i).inner_text()
                data.append(text)

            return data
        except Exception as e:
            logger.error(f"Failed to extract data: {e}")
            return []

    @xray
    def close(self) -> str:
        """Close the browser."""
        try:
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
        except Exception as e:
            return f"Error closing browser: {str(e)}"


# Standalone helper functions for AI-powered analysis
def analyze_page(html_content: str, question: str) -> str:
    """Ask a question about page content using AI."""
    return llm_do(
        f"Based on this HTML content, {question}\n\nHTML (first 5000 chars): {html_content[:5000]}",
        model="co/gpt-4o",
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
        model="co/gpt-4o",
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