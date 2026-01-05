"""
File system operations for research agents.
"""
import os
from connectonion import xray

class FileTools:
    """Tools for reading and writing files."""

    @xray
    def append_to_file(self, filepath: str, content: str) -> str:
        """
        Appends content to a specified file.
        Useful for logging research notes or findings.
        """
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content + "\n")
        return f"Successfully appended to {filepath}"

    @xray
    def write_file(self, filepath: str, content: str) -> str:
        """
        Writes (or overwrites) content to a specified file.
        Useful for saving final reports.
        """
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"

    @xray
    def read_file(self, filepath: str) -> str:
        """
        Reads the entire content of a specified file.
        Useful for reviewing notes.
        """
        if not os.path.exists(filepath):
            return f"File not found: {filepath}"
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    @xray
    def delete_file(self, filepath: str) -> str:
        """
        Deletes a specified file.
        Useful for cleaning up temporary notes.
        """
        if os.path.exists(filepath):
            os.remove(filepath)
            return f"Successfully deleted file: {filepath}"
        return f"File not found: {filepath}"