#!/usr/bin/env python3
"""Quick NVIDIA NIM setup for LAXCODE"""

import json
import os
from pathlib import Path


def quick_setup():
    """Quick setup for NVIDIA NIM"""
    print("=" * 50)
    print("LAXCODE Quick Setup - NVIDIA NIM")
    print("=" * 50)
    print()
    
    # Get API key
    api_key = input("Enter your NVIDIA NIM API key: ").strip()
    
    if not api_key:
        print("Error: No API key provided")
        return False
    
    # Create config directory
    config_dir = Path.home() / ".laxcode"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create config
    config = {
        "provider": "nvidia",
        "model": "llama-3.1-8b",
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 0.95,
        "timeout": 120,
        "animations_enabled": True,
        "show_tokens": True,
        "auto_save": True,
        "theme": "dark",
    }
    
    # Save config
    config_file = config_dir / "config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    # Save API key to file (in a real app, use environment variables instead)
    key_file = config_dir / "api_key.txt"
    with open(key_file, 'w', encoding='utf-8') as f:
        f.write(api_key)
    
    # Also set environment variable for current session
    os.environ["NVIDIA_API_KEY"] = api_key
    
    print()
    print("=" * 50)
    print("Setup Complete!")
    print("=" * 50)
    print()
    print(f"Config saved to: {config_file}")
    print(f"API key saved to: {key_file}")
    print()
    print("To set the API key permanently, run:")
    print(f'  setx NVIDIA_API_KEY "{api_key}"')
    print()
    print("Now you can run: laxcode")
    
    return True


if __name__ == "__main__":
    quick_setup()
