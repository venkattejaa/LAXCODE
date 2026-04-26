"""Search tools for LAXCODE"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, List, Optional, Tuple

from .base import Tool, ToolResult, ToolParameter, register_tool


@register_tool
class GrepTool(Tool):
    """Search for patterns in files"""
    
    name = "grep"
    description = "Search for a regex pattern in files. Use this to find code, references, or text across the codebase."
    parameters = [
        ToolParameter(
            name="pattern",
            type="string",
            description="Regular expression pattern to search for",
            required=True
        ),
        ToolParameter(
            name="path",
            type="string",
            description="Directory or file to search in (default: current directory)",
            required=False,
            default=""
        ),
        ToolParameter(
            name="include",
            type="string",
            description="File pattern to include (e.g., '*.py', '*.js')",
            required=False,
            default=""
        ),
    ]
    
    async def execute(self, pattern: str, path: str = "", include: str = "") -> ToolResult:
        try:
            search_path = Path(path) if path else Path(os.getcwd())
            search_path = search_path.resolve()
            
            if not search_path.exists():
                return ToolResult.error(f"Path not found: {path}")
            
            # Compile regex
            try:
                regex = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                return ToolResult.error(f"Invalid regex pattern: {e}")
            
            # Determine files to search
            files_to_search = []
            
            if search_path.is_file():
                files_to_search = [search_path]
            else:
                if include:
                    files_to_search = list(search_path.rglob(include))
                else:
                    # Default: search common code files
                    for ext in ['*.py', '*.js', '*.ts', '*.tsx', '*.jsx', '*.java', '*.cpp', '*.c', '*.h', '*.rs', '*.go', '*.rb', '*.php', '*.md']:
                        files_to_search.extend(search_path.rglob(ext))
                
                files_to_search = [f for f in files_to_search if f.is_file()]
            
            # Search in files
            matches = []
            
            for file_path in files_to_search:
                try:
                    content = file_path.read_text(encoding='utf-8', errors='replace')
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        if regex.search(line):
                            # Get context (lines before and after)
                            rel_path = file_path.relative_to(search_path) if search_path in file_path.parents else file_path.name
                            
                            matches.append({
                                'file': str(rel_path),
                                'line': line_num,
                                'content': line.strip(),
                                'full_path': str(file_path)
                            })
                            
                            # Limit results
                            if len(matches) >= 100:
                                break
                    
                    if len(matches) >= 100:
                        break
                        
                except (PermissionError, UnicodeDecodeError):
                    continue
                except Exception:
                    continue
            
            # Format results
            if not matches:
                return ToolResult.ok(
                    output=f"No matches found for pattern: {pattern}",
                    pattern=pattern,
                    files_searched=len(files_to_search),
                    matches_found=0,
                )
            
            lines = []
            current_file = None
            
            for match in matches[:50]:  # Limit display
                if match['file'] != current_file:
                    lines.append(f"\n[bold cyan]{match['file']}[/bold cyan]")
                    current_file = match['file']
                
                lines.append(f"  {match['line']:4d}: {match['content'][:80]}")
            
            if len(matches) > 50:
                lines.append(f"\n... and {len(matches) - 50} more matches")
            
            return ToolResult.ok(
                output='\n'.join(lines),
                pattern=pattern,
                files_searched=len(files_to_search),
                matches_found=len(matches),
            )
            
        except Exception as e:
            return ToolResult.error(f"Error searching: {e}")
