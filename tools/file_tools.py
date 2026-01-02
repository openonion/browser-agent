"""
File system operations for research agents.
"""
import os
from connectonion import xray

class FileTools:
    """Tools for reading and writing files."""

    @staticmethod
    @xray
    def append_to_file(filepath: str, content: str) -> str:
        """
        Appends content to a specified file.
        Useful for logging research notes or findings.
        """
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content + "\n")
        return f"Successfully appended to {filepath}"

    @staticmethod
    @xray
    def read_file(filepath: str) -> str:
        """
        Reads the entire content of a specified file.
        Useful for reviewing notes.
        """
        if not os.path.exists(filepath):
            return f"File not found: {filepath}"
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    @xray
    def delete_file(filepath: str) -> str:
        """
        Deletes a specified file.
        Useful for cleaning up temporary notes.
        """
        if os.path.exists(filepath):
            os.remove(filepath)
            return f"Successfully deleted file: {filepath}"
        return f"File not found: {filepath}"

