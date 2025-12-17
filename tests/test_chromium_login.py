from playwright.sync_api import sync_playwright
import time

def test_chromium_login():
    """
    Launches a Chromium browser with the --disable-blink-features=AutomationControlled flag,
    navigates to Google's login page, and pauses to allow for a manual login attempt.
    """
    with sync_playwright() as p:
        print("Launching Chromium browser with anti-detection arguments...")
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox", # Required for some environments, generally good for anti-detection
                "--disable-setuid-sandbox", # Another anti-detection measure
                "--disable-gpu", # Often helps with compatibility/stability
            ]
        )
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36", # Realistic User-Agent
            ignore_https_errors=True # To bypass potential SSL errors from bot detection
        )
        
        print("Navigating to Google login page...")
        page.goto("https://accounts.google.com/signin")
        print("Navigation complete.")
        
        print("\n" + "="*50)
        print("MANUAL LOGIN TEST (Chromium)")
        print("The browser window is now open. Please attempt to log in.")
        print("The script will close the browser in 60 seconds.")
        print("="*50 + "\n")
        
        # Keep the browser open for 60 seconds for manual testing
        time.sleep(60)
        
        browser.close()
        print("Browser closed.")

if __name__ == "__main__":
    test_chromium_login()
