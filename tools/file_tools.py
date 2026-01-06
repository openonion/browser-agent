"""
File system operations for research agents.
"""
import os
from connectonion import xray

class FileTools:
    """Tools for reading and writing files."""

    @xray
    def append_research_note(self, filepath: str, content: str) -> str:
        """Appends content to a specified file."""
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content + "\n")
        return f"Successfully appended note to: {filepath}"

    @xray
    def write_final_report(self, filepath: str, content: str) -> str:
        """Writes (or overwrites) content to a specified file."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote final report to: {filepath}"

    @xray
    def review_research_notes(self, filepath: str) -> str:
        """Reads the entire content of a specified file."""
        if not os.path.exists(filepath):
            return f"Research notes not found: {filepath}"
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    @xray
    def delete_research_notes(self, filepath: str) -> str:
        """Deletes a specified file."""
        if os.path.exists(filepath):
            os.remove(filepath)
            return f"Successfully deleted research notes: {filepath}"
        return f"Research notes not found: {filepath}"