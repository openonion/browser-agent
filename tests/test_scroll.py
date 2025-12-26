"""Test scroll() with new consolidated scroll.py module."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from web_automation import WebAutomation
import time

web = WebAutomation(use_chrome_profile=True)
web.open_browser(headless=False)
web.go_to("https://mail.google.com")
time.sleep(3)

print("\n" + "="*60)
print("TEST: scroll() - AI strategy with fallback")
print("="*60)
result = web.scroll(times=3, description="the email list")
print(f"Result: {result}")

print("\n" + "="*60)
print("DONE")
print("="*60)

web.close()
