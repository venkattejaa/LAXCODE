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
from ..providers.base import Message, Provider, ProviderConfig
from ..providers.nvidia_nim import NvidiaNIMProvider, NvidiaNIMModelInfo
from ..providers.openai import OpenAIProvider
from ..providers.anthropic import AnthropicProvider
from ..tools.base import ToolRegistry, get_registry, ToolResult
from ..tools.file_tools import FileReadTool, FileEditTool, GlobTool
from ..tools.shell_tools import BashTool, ViewTool
from ..tools.search_tools import GrepTool


SYSTEM_PROMPT = """You are LAXCODE, an agentic AI coding assistant powered by Laxmana AI.

Your mission is to help users write, edit, and understand code efficiently.

You have access to the following tools:
- `read`: Read file contents with line numbers
- `edit`: Edit files by replacing specific text
- `glob`: Find files matching glob patterns
- `grep`: Search for patterns across files
- `bash`: Execute shell commands
- `view`: View directory structure

When responding:
1. Be concise but thorough in your explanations
2. When editing files, be precise with the old_string to ensure exact matches
3. Always verify changes by reading files when needed
4. Explain your reasoning for code changes
5. Use the tools available to gather information before making changes

Current platform: {platform}
Working directory: {cwd}

Remember: You are LAXCODE. You don't speak or listen - you code with precision and efficiency.
"""


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
        """Show splash screen with v1.2 teaser"""
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

[bold magenta]═══════════════════════════════════════════════════════════[/bold magenta]

[bold green]Version 1.1.0[/bold green]  |  [bold cyan]NVIDIA NIM Ready[/bold cyan]  |  [bold yellow]Open Source[/bold yellow]

[dim]═══════════════════════════════════════════════════════════[/dim]

[bold bright_yellow]🚀 LAXMANA v1.2 COMING SOON![/bold bright_yellow]

[dim]Upcoming features in v1.2:[/dim]
  • Enhanced Laxmana AI animations with voice waveform sync
  • Multi-agent collaboration mode
  • Code review & auto-refactoring
  • Project-wide intelligent search
  • GitHub Copilot-style completions
  • Local model support (Llama.cpp)

[dim]═══════════════════════════════════════════════════════════[/dim]

[green]Ready to code! Type /help for available commands.[/green]
"""
        self.console.print(splash)
    
    async def process_message(self, user_input: str) -> str:
        """Process a user message"""
        if not self.provider or not self.session:
            return "Error: Agent not initialized. Run 'laxcode setup' first."
        
        # Add user message to session
        self.session.add_user_message(user_input)
        
        # Prepare messages for provider
        messages = [
            Message.system(self.session.messages[0].content)  # System prompt
        ]
        
        # Add conversation history
        for msg in self.session.messages[1:]:
            if msg.role == "user":
                messages.append(Message.user(msg.content))
            elif msg.role == "assistant":
                messages.append(Message.assistant(msg.content))
        
        # Get tool schemas
        tool_schemas = self.tool_registry.get_all_schemas()
        
        # Show animation
        if self.simple_animator:
            self.simple_animator.set_mode(AnimationMode.PROCESSING)
            with self.console.status(
                f"[cyan]{self.simple_animator.get_colored_frame()}[/cyan] Thinking...",
                spinner="dots"
            ):
                response = await self.provider.chat(messages)
        else:
            response = await self.provider.chat(messages)
        
        # Process tool calls if any
        assistant_message = response.content
        
        if response.tool_calls:
            # Execute tool calls
            tool_results = []
            
            for tool_call in response.tool_calls:
                tool = self.tool_registry.get(tool_call.name)
                if tool:
                    result = await tool.execute(**tool_call.arguments)
                    tool_results.append({
                        "tool": tool_call.name,
                        "result": result.to_dict()
                    })
            
            # Add tool results to conversation
            if tool_results:
                tool_summary = "\n".join([
                    f"[{r['tool']}: {r['result']['output'][:100]}...]"
                    if len(r['result']['output']) > 100
                    else f"[{r['tool']}: {r['result']['output']}]"
                    for r in tool_results
                ])
                assistant_message += f"\n\n[Tool Results]: {tool_summary}"
        
        # Add assistant response to session
        self.session.add_assistant_message(
            assistant_message,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            model=response.model
        )
        
        # Update token counts
        self.session.update_tokens(response.input_tokens, response.output_tokens)
        
        # Auto-save session
        if self.config.auto_save:
            self.session_store.save(self.session)
        
        return assistant_message
    
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
            yield f"\n\n[Error: {e}]"
        
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
            self.console.print("\n[dim]Goodbye! 👋[/dim]\n")
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

[bold cyan]Available Tools:[/bold cyan]

  • read - Read file contents with line numbers
  • edit - Edit files by replacing text
  • glob - Find files by pattern
  • grep - Search for patterns
  • bash - Execute shell commands
  • view - View directory structure

[bold cyan]Tips:[/bold cyan]

  • Use natural language to ask questions or request code changes
  • The AI can read files, make edits, run commands, and search code
  • Sessions are automatically saved
  • Type Ctrl+C to cancel current operation

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
            dangerous = " [red](dangerous)[/red]" if tool.dangerous else ""
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
