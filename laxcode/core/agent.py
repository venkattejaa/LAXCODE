"""Main agent for LAXCODE"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import sys
from typing import Any, Dict, List, Optional, AsyncIterator

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.text import Text
from rich.align import Align

from ..animations.core import LaxmanaAnimator, AnimationMode, SimpleAnimator
from ..config.manager import ConfigManager, get_config_manager
from ..core.session import Session, get_session_store
from ..providers.base import Message, Provider, ProviderConfig, ToolCall
from ..providers.nvidia_nim import NvidiaNIMProvider, NvidiaNIMModelInfo
from ..providers.openai import OpenAIProvider
from ..providers.anthropic import AnthropicProvider
from ..tools.base import ToolRegistry, get_registry, ToolResult
from ..tools.file_tools import FileReadTool, FileEditTool, GlobTool
from ..tools.shell_tools import BashTool, ViewTool
from ..tools.search_tools import GrepTool


SYSTEM_PROMPT = """You are LAXCODE, an agentic AI coding assistant. You help users write, edit, debug, and understand code.

## Tools available
- `read`: Read file contents with line numbers
- `edit`: Edit a file by replacing specific text (old_string → new_string)
- `glob`: Find files matching a glob pattern
- `grep`: Search for a regex pattern across files
- `bash`: Execute a shell command (requires confirmation)
- `view`: View directory structure

## How to behave
**Use tools directly. Do not describe what you are about to do — just do it.**
- Wrong: "I will now create the file using the edit tool..."
- Right: call `edit` immediately

**Agentic loop: keep using tools until the task is fully complete.**
After each tool result, decide if more steps are needed. Only stop when the task is done and verified.

**Always verify your work.** After writing or editing a file, call `read` to confirm the content is correct.

**For new files**, use `edit` with an empty `old_string` to create the file from scratch.

## Code quality rules
1. **Never import or reference laxcode internals in generated code.** Generated code must be completely standalone and runnable without LAXCODE installed.
   BAD: `from laxcode import tools`
   GOOD: standalone Python with only standard library or specified dependencies

2. **Write clean, idiomatic code.**
   - Proper indentation (4 spaces for Python)
   - Docstrings on all functions and classes
   - Type hints where appropriate
   - Meaningful variable names

3. **Multiline file content must be properly formatted.**
   When writing multiline content with `edit`, pass the actual newlines — never use `\\n` escape sequences as literal text.

4. **Never truncate code.** Always write complete, working implementations.

5. **Match the language and style of existing code** when editing files.

## File writing example
To create `hello.py`:
```
edit(
    file_path="hello.py",
    old_string="",
    new_string="""def greet(name: str) -> str:
    \"\"\"Return a greeting message.\"\"\"
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
"""
)
```

## Error handling
If a tool fails:
1. Read the error carefully
2. Fix the issue (wrong path, wrong old_string, etc.)
3. Retry — do not give up after one failure

If `edit` fails because `old_string` doesn't match, use `read` first to see the exact current content, then retry with the correct string.

## Shell commands
Before running bash, explain what the command does and why. Wait for confirmation on destructive operations.

Safe to run without asking: `python`, `pip`, `ls`, `cat`, `echo`, `mkdir`, `cd`
Always ask before: `rm`, `git push`, `pip uninstall`, anything with `sudo`

## Session context
Platform: {platform}
Working directory: {cwd}

