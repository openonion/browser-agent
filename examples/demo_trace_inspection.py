"""
Demo: Trace Inspection with xray.trace()

This example shows how to use xray.trace() to inspect the agent's execution history
and verify that the image_result_formatter plugin correctly converts screenshots
to multimodal vision format.

You'll see:
- Tool execution trace with timing
- Message inspection showing MULTIMODAL format
- Verification that base64 data was converted

Run:
    python examples/demo_trace_inspection.py
"""
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from connectonion import Agent, xray
from connectonion.useful_plugins import image_result_formatter
from browser_agent.web_automation import WebAutomation

# Create web automation instance
web = WebAutomation(use_chrome_profile=False)

# Create agent with image_result_formatter plugin
agent = Agent(
    name="trace_test",
    model="co/gpt-4o-mini",
    tools=web,
    plugins=[image_result_formatter],
    max_iterations=10
)

print("="*60)
print("Testing Image Formatter Plugin with xray.trace()")
print("="*60)
print("\nRunning test...\n")

# Simple test
result = agent.input("""
1. Open the browser (headless)
2. Go to example.com
3. Take a screenshot
4. Close the browser
""")

print(f"\n{'='*60}")
print("XRAY TRACE - Tool Execution History")
print("="*60)
print()

# Use xray.trace() - it will automatically find the agent from the stack
xray.trace()

print(f"\n{'='*60}")
print("MESSAGE INSPECTION - Checking for Image Format")
print("="*60)

# Inspect messages to verify image_result_formatter converted screenshots
messages = agent.current_session['messages']

print(f"\nTotal messages: {len(messages)}\n")

for i, msg in enumerate(messages):
    role = msg['role']

    if role == 'user':
        content = msg.get('content', '')
        if isinstance(content, list):
            # Multimodal message (image + text)
            print(f"Message {i}: ✓ USER (MULTIMODAL - image_result_formatter worked!)")
            for part in content:
                if part.get('type') == 'text':
                    print(f"  - Text: {part['text'][:80]}...")
                elif part.get('type') == 'image_url':
                    url = part['image_url']['url']
                    print(f"  - Image URL: {url[:70]}...")
        else:
            print(f"Message {i}: USER - {str(content)[:80]}...")

    elif role == 'tool':
        tool_call_id = msg.get('tool_call_id', 'N/A')
        content = msg.get('content', '')

        # Check if this is the shortened screenshot message
        if 'Screenshot captured' in content or 'image provided' in content:
            print(f"Message {i}: ✓ TOOL (Shortened by image_result_formatter)")
            print(f"  - Content: {content}")
        else:
            print(f"Message {i}: TOOL - {str(content)[:80]}...")

    elif role == 'assistant':
        if 'tool_calls' in msg:
            tool_names = [tc['function']['name'] for tc in msg['tool_calls']]
            print(f"Message {i}: ASSISTANT - Calling: {', '.join(tool_names)}")
        else:
            print(f"Message {i}: ASSISTANT - {msg.get('content', '')[:80]}...")

print(f"\n{'='*60}")
print("✅ Inspection complete!")
print("="*60)
print("\nLook for:")
print("  ✓ USER (MULTIMODAL) messages - image_result_formatter added these")
print("  ✓ TOOL messages with 'Screenshot captured' - base64 removed")
