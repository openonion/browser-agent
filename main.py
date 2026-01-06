"""Host browser-agent as HTTP/WebSocket service.
Usage:
    # Local development (open trust for testing)
    python main.py
    # Production deployment (strict trust)
    TRUST=strict python main.py
    # Deploy to ConnectOnion Cloud
    co deploy
"""
import os
from connectonion import host
from agent import agent

if __name__ == "__main__":
    trust = os.environ.get("TRUST", "open")  # Default to open for local dev
    print(f"Starting browser-agent with trust={trust}")
    print("WebSocket endpoint: ws://localhost:8000/ws")
    print("HTTP endpoint: http://localhost:8000/input")
    host(agent, trust=trust, relay_url=None)  # Disable relay for local testing