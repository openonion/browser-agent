"""Host browser-agent as HTTP service.

Usage:
    # Local development
    python main.py

    # Deploy to ConnectOnion Cloud
    co deploy
"""
from connectonion import host
from agent import agent

if __name__ == "__main__":
    host(agent, trust="strict")
