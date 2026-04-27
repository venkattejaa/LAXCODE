"""Diff-based file editing for LAXCODE"""

from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base import Tool, ToolResult, ToolParameter, register_tool


@register_tool
class FileDiffTool(Tool):
    """Apply unified diff to a file - safer than full rewrites"""
    
    name = "apply_diff"
    description = "Apply a unified diff patch to a file. Use this for precise, line-by-line edits that can be reviewed before applying."
    parameters = [
        ToolParameter(
            name="file_path",
            type="string",
            description="The absolute path to the file to edit",
            required=True
        ),
        ToolParameter(
            name="diff",
            type="string",
            description="Unified diff format patch to apply. Must include @@ headers and proper +/- lines",
            required=True
        ),
    ]
    
    async def execute(self, file_path: str, diff: str) -> ToolResult:
        try:
            path = Path(file_path).resolve()
            
            # Security check
            cwd = Path.cwd().resolve()
            if not str(path).startswith(str(cwd)):
                return ToolResult.error(
                    f"Security error: Cannot edit files outside of workspace"
                )
            
            if not path.exists():
                return ToolResult.error(f"File not found: {file_path}")
            
            if not path.is_file():
                return ToolResult.error(f"Path is not a file: {file_path}")
            
            content = path.read_text(encoding='utf-8', errors='replace')
            lines = content.split('\n')
            
            # Parse the diff
            hunks = self._parse_diff(diff)
            if not hunks:
                return ToolResult.error("Invalid diff format. Expected unified diff with @@ headers")
            
            # Apply hunks in reverse order (to maintain line numbers)
            new_lines = lines.copy()
            applied_hunks = []
            
            for hunk in reversed(hunks):
                result = self._apply_hunk(new_lines, hunk)
                if not result[0]:
                    return ToolResult.error(
                        f"Failed to apply hunk at line {hunk['start_line']}: {result[1]}"
                    )
                new_lines = result[1]
                applied_hunks.append(hunk)
            
            # Write back
            new_content = '\n'.join(new_lines)
            path.write_text(new_content, encoding='utf-8')
            
            return ToolResult.ok(
                output=f"Successfully applied diff to {file_path} ({len(applied_hunks)} hunks)",
                file_path=str(path),
                hunks_applied=len(applied_hunks),
                lines_changed=len(new_lines) - len(lines)
            )
            
        except Exception as e:
            return ToolResult.error(f"Error applying diff: {e}")
    
    def _parse_diff(self, diff: str) -> List[Dict[str, Any]]:
        """Parse unified diff into hunks"""
        hunks = []
        lines = diff.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for hunk header: @@ -start,count +start,count @@
            if line.startswith('@@'):
                match = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
                if not match:
                    i += 1
                    continue
                
                old_start = int(match.group(1))
                old_count = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_count = int(match.group(4)) if match.group(4) else 1
                
                # Collect hunk lines
                hunk_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith('@@'):
                    if lines[i].startswith('---') or lines[i].startswith('+++'):
                        i += 1
                        continue
                    hunk_lines.append(lines[i])
                    i += 1
                
                hunks.append({
                    'start_line': old_start,
                    'old_count': old_count,
                    'new_start': new_start,
                    'new_count': new_count,
                    'lines': hunk_lines
                })
            else:
                i += 1
        
        return hunks
    
    def _apply_hunk(self, lines: List[str], hunk: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Apply a single hunk to the file"""
        start = hunk['start_line'] - 1  # Convert to 0-indexed
        hunk_lines = hunk['lines']
        
        new_lines = lines.copy()
        
        # Collect context and changes
        old_lines = []
        new_hunk_lines = []
        
        for line in hunk_lines:
            if line.startswith('-'):
                old_lines.append(line[1:])
            elif line.startswith('+'):
                new_hunk_lines.append(line[1:])
            else:
                # Context line
                old_lines.append(line)
                new_hunk_lines.append(line)
        
        # Verify old lines match
        if start + len(old_lines) > len(lines):
            return False, lines
        
        for i, old_line in enumerate(old_lines):
            if start + i < len(lines) and lines[start + i] != old_line:
                if i < len(old_lines) - 1:  # Allow last line to be partial
                    return False, lines
        
        # Apply the hunk
        new_lines = lines[:start] + new_hunk_lines + lines[start + len(old_lines):]
        
        return True, new_lines
    
    @staticmethod
    def generate_diff(original: str, modified: str, file_path: str = "file.py") -> str:
        """Generate unified diff between two strings"""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}"
        )
        
        return ''.join(diff)


@register_tool
class TestRunnerTool(Tool):
    """Run tests and return results"""
    
    name = "run_tests"
    description = "Run Python tests using pytest and return results with pass/fail status"
    parameters = [
        ToolParameter(
            name="test_path",
            type="string",
            description="Path to test file or directory (e.g., 'tests/' or 'test_module.py')",
            required=False,
            default=""
        ),
        ToolParameter(
            name="verbose",
            type="boolean",
            description="Show verbose output including passed tests",
            required=False,
            default=False
        ),
    ]
    dangerous = True
    
    async def execute(self, test_path: str = "", verbose: bool = False) -> ToolResult:
        import subprocess
        import asyncio
        
        try:
            cmd = ["python", "-m", "pytest"]
            
            if test_path:
                cmd.append(test_path)
            
            if verbose:
                cmd.append("-v")
            else:
                cmd.append("-q")
            
            # Run tests with timeout
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=60
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return ToolResult.error("Test execution timed out after 60 seconds")
            
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            # Parse results
            exit_code = proc.returncode
            passed = exit_code == 0
            
            output = stdout_str
            if stderr_str:
                output += "\n[stderr]\n" + stderr_str
            
            # Extract summary
            summary = ""
            for line in stdout_str.split('\n'):
                if 'passed' in line or 'failed' in line or 'error' in line:
                    summary = line
                    break
            
            return ToolResult.ok(
                output=output,
                passed=passed,
                exit_code=exit_code,
                summary=summary or "Tests completed"
            )
            
        except FileNotFoundError:
            return ToolResult.error("pytest not found. Install with: pip install pytest")
        except Exception as e:
            return ToolResult.error(f"Error running tests: {e}")


@register_tool  
class CodeLinterTool(Tool):
    """Run code linting with ruff or flake8"""
    
    name = "lint"
    description = "Run Python linter (ruff) on code files to check for style issues"
    parameters = [
        ToolParameter(
            name="file_path",
            type="string",
            description="Path to file or directory to lint",
            required=True
        ),
        ToolParameter(
            name="fix",
            type="boolean",
            description="Automatically fix linting errors where possible",
            required=False,
            default=False
        ),
    ]
    
    async def execute(self, file_path: str, fix: bool = False) -> ToolResult:
        import subprocess
        import asyncio
        
        try:
            cmd = ["python", "-m", "ruff", "check"]
            
            if fix:
                cmd.append("--fix")
            
            cmd.append(file_path)
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=30
            )
            
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            output = stdout_str
            if stderr_str:
                output += "\n[stderr]\n" + stderr_str
            
            return ToolResult.ok(
                output=output,
                exit_code=proc.returncode,
                issues_found="All checks passed" not in stdout_str
            )
            
        except FileNotFoundError:
            return ToolResult.error("ruff not found. Install with: pip install ruff")
        except Exception as e:
            return ToolResult.error(f"Error linting: {e}")
