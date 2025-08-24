"""
Galaxy Warp waveform style - starfield warp with circular spectrum ripples.
"""
import math
import random
from typing import Dict, Any
from .base_style import BaseWaveformStyle
from .style_factory import register_style


@register_style
class GalaxyWarpStyle(BaseWaveformStyle):
    """Hyperspace starfield with reactive circular spectrum ripples."""

    def __init__(self, canvas, width: int, height: int, config: Dict[str, Any]):
        super().__init__(canvas, width, height, config)
        self._display_name = "Galaxy Warp"
        self._description = "Hyperspace starfield and audio-reactive ripples"

        # Colors / config
        self.bg_color = config.get('bg_color', '#050510')
        self.star_color = config.get('star_color', '#b0d8ff')
        self.accent = config.get('accent', '#7a5cff')
        self.accent2 = config.get('accent2', '#ff9d00')
        self.text_color = config.get('text_color', '#e8f0ff')

        self.star_count = config.get('star_count', 120)
        self.star_speed = config.get('star_speed', 1.6)
        self.star_depth = config.get('star_depth', 0.995)

        self.ring_count = config.get('ring_count', 4)
        self.ring_thickness = config.get('ring_thickness', 3)
        self.ripple_speed = config.get('ripple_speed', 1.8)
        self.ripple_gain = config.get('ripple_gain', 22.0)

        # Starfield
        self._stars = [self._spawn_star() for _ in range(self.star_count)]

    def _spawn_star(self):
        # Polar distribution for nice density
        angle = random.random() * 2 * math.pi
        radius = (random.random() ** 0.6) * max(self.width, self.height) * 0.8
        depth = random.random() * 0.7 + 0.3
        return {
            'x': self.width/2 + radius * math.cos(angle),
            'y': self.height/2 + radius * math.sin(angle),
            'z': depth,
            'tw': random.random() * 2 * math.pi
        }

    def _advance_starfield(self):
        cx, cy = self.width / 2, self.height / 2
        for s in self._stars:
            vx = (s['x'] - cx) * self.star_speed * 0.02
            vy = (s['y'] - cy) * self.star_speed * 0.02
            s['x'] += vx * (1.6 - s['z'])
            s['y'] += vy * (1.6 - s['z'])
            s['z'] *= self.star_depth
            s['tw'] += 0.2
            # Respawn if out of bounds
            if s['x'] < -50 or s['x'] > self.width + 50 or s['y'] < -50 or s['y'] > self.height + 50:
                ns = self._spawn_star()
                s.update(ns)

    def _draw_starfield(self, intensity: float):
        if not self.canvas:
            return
        # Background
        self.canvas.create_rectangle(0, 0, self.width, self.height, outline="", fill=self.bg_color)
        # Parallax stars
        for s in self._stars:
            twinkle = 0.6 + 0.4 * math.sin(s['tw'])
            r = max(1, int((1.8 - s['z']) * (1.5 + intensity * 1.5) * twinkle))
            color = self.interpolate_color(self.star_color, self.accent, 0.3 + 0.7 * (1 - s['z']))
            self.canvas.create_oval(s['x'] - r, s['y'] - r, s['x'] + r, s['y'] + r, outline="", fill=color)

    def _draw_ripples(self, message: str):
        cx, cy = self.width // 2, self.height // 2 - 6
        energy = sum(self.audio_levels) / max(1, len(self.audio_levels)) if self.audio_levels else self.current_level
        base = 12 + energy * self.ripple_gain
        for i in range(self.ring_count):
            phase = self.animation_time * self.ripple_speed + i * 0.8
            radius = base + i * 16 + 6 * math.sin(phase)
            fade = max(0.0, 1.0 - i * 0.22)
            color = self.interpolate_color(self.accent, self.accent2, (math.sin(phase*0.9)*0.5+0.5))
            color = self.interpolate_color(color, self.bg_color, 0.4)
            self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                     outline=color, width=self.ring_thickness)
        self.draw_text(message, self.width // 2, self.height - 12, self.text_color)

    def draw_recording_state(self, message: str = "Recording..."):
        if not self.canvas:
            return
        self.clear_canvas()
        self._advance_starfield()
        self._draw_starfield(self.current_level)
        self._draw_ripples(message)

    def draw_processing_state(self, message: str = "Processing..."):
        if not self.canvas:
            return
        self.clear_canvas()
        # Slow warp plus concentric loading arcs
        self._advance_starfield()
        self._draw_starfield(0.2)
        cx, cy = self.width // 2, self.height // 2 - 4
        for i in range(5):
            a1 = (self.animation_time * 120 + i * 40) % 360
            a2 = a1 + 140
            radius = 14 + i * 12
            color = self.interpolate_color(self.accent, self.bg_color, 0.5 + i*0.08)
            self.canvas.create_arc(cx - radius, cy - radius, cx + radius, cy + radius,
                                   start=a1, extent=a2 - a1, outline=color, width=3, style='arc')
        self.draw_text(message, self.width // 2, self.height - 12, self.text_color)

    def draw_transcribing_state(self, message: str = "Transcribing..."):
        if not self.canvas:
            return
        self.clear_canvas()
        # Spiral path tracing
        self._advance_starfield()
        self._draw_starfield(0.35)
        cx, cy = self.width // 2, self.height // 2 - 4
        pts = []
        turns = 2.5
        steps = 220
        for k in range(steps):
            t = k / steps * turns * 2 * math.pi + self.animation_time * 1.4
            r = 8 + 0.4 * k
            x = cx + r * math.cos(t)
            y = cy + r * math.sin(t)
            pts.extend([x, y])
        color = self.interpolate_color(self.accent, self.accent2, (math.sin(self.animation_time*2)*0.5+0.5))
        self.canvas.create_line(pts, fill=color, width=2, smooth=True)
        self.draw_text(message, self.width // 2, self.height - 12, self.text_color)

    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        return {
            'bg_color': '#050510',
            'star_color': '#b0d8ff',
            'accent': '#7a5cff',
            'accent2': '#ff9d00',
            'text_color': '#e8f0ff',
            'star_count': 120,
            'star_speed': 1.6,
            'star_depth': 0.995,
            'ring_count': 4,
            'ring_thickness': 3,
            'ripple_speed': 1.8,
            'ripple_gain': 22.0,
        }

    @classmethod
    def get_preview_config(cls) -> Dict[str, Any]:
        cfg = cls.get_default_config()
        cfg.update({
            'star_count': 80,
            'ring_count': 3,
        })
        return cfg
