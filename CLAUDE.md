# CLAUDE.md

This file provides guidance to Claude when working with code in this repository.

## Project Overview

This is a **natural language browser automation agent** built with ConnectOnion and Playwright. It transforms natural language commands like "go to Google and search for AI news" into executable browser actions. The agent follows the ConnectOnion philosophy: "Keep simple things simple, make complicated things possible."

## Core Architecture

### Two-Layer Design

1. **Web Automation Layer** (`tools/web_automation.py`):
   - `WebAutomation` class provides browser control primitives
   - All methods decorated with `@xray` for behavior tracking
   - AI-powered element finding using `find_element_by_description()`
   - Form handling, screenshots, navigation, data extraction

2. **Agent Layer** (`agent.py`):
   - ConnectOnion Agent orchestrates tool calls
   - Natural language understanding via LLM (`co/gemini-2.5-flash` by default)
   - System prompt defines agent personality (`prompts/browser_agent.md`)
   - Interactive CLI and automated task modes

### Key Design Pattern

**Functions as Tools**: All `WebAutomation` methods automatically become agent tools. No manual tool registration needed - just pass the class instance:

```python
web = WebAutomation()
agent = Agent(
    name="playwright_agent",
    tools=web,  # All methods become tools
    max_iterations=50
)
```

## Development Commands

### Setup
```bash
# Recommended: Run the setup script
./setup.sh

# Manual Setup:
# 1. Install dependencies
pip install -r requirements.txt
playwright install

# 2. Authenticate with ConnectOnion (creates .env with OPENONION_API_KEY)
co auth
```

### Running the Agent

```bash
# Interactive mode - starts a chat session
python agent.py

# Automated task from command line
python agent.py "Open browser, go to news.ycombinator.com, take a screenshot"
```

### Testing

```bash
# Run complete test suite (4 tests: auth, browser, agent control, search)
python tests/test_all.py

# Run from project root
python -m tests.test_all

# Individual test files
python tests/test_direct.py
```

## Key Implementation Details

### Natural Language Element Finding

Located in `tools/web_automation.py` - `find_element_by_description()`:
- Takes natural language descriptions ("the blue submit button")
- Uses `llm_do()` to analyze HTML and generate CSS selectors
- Validates selector works on page before returning
- Falls back to text matching if AI approach fails

This is the core innovation that makes the agent feel natural to use.

### AI-Powered Tools Pattern

The agent uses ConnectOnion's `llm_do()` helper for intelligent operations:
- `find_element_by_description()`: Convert descriptions to selectors
- `analyze_page()`: Answer questions about page content
- `smart_fill_form()`: Generate appropriate form values from user info

These tools combine traditional automation (Playwright) with AI reasoning.

### Screenshot Workflow

Per `prompts/browser_agent.md` guidelines, the agent should:
1. Take screenshots after navigation
2. Take screenshots of empty forms before filling
3. Take screenshots after filling forms
4. Take screenshots after submission
5. Save all screenshots to `screenshots/` directory (auto-created)

### Browser Lifecycle

- Browser opens on first navigation command
- Stays open during interactive sessions
- Auto-closes at end of automated tasks
- Manual close via `close()` tool or "Close the browser" command

## Environment Configuration

### Required
```bash
# Created automatically by `co auth`
OPENONION_API_KEY=your_token_here
```

### ConnectOnion Project Metadata
- Stored in `.co/config.toml`
- Agent address, email, default model settings
- Do not modify manually - managed by `co` CLI

## Code Patterns to Follow

### Adding New Browser Tools

1. Add method to `WebAutomation` class in `tools/web_automation.py`
2. Decorate with `@xray` for behavior tracking
3. Return descriptive strings, not just success/failure
4. Handle `self.page is None` gracefully

Example:
```python
@xray
def hover_over(self, description: str) -> str:
    """Hover over an element using natural language description."""
    if not self.page:
        return "Browser not open"

    try:
        selector = self.find_element_by_description(description)
        if selector.startswith("Could not"):
            return selector

        self.page.hover(selector)
        return f"Hovered over '{description}'"
    except Exception as e:
        return f"Hover failed: {str(e)}"
```

### Error Handling Philosophy

Try-except is sometimes over-engineering. Only catch exceptions when you need to provide user-friendly error messages. Otherwise, let errors bubble up to the agent for retry.

### Model Selection

- Default: `co/gemini-2.5-flash` (fast, cost-effective)
- For complex HTML analysis: `co/gpt-4o` (higher accuracy)
- For testing: `co/o4-mini` (cheapest option)
- All models use ConnectOnion managed keys (`co/` prefix)

## Testing Strategy

### Test Structure (`tests/test_all.py`)

Four-stage validation:
1. **Authentication**: Verify ConnectOnion tokens work
2. **Direct Browser**: Test `WebAutomation` methods directly
3. **Agent Browser**: Test agent tool orchestration
4. **Google Search**: End-to-end complex workflow

Each test is independent and reports pass/fail clearly.