You are LAXCODE. Ship working code.
"""

MAX_TOOL_ITERATIONS = 10  # prevent infinite loops


class LaxcodeAgent:
    """Main LAXCODE agent with Laxmana AI animations"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.console = Console()
        self.config_manager = config_manager or get_config_manager()
        self.config = self.config_manager.load()
        self.session_store = get_session_store()
        self.session: Optional[Session] = None
        self.provider: Optional[Provider] = None
        self.animator: Optional[LaxmanaAnimator] = None
        self.simple_animator: Optional[SimpleAnimator] = None
        
        # Register tools
        self.tool_registry = get_registry()
        self._register_default_tools()
        
    def _register_default_tools(self) -> None:
        """Register default tools"""
        from ..tools import get_all_tools
        for tool_class in get_all_tools():
            self.tool_registry.register(tool_class)
    
    async def initialize(self) -> bool:
        """Initialize the agent"""
        # Check if API key is configured
        api_key = self.config_manager.get_api_key(self.config.provider)
        
        if not api_key:
            self.console.print("[yellow]No API key configured. Run 'laxcode setup' to configure.[/yellow]")
            return False
        
        # Get the full model name (convert alias to full name for NVIDIA)
        model = self.config.model
        if self.config.provider == "nvidia":
            from ..providers.nvidia_nim import NvidiaNIMProvider
            model = NvidiaNIMProvider.AVAILABLE_MODELS.get(model, model)
        
        # Initialize provider
        provider_config = ProviderConfig(
            api_key=api_key,
            model=model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
            timeout=self.config.timeout,
        )
        
        if self.config.provider == "nvidia":
            self.provider = NvidiaNIMProvider(provider_config)
        elif self.config.provider == "openai":
            self.provider = OpenAIProvider(provider_config)
        elif self.config.provider == "anthropic":
            self.provider = AnthropicProvider(provider_config)
        else:
            self.console.print(f"[red]Unknown provider: {self.config.provider}[/red]")
            return False
        
        # Initialize animator if enabled
        if self.config.animations_enabled:
            try:
                self.animator = LaxmanaAnimator(self.console)
                self.simple_animator = SimpleAnimator(self.console)
            except Exception:
                self.animator = None
                self.simple_animator = None
        
        # Create new session
        self.session = self.session_store.create(workspace=str(os.getcwd()))
        
        # Add system message
        system_content = SYSTEM_PROMPT.format(
            platform=f"{platform.system()} {platform.release()}",
            cwd=os.getcwd()
        )
        self.session.add_system_message(system_content)
        
        return True
    
    async def show_splash(self) -> None:
        """Show splash screen"""
        splash = """
[bold cyan]
██╗      █████╗ ██╗  ██╗ ██████╗ ██████╗ ██████╗ ███████╗
██║     ██╔══██╗╚██╗██╔╝██╔════╝██╔═══██╗██╔══██╗██╔════╝
██║     ███████║ ╚███╔╝ ██║     ██║   ██║██║  ██║█████╗  
██║     ██╔══██║ ██╔██╗ ██║     ██║   ██║██║  ██║██╔══╝  
███████╗██║  ██║██╔╝ ██╗╚██████╗╚██████╔╝██████╔╝███████╗
╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
[/bold cyan]

[bold yellow]           Powered by Laxmana AI[/bold yellow]
[dim]     Agentic Coding Assistant for Developers[/dim]

[green]Ready to code! Type /help for available commands.[/green]
"""
        self.console.print(splash)

    async def _execute_tool_call(self, tool_call) -> Dict[str, Any]:
        """Execute a single tool call and return result dict"""
        tool = self.tool_registry.get(tool_call.name)
        if not tool:
            return {
                "tool": tool_call.name,
                "success": False,
                "output": f"Unknown tool: {tool_call.name}"
            }
        
        try:
            result = await tool.execute(**tool_call.arguments)
            return {
                "tool": tool_call.name,
                "success": result.success,
                "output": result.output,
                "error": result.error or ""
            }
        except Exception as e:
            return {
                "tool": tool_call.name,
                "success": False,
                "output": "",
                "error": str(e)
            }

    async def process_message(self, user_input: str) -> str:
        """Process a user message with a proper agentic loop"""
        if not self.provider or not self.session:
            return "Error: Agent not initialized. Run 'laxcode setup' first."
        
        # Add user message to session
        self.session.add_user_message(user_input)
        
        iteration = 0
        final_response = ""
        
        while iteration < MAX_TOOL_ITERATIONS:
            iteration += 1
            
            # Build message list from session
            messages = [
                Message.system(self.session.messages[0].content)
            ]
            
            for msg in self.session.messages[1:]:
                if msg.role == "user":
                    messages.append(Message.user(msg.content))
                elif msg.role == "assistant":
                    messages.append(Message.assistant(msg.content))
            
            # Get tool schemas for the provider
            tool_schemas = self.tool_registry.get_all_schemas()
            
            # Call LLM
            if self.simple_animator:
                self.simple_animator.set_mode(AnimationMode.PROCESSING)
                with self.console.status(
                    f"[cyan]{self.simple_animator.get_colored_frame()}[/cyan] Thinking...",
                    spinner="dots"
                ):
                    response = await self.provider.chat(messages, tools=tool_schemas)
            else:
                response = await self.provider.chat(messages, tools=tool_schemas)
            
            final_response = response.content
            
            # No tool calls → done
            if not response.tool_calls:
                self.session.add_assistant_message(
                    final_response,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    model=response.model
                )
                self.session.update_tokens(response.input_tokens, response.output_tokens)
                break
            
            # Execute all tool calls
            if self.simple_animator:
                self.simple_animator.set_mode(AnimationMode.WORKING)
            
            tool_results_text = []
            for tool_call in response.tool_calls:
                result = await self._execute_tool_call(tool_call)
                
                # Show tool activity to user
                status_icon = "✓" if result["success"] else "✗"
                status_color = "green" if result["success"] else "red"
                self.console.print(
                    f"  [{status_color}]{status_icon}[/{status_color}] "
                    f"[dim]{result['tool']}[/dim]"
                )
                
                if result["output"]:
                    output_preview = result["output"][:200] + "..." if len(result["output"]) > 200 else result["output"]
                    self.console.print(
                        Panel(output_preview, border_style="dim", padding=(0, 1))
                    )
                
                tool_results_text.append(
                    f"[Tool: {result['tool']}]
"
                    f"Success: {result['success']}
"
                    f"Output: {result['output']}
"
                    f"Error: {result['error']}"
                )
            
            # Feed tool results back into conversation
            combined = response.content + "

