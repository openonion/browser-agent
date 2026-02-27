"""
Test Chromium profile persistence with manual login.
"""
import pytest
import time
import sys
from pathlib import Path

# Ensure tools can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.browser import Browser

@pytest.mark.manual
@pytest.mark.chrome_profile
def test_chromium_profile_persistence():
    """
    Test that the Chrome profile persists login state across sessions.
    
    Step 1: Open browser -> Manual Login -> Close
    Step 2: Reopen browser -> Check if logged in automatically
    """
    print("\n=== Step 1: Initial Login ===")
    web1 = Browser(headless=False)
    web1.open_browser()
    
    print("Navigating to Gmail...")
    web1.go_to("https://mail.google.com")
    
    # Pause for manual login
    print("Please login to Gmail in the opened window.")
    web1.wait_for_manual_login("Gmail")
    
    # Close the first session
    print("Closing browser to save profile state...")
    web1.close()
    time.sleep(2) # Give it a moment to release locks

    print("\n=== Step 2: Verification (New Session) ===")
    # Open a FRESH instance pointing to the SAME profile
    web2 = Browser(headless=False)
    web2.open_browser()
    
    print("Navigating to Gmail again (should be logged in)...")
    web2.go_to("https://mail.google.com")
    
    # Give it a moment to redirect
    time.sleep(5)
    current_url = web2.page.url
    print(f"Current URL: {current_url}")
    
    # Check if we are logged in (URL should NOT be the signin page)
    is_logged_in = "accounts.google.com/signin" not in current_url and ("mail.google.com" in current_url)
    
    if is_logged_in:
        print("✅ SUCCESS: Profile persisted! You are still logged in.")
    else:
        print("❌ FAILURE: You were redirected to login. Profile might not have saved.")
        
    web2.close()
    
    assert is_logged_in, "Failed to persist login session across browser restarts."

if __name__ == "__main__":
    test_chromium_profile_persistence()