"""Configuration manager for LAXCODE"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text


DEFAULT_CONFIG = {
    "provider": "nvidia",
    "model": "llama-3.1-8b",
    "temperature": 0.7,
    "max_tokens": 4096,
    "top_p": 0.95,
    "timeout": 120,
    "api_keys": {},
    "aliases": {
        "nvidia": "NVIDIA NIM",
        "openai": "OpenAI",
        "anthropic": "Anthropic Claude",
    },
    "theme": "dark",
    "animations_enabled": True,
    "show_tokens": True,
    "auto_save": True,
    "workspace": str(Path.cwd()),
}


@dataclass
class LaxcodeConfig:
    """LAXCODE configuration"""
    provider: str = "nvidia"
    model: str = "llama-3.1-8b"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.95
    timeout: float = 120.0
    api_keys: Dict[str, str] = field(default_factory=dict)
    aliases: Dict[str, str] = field(default_factory=lambda: DEFAULT_CONFIG["aliases"])
    theme: str = "dark"
    animations_enabled: bool = True
    show_tokens: bool = True
    auto_save: bool = True
    workspace: str = field(default_factory=lambda: str(Path.cwd()))
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LaxcodeConfig":
        # Filter to only valid fields
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


class ConfigManager:
    """Manages LAXCODE configuration"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".laxcode"
        self.config_file = self.config_dir / "config.json"
        self.config = LaxcodeConfig()
        self.console = Console()
        
    def load(self) -> LaxcodeConfig:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.config = LaxcodeConfig.from_dict(data)
                
                # Also load from environment variables
                self._load_from_env()
                
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not load config: {e}[/yellow]")
                self.config = LaxcodeConfig()
        else:
            self._load_from_env()
        
        return self.config
    
    def _load_from_env(self) -> None:
        """Load API keys from environment variables"""
        # NVIDIA NIM
        nvidia_key = os.getenv("NVIDIA_API_KEY")
        if nvidia_key:
            self.config.api_keys["nvidia"] = nvidia_key
        
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.config.api_keys["openai"] = openai_key
        
        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.config.api_keys["anthropic"] = anthropic_key
    
    def save(self) -> None:
        """Save configuration to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Don't save API keys to file for security
        config_dict = self.config.to_dict()
        config_dict.pop("api_keys", None)
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2)
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider"""
        # Check config first
        key = self.config.api_keys.get(provider)
        if key:
            return key
        
        # Check environment
        env_vars = {
            "nvidia": "NVIDIA_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }
        
        env_var = env_vars.get(provider)
        if env_var:
            env_key = os.getenv(env_var)
            if env_key:
                return env_key
        
        # Check saved key file (for non-environment setup)
        key_file = self.config_dir / f"{provider}_key.txt"
        if key_file.exists():
            try:
                with open(key_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception:
                pass
        
        return None
    
    def set_api_key(self, provider: str, key: str) -> None:
        """Set API key for a provider"""
        self.config.api_keys[provider] = key
    
    def setup_wizard(self) -> bool:
        """Interactive setup wizard"""
        self.console.print(Panel(
            Text("Welcome to LAXCODE Setup", justify="center"),
            style="bold cyan"
        ))
        
        self.console.print("\n[bold]Let's configure your API keys and preferences.[/bold]\n")
        
        # Provider selection
        self.console.print("[bold]Step 1: Choose your AI Provider[/bold]")
        self.console.print("""
1. NVIDIA NIM (Free models, recommended) - https://build.nvidia.com/explore
2. OpenAI (Requires paid API key) - https://platform.openai.com
3. Anthropic Claude (Requires paid API key) - https://console.anthropic.com
""")
        
        choice = Prompt.ask(
            "Select provider",
            choices=["1", "2", "3"],
            default="1"
        )
        
        providers = {
            "1": ("nvidia", "NVIDIA_API_KEY", "https://build.nvidia.com/explore"),
            "2": ("openai", "OPENAI_API_KEY", "https://platform.openai.com"),
            "3": ("anthropic", "ANTHROPIC_API_KEY", "https://console.anthropic.com"),
        }
        
        provider, env_var, url = providers[choice]
        self.config.provider = provider
        
        self.console.print(f"\n[bold]Step 2: API Key Configuration[/bold]")
        self.console.print(f"Provider: [cyan]{provider.upper()}[/cyan]")
        self.console.print(f"Get your API key from: [blue]{url}[/blue]\n")
        
        # Check if key exists in environment
        existing_key = os.getenv(env_var)
        if existing_key:
            self.console.print(f"[green][OK] Found {env_var} in environment variables[/green]")
            use_existing = Confirm.ask("Use existing API key from environment?", default=True)
            if use_existing:
                self.config.api_keys[provider] = existing_key
            else:
                existing_key = None
        
        if not existing_key:
            api_key = Prompt.ask(f"Enter your {provider.upper()} API key", password=True)
            if api_key:
                self.config.api_keys[provider] = api_key
                # Save key to file for persistence
                key_file = self.config_dir / f"{provider}_key.txt"
                self.config_dir.mkdir(parents=True, exist_ok=True)
                with open(key_file, 'w', encoding='utf-8') as f:
                    f.write(api_key)
                self.console.print("[green][OK] API key configured[/green]")
            else:
                self.console.print("[yellow][WARN] No API key provided. You can set it later.[/yellow]")
        
        # Model selection for NVIDIA
        if provider == "nvidia":
            self.console.print("\n[bold]Step 3: Select Model[/bold]")
            self.console.print("""
Available models:
1. llama-3.1-8b (Fast, efficient) [Recommended]
2. llama-3.1-70b (High quality)
3. llama-3.1-405b (Best quality, slower)
4. nemotron-4-340b (NVIDIA's model)
5. phi-3-medium (Fast, capable)
6. mistral-7b (Efficient)
7. mixtral-8x7b (MoE architecture)
8. gemma-2-9b (Lightweight)
""")
            
            model_choice = Prompt.ask(
                "Select model",
                choices=["1", "2", "3", "4", "5", "6", "7", "8"],
                default="1"
            )
            
            models = {
                "1": "llama-3.1-8b",
                "2": "llama-3.1-70b",
                "3": "llama-3.1-405b",
                "4": "nemotron-4-340b",
                "5": "phi-3-medium",
                "6": "mistral-7b",
                "7": "mixtral-8x7b",
                "8": "gemma-2-9b",
            }
            
            self.config.model = models[model_choice]
        
        # Additional preferences
        self.console.print("\n[bold]Step 4: Preferences[/bold]")
        
        self.config.animations_enabled = Confirm.ask(
            "Enable Laxmana AI animations?",
            default=True
        )
        
        self.config.show_tokens = Confirm.ask(
            "Show token usage in responses?",
            default=True
        )
        
        # Save configuration
        self.save()
        
        self.console.print("\n" + "=" * 50)
        self.console.print("[bold green][OK] LAXCODE Configuration Complete![/bold green]")
        self.console.print("=" * 50)
        self.console.print(f"\nProvider: [cyan]{provider.upper()}[/cyan]")
        self.console.print(f"Model: [cyan]{self.config.model}[/cyan]")
        self.console.print(f"Animations: [cyan]{'Enabled' if self.config.animations_enabled else 'Disabled'}[/cyan]")
        self.console.print(f"\nConfig saved to: [dim]{self.config_file}[/dim]")
        
        return True
    
    def show_config(self) -> None:
        """Display current configuration"""
        self.console.print(Panel(
            Text("LAXCODE Configuration", justify="center"),
            style="bold cyan"
        ))
        
        lines = [
            f"[bold]Provider:[/bold] {self.config.provider}",
            f"[bold]Model:[/bold] {self.config.model}",
            f"[bold]Temperature:[/bold] {self.config.temperature}",
            f"[bold]Max Tokens:[/bold] {self.config.max_tokens:,}",
            f"[bold]Top P:[/bold] {self.config.top_p}",
            f"[bold]Timeout:[/bold] {self.config.timeout}s",
            f"[bold]Animations:[/bold] {'Enabled' if self.config.animations_enabled else 'Disabled'}",
            f"[bold]Show Tokens:[/bold] {'Yes' if self.config.show_tokens else 'No'}",
            f"[bold]Config File:[/bold] {self.config_file}",
            "",
            "[bold]API Keys:[/bold]",
        ]
        
        for provider in ["nvidia", "openai", "anthropic"]:
            has_key = self.get_api_key(provider) is not None
            key_status = "[Set]" if has_key else "[Not set]"
            color = "green" if has_key else "red"
            lines.append(f"  {provider}: [{color}]{key_status}[/{color}]")
        
        self.console.print("\n".join(lines))
    
    def get_provider_config(self) -> Dict[str, Any]:
        """Get configuration for current provider"""
        return {
            "api_key": self.get_api_key(self.config.provider),
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "timeout": self.config.timeout,
        }


# Global config manager instance
_config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """Get the global config manager"""
    return _config_manager