[Tool Results]
" + "
---
".join(tool_results_text)
            
            self.session.add_assistant_message(
                combined,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                model=response.model
            )
            self.session.update_tokens(response.input_tokens, response.output_tokens)
            
            # Add tool results as user context for next iteration
            self.session.add_user_message(
                f"[Tool results from previous step]
" + "
---
".join(tool_results_text) + "

Continue with the task. If it is complete, summarize what was done."
            )
        else:
            # Hit max iterations
            final_response += f"

[Warning: reached max tool iterations ({MAX_TOOL_ITERATIONS})]"
        
        # Auto-save session
        if self.config.auto_save:
            self.session_store.save(self.session)
        
        return final_response
    
    async def stream_message(self, user_input: str) -> AsyncIterator[str]:
        """Stream a response to a user message"""
        if not self.provider or not self.session:
            yield "Error: Agent not initialized. Run 'laxcode setup' first."
            return
        
        # Add user message to session
        self.session.add_user_message(user_input)
        
        # Prepare messages
        messages = [
            Message.system(self.session.messages[0].content)
        ]
        
        for msg in self.session.messages[1:]:
            if msg.role == "user":
                messages.append(Message.user(msg.content))
            elif msg.role == "assistant":
                messages.append(Message.assistant(msg.content))
        
        # Stream response
        full_response = []
        
        if self.simple_animator:
            self.simple_animator.set_mode(AnimationMode.WORKING)
        
        try:
            async for chunk in self.provider.chat_stream(messages):
                full_response.append(chunk)
                yield chunk
        except Exception as e:
            yield f"

