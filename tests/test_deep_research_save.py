import os
import pytest
from agents.deep_research import DeepResearch

@pytest.mark.integration
def test_deep_research_can_write_file(web):
    """Test that the DeepResearch sub-agent can write files."""
    web.open_browser(headless=True) 
    deep_researcher = DeepResearch(web)
    
    report_file = "research_results.md"
    if os.path.exists(report_file):
        os.remove(report_file)
        
    # Simplify the task but be very strict about saving
    prompt = "Write 'Test Report Content' to a file named 'research_results.md' using your write_file tool. Do not do any research."
    deep_researcher.perform_deep_research(prompt)
    
    # Assert existence
    assert os.path.exists(report_file), f"File {report_file} was not created"
    
    # Cleanup
    os.remove(report_file)