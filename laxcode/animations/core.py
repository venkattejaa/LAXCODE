"""Core animation engine for Laxmana AI - Terminal-based animations"""

from __future__ import annotations

import asyncio
import math
import random
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, List, Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.style import Style


class AnimationMode(Enum):
    """Animation modes matching the HTML version"""
    IDLE = "idle"           # Gold - waiting for input
    LISTENING = "listening" # Green - ready to receive
    PROCESSING = "processing" # Purple - thinking/working
    WORKING = "working"     # Cyan - generating code
    ERROR = "error"         # Red - error state
    SUCCESS = "success"     # Green pulse - completed


@dataclass
class Theme:
    """Color theme for animations"""
    primary: tuple[int, int, int]  # RGB
    secondary: tuple[int, int, int]
    accent: tuple[int, int, int]
    glow: str
    symbol: str


THEMES = {
    AnimationMode.IDLE: Theme(
        primary=(251, 191, 36),      # Gold
        secondary=(255, 215, 100),
        accent=(252, 211, 77),
        glow="bright_yellow",
        symbol="*"
    ),
    AnimationMode.LISTENING: Theme(
        primary=(16, 185, 129),      # Emerald
        secondary=(52, 211, 153),
        accent=(110, 231, 183),
        glow="bright_green",
        symbol="*"
    ),
    AnimationMode.PROCESSING: Theme(
        primary=(168, 85, 247),      # Purple
        secondary=(192, 132, 252),
        accent=(216, 180, 254),
        glow="bright_magenta",
        symbol="#"
    ),
    AnimationMode.WORKING: Theme(
        primary=(56, 189, 248),      # Cyan
        secondary=(125, 211, 252),
        accent=(186, 230, 253),
        glow="bright_cyan",
        symbol="#"
    ),
    AnimationMode.ERROR: Theme(
        primary=(239, 68, 68),       # Red
        secondary=(248, 113, 113),
        accent=(252, 165, 165),
        glow="bright_red",
        symbol="x"
    ),
    AnimationMode.SUCCESS: Theme(
        primary=(34, 197, 94),       # Green
        secondary=(74, 222, 128),
        accent=(134, 239, 172),
        glow="bright_green",
        symbol="ok"
    ),
}


class LaxmanaAnimator:
    """Laxmana AI Animation Engine for Terminal"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.mode = AnimationMode.IDLE
        self._time = 0.0
        
    def set_mode(self, mode: AnimationMode, status_text: str = "") -> None:
        """Change animation mode"""
        self.mode = mode

    def set_progress(self, progress: float) -> None:
        """Set progress (0.0 to 1.0)"""
        pass
    
    def start(self) -> None:
        """Start animation in background"""
        pass
    
    def stop(self) -> None:
        """Stop animation"""
        pass
    
    def __enter__(self) -> 'LaxmanaAnimator':
        self.start()
        return self
    
    def __exit__(self, *args) -> None:
        self.stop()


class SimpleAnimator:
    """Simplified animator for non-async contexts"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.mode = AnimationMode.IDLE
        self._spinner_chars = {
            AnimationMode.IDLE: "oO",
            AnimationMode.PROCESSING: "#*",
            AnimationMode.WORKING: "-=",
            AnimationMode.ERROR: "xx",
            AnimationMode.SUCCESS: "ok"
        }
        self._idx = 0
    
    def set_mode(self, mode: AnimationMode) -> None:
        """Set animation mode"""
        self.mode = mode
        self._idx = 0
    
    def get_frame(self) -> str:
        """Get a single animation frame"""
        chars = self._spinner_chars.get(self.mode, self._spinner_chars[AnimationMode.IDLE])
        self._idx = (self._idx + 1) % len(chars)
        return chars[self._idx]
    
    def get_colored_frame(self) -> str:
        """Get colored frame with theme"""
        theme = THEMES[self.mode]
        frame = self.get_frame()
        return f"[{theme.glow}]{frame}[/{theme.glow}]"
