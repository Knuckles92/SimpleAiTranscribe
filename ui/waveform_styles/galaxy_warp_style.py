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

    def draw_idle_state(self, message: str = ""):
        """Draw minimal starfield with static ripples for idle state."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        
        # Only draw if we have a message
        if message:
            # Static starfield (no animation)
            self.canvas.create_rectangle(0, 0, self.width, self.height, 
                                       outline="", fill=self.bg_color)
            
            # Draw static stars (no movement, no twinkling)
            for s in self._stars[:30]:  # Use only a subset of stars for idle
                r = max(1, int((1.8 - s['z']) * 0.8))  # Smaller, dimmer stars
                # Use very muted colors
                color = self.interpolate_color(self.star_color, self.bg_color, 0.6)
                self.canvas.create_oval(s['x'] - r, s['y'] - r, s['x'] + r, s['y'] + r, 
                                      outline="", fill=color)
            
            # Draw static concentric ripples (no animation)
            center_x, center_y = self.width // 2, (self.height // 2) - 5
            
            for i in range(3):  # Fewer rings
                radius = 20 + i * 12  # Static radii
                # Very muted colors
                color = self.interpolate_color(self.accent, self.bg_color, 0.7)
                self.canvas.create_oval(center_x - radius, center_y - radius, 
                                      center_x + radius, center_y + radius,
                                      outline=color, width=1)  # Thinner lines
            
            # Draw small center dot
            self.canvas.create_oval(center_x - 2, center_y - 2, center_x + 2, center_y + 2,
                                  fill=self.interpolate_color(self.accent2, self.bg_color, 0.5), 
                                  outline="")
            
            # Draw status text
            self.draw_text(message, self.width // 2, self.height - 12, self.text_color)

    def draw_canceling_state(self, message: str = "Cancelled"):
        """Draw galaxy collapse into black hole for canceling state."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._advance_starfield()
        self._draw_starfield(0.3)
        
        # Get cancellation progress (0.0 to 1.0)
        progress = self.get_cancellation_progress()
        
        # Collapse effect - warp field contracts toward center
        center_x, center_y = self.width // 2, (self.height // 2) - 5
        
        # Draw collapsing warp field
        warp_layers = 8
        for layer in range(warp_layers):
            layer_alpha = 1.0 - (layer / warp_layers) * progress
            if layer_alpha <= 0:
                continue
                
            layer_radius = (30 + layer * 10) * (1.0 - progress * 0.8)
            if layer_radius <= 0:
                continue
            
            # Calculate warp field points
            points = []
            num_points = 16
            for i in range(num_points):
                angle = (i / num_points) * 2 * math.pi
                
                # Apply collapse distortion
                distortion = math.sin(self.animation_time * 2 + angle * 3) * (1.0 - progress)
                radius = layer_radius + distortion * 5
                
                # Point gets pulled toward center as progress increases
                x = center_x + math.cos(angle) * radius * (1.0 - progress * 0.5)
                y = center_y + math.sin(angle) * radius * (1.0 - progress * 0.5)
                points.extend([x, y])
            
            # Close the loop
            if len(points) >= 4:
                points.extend([points[0], points[1]])
            
            # Color fades to black/red
            base_color = self.accent if layer % 2 == 0 else self.accent2
            collapsed_color = self.interpolate_color(base_color, "#330000", progress * 0.8)
            final_color = self.interpolate_color(collapsed_color, "#000000", progress * 0.6)
            
            # Draw collapsing warp ring
            if len(points) >= 4:
                line_width = max(1, int(2 * layer_alpha))
                self.canvas.create_line(
                    points, fill=final_color, width=line_width, smooth=True
                )
        
        # Draw central singularity (black hole effect)
        singularity_radius = int(progress * 15)
        if singularity_radius > 0:
            # Event horizon
            self.canvas.create_oval(
                center_x - singularity_radius, center_y - singularity_radius,
                center_x + singularity_radius, center_y + singularity_radius,
                fill="#000000", outline=""
            )
            
            # Accretion disk
            if progress > 0.3:
                disk_radius = singularity_radius + 8
                disk_color = self.interpolate_color("#ff4400", "#000000", (progress - 0.3) * 1.4)
                self.canvas.create_oval(
                    center_x - disk_radius, center_y - disk_radius,
                    center_x + disk_radius, center_y + disk_radius,
                    fill="", outline=disk_color, width=2
                )
        
        # Draw warping text that gets stretched toward center
        text_distortion = progress * 3
        text_x = self.width // 2
        text_y = self.height - 12 + text_distortion
        
        text_color = self.interpolate_color(self.text_color, "#000000", progress * 0.8)
        self.draw_text(message, int(text_x), int(text_y), text_color)

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
