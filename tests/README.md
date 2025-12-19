# Playwright Agent Tests

This directory contains pytest-based tests for the ConnectOnion Playwright browser automation agent.

## Setup

Before running tests, ensure you have:

1. **Authenticated with ConnectOnion:**
   ```bash
   co auth
   ```

2. **Installed dependencies:**
   ```bash
   pip install python-dotenv playwright pytest connectonion tox
   playwright install
   ```

3. **Environment configured:**
   - The `OPENONION_API_KEY` should be in your `.env` file
   - This is automatically set up by `co auth`

## Running Tests

### Tox vs Pytest: When to Use What?

**Use Tox when:**
- Running tests in CI/CD pipelines
- Testing across multiple Python versions
- Need isolated, reproducible environments
- Running tests before releasing/deploying
- Want automated environment setup

**Use pytest directly when:**
- Developing and debugging tests
- Quick iteration during development
- Running specific tests repeatedly
- Need faster feedback loop

### Using Tox (Recommended for CI/CD)

Tox creates isolated environments and runs tests automatically:

```bash
# List all available environments
tox list

# Run automated tests (default - skips manual tests)
tox -e automated

# Run quick tests only (skip slow and manual tests)
tox -e quick

# Run integration tests only
tox -e integration

# Run tests with coverage report
tox -e coverage

# Run image plugin tests only
tox -e image

# Run manual tests (requires interaction)
tox -e manual

# Test across multiple Python versions (if installed)
tox -e py39,py310,py311

# Recreate environments (if dependencies changed)
tox -r -e automated
```

### Using pytest Directly

Pytest is faster for development and debugging:

#### Run all automated tests (excludes manual tests):
```bash
pytest tests/ -m "not manual"
```

#### Run all tests including manual ones:
```bash
pytest tests/  # Run all tests
```

#### Run specific test files:
```bash
pytest tests/test_all.py           # Core integration tests
pytest tests/test_image_plugin.py  # Image plugin tests
pytest tests/test_direct.py        # Direct API tests
```

#### Run tests by marker:
```bash
pytest -m integration           # Only integration tests
pytest -m screenshot           # Only screenshot tests
pytest -m "not slow"           # Skip slow tests
pytest -m "not manual"         # Skip manual interaction tests
```

#### Run with verbose output:
```bash
pytest tests/ -v              # Verbose
pytest tests/ -vv             # Very verbose
pytest tests/ -s              # Show print statements
```

## Legacy Running (old way):

### Run individual test files:
```bash
python tests/test_all.py
python tests/test_direct.py
```

## Tox Environments Explained

The `tox.ini` file defines these environments:

| Environment | Purpose | Tests Run |
|------------|---------|-----------|
| `automated` | Default - automated tests only | All tests except `@pytest.mark.manual` |
| `quick` | Fast feedback loop | Skip slow and manual tests |
| `integration` | Integration tests only | Only `@pytest.mark.integration` |
| `image` | Image plugin tests | Only `test_image_plugin.py` |
| `manual` | Manual interaction tests | Only `@pytest.mark.manual` |
| `coverage` | Code coverage report | Automated tests with coverage |
| `py39`, `py310`, `py311` | Version-specific | All tests on specific Python version |
| `lint` | Code linting | Runs ruff linter (optional) |

## Test Coverage

The test suite includes:

### Automated Tests:
1. **test_all.py** - Core integration tests:
   - `test_authentication` - Verifies ConnectOnion auth works
   - `test_browser_direct` - Direct WebAutomation API calls
   - `test_agent_browser` - Agent-controlled browser

2. **test_image_plugin.py** - Image plugin tests:
   - `test_image_plugin_with_screenshot` - Full workflow with image formatter
   - `test_image_plugin_basic` - Plugin loading verification

3. **test_direct.py** - Direct API tests:
   - `test_wikipedia_search_direct` - Wikipedia search without agent (parametrized with 2 search terms)

### Manual Tests (marked with `@pytest.mark.manual`):
4. **test_final_scroll.py** - Gmail scroll testing (requires manual login)

### Investigation Scripts:
5. **investigate_gmail.py** - Deep dive into Gmail DOM structure (not a test, manual investigation)

## Test Markers

Tests are organized with pytest markers:
- `@pytest.mark.integration` - Tests that make real API calls
- `@pytest.mark.screenshot` - Tests that generate screenshots
- `@pytest.mark.slow` - Tests that take >10 seconds
- `@pytest.mark.manual` - Tests requiring manual interaction
- `@pytest.mark.chrome_profile` - Tests requiring Chrome user profile

## Test Structure

Each pytest test:
- Uses fixtures from `conftest.py` for common setup
- Has proper assertions instead of print statements
- Cleans up resources automatically (via fixtures)
- Can run independently or as part of suite

## Expected Output

Successful pytest run looks like:
```
$ pytest tests/ -v -m "not manual"

========================= test session starts ==========================
platform darwin -- Python 3.11.0, pytest-7.4.0
collected 8 items / 1 deselected

tests/test_all.py::test_authentication PASSED                    [ 12%]
tests/test_all.py::test_browser_direct PASSED                    [ 25%]
tests/test_all.py::test_agent_browser PASSED                     [ 37%]
tests/test_image_plugin.py::test_image_plugin_basic PASSED       [ 50%]
tests/test_image_plugin.py::test_image_plugin_with_screenshot PASSED [ 62%]
tests/direct_test.py::test_wikipedia_search_direct[Playwright] PASSED [ 75%]
tests/direct_test.py::test_wikipedia_search_direct[Python automation] PASSED [100%]

========================= 7 passed, 1 deselected in 45.32s =========================
```

## Troubleshooting

### Authentication fails
- Run `co auth` to authenticate
- Check `.env` file has `OPENONION_API_KEY`

### Browser tests fail
- Ensure Playwright is installed: `playwright install`
- Check you have Chrome/Chromium installed
- Try running with visible browser: modify WebAutomation to use `headless=False`

### Timeouts
- Tests have reasonable timeouts
- Complex searches may take longer
- Adjust `max_iterations` in agent if needed

## Adding New Tests

To add a new pytest test:

1. Create a function starting with `test_`
2. Use proper `assert` statements (not return True/False)
3. Add appropriate markers (`@pytest.mark.integration`, etc.)
4. Use fixtures from `conftest.py` for common setup
5. Follow the pattern of existing tests

Example:
```python
import pytest
from connectonion import Agent
from web_automation import WebAutomation


@pytest.mark.integration
def test_form_fill(web, agent):
    """Test filling out a form using fixtures."""
    # web and agent fixtures are auto-injected
    result = agent.input("Go to example.com/form and fill it out")

    # Use assertions, not returns
    assert result, "Agent should return a result"
    assert "form" in result.lower(), f"Should mention form: {result}"


@pytest.mark.integration
@pytest.mark.screenshot
def test_form_fill_with_screenshot():
    """Test form fill with explicit setup (no fixtures)."""
    web = WebAutomation()
    agent = Agent(
        name="form_test",
        model="co/o4-mini",
        tools=web
    )

    result = agent.input("Go to example.com/form, fill it out, take screenshot")

    assert result, "Agent should return a result"

    # Cleanup
    if web.page:
        web.close()
```

## Fixtures Available

From `conftest.py`:
- `web` - WebAutomation instance (auto-cleanup)
- `agent` - Agent with web tools (co/o4-mini model)
- `agent_with_prompt` - Agent with prompt.md system prompt
- `check_api_key` - Validates OPENONION_API_KEY exists
- `setup_screenshots_dir` - Ensures screenshots/ directory exists