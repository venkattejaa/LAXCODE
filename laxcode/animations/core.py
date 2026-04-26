"""Core animation engine for Laxmana AI - Terminal-based animations"""

from __future__ import annotations

import asyncio
import math
import random
import time
from dataclasses import dataclass, field
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
    
    @property
    def primary_hex(self) -> str:
        return f"#{self.primary[0]:02x}{self.primary[1]:02x}{self.primary[2]:02x}"
    
    @property
    def secondary_hex(self) -> str:
        return f"#{self.secondary[0]:02x}{self.secondary[1]:02x}{self.secondary[2]:02x}"
    
    @property
    def accent_hex(self) -> str:
        return f"#{self.accent[0]:02x}{self.accent[1]:02x}{self.accent[2]:02x}"


THEMES = {
    AnimationMode.IDLE: Theme(
        primary=(251, 191, 36),      # Gold
        secondary=(255, 215, 100),
        accent=(252, 211, 77),
        glow="bright_yellow",
        symbol="◉"
    ),
    AnimationMode.LISTENING: Theme(
        primary=(16, 185, 129),      # Emerald
        secondary=(52, 211, 153),
        accent=(110, 231, 183),
        glow="bright_green",
        symbol="◉"
    ),
    AnimationMode.PROCESSING: Theme(
        primary=(168, 85, 247),      # Purple
        secondary=(192, 132, 252),
        accent=(216, 180, 254),
        glow="bright_magenta",
        symbol="◈"
    ),
    AnimationMode.WORKING: Theme(
        primary=(56, 189, 248),      # Cyan
        secondary=(125, 211, 252),
        accent=(186, 230, 253),
        glow="bright_cyan",
        symbol="◈"
    ),
    AnimationMode.ERROR: Theme(
        primary=(239, 68, 68),       # Red
        secondary=(248, 113, 113),
        accent=(252, 165, 165),
        glow="bright_red",
        symbol="✖"
    ),
    AnimationMode.SUCCESS: Theme(
        primary=(34, 197, 94),       # Green
        secondary=(74, 222, 128),
        accent=(134, 239, 172),
        glow="bright_green",
        symbol="✓"
    ),
}


@dataclass
class Particle:
    """A single particle in the animation"""
    x: float
    y: float
    vx: float
    vy: float
    life: float = 1.0
    max_life: float = 1.0
    size: int = 1
    char: str = "•"
    
    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt / self.max_life
    
    @property
    def is_alive(self) -> bool:
        return self.life > 0


@dataclass
class EyeState:
    """Animated eye state"""
    x_offset: float = 0.0
    y_offset: float = 0.0
    squint: float = 1.0
    blink_timer: float = 0.0
    is_blinking: bool = False
    
    def update(self, dt: float, mode: AnimationMode) -> None:
        # Random blinking
        if not self.is_blinking and random.random() < 0.01:
            self.is_blinking = True
            self.blink_timer = 0.15
        
        if self.is_blinking:
            self.blink_timer -= dt
            if self.blink_timer <= 0:
                self.is_blinking = False
        
        # Mode-based squint
        target_squint = 4.0 if mode == AnimationMode.IDLE else 6.0
        if mode == AnimationMode.ERROR:
            target_squint = 2.0
        self.squint += (target_squint - self.squint) * dt * 5


