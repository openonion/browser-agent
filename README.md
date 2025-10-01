# Playwright Web Automation Agent

A natural language browser automation agent powered by ConnectOnion and Playwright.

## Quick Start

```bash
# 1. Setup
pip install python-dotenv playwright connectonion
playwright install
co auth

# 2. Test it - just run this one command
python agent.py
```

That's it! The agent will open a browser, visit example.com, take a screenshot, and close the browser.

## Use in Your Code

```python
from agent import agent

# Just give it natural language commands
result = agent.input("Go to google.com and search for AI news")
print(result)
```

## Features

- 🌐 **Natural language browser control** - Just describe what you want
- 📸 **Automatic screenshots** - Capture any page state
- 🔍 **Smart element finding** - No CSS selectors needed
- 📝 **Form automation** - Fill and submit forms intelligently
- 🎯 **Multi-step workflows** - Complex automation sequences

## Project Structure

```
playwright-agent/
├── agent.py              # Main agent with Playwright tools
├── web_automation.py     # Browser automation implementation
├── prompt.md            # Agent system prompt
├── tests/
│   ├── test_browser.py  # Test suite
│   └── README.md        # Test documentation
├── .env                 # API keys (created by co auth)
└── README.md           # This file
```

## How It Works

1. **Natural Language Input**: You describe what you want in plain English
2. **AI Planning**: The agent understands and plans the browser actions
3. **Tool Execution**: Playwright performs the actual browser control
4. **Result Reporting**: Agent reports what was done at each step

## Examples

```python
from agent import agent

# Simple navigation
agent.input("Open browser and go to news.ycombinator.com, then close")

# Search automation
agent.input("Go to google.com, search for ConnectOnion, take a screenshot, close browser")

# Form filling
agent.input("Go to example.com/contact, fill name with John Doe, fill email with john@example.com, submit, close browser")
```

## How to Extend

Add new methods to `WebAutomation` class in `web_automation.py`:

```python
@xray
def scroll_down(self) -> str:
    """Scroll down the page."""
    if not self.page:
        return "Browser not open"
    self.page.evaluate("window.scrollBy(0, 500)")
    return "Scrolled down"
```

The agent automatically uses new methods based on natural language commands.

## Run Tests

```bash
python tests/test_all.py
```