"""
Quick test to verify plugins work with browser-agent
"""
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from connectonion import Agent
from connectonion.useful_plugins import image_result_formatter
from web_automation import WebAutomation

# Create web automation instance
web = WebAutomation(use_chrome_profile=False)

# Create agent with plugins
agent = Agent(
    name="plugin_test",
    model="co/gpt-4o-mini",
    tools=web,
    plugins=[image_result_formatter],
    max_iterations=10
)

print("="*60)
print("Testing Browser Agent with Plugins")
print("="*60)
print("\nPlugins loaded:")
print("  ✓ image_result_formatter - Converts screenshots to vision format")
print("\nRunning simple test...\n")

# Simple test
result = agent.input("""
1. Open the browser (headless)
2. Go to example.com
3. Take a screenshot
4. Close the browser
""")

print(f"\n✅ Test completed!")
print(f"Result: {result}")
