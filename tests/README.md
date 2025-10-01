# Playwright Agent Tests

This directory contains tests for the ConnectOnion Playwright browser automation agent.

## Setup

Before running tests, ensure you have:

1. **Authenticated with ConnectOnion:**
   ```bash
   co auth
   ```

2. **Installed dependencies:**
   ```bash
   pip install python-dotenv playwright
   playwright install
   ```

3. **Environment configured:**
   - The `OPENONION_API_KEY` should be in your `.env` file
   - This is automatically set up by `co auth`

## Running Tests

### Run all tests:
```bash
python tests/test_browser.py
```

### Run from project root:
```bash
cd playwright-agent
python -m tests.test_browser
```

## Test Coverage

The test suite covers:

1. **Authentication Test** - Verifies co/ model authentication works
2. **Browser Open Test** - Opens browser and navigates to a website
3. **Screenshot Test** - Takes and saves screenshots
4. **Search Test** - Performs a Google search

## Test Structure

Each test:
- Is independent and can run standalone
- Reports clear success/failure status
- Cleans up resources (closes browsers, removes test files)
- Has a timeout to prevent hanging

## Expected Output

Successful run looks like:
```
============================================================
🧪 Playwright Agent Test Suite
============================================================
🔐 Testing Authentication...
✅ Token found: eyJhbGciOiJIUzI1NiIs...
✅ Agent responded: hello

🌐 Testing Browser Open...
✅ Browser opened: Successfully navigated to example.com

📸 Testing Screenshot...
✅ Screenshot test: Screenshot saved as test_google.png
✅ Screenshot file created

🔍 Testing Search...
✅ Search completed: Found search results for OpenAI...

============================================================
📊 Test Results Summary
============================================================
✅ PASSED: Authentication
✅ PASSED: Browser Open
✅ PASSED: Screenshot
✅ PASSED: Search

🏁 Total: 4/4 tests passed
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

To add a new test:

1. Create a function starting with `test_`
2. Return `True` for success, `False` for failure
3. Add to the `tests` list in `run_all_tests()`
4. Follow the pattern of existing tests

Example:
```python
def test_form_fill():
    """Test filling out a form."""
    print("\n📝 Testing Form Fill...")

    try:
        web = WebAutomation()
        agent = Agent(
            name="form_test",
            model="co/o4-mini",
            tools=web
        )

        result = agent.input("Go to example.com/form and fill it out")
        print(f"✅ Form test: {result}")
        return True
    except Exception as e:
        print(f"❌ Form test failed: {e}")
        return False
```