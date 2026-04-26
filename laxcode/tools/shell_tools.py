"""Shell command tools for LAXCODE"""

from __future__ import annotations

import asyncio
import os
import platform
import shlex
import subprocess
from pathlib import Path
from typing import Any, Optional

from .base import Tool, ToolResult, ToolParameter, register_tool


@register_tool
class BashTool(Tool):
    """Execute shell commands"""
    
    name = "bash"
    description = "Execute a bash command. Use this to run shell commands, check files, install packages, etc."
    parameters = [
        ToolParameter(
            name="command",
            type="string",
            description="The bash command to execute",
            required=True
        ),
        ToolParameter(
            name="description",
            type="string",
            description="Brief description of what the command does",
            required=False,
            default=""
        ),
        ToolParameter(
            name="timeout",
            type="integer",
            description="Timeout in seconds (default: 120)",
            required=False,
            default=120
        ),
        ToolParameter(
            name="workdir",
            type="string",
            description="Working directory for the command (default: current directory)",
            required=False,
            default=""
        ),
    ]
    dangerous = True
    
    async def execute(self, command: str, description: str = "", timeout: int = 120, workdir: str = "") -> ToolResult:
        """Execute a bash command with safety checks"""
        try:
            # Security: Check for dangerous commands
            dangerous_commands = [
                "rm -rf /", "rm -rf ~", "rm -rf /*", "rm -rf .",
                "> /dev/sda", "mkfs.", "dd if=/dev/zero",
                ":(){ :|:& };:", "del /f /s /q", "format ",
                "rd /s /q", "reg delete", "shutdown", "reboot",
                "poweroff", "halt", "init 0", "init 6",
            ]
            
            cmd_lower = command.lower()
            for dangerous in dangerous_commands:
                if dangerous in cmd_lower:
                    return ToolResult.error(
                        f"Security error: Dangerous command detected: {dangerous}"
                    )
            
            # Determine working directory
            cwd = Path(workdir) if workdir else Path(os.getcwd())
            cwd = cwd.resolve()
            
            # Security check for workdir
            if workdir:
                current_dir = Path(os.getcwd()).resolve()
                if not str(cwd).startswith(str(current_dir)):
                    return ToolResult.error(
                        f"Security error: Cannot execute commands outside of workspace"
                    )
            
            # Execute command
            if platform.system() == "Windows":
                # Windows execution
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(cwd),
                    shell=True
                )
            else:
                # Unix execution
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(cwd),
                    shell=True
                )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult.error(f"Command timed out after {timeout} seconds")
            
            # Decode output
            stdout_str = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            # Build result
            output_parts = []
            if stdout_str:
                output_parts.append(stdout_str)
            if stderr_str:
                output_parts.append(f"[stderr]\n{stderr_str}")
            
            output = '\n'.join(output_parts) if output_parts else "(no output)"
            
            success = process.returncode == 0
            
            if success:
                return ToolResult.ok(
                    output=output,
                    return_code=process.returncode,
                    command=command,
                    description=description or "Shell command executed",
                )
            else:
                return ToolResult.error(
                    f"Command failed with exit code {process.returncode}\n{output}",
                    return_code=process.returncode,
                    command=command,
                    stdout=stdout_str,
                    stderr=stderr_str,
                )
                
        except Exception as e:
            return ToolResult.error(f"Error executing command: {e}")


@register_tool
class ViewTool(Tool):
    """View directory contents"""
    
    name = "view"
    description = "View the contents of a directory. Use this to explore the file system."
    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="Directory path to view (default: current directory)",
            required=False,
            default=""
        ),
        ToolParameter(
            name="depth",
            type="integer",
            description="How many levels deep to show (default: 1)",
            required=False,
            default=1
        ),
    ]
    
    async def execute(self, path: str = "", depth: int = 1) -> ToolResult:
        try:
            target_path = Path(path) if path else Path(os.getcwd())
            target_path = target_path.resolve()
            
            if not target_path.exists():
                return ToolResult.error(f"Path not found: {path}")
            
            if not target_path.is_dir():
                return ToolResult.error(f"Path is not a directory: {path}")
            
            def format_tree(p: Path, level: int = 0, max_depth: int = 1) -> List[str]:
                lines = []
                if level > max_depth:
                    return lines
                
                try:
                    entries = sorted(p.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
                except PermissionError:
                    return [f"{'  ' * level}[Permission Denied]"]
                
                for i, entry in enumerate(entries):
                    is_last = i == len(entries) - 1
                    prefix = "  " * level + ("└── " if is_last else "├── ")
                    
                    if entry.is_dir():
                        lines.append(f"{prefix}📁 {entry.name}/")
                        if level < max_depth:
                            lines.extend(format_tree(entry, level + 1, max_depth))
                    else:
                        size = entry.stat().st_size
                        size_str = f" ({self._format_size(size)})" if size > 0 else ""
                        lines.append(f"{prefix}📄 {entry.name}{size_str}")
                
                return lines
            
            lines = [f"📂 {target_path}", ""]
            lines.extend(format_tree(target_path, 0, depth))
            
            return ToolResult.ok(
                output='\n'.join(lines),
                path=str(target_path),
                entries_found=len(list(target_path.iterdir())),
            )
            
        except Exception as e:
            return ToolResult.error(f"Error viewing directory: {e}")
    
    def _format_size(self, size: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
