from agents.deep_research import DeepResearch
from tools.browser import Browser
import os

def test_standalone_deep_research():
    print("Testing DeepResearch standalone...")
    web = Browser(headless=True)
    researcher = DeepResearch(web)
    
    # Simple topic
    topic = "What is the capital of France and its population?"
    result = researcher.perform_deep_research(topic)
    
    print("\nRESEARCH RESULT:")
    print(result)
    
    web.close()

if __name__ == "__main__":
    test_standalone_deep_research()

