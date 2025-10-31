# Manual Login Example

## How It Works

The agent can pause for you to login manually, then continue automation.

## Example Task

```python
from agent import agent

# Ask agent to access Gmail
result = agent.input("""
Go to gmail.com
If you need to login, wait for me to login manually
Then take a screenshot of my inbox
Close the browser
""")
```

## What Happens

1. **Agent opens browser** → Chromium with your saved profile
2. **Navigates to gmail.com**
3. **Sees login page** → Calls `wait_for_manual_login("Gmail")`
4. **You see in terminal:**
   ```
   ============================================================
   ⏸️  MANUAL LOGIN REQUIRED
   ============================================================
   Please login to Gmail in the browser window.
   Once you're logged in and ready to continue:
     Type 'yes' or 'Y' and press Enter
   ============================================================

   Ready to continue? (yes/Y):
   ```
5. **You login in the browser window**
6. **Type `yes` in terminal**
7. **Agent continues** → Takes screenshot, closes browser

## Profile Persistence

### First Run
- Profile doesn't exist → Copies from your Chrome
- You login manually → Cookies saved to `chromium_automation_profile/`

### Subsequent Runs
- Profile exists with cookies → **Already logged in!**
- No manual login needed
- Cookies persist across runs

## Refreshing Cookies

If you need fresh cookies from Chrome:

```bash
rm -rf chromium_automation_profile
python agent.py  # Will copy fresh profile
```

## Benefits

✅ **Secure** - You handle login yourself
✅ **Flexible** - Works with any authentication (2FA, OAuth, etc.)
✅ **Persistent** - Login once, works forever (until cookies expire)
✅ **Simple** - Agent detects when login is needed automatically
