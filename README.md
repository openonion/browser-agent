# Playwright Web Automation Agent

A natural language browser automation agent powered by ConnectOnion and Playwright.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/openonion/browser-agent.git
cd browser-agent

# Run the setup script (installs everything)
./setup.sh

# Test it - just run this one command
python agent.py
```

That's it! The agent will open a browser, visit Hacker News, take a screenshot, and close the browser.

### Manual Setup (if you prefer)

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Initialize ConnectOnion project
co init

# 3. Install Playwright browsers
playwright install

# 4. Authenticate with ConnectOnion
co auth
```

### What the Setup Script Does

The `setup.sh` script automatically:
- Installs all Python dependencies from `requirements.txt`
- Initializes the ConnectOnion project (creates `.co/` directory)
- Installs Playwright browsers (Chrome, Firefox, etc.)
- Sets up authentication (creates `.env` with your API key)

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
- 🔐 **Chrome profile support** - Use your cookies, sessions, and login states
- 🖼️ **Vision support** - LLM can see and analyze screenshots automatically

## Project Structure

```
browser-agent/
├── agent.py                 # Main agent with Playwright tools
├── web_automation.py        # Browser automation implementation
├── prompt.md               # Agent system prompt
├── requirements.txt        # Python dependencies
├── setup.sh               # Automated setup script
├── tests/
│   ├── test_all.py        # Complete test suite
│   ├── direct_test.py     # Direct browser tests
│   └── README.md          # Test documentation
├── screenshots/           # Auto-generated screenshots
├── chrome_profile_copy/   # Chrome profile copy (created on first run)
├── .co/                   # ConnectOnion project config (created by setup)
├── .env                   # API keys (created by co auth)
└── README.md             # This file
```

## How It Works

1. **Natural Language Input**: You describe what you want in plain English
2. **AI Planning**: The agent understands and plans the browser actions
3. **Tool Execution**: Playwright performs the actual browser control
4. **Result Reporting**: Agent reports what was done at each step

## Image Result Formatter Plugin

The browser agent uses the **image_result_formatter plugin** to automatically convert screenshots to vision format. When a tool returns a base64-encoded screenshot, the plugin:

1. Detects the base64 image data
2. Converts it to multimodal message format
3. Allows the LLM to **see and analyze** the screenshot visually

```
🖼️ Formatted 'take_screenshot' result as image
```

This enables powerful visual workflows:
- **Visual verification** - LLM can confirm if actions succeeded by seeing the page
- **Content extraction** - Read text, identify elements from screenshots
- **Error detection** - Spot visual problems like missing buttons or error messages
- **Automatic analysis** - LLM describes what it sees in the screenshot

### Example

```python
from connectonion import Agent
from connectonion.useful_plugins import image_result_formatter
from web_automation import WebAutomation

web = WebAutomation()
agent = Agent(
    name="browser",
    tools=web,
    plugins=[image_result_formatter]  # Auto-format screenshots for vision
)

agent.input("Go to example.com, take a screenshot, and describe what you see")
# The LLM will actually SEE the screenshot and describe:
# "I can see a simple webpage with the heading 'Example Domain' and
#  some descriptive text about this domain being used in examples..."
```

See `test_plugins.py` for a working demo.

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

## Chrome Profile Support

By default, the agent uses your Chrome profile data (cookies, sessions, logins). This means:

- ✅ **Stay logged in** - Access sites where you're already authenticated
- ✅ **No conflicts** - Your regular Chrome can stay open while agent runs
- ✅ **Fast** - First run copies profile (~50s), subsequent runs are instant
- ✅ **Private** - Profile copy stored locally in `chrome_profile_copy/` (gitignored)

### How It Works

On first run, the agent copies essential Chrome profile data to `./chrome_profile_copy/`:
- Cookies and sessions
- Saved passwords (encrypted)
- Bookmarks and history
- Extensions (skips cache for speed)

Subsequent runs reuse this copy, so startup is fast.

### Disable Chrome Profile

To use a fresh browser without your Chrome data:

```python
# In agent.py, line 21
web = WebAutomation(use_chrome_profile=False)
```

### Update Profile Copy

To get latest cookies/sessions from your Chrome:

```bash
rm -rf chrome_profile_copy/
python agent.py  # Will create fresh copy
```

## Run Tests

```bash
python tests/test_all.py
```