"""Main entry point for LAXCODE"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .config.manager import ConfigManager, get_config_manager
from .core.agent import LaxcodeAgent
from .providers.nvidia_nim import NvidiaNIMModelInfo


def show_version() -> None:
    """Show version information"""
    console = Console()
    version_text = """
[bold cyan]LAXCODE[/bold cyan] [bold]v1.1.0[/bold]

[dim]Powered by Laxmana AI[/dim]
[dim]Agentic Coding Assistant for Developers[/dim]

[bold green]Features:[/bold green]
  • NVIDIA NIM API support (Free models)
  • OpenAI API support
  • Anthropic Claude API support
  • Laxmana AI animations
  • File operations (read, edit, glob)
  • Shell command execution
  • Code search (grep)
  • Session management

[bold yellow]Version 1.2 Coming Soon![/bold yellow]
  • Enhanced animations
  • Multi-agent mode
  • Auto-refactoring

[dim]GitHub: https://github.com/venkattejaa/LAXCODE[/dim]
"""
    console.print(version_text)


async def run_setup() -> int:
    """Run setup wizard"""
    config_manager = get_config_manager()
    success = config_manager.setup_wizard()
    return 0 if success else 1


async def run_chat(initial_message: Optional[str] = None) -> int:
    """Run interactive chat mode"""
    config_manager = get_config_manager()
    agent = LaxcodeAgent(config_manager)
    
    if not await agent.initialize():
        console = Console()
        console.print("\n[red]Failed to initialize LAXCODE.[/red]")
        console.print("[yellow]Please run 'laxcode setup' to configure your API key.[/yellow]\n")
        return 1
    
    try:
        if initial_message:
            # Process single message
            response = await agent.process_message(initial_message)
            agent.render_response(response)
        else:
            # Run interactive mode
            await agent.run_interactive()
        
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        console = Console()
        console.print(f"\n[red]Error: {e}[/red]\n")
        return 1
    finally:
        await agent.close()


async def run_config_command() -> int:
    """Show configuration"""
    config_manager = get_config_manager()
    config_manager.show_config()
    return 0


async def run_models_command() -> int:
    """Show available models"""
    console = Console()
    console.print(NvidiaNIMModelInfo.print_model_table())
    return 0


async def run_tools_command() -> int:
    """List available tools"""
    from .tools.base import get_registry
    
    console = Console()
    registry = get_registry()
    
    console.print("[bold cyan]Available Tools:[/bold cyan]\n")
    
    for tool in registry.get_all_tools():
        dangerous = " [red](requires confirmation)[/red]" if tool.dangerous else ""
        console.print(f"  [bold]{tool.name}[/bold]{dangerous}")
        console.print(f"    {tool.description}")
        console.print()
    
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        prog="laxcode",
        description="LAXCODE - Agentic AI Coding Assistant powered by Laxmana AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  laxcode                    Start interactive chat
  laxcode "hello world"      Send a single message
  laxcode setup              Configure API keys
  laxcode config             Show configuration
  laxcode models             List available models
  laxcode tools              List available tools

For more help: https://github.com/venkattejaa/LAXCODE
        """
    )
    
    parser.add_argument(
        "message",
        nargs="?",
        help="Message to send (if not provided, starts interactive mode)"
    )
    
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Show version information"
    )
    
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run setup wizard"
    )
    
    parser.add_argument(
        "--config",
        action="store_true",
        help="Show configuration"
    )
    
    parser.add_argument(
        "--models",
        action="store_true",
        help="List available models"
    )
    
    parser.add_argument(
        "--tools",
        action="store_true",
        help="List available tools"
    )
    
    args = parser.parse_args(argv)
    
    # Handle version first
    if args.version:
        show_version()
        return 0
    
    # Run async commands
    try:
        if args.setup:
            return asyncio.run(run_setup())
        elif args.config:
            return asyncio.run(run_config_command())
        elif args.models:
            return asyncio.run(run_models_command())
        elif args.tools:
            return asyncio.run(run_tools_command())
        else:
            return asyncio.run(run_chat(args.message))
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[dim]Interrupted.[/dim]")
        return 0


if __name__ == "__main__":
    sys.exit(main())
