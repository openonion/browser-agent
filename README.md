# Browser Agent

A natural language browser automation agent powered by ConnectOnion and Playwright.

## Quick Start

The fastest way to use the browser agent is via the ConnectOnion CLI:

```bash
pip install connectonion
co browser
```

## For Developers

If you want to customize the browser agent (modify tools, prompts, or add new capabilities), clone this repo as a starting point:

```bash
git clone https://github.com/openonion/browser-agent.git
cd browser-agent
./setup.sh
```

### Customizing Browser Tools

The browser tools live in the ConnectOnion SDK. Instead of modifying them directly, use `co copy` to copy them into your project for customization:

```bash
# Copy browser tools to your local ./tools/ directory
co copy browser_tools
```

This gives you a local copy you can modify freely. The default `tools/browser.py` is a thin re-export from the SDK:

```python
from connectonion.useful_tools.browser_tools import BrowserAutomation
web = BrowserAutomation()
```

After running `co copy`, you'll have the full source locally and can customize element finding, scrolling, keyboard handling, etc.

### Manual Setup

```bash
pip install -r requirements.txt
co init
playwright install
co auth
```

## Usage

```bash
# Single task
python cli.py run "Go to news.ycombinator.com and find the top story"

# Interactive mode
python cli.py interactive
```

```python
from agent import create_agent

agent = create_agent()
agent.input("Go to google.com and search for AI news")
```

## Features

- Natural language browser control
- Automatic screenshots with vision support (LLM sees the page)
- Smart element finding (no CSS selectors needed)
- Form automation
- Persistent Chrome profile (cookies, sessions survive restarts)
- Deep Research Mode (spawns sub-agents for multi-source research)
- Platform-aware keyboard shortcuts (auto-detects macOS/Windows/Linux)

## Project Structure

```
browser-agent/
├── cli.py                   # CLI entry point
├── agent.py                 # Agent configuration
├── main.py                  # HTTP/WebSocket host
├── tools/
│   ├── browser.py           # Re-exports BrowserAutomation from SDK
│   ├── file_tools.py        # File operations for research
│   └── deep_research.py     # Deep research tool
├── agents/
│   └── deep_research.py     # Deep research sub-agent
├── prompts/
│   ├── agent.md             # Main agent prompt
│   ├── deep_research.md     # Research sub-agent prompt
│   ├── element_matcher.md   # Element finding strategy
│   ├── form_filler.md       # Form handling strategy
│   └── scroll_strategy.md   # Scrolling strategy
├── tests/
└── requirements.txt
```

## How It Works

1. You describe what you want in plain English
2. The agent plans browser actions via LLM
3. Playwright executes the browser control
4. Screenshots feed back to the LLM for visual verification
5. Agent reports results at each step

## Run Tests

```bash
python tests/test_all.py
```
