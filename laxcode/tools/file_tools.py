"""File operation tools for LAXCODE"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List, Optional

from .base import Tool, ToolResult, ToolParameter, register_tool


@register_tool
class FileReadTool(Tool):
    """Read file contents"""
    
    name = "read"
    description = "Read the contents of a file at the specified path. Use this when you need to examine the contents of an existing file."
    parameters = [
        ToolParameter(
            name="file_path",
            type="string",
            description="The absolute path to the file to read",
            required=True
        ),
        ToolParameter(
            name="offset",
            type="integer",
            description="Line number to start reading from (1-indexed)",
            required=False,
            default=1
        ),
        ToolParameter(
            name="limit",
            type="integer",
            description="Maximum number of lines to read",
            required=False,
            default=2000
        ),
    ]
    
    async def execute(self, file_path: str, offset: int = 1, limit: int = 2000) -> ToolResult:
        try:
            path = Path(file_path).resolve()
            
            # Security check - ensure file is within workspace
            cwd = Path(os.getcwd()).resolve()
            if not str(path).startswith(str(cwd)):
                return ToolResult.error(
                    f"Security error: Cannot read files outside of workspace. "
                    f"Path: {path} is not within {cwd}"
                )
            
            if not path.exists():
                return ToolResult.error(f"File not found: {file_path}")
            
            if not path.is_file():
                return ToolResult.error(f"Path is not a file: {file_path}")
            
            # Read the file
            content = path.read_text(encoding='utf-8', errors='replace')
            lines = content.split('\n')
            
            # Apply offset and limit
            start_line = max(0, offset - 1)
            end_line = min(len(lines), start_line + limit)
            
            selected_lines = lines[start_line:end_line]
            result_content = '\n'.join(selected_lines)
            
            # Add line numbers
            numbered_lines = []
            for i, line in enumerate(selected_lines, start=start_line + 1):
                numbered_lines.append(f"{i}: {line}")
            
            numbered_content = '\n'.join(numbered_lines)
            total_lines = len(lines)
            
            return ToolResult.ok(
                output=numbered_content,
                file_path=str(path),
                total_lines=total_lines,
                lines_read=len(selected_lines),
                start_line=start_line + 1,
                end_line=end_line,
            )
            
        except PermissionError:
            return ToolResult.error(f"Permission denied: {file_path}")
        except Exception as e:
            return ToolResult.error(f"Error reading file: {e}")


@register_tool
class FileEditTool(Tool):
    """Edit file contents"""
    
    name = "edit"
    description = "Edit a file by replacing text. Use this to make precise changes to files."
    parameters = [
        ToolParameter(
            name="file_path",
            type="string",
            description="The absolute path to the file to edit",
            required=True
        ),
        ToolParameter(
            name="old_string",
            type="string",
            description="The text to replace (must match exactly, including indentation)",
            required=True
        ),
        ToolParameter(
            name="new_string",
            type="string",
            description="The text to replace with",
            required=True
        ),
    ]
    
    async def execute(self, file_path: str, old_string: str, new_string: str) -> ToolResult:
        try:
            path = Path(file_path).resolve()
            
            # Security check
            cwd = Path(os.getcwd()).resolve()
            if not str(path).startswith(str(cwd)):
                return ToolResult.error(
                    f"Security error: Cannot edit files outside of workspace"
                )
            
            if not path.exists():
                return ToolResult.error(f"File not found: {file_path}")
            
            if not path.is_file():
                return ToolResult.error(f"Path is not a file: {file_path}")
            
            content = path.read_text(encoding='utf-8', errors='replace')
            
            # Count occurrences
            occurrences = content.count(old_string)
            
            if occurrences == 0:
                return ToolResult.error(
                    f"Text not found in file: {repr(old_string[:50])}..."
                )
            
            if occurrences > 1:
                return ToolResult.error(
                    f"Multiple occurrences found ({occurrences}). "
                    f"Please make the old_string more specific to match exactly one location."
                )
            
            # Perform the replacement
            new_content = content.replace(old_string, new_string, 1)
            
            # Write back
            path.write_text(new_content, encoding='utf-8')
            
            # Calculate line numbers
            lines_before = content[:content.index(old_string)].count('\n') + 1
            lines_after = new_content.count('\n') - content.count('\n')
            
            return ToolResult.ok(
                output=f"Successfully edited {file_path}",
                file_path=str(path),
                lines_changed=lines_after + 1,
                start_line=lines_before,
            )
            
        except PermissionError:
            return ToolResult.error(f"Permission denied: {file_path}")
        except Exception as e:
            return ToolResult.error(f"Error editing file: {e}")


@register_tool
class GlobTool(Tool):
    """Find files by pattern"""
    
    name = "glob"
    description = "Find files matching a glob pattern. Use this to explore the codebase structure."
    parameters = [
        ToolParameter(
            name="pattern",
            type="string",
            description="Glob pattern to match (e.g., '**/*.py', 'src/**/*.js')",
            required=True
        ),
        ToolParameter(
            name="path",
            type="string",
            description="Directory to search in (default: current directory)",
            required=False,
            default=""
        ),
    ]
    
    async def execute(self, pattern: str, path: str = "") -> ToolResult:
        try:
            search_path = Path(path) if path else Path(os.getcwd())
            search_path = search_path.resolve()
            
            if not search_path.exists():
                return ToolResult.error(f"Path not found: {path}")
            
            if not search_path.is_dir():
                return ToolResult.error(f"Path is not a directory: {path}")
            
            # Find matching files
            matches = sorted(search_path.glob(pattern), key=lambda p: (p.is_file(), p.name))
            
            # Format results
            lines = []
            for match in matches:
                rel_path = match.relative_to(search_path)
                file_type = "📄" if match.is_file() else "📁"
                lines.append(f"{file_type} {rel_path}")
            
            output = '\n'.join(lines) if lines else "No files found matching the pattern"
            
            return ToolResult.ok(
                output=output,
                matches_found=len(matches),
                pattern=pattern,
                search_path=str(search_path),
            )
            
        except Exception as e:
            return ToolResult.error(f"Error globbing: {e}")