class LaxmanaAnimator:
    """
    Laxmana AI Animation Engine for Terminal
    Converts HTML Canvas animations to Rich terminal output
    """
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.mode = AnimationMode.IDLE
        self._current_theme = THEMES[self.mode]
        self._time = 0.0
        self._breath_scale = 1.0
        self._hover_scale = 0.0
        self._particles: List[Particle] = []
        self._sparks: List[Particle] = []
        self._eye_state = EyeState()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._live: Optional[Live] = None
        self._status_text = "Ready"
        self._progress = 0.0
        
    def set_mode(self, mode: AnimationMode, status_text: str = "") -> None:
        """Change animation mode"""
        if mode != self.mode:
            self.mode = mode
            self._current_theme = THEMES[mode]
            # Trigger shockwave effect on mode change
            self._add_shockwave()
        if status_text:
            self._status_text = status_text
    
    def set_progress(self, progress: float) -> None:
        """Set progress (0.0 to 1.0)"""
        self._progress = max(0.0, min(1.0, progress))
    
    def _add_shockwave(self) -> None:
        """Add shockwave particles on mode change"""
        for _ in range(12):
            angle = random.random() * 2 * math.pi
            speed = random.uniform(0.5, 1.5)
            self._particles.append(Particle(
                x=0, y=0,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=1.0,
                max_life=0.5,
                size=2,
                char=self._current_theme.symbol
            ))
    
    def _update_particles(self, dt: float) -> None:
        """Update particle system"""
        # Update existing particles
        for p in self._particles:
            p.update(dt)
        self._particles = [p for p in self._particles if p.is_alive]
        
        # Spawn new ambient particles
        if len(self._particles) < 20 and random.random() < 0.1:
            angle = random.random() * 2 * math.pi
            self._particles.append(Particle(
                x=0, y=0,
                vx=math.cos(angle) * random.uniform(0.1, 0.3),
                vy=math.sin(angle) * random.uniform(0.1, 0.3),
                life=1.0,
                max_life=random.uniform(2.0, 4.0),
                char=random.choice(["•", "·", "∘"])
            ))
        
        # Update sparks for processing/working modes
        if self.mode in (AnimationMode.PROCESSING, AnimationMode.WORKING):
            for s in self._sparks:
                s.update(dt)
            self._sparks = [s for s in self._sparks if s.is_alive]
            
            if len(self._sparks) < 8 and random.random() < 0.2:
                angle = random.random() * 2 * math.pi
                self._sparks.append(Particle(
                    x=random.uniform(-3, 3), y=random.uniform(-1, 1),
                    vx=math.cos(angle) * random.uniform(0.2, 0.8),
                    vy=math.sin(angle) * random.uniform(0.2, 0.8) - 0.1,
                    life=1.0,
                    max_life=random.uniform(0.5, 1.0),
                    char=random.choice(["✦", "✧", "★", "☆"])
                ))
    
    def _render_core(self) -> Text:
        """Render the Laxmana AI core with eyes"""
        theme = self._current_theme
        
        # Breathing animation
        breath = 1.0 + math.sin(self._time * 2) * 0.1
        scale = int(10 * breath * self._breath_scale)
        
        # Create core visualization
        lines = []
        
        # Build the core with gradient effect
        for row in range(-4, 5):
            line = ""
            for col in range(-8, 9):
                dist = math.sqrt(col**2 + row**2)
                
                # Core blob shape with noise
                noise = math.sin(col * 0.5 + self._time * 3) * 0.3 + \
                       math.cos(row * 0.7 - self._time * 2) * 0.3
                threshold = 4 + noise
                
                if dist < threshold:
                    # Inside the blob
                    intensity = 1 - (dist / threshold)
                    if intensity > 0.7:
                        line += f"[{theme.glow}]█[/{theme.glow}]"
                    elif intensity > 0.4:
                        line += f"[{theme.glow}]▓[/{theme.glow}]"
                    elif intensity > 0.2:
                        line += f"[{theme.secondary_hex}]▒[/]"
                    else:
                        line += f"[{theme.accent_hex}]░[/]"
                elif dist < threshold + 1.5:
                    # Glow area
                    line += f"[{theme.accent_hex}]{theme.symbol}[/]"
                else:
                    line += " "
            
            lines.append(line)
        
        # Add eyes to the core
        if not self._eye_state.is_blinking:
            eye_y = 4
            eye_open = "◉"
            eye_closed = "─"
            
            # Calculate eye positions with slight movement
            left_eye_x = 8 + int(self._eye_state.x_offset)
            right_eye_x = 12 + int(self._eye_state.x_offset)
            eye_y_pos = eye_y + int(self._eye_state.y_offset)
            
            if 0 <= eye_y_pos < len(lines):
                line_list = list(lines[eye_y_pos])
                eye_char = eye_open if self._eye_state.squint > 3 else eye_closed
                
                if left_eye_x < len(line_list):
                    line_list[left_eye_x] = f"[bold white]{eye_char}[/]"
                if right_eye_x < len(line_list):
                    line_list[right_eye_x] = f"[bold white]{eye_char}[/]"
                lines[eye_y_pos] = "".join(line_list)
        
        return Text.from_markup("\n".join(lines))
    
    def _render_particles(self) -> Text:
        """Render particle effects"""
        theme = self._current_theme
        grid = [[" " for _ in range(25)] for _ in range(12)]
        
        for p in self._particles:
            x = int(12 + p.x * 8)
            y = int(6 + p.y * 4)
            if 0 <= x < 25 and 0 <= y < 12:
                alpha = int(p.life * 255)
                grid[y][x] = p.char
        
        for s in self._sparks:
            x = int(12 + s.x * 4)
            y = int(6 + s.y * 2)
            if 0 <= x < 25 and 0 <= y < 12:
                grid[y][x] = f"[bold {theme.glow}]{s.char}[/]"
        
        lines = ["".join(row) for row in grid]
        return Text.from_markup("\n".join(lines))
    
    def _render_waveform(self) -> Text:
        """Render audio waveform effect for working mode"""
        if self.mode != AnimationMode.WORKING:
            return Text("")
        
        theme = self._current_theme
        width = 25
        height = 3
        
        lines = []
        for row in range(height):
            line = ""
            for col in range(width):
                # Waveform pattern
                wave = math.sin(col * 0.5 + self._time * 8) * \
                       math.cos(self._time * 3) * self._progress
                
                if abs(wave - (row - height/2)) < 0.5:
                    line += f"[{theme.glow}]█[/]"
                else:
                    line += " "
            lines.append(line)
        
        return Text.from_markup("\n".join(lines))
    
    def _render_frame(self) -> Panel:
        """Render complete animation frame"""
        # Update time
        self._time += 0.05
        
        # Update animation state
        dt = 0.016  # ~60fps
        self._update_particles(dt)
        self._eye_state.update(dt, self.mode)
        
        # Build the frame
        core = self._render_core()
        particles = self._render_particles()
        waveform = self._render_waveform()
        
        # Combine layers
        content = Text()
        content.append(f"\n[bold {self._current_theme.glow}]LAXMANA AI[/]\n", style="bold")
        content.append(f"[dim]{self._status_text}[/]\n\n")
        
        # Progress bar for working mode
        if self.mode == AnimationMode.WORKING and self._progress > 0:
            bar_width = 20
            filled = int(bar_width * self._progress)
            bar = "█" * filled + "░" * (bar_width - filled)
            content.append(f"[{self._current_theme.glow}]{bar}[/] {int(self._progress*100)}%\n\n")
        
        content.append(core)
        content.append("\n")
        content.append(waveform)
        
        # Mode indicator
        mode_colors = {
            AnimationMode.IDLE: "dim",
            AnimationMode.LISTENING: "green",
            AnimationMode.PROCESSING: "magenta",
            AnimationMode.WORKING: "cyan",
            AnimationMode.ERROR: "red",
            AnimationMode.SUCCESS: "green"
        }
        
        content.append(f"\n[{mode_colors[self.mode]}]● {self.mode.value.upper()}[/]")
        
        return Panel(
            Align.center(content),
            border_style=self._current_theme.glow,
            padding=(1, 2)
        )
    
    async def animate(self) -> None:
        """Run animation loop"""
        self._running = True
        
        with Live(
            self._render_frame(),
            console=self.console,
            refresh_per_second=30,
            screen=False
        ) as live:
            while self._running:
                live.update(self._render_frame())
                await asyncio.sleep(0.033)  # ~30fps
    
    def start(self) -> None:
        """Start animation in background"""
        if self._task is None:
            self._running = True
            loop = asyncio.get_event_loop()
            self._task = loop.create_task(self.animate())
    
    def stop(self) -> None:
        """Stop animation"""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
    
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
            AnimationMode.IDLE: "◐◓◑◒",
            AnimationMode.PROCESSING: "◈◉◈◉",
            AnimationMode.WORKING: "▁▂▃▄▅▆▇█▇▆▅▄▃▂",
            AnimationMode.ERROR: "✖✗✖✗",
            AnimationMode.SUCCESS: "✓✓✓✓"
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
        return f"[{theme.glow}]{frame}[/]"
