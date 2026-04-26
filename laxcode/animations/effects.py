"""Animation effects for Laxmana AI"""

from __future__ import annotations

import asyncio
import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from rich.text import Text
from rich.console import Console


@dataclass
class ParticleEffect:
    """A particle effect"""
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    char: str
    color: str
    size: int = 1
    
    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
    
    @property
    def is_alive(self) -> bool:
        return self.life > 0
    
    def get_color_intensity(self) -> str:
        intensity = max(0.2, self.life / self.max_life)
        return f"[{self.color}]"


class ParticleSystem:
    """System for managing particles"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.particles: List[ParticleEffect] = []
        self.width = 25
        self.height = 12
    
    def spawn_burst(self, x: float, y: float, count: int = 10, color: str = "yellow") -> None:
        """Spawn a burst of particles"""
        for _ in range(count):
            angle = random.random() * 2 * math.pi
            speed = random.uniform(0.5, 2.0)
            self.particles.append(ParticleEffect(
                x=x,
                y=y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=random.uniform(0.5, 1.5),
                max_life=1.5,
                char=random.choice(["✦", "✧", "★", "☆", "•", "·", "∘"]),
                color=color,
                size=1
            ))
    
    def spawn_trail(self, x: float, y: float, color: str = "cyan") -> None:
        """Spawn a trail particle"""
        self.particles.append(ParticleEffect(
            x=x,
            y=y,
            vx=random.uniform(-0.1, 0.1),
            vy=random.uniform(-0.2, 0.2),
            life=1.0,
            max_life=1.0,
            char=random.choice(["·", "∘", "."]),
            color=color,
            size=1
        ))
    
    def update(self, dt: float) -> None:
        """Update all particles"""
        for p in self.particles:
            p.update(dt)
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.is_alive]
    
    def render(self) -> Text:
        """Render particles to text"""
        # Create grid
        grid = [[" " for _ in range(self.width)] for _ in range(self.height)]
        
        # Place particles
        for p in self.particles:
            px = int(p.x + self.width / 2)
            py = int(p.y + self.height / 2)
            
            if 0 <= px < self.width and 0 <= py < self.height:
                intensity = p.life / p.max_life
                if intensity > 0.5:
                    grid[py][px] = f"[bold {p.color}]{p.char}[/]"
                else:
                    grid[py][px] = f"[dim {p.color}]{p.char}[/]"
        
        # Build text
        lines = ["".join(row) for row in grid]
        return Text.from_markup("\n".join(lines))


class EnergySparks:
    """Energy spark effects for processing mode"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.sparks: List[ParticleEffect] = []
        self.time = 0.0
    
    def update(self, dt: float, intensity: float = 1.0) -> None:
        """Update sparks"""
        self.time += dt
        
        # Update existing sparks
        for s in self.sparks:
            s.update(dt)
            # Add upward drift
            s.vy -= 0.1 * dt
        
        # Remove dead sparks
        self.sparks = [s for s in self.sparks if s.is_alive]
        
        # Spawn new sparks based on intensity
        spawn_chance = 0.3 * intensity
        if random.random() < spawn_chance and len(self.sparks) < 15:
            self.sparks.append(ParticleEffect(
                x=random.uniform(-3, 3),
                y=random.uniform(-1, 1),
                vx=random.uniform(-1, 1),
                vy=random.uniform(0.5, 2.0),
                life=random.uniform(0.3, 0.8),
                max_life=0.8,
                char=random.choice(["✦", "✧", "⚡", "↑"]),
                color=random.choice(["bright_magenta", "bright_purple", "bright_cyan"])
            ))
    
    def render(self) -> Text:
        """Render sparks"""
        lines = []
        
        for s in self.sparks:
            intensity = s.life / s.max_life
            x = int(s.x + 12)
            y = int(s.y + 6)
            
            if 0 <= x < 25 and 0 <= y < 12:
                if intensity > 0.7:
                    lines.append(f"[bold {s.color}]{s.char}[/]")
                else:
                    lines.append(f"[{s.color}]{s.char}[/]")
        
        return Text.from_markup(" ".join(lines) if lines else "")


class WaveformEffect:
    """Audio waveform effect for working mode"""
    
    def __init__(self, width: int = 25):
        self.width = width
        self.time = 0.0
        self.amplitude = 1.0
        self.frequency = 2.0
    
    def update(self, dt: float, amplitude: float = 1.0) -> None:
        """Update waveform"""
        self.time += dt * 5
        self.amplitude = amplitude
    
    def render(self) -> Text:
        """Render waveform as bars"""
        bars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▂"]
        
        result = []
        for i in range(self.width):
            # Calculate wave height
            phase = (i / self.width) * 2 * math.pi * self.frequency + self.time
            wave = math.sin(phase) * self.amplitude
            
            # Map to bar index
            bar_idx = int((wave + 1) / 2 * (len(bars) - 1))
            bar_idx = max(0, min(len(bars) - 1, bar_idx))
            
            # Color based on amplitude
            if self.amplitude > 0.7:
                result.append(f"[bright_cyan]{bars[bar_idx]}[/]")
            elif self.amplitude > 0.3:
                result.append(f"[cyan]{bars[bar_idx]}[/]")
            else:
                result.append(f"[dim cyan]{bars[bar_idx]}[/]")
        
        return Text.from_markup("".join(result))


