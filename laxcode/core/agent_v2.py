"""ReAct-style Agent for LAXCODE v2"""

from __future__ import annotations

import json
import os
import platform
import re
from typing import Any, Dict, List, Optional, AsyncIterator

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown

from ..providers.base import Message


class ReActAgent:
    """
    ReAct-style agent with explicit planning
    
    Thought → Action → Observation → ... → Answer
    """
    
    SYSTEM_PROMPT = """You are LAXCODE, an autonomous coding agent.

Your task is to complete coding tasks by thinking step-by-step and using tools.

## Response Format
You must respond in this exact format:

```
Thought: [Your reasoning about what needs to be done]

Action: [JSON tool call]

Observation: [Wait for tool result]
```

## Tool Calling Format
Use this JSON format for tool calls:
```json
{
  "tool": "tool_name",
  "arguments": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

## Available Tools
- `read(file_path, offset=1, limit=2000)` - Read file contents
- `edit(file_path, old_string, new_string)` - Edit file by replacing text
- `apply_diff(file_path, diff)` - Apply unified diff patch
- `glob(pattern, path=".")` - Find files matching pattern
- `grep(pattern, path=".", include="")` - Search for regex
- `bash(command, description="", timeout=120)` - Run shell command
- `view(path=".", depth=2)` - View directory structure
- `run_tests(test_path="", verbose=False)` - Run pytest tests
- `lint(file_path, fix=False)` - Run ruff linter

## Rules
1. ALWAYS use Thought → Action → Observation format
2. Break complex tasks into steps
3. Read files before editing them
4. Test your changes after making edits
5. Use diff-based editing for safety
6. Explain your reasoning clearly in Thought sections

## Example

User: Create a calculator with add and subtract functions

Assistant:
Thought: I need to create a calculator module with two functions. Let me start by creating the file.

Action:
```json
{
  "tool": "edit",
  "arguments": {
    "file_path": "calculator.py",
    "old_string": "",
    "new_string": "def add(a: float, b: float) -> float:\n    '''Add two numbers.'''\n    return a + b\n\ndef subtract(a: float, b: float) -> float:\n    '''Subtract b from a.'''\n    return a - b\n"
  }
}
```

Observation: Successfully created calculator.py

Thought: Now I should verify the file was created correctly and then create tests.

Action:
```json
{
  "tool": "read",
  "arguments": {
    "file_path": "calculator.py"
  }
}
```

Observation: [Shows file contents]

Thought: The file looks good. Now let me create tests.

[Continue until task complete]

Remember: Always verify your work with tests or by reading files back.
"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.max_iterations = 15
        
    def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse tool call from assistant response"""
        # Look for JSON in code blocks
        json_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
        if not json_match:
            # Try without code blocks
            json_match = re.search(r'Action:\s*\n?\s*(\{.*?\})', text, re.DOTALL)
        
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        return None
    
    def extract_thought(self, text: str) -> str:
        """Extract thought from response"""
        match = re.search(r'Thought:\s*(.+?)(?=\n\n|Action:|$)', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def format_observation(self, result: Any) -> str:
        """Format tool result as observation"""
        if isinstance(result, dict):
            if result.get('success'):
                return f"Success: {result.get('output', 'Done')}"
            else:
                return f"Error: {result.get('error', 'Unknown error')}"
        return str(result)
    
    async def run(self, task: str, provider: Any, tool_registry: Any) -> str:
        """Run ReAct loop for a task"""
        
        messages = [
            Message.system(self.SYSTEM_PROMPT),
            Message.user(task)
        ]
        
        iteration = 0
        history = []
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # Get LLM response
            response = await provider.chat(messages)
            content = response.content
            
            # Extract thought
            thought = self.extract_thought(content)
            if thought:
                self.console.print(f"\n[dim]Thought:[/dim] {thought}\n")
            
            # Parse tool call
            tool_call = self.parse_tool_call(content)
            
            if not tool_call:
                # No tool call - task complete
                return content
            
            # Show action
            tool_name = tool_call.get('tool', 'unknown')
            self.console.print(f"[cyan]Action:[/cyan] {tool_name}")
            
            # Execute tool
            tool = tool_registry.get(tool_name)
            if tool:
                try:
                    result = await tool.execute(**tool_call.get('arguments', {}))
                    observation = self.format_observation(result.to_dict() if hasattr(result, 'to_dict') else result)
                except Exception as e:
                    observation = f"Error: {e}"
            else:
                observation = f"Error: Unknown tool '{tool_name}'"
            
            # Show observation
            self.console.print(f"[dim]Observation:[/dim] {observation[:200]}...")
            
            # Add to messages for next iteration
            messages.append(Message.assistant(content))
            messages.append(Message.user(f"Observation: {observation}"))
        
        return "[Reached max iterations]"
