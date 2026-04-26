"""Main entry point for LAXCODE"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .config.manager import ConfigManager, get_config_manager, LaxcodeConfig
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
  - NVIDIA NIM API support (Free models)
  - OpenAI API support
  - Anthropic Claude API support
  - Laxmana AI animations
  - File operations (read, edit, glob)
  - Shell command execution
  - Code search (grep)
  - Session management

[bold yellow]Version 1.2 Coming Soon![/bold yellow]
  - Enhanced animations
  - Multi-agent mode
  - Auto-refactoring

[dim]GitHub: https://github.com/venkattejaa/LAXCODE[/dim]
"""
    console.print(version_text)


def quick_setup_nvidia(api_key: str, model: str = "llama-3.1-8b") -> bool:
    """Quick setup for NVIDIA NIM without interactive prompts"""
    config_manager = get_config_manager()
    config = config_manager.config
    
    # Set provider and model
    config.provider = "nvidia"
    config.model = model
    
    # Set API key
    config_manager.config.api_keys["nvidia"] = api_key
    
    # Also set environment variable for current session
    os.environ["NVIDIA_API_KEY"] = api_key
    
    # Ensure config directory exists
    config_manager.config_dir.mkdir(parents=True, exist_ok=True)
    
    # Save config (without API keys in the JSON for security)
    config_manager.save()
    
    # Save API key to a separate file for persistence
    key_file = config_manager.config_dir / "nvidia_key.txt"
    with open(key_file, 'w', encoding='utf-8') as f:
        f.write(api_key)
    
    console = Console()
    console.print("\n[bold green]Setup Complete![/bold green]")
    console.print(f"Provider: NVIDIA NIM")
    console.print(f"Model: {model}")
    console.print(f"Config saved to: {config_manager.config_file}")
    console.print(f"\n[dim]Tip: Set environment variable for permanent storage:[/dim]")
    console.print(f'  [cyan]setx NVIDIA_API_KEY "{api_key}"[/cyan]\n')
    
    return True


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
        console.print("Or use: [cyan]laxcode --set-nvidia-key YOUR_API_KEY[/cyan]\n")
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
    # Parse arguments manually first to handle special commands
    args_list = argv if argv is not None else sys.argv[1:]
    
    # Check for special commands that don't need argparse
    if args_list:
        first_arg = args_list[0]
        
        # Handle version flags
        if first_arg in ("-v", "--version", "version"):
            show_version()
            return 0
        
        # Handle help
        if first_arg in ("-h", "--help", "help"):
            show_help()
            return 0
        
        # Handle commands that don't need API initialization
        if first_arg == "tools":
            return asyncio.run(run_tools_command())
        if first_arg == "models":
            return asyncio.run(run_models_command())
        if first_arg == "config":
            return asyncio.run(run_config_command())
        if first_arg == "setup":
            return asyncio.run(run_setup())
        
        # Handle API key setup
        if first_arg.startswith("--set-nvidia-key") or first_arg.startswith("--set-openai-key") or first_arg.startswith("--set-anthropic-key"):
            # Parse these with argparse
            pass
        else:
            # Not a special command, treat as message or use argparse
            pass
    
    # Full argparse handling
    parser = argparse.ArgumentParser(
        prog="laxcode",
        description="LAXCODE - Agentic AI Coding Assistant powered by Laxmana AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  laxcode                    Start interactive chat
  laxcode "hello world"      Send a single message
  laxcode setup              Configure API keys (interactive)
  laxcode config             Show configuration
  laxcode models             List available models
  laxcode tools              List available tools
  laxcode --version          Show version

Setup:
  laxcode --set-nvidia-key KEY    Set NVIDIA NIM API key
  laxcode --set-openai-key KEY    Set OpenAI API key
  laxcode --set-anthropic-key KEY Set Anthropic API key

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
        help="Run interactive setup wizard"
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
    
    # Non-interactive API key setup
    parser.add_argument(
        "--set-nvidia-key",
        metavar="KEY",
        help="Set NVIDIA NIM API key"
    )
    
    parser.add_argument(
        "--set-openai-key",
        metavar="KEY",
        help="Set OpenAI API key"
    )
    
    parser.add_argument(
        "--set-anthropic-key",
        metavar="KEY",
        help="Set Anthropic API key"
    )
    
    parser.add_argument(
        "--model",
        default="llama-3.1-8b",
        help="Model to use (default: llama-3.1-8b)"
    )
    
    args = parser.parse_args(argv)
    
    # Handle version first (no init required)
    if args.version:
        show_version()
        return 0
    
    # Handle non-interactive API key setup (no init required)
    if args.set_nvidia_key:
        return 0 if quick_setup_nvidia(args.set_nvidia_key, args.model) else 1
    
    if args.set_openai_key:
        config_manager = get_config_manager()
        config_manager.config.provider = "openai"
        config_manager.config.api_keys["openai"] = args.set_openai_key
        os.environ["OPENAI_API_KEY"] = args.set_openai_key
        config_manager.save()
        console = Console()
        console.print("[green]OpenAI API key configured![/green]\n")
        return 0
    
    if args.set_anthropic_key:
        config_manager = get_config_manager()
        config_manager.config.provider = "anthropic"
        config_manager.config.api_keys["anthropic"] = args.set_anthropic_key
        os.environ["ANTHROPIC_API_KEY"] = args.set_anthropic_key
        config_manager.save()
        console = Console()
        console.print("[green]Anthropic API key configured![/green]\n")
        return 0
    
    # Handle commands that don't need agent initialization
    try:
        if args.tools:
            return asyncio.run(run_tools_command())
        elif args.models:
            return asyncio.run(run_models_command())
        elif args.config:
            return asyncio.run(run_config_command())
        elif args.setup:
            return asyncio.run(run_setup())
        else:
            return asyncio.run(run_chat(args.message))
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[dim]Interrupted.[/dim]")
        return 0


def show_help() -> None:
    """Show help message"""
    help_text = """
[bold cyan]LAXCODE v1.1.0[/bold cyan] - Agentic AI Coding Assistant

[bold]Usage:[/bold]
  laxcode [message]              Start interactive chat or send message
  laxcode setup                  Configure API keys
  laxcode config                 Show current configuration
  laxcode models                 List available models
  laxcode tools                  List available tools
  laxcode --version              Show version

[bold]Setup Commands:[/bold]
  laxcode --set-nvidia-key KEY       Set NVIDIA NIM API key
  laxcode --set-openai-key KEY       Set OpenAI API key
  laxcode --set-anthropic-key KEY    Set Anthropic API key

[bold]Quick Tools (in interactive mode):[/bold]
  /help                          Show help
  /config                        Show configuration
  /sessions                      List saved sessions
  /tools                         List tools
  /models                        Show models
  /clear                         Clear screen
  /exit                          Exit LAXCODE
  /read <path>                   Read file
  /glob <pattern>                Find files
  /grep <pattern>                Search files

[bold]For more help:[/bold] https://github.com/venkattejaa/LAXCODE
"""
    console = Console()
    console.print(help_text)


if __name__ == "__main__":
    sys.exit(main())
