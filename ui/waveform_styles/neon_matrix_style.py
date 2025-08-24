"""
Neon Matrix waveform style - cyberpunk "code rain" with reactive neon bars.
"""
import math
import random
from typing import Dict, Any
from .base_style import BaseWaveformStyle
from .style_factory import register_style


@register_style
class NeonMatrixStyle(BaseWaveformStyle):
    """Cyberpunk neon style with Matrix-like rain and reactive bars."""

    def __init__(self, canvas, width: int, height: int, config: Dict[str, Any]):
        super().__init__(canvas, width, height, config)
        self._display_name = "Neon Matrix"
        self._description = "Cyberpunk code rain with neon equalizer bars"

        # Config
        self.bg_color = config.get('bg_color', '#0a0f14')
        self.primary = config.get('primary', '#39ff14')  # neon green
        self.secondary = config.get('secondary', '#00e5ff')  # neon cyan
        self.alert = config.get('alert', '#ff2a6d')
        self.text_color = config.get('text_color', '#d0f5ff')
        self.bar_count = config.get('bar_count', 18)
        self.bar_width = config.get('bar_width', 7)
        self.bar_spacing = config.get('bar_spacing', 3)
        self.rain_columns = config.get('rain_columns', 24)
        self.rain_speed = config.get('rain_speed', 110.0)
        self.glow_intensity = config.get('glow_intensity', 0.4)

        # Rain state
        self._rain_offsets = [random.random() * 1000 for _ in range(self.rain_columns)]

    def _draw_bg_glow(self):
        if not self.canvas:
            return
        # Subtle vignette
        step = 8
        for i in range(6):
            alpha = i / 6.0
            color = self.interpolate_color(self.secondary, self.bg_color, alpha)
            m = 4 + i * step
            self.canvas.create_rectangle(m, m, self.width - m, self.height - m,
                                         outline="", fill=color)

    def _draw_code_rain(self, intensity: float):
        if not self.canvas:
            return
        col_w = self.width / self.rain_columns
        t = self.animation_time
        for c in range(self.rain_columns):
            x = int(c * col_w + col_w * 0.5)
            # speed varies per column
            speed = self.rain_speed * (0.6 + 0.8 * math.sin(0.7 * c + t))
            offset = (self._rain_offsets[c] + t * speed) % (self.height + 60)
            length = 40 + int(80 * (0.5 + 0.5 * math.sin(0.9 * t + c)))

            # gradient trail
            steps = 8
            for s in range(steps):
                y = int((offset - s * (length / steps)) % (self.height + 60)) - 30
                factor = max(0.0, 1.0 - s / steps)
                factor *= 0.5 + 0.5 * intensity
                r, g, b = self.hsv_to_rgb((120 + 40 * math.sin(0.2 * c + t)) % 360, 1.0, factor)
                color = self.rgb_to_hex(r, g, b)
                self.canvas.create_line(x, y - 6, x, y + 6, fill=color, width=2)

    def _draw_bars(self, message: str, pulse: float):
        if not self.canvas:
            return
        total_w = self.bar_count * (self.bar_width + self.bar_spacing) - self.bar_spacing
        start_x = (self.width - total_w) // 2
        center_y = self.height // 2 - 4
        max_h = self.height - 36

        for i in range(self.bar_count):
            x1 = start_x + i * (self.bar_width + self.bar_spacing)
            level = self.audio_levels[i] if i < len(self.audio_levels) else 0.0
            # Add knight-rider sweep
            sweep = 0.5 + 0.5 * math.sin(self.animation_time * 3 + i * 0.4)
            l = max(0.05, min(1.0, level * 0.8 + 0.2 * sweep))
            h = max(6, int(l * max_h))
            y1 = center_y - h // 2
            y2 = y1 + h

            # Neon gradient from cyan to green, tipping to alert on peaks
            peak = max(0.0, (l - 0.78) / 0.22)
            color_mid = self.interpolate_color(self.secondary, self.primary, l)
            color = self.interpolate_color(color_mid, self.alert, peak)

            # Glow effect: draw multiple rectangles
            for gidx in range(3):
                expand = 2 * gidx
                alpha = max(0.0, 0.6 - gidx * 0.25) * (0.7 + 0.3 * pulse)
                glow = self.interpolate_color(color, self.bg_color, 1.0 - alpha)
                self.canvas.create_rectangle(
                    x1 - expand, y1 - expand, x1 + self.bar_width + expand, y2 + expand,
                    outline="", fill=glow
                )
            # Core bar
            self.canvas.create_rectangle(x1, y1, x1 + self.bar_width, y2, outline="", fill=color)

        # Status text with subtle glow
        self.draw_text(message, self.width // 2, self.height - 12, self.text_color)

    def draw_recording_state(self, message: str = "Recording..."):
        if not self.canvas:
            return
        self.clear_canvas()
        self._draw_bg_glow()
        intensity = min(1.0, 0.4 + self.current_level * 0.8)
        self._draw_code_rain(intensity)
        pulse = 0.5 + 0.5 * math.sin(self.animation_time * 4)
        self._draw_bars(message, pulse)

    def draw_processing_state(self, message: str = "Processing..."):
        if not self.canvas:
            return
        self.clear_canvas()
        self._draw_bg_glow()
        # Concentric neon squares pulsing
        cx, cy = self.width // 2, self.height // 2 - 4
        base = 8 + 4 * math.sin(self.animation_time * 3)
        for i in range(6):
            size = base + i * 10
            alpha = max(0.0, 0.8 - i * 0.12)
            color = self.interpolate_color(self.secondary, self.bg_color, 1.0 - alpha)
            self.canvas.create_rectangle(cx - size, cy - size, cx + size, cy + size,
                                         outline=color, width=2)
        self.draw_text(message, self.width // 2, self.height - 12, self.text_color)

    def draw_transcribing_state(self, message: str = "Transcribing..."):
        if not self.canvas:
            return
        self.clear_canvas()
        self._draw_bg_glow()
        # Flowing neon path that traces text
        path = []
        for x in range(0, self.width, 3):
            y = self.height // 2 - 6 + 10 * math.sin(0.08 * x + self.animation_time * 3)
            y += 4 * math.sin(0.18 * x + self.animation_time * 2)
            path.extend([x, y])
        if len(path) >= 4:
            for i in range(4):
                fade = i * 0.18
                color = self.interpolate_color(self.primary, self.secondary, (math.sin(self.animation_time*2 + i)*0.5+0.5))
                color = self.interpolate_color(color, self.bg_color, fade)
                self.canvas.create_line(path, fill=color, width=2+i, smooth=True)
        self.draw_text(message, self.width // 2, self.height - 12, self.text_color)

    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        return {
            'bg_color': '#0a0f14',
            'primary': '#39ff14',
            'secondary': '#00e5ff',
            'alert': '#ff2a6d',
            'text_color': '#d0f5ff',
            'bar_count': 18,
            'bar_width': 7,
            'bar_spacing': 3,
            'rain_columns': 24,
            'rain_speed': 110.0,
            'glow_intensity': 0.4,
        }

    @classmethod
    def get_preview_config(cls) -> Dict[str, Any]:
        cfg = cls.get_default_config()
        cfg.update({
            'bar_count': 12,
            'rain_columns': 16,
            'rain_speed': 140.0,
        })
        return cfg
