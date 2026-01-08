"""
Tool for performing deep research using the specialized sub-agent.
"""
from pathlib import Path

def perform_deep_research(topic: str) -> str:
    """
    Conducts deep, multi-step research on a specific topic.
    
    This tool uses a specialized sub-agent that shares the browser session
    to exhaustively research the given topic, navigate multiple pages, 
    and synthesize a detailed report.

    Args:
        topic: The full research request or question.
        
    Returns:
        A comprehensive summary of the research findings.
    """
    # Import inside function to avoid circular dependency
    from agents.deep_research import deep_research_agent

    # Ensure a clean slate for the new research task
    for filename in ["research_notes.md", "research_results.md"]:
        Path(filename).unlink(missing_ok=True)

    print(f"\nLaunching Deep Research for: {topic}")
    
    # Run the agent
    result = deep_research_agent.input(topic)
    
    # Safety cleanup: Ensure notes are deleted even if the agent forgot
    Path("research_notes.md").unlink(missing_ok=True)

    print(f"\nDeep Research Complete.")
    return result