class BreathingEffect:
    """Breathing/pulsing effect for the core"""
    
    def __init__(self):
        self.time = 0.0
        self.phase = 0.0
        self.speed = 1.0
    
    def update(self, dt: float, speed: float = 1.0) -> None:
        """Update breathing"""
        self.speed = speed
        self.time += dt * speed * 2
        self.phase = math.sin(self.time) * 0.5 + 0.5
    
    def get_scale(self) -> float:
        """Get current scale based on breathing"""
        return 1.0 + self.phase * 0.1
    
    def get_intensity(self) -> float:
        """Get current intensity"""
        return self.phase
    
    def render_indicator(self, color: str = "yellow") -> Text:
        """Render a breathing indicator"""
        intensity = self.phase
        filled = int(intensity * 10)
        bar = "█" * filled + "░" * (10 - filled)
        return Text.from_markup(f"[{color}]{bar}[/{color}]")


class ConnectionLines:
    """Neural network connection lines effect"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.points: List[Tuple[float, float]] = []
        self.time = 0.0
    
    def update(self, dt: float) -> None:
        """Update connections"""
        self.time += dt
        
        # Update points
        for i, (x, y) in enumerate(self.points):
            # Gentle floating motion
            new_x = x + math.sin(self.time + i) * 0.01
            new_y = y + math.cos(self.time + i * 0.5) * 0.01
            self.points[i] = (new_x, new_y)
        
        # Ensure minimum points
        while len(self.points) < 8:
            self.points.append((
                random.uniform(-10, 10),
                random.uniform(-5, 5)
            ))
    
    def render(self) -> Text:
        """Render connection lines"""
        lines = []
        
        # Draw connections between nearby points
        for i, (x1, y1) in enumerate(self.points):
            for j, (x2, y2) in enumerate(self.points[i+1:], i+1):
                dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                
                if dist < 8:
                    intensity = 1 - (dist / 8)
                    if intensity > 0.3:
                        lines.append(f"[dim cyan]{'─' if abs(y2-y1) < 1 else '│'}[/]")
        
        return Text.from_markup(" ".join(lines) if lines else "")


class GlowEffect:
    """Ambient glow effect"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.pulse = 0.0
        self.time = 0.0
    
    def update(self, dt: float, intensity: float = 1.0) -> None:
        """Update glow"""
        self.time += dt * 2
        self.pulse = (math.sin(self.time) * 0.5 + 0.5) * intensity
    
    def render(self, width: int = 25, color: str = "yellow") -> Text:
        """Render glow effect"""
        # Create radial gradient
        center_x = width // 2
        chars = ["█", "▓", "▒", "░", " "]
        
        result = []
        for i in range(width):
            dist = abs(i - center_x) / (width / 2)
            if dist < 1:
                char_idx = int(dist * (len(chars) - 1))
                char_idx = min(len(chars) - 1, char_idx)
                alpha = int(self.pulse * 255)
                result.append(f"[dim {color}]{chars[char_idx]}[/]")
            else:
                result.append(" ")
        
        return Text.from_markup("".join(result))


class TypingEffect:
    """Typing animation effect"""
    
    def __init__(self, text: str = "", speed: float = 0.05):
        self.full_text = text
        self.current_text = ""
        self.speed = speed
        self.time = 0.0
        self.complete = False
    
    def set_text(self, text: str) -> None:
        """Set new text to type"""
        self.full_text = text
        self.current_text = ""
        self.time = 0.0
        self.complete = False
    
    def update(self, dt: float) -> None:
        """Update typing"""
        self.time += dt
        
        chars_to_add = int(self.time / self.speed)
        if chars_to_add > len(self.current_text):
            self.current_text = self.full_text[:chars_to_add]
        
        if self.current_text == self.full_text:
            self.complete = True
    
    def get_display_text(self) -> str:
        """Get current display text with cursor"""
        if self.complete:
            return self.current_text
        else:
            return self.current_text + "│"


class StatusIndicator:
    """Status text indicator with animation"""
    
    def __init__(self):
        self.status = "Ready"
        self.dots = 0
        self.time = 0.0
    
    def set_status(self, status: str) -> None:
        """Set status text"""
        self.status = status
        self.dots = 0
        self.time = 0.0
    
    def update(self, dt: float) -> None:
        """Update animation"""
        self.time += dt
        if self.time > 0.5:
            self.time = 0
            self.dots = (self.dots + 1) % 4
    
    def render(self) -> Text:
        """Render status with animated dots"""
        dots_str = "." * self.dots
        return Text.from_markup(f"[dim]{self.status}{dots_str}[/]")


class AnimationComposer:
    """Compose multiple animations together"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.particles = ParticleSystem(console)
        self.sparks = EnergySparks(console)
        self.waveform = WaveformEffect()
        self.breathing = BreathingEffect()
        self.connections = ConnectionLines(console)
        self.glow = GlowEffect(console)
        self.status = StatusIndicator()
    
    def update(self, dt: float, mode: str = "idle") -> None:
        """Update all animations"""
        self.breathing.update(dt)
        self.particles.update(dt)
        self.connections.update(dt)
        self.status.update(dt)
        
        if mode in ("processing", "working"):
            self.sparks.update(dt, intensity=1.5 if mode == "working" else 1.0)
            self.waveform.update(dt, amplitude=0.8 if mode == "working" else 0.5)
            self.glow.update(dt, intensity=0.8)
        else:
            self.glow.update(dt, intensity=0.4)
    
    def render_frame(self, mode: str = "idle", color: str = "yellow") -> Text:
        """Render composed frame"""
        lines = []
        
        # Status line
        lines.append(self.status.render())
        lines.append("")
        
        # Breathing indicator
        lines.append(self.breathing.render_indicator(color))
        lines.append("")
        
        # Glow effect
        if mode in ("processing", "working"):
            lines.append(self.glow.render(color="cyan" if mode == "working" else "magenta"))
        
        # Waveform for working mode
        if mode == "working":
            lines.append(self.waveform.render())
            lines.append("")
        
        # Particles
        if mode in ("processing", "working"):
            lines.append(self.sparks.render())
            lines.append(self.connections.render())
        
        return Text.assemble(*lines)
