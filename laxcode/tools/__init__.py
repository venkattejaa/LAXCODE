"""Tools for LAXCODE"""

from .base import Tool, ToolResult
from .file_tools import FileReadTool, FileEditTool, GlobTool
from .shell_tools import BashTool
from .search_tools import GrepTool

__all__ = [
    "Tool",
    "ToolResult",
    "FileReadTool",
    "FileEditTool",
    "GlobTool",
    "BashTool",
    "GrepTool",
    "get_all_tools",
]


def get_all_tools() -> list[type[Tool]]:
    """Get all available tools"""
    return [
        FileReadTool,
        FileEditTool,
        GlobTool,
        BashTool,
        GrepTool,
    ]