[Error: {e}]"
        
        # Store complete response
        complete = "".join(full_response)
        self.session.add_assistant_message(complete)
        
        if self.config.auto_save:
            self.session_store.save(self.session)
    
    def render_response(self, content: str) -> None:
        """Render assistant response with proper formatting"""
        # Check for code blocks
        if "```" in content:
            parts = content.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    # Regular text
                    if part.strip():
                        self.console.print(Markdown(part))
                else:
                    # Code block
                    lines = part.split("\n")
                    lang = lines[0].strip() if lines else ""
                    code = "\n".join(lines[1:]) if len(lines) > 1 else ""
                    
                    if code.strip():
                        syntax = Syntax(code, lang or "text", theme="monokai", line_numbers=True)
                        self.console.print(Panel(syntax, border_style="cyan"))
        else:
            self.console.print(Markdown(content))
    
    async def run_interactive(self) -> None:
        """Run interactive mode"""
        await self.show_splash()
        
        self.console.print("\n[dim]Session ID:[/dim] [cyan]{}[/cyan]\n".format(
            self.session.session_id if self.session else "N/A"
        ))
        
        while True:
            try:
                # Get user input
                user_input = self.console.input("[bold green]❯❯❯[/bold green] ")
                user_input = user_input.strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith("/"):
                    if await self._handle_command(user_input):
                        break
                    continue
                
                # Process message
                if self.simple_animator:
                    self.simple_animator.set_mode(AnimationMode.PROCESSING)
                
                response = await self.process_message(user_input)
                
                # Render response
                self.console.print()
                self.render_response(response)
                self.console.print()
                
            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]Interrupted. Type /exit to quit.[/yellow]\n")
            except Exception as e:
                self.console.print(f"\n[red]Error: {e}[/red]\n")
    
    async def _handle_command(self, command: str) -> bool:
        """Handle special commands, returns True if should exit"""
        cmd = command.lower().strip()
        
        if cmd in ["/exit", "/quit", "/q"]:
            self.console.print("\n[dim]Goodbye![/dim]\n")
            return True
        
        elif cmd == "/help":
            self._show_help()
        
        elif cmd == "/config":
            self.config_manager.show_config()
        
        elif cmd == "/sessions":
            self._list_sessions()
        
        elif cmd == "/clear":
            self.console.clear()
        
        elif cmd == "/tools":
            self._list_tools()
        
        elif cmd == "/models":
            self._show_models()
        
        elif cmd.startswith("/read "):
            path = command[6:].strip()
            await self._quick_read(path)
        
        elif cmd.startswith("/glob "):
            pattern = command[6:].strip()
            await self._quick_glob(pattern)
        
        elif cmd.startswith("/grep "):
            pattern = command[6:].strip()
            await self._quick_grep(pattern)
        
        else:
            self.console.print(f"[yellow]Unknown command: {command}[/yellow]")
            self.console.print("Type /help for available commands.\n")
        
        return False
    
    def _show_help(self) -> None:
        """Show help message"""
        help_text = """
[bold cyan]LAXCODE Commands:[/bold cyan]

  [bold]/help[/bold]      Show this help message
  [bold]/config[/bold]    Show current configuration
  [bold]/sessions[/bold]  List saved sessions
  [bold]/tools[/bold]     List available tools
  [bold]/models[/bold]    Show available models
  [bold]/clear[/bold]     Clear the screen
  [bold]/exit[/bold]      Exit LAXCODE

[bold cyan]Quick Tools:[/bold cyan]

  [bold]/read <path>[/bold]      Read a file
  [bold]/glob <pattern>[/bold]   Find files matching pattern
  [bold]/grep <pattern>[/bold]   Search for pattern in files

"""
        self.console.print(help_text)
    
    def _list_sessions(self) -> None:
        """List saved sessions"""
        sessions = self.session_store.list_sessions()
        
        if not sessions:
            self.console.print("[dim]No saved sessions.[/dim]\n")
            return
        
        self.console.print("[bold cyan]Saved Sessions:[/bold cyan]\n")
        for s in sessions[:10]:
            self.console.print(
                f"  [bold]{s.session_id}[/bold] - "
                f"{len(s.messages)} messages - "
                f"{s.updated_at[:19]}"
            )
        self.console.print()
    
    def _list_tools(self) -> None:
        """List available tools"""
        self.console.print("[bold cyan]Available Tools:[/bold cyan]\n")
        
        for tool in self.tool_registry.get_all_tools():
            dangerous = " [red](requires confirmation)[/red]" if tool.dangerous else ""
            self.console.print(f"  [bold]{tool.name}[/bold]{dangerous}")
            self.console.print(f"    {tool.description}")
            self.console.print()
    
    def _show_models(self) -> None:
        """Show available models"""
        if self.config.provider == "nvidia":
            self.console.print(NvidiaNIMModelInfo.print_model_table())
        else:
            self.console.print(f"[cyan]Current provider:[/cyan] {self.config.provider}")
            self.console.print(f"[cyan]Current model:[/cyan] {self.config.model}\n")
    
    async def _quick_read(self, path: str) -> None:
        """Quickly read a file"""
        tool = FileReadTool()
        result = await tool.execute(file_path=path)
        
        if result.success:
            self.console.print(f"\n[dim]File: {result.data.get('file_path')}[/dim]")
            self.console.print(f"[dim]Lines: {result.data.get('start_line')}-{result.data.get('end_line')} of {result.data.get('total_lines')}[/dim]\n")
            
            syntax = Syntax(result.output, "python", theme="monokai", line_numbers=False)
            self.console.print(Panel(syntax, border_style="cyan"))
        else:
            self.console.print(f"[red]Error: {result.error}[/red]")
        self.console.print()
    
    async def _quick_glob(self, pattern: str) -> None:
        """Quickly glob files"""
        tool = GlobTool()
        result = await tool.execute(pattern=pattern)
        
        if result.success:
            self.console.print(f"\n[dim]Pattern: {pattern}[/dim]")
            self.console.print(f"[dim]Found: {result.data.get('matches_found', 0)} files[/dim]\n")
            self.console.print(result.output)
        else:
            self.console.print(f"[red]Error: {result.error}[/red]")
        self.console.print()
    
    async def _quick_grep(self, pattern: str) -> None:
        """Quickly grep for pattern"""
        tool = GrepTool()
        result = await tool.execute(pattern=pattern)
        
        if result.success:
            self.console.print(f"\n[dim]Pattern: {pattern}[/dim]")
            self.console.print(f"[dim]Matches: {result.data.get('matches_found', 0)}[/dim]\n")
            self.console.print(result.output)
        else:
            self.console.print(f"[red]Error: {result.error}[/red]")
        self.console.print()
    
    async def close(self) -> None:
        """Clean up resources"""
        if self.provider:
            if hasattr(self.provider, 'close'):
                await self.provider.close()
        
        if self.session and self.config.auto_save:
            self.session_store.save(self.session)
