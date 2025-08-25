"""
Minimalist Zen style - clean, elegant design with purposeful animations and refined aesthetics.
"""
import math
from typing import Dict, Any
from .base_style import BaseWaveformStyle
from .style_factory import register_style


@register_style
class MinimalistStyle(BaseWaveformStyle):
    """Minimalist zen style with elegant simplicity and purposeful design."""

    def __init__(self, canvas, width: int, height: int, config: Dict[str, Any]):
        super().__init__(canvas, width, height, config)

        self._display_name = "Minimalist Zen"
        self._description = "Clean, elegant design with purposeful simplicity"

        # Core visual elements
        self.bar_count = config.get('bar_count', 7)  # Fewer bars for cleaner look
        self.bar_width = config.get('bar_width', 3)
        self.bar_spacing = config.get('bar_spacing', 12)  # More spacing for breathing room

        # Refined color palette with better contrast
        self.bg_color = config.get('bg_color', '#ffffff')  # Pure white background
        self.primary_color = config.get('primary_color', '#2c3e50')  # Deep blue-gray
        self.accent_color = config.get('accent_color', '#3498db')  # Clear blue
        self.muted_color = config.get('muted_color', '#bdc3c7')  # Light gray
        self.text_color = config.get('text_color', '#2c3e50')  # Same as primary for consistency

        # Refined animation settings
        self.breathing_speed = config.get('breathing_speed', 1.5)  # Slightly faster for responsiveness
        self.pulse_speed = config.get('pulse_speed', 2.0)
        self.fade_speed = config.get('fade_speed', 1.0)
        self.smoothing = config.get('smoothing', 0.15)  # More smoothing for zen feel
        
    def draw_recording_state(self, message: str = "Recording..."):
        """Draw clean, responsive waveform bars with breathing animation."""
        if not self.canvas:
            return

        self.clear_canvas()
        self._draw_clean_background()

        # Calculate bar positions with proper centering
        total_width = (self.bar_count - 1) * self.bar_spacing
        start_x = (self.width - total_width) // 2

        # Draw elegant waveform bars
        for i in range(self.bar_count):
            x = start_x + i * self.bar_spacing

            # Get audio level with smooth interpolation
            if i < len(self.audio_levels):
                level = self.audio_levels[i]
            else:
                level = 0.0

            # Apply gentle breathing effect
            breathing = 1.0 + 0.08 * math.sin(self.animation_time * self.breathing_speed + i * 0.5)
            smoothed_level = max(0.1, level * breathing)  # Minimum height for visual presence

            # Calculate bar height with elegant proportions
            min_height = 4
            max_height = self.height - 35  # Leave room for text and padding
            bar_height = min_height + smoothed_level * (max_height - min_height)

            # Center the bar vertically
            center_y = self.height // 2 - 5  # Slight offset for text space
            y1 = center_y - bar_height // 2
            y2 = center_y + bar_height // 2

            # Elegant color progression
            if smoothed_level > 0.6:
                color = self.accent_color
            elif smoothed_level > 0.2:
                # Smooth transition from primary to accent
                blend_factor = (smoothed_level - 0.2) / 0.4
                color = self.interpolate_color(self.primary_color, self.accent_color, blend_factor)
            else:
                color = self.primary_color

            # Draw rounded rectangle bar
            self.canvas.create_rectangle(
                x - self.bar_width // 2, y1,
                x + self.bar_width // 2, y2,
                fill=color, outline="", width=0
            )

        # Draw clean status text
        self._draw_status_text(message)
        
    def draw_processing_state(self, message: str = "Processing..."):
        """Draw elegant pulsing circle with clean animation."""
        if not self.canvas:
            return

        self.clear_canvas()
        self._draw_clean_background()

        center_x = self.width // 2
        center_y = self.height // 2 - 8

        # Smooth pulsing animation
        pulse = 1.0 + 0.3 * math.sin(self.animation_time * self.pulse_speed)
        base_radius = 16
        radius = base_radius * pulse

        # Draw main circle with gradient effect
        self.canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline=self.accent_color, width=2, fill=""
        )

        # Inner filled circle for depth
        inner_radius = radius * 0.4
        self.canvas.create_oval(
            center_x - inner_radius, center_y - inner_radius,
            center_x + inner_radius, center_y + inner_radius,
            fill=self.accent_color, outline=""
        )

        # Subtle outer ring
        outer_radius = radius * 1.3
        outer_alpha = 0.3 + 0.2 * math.sin(self.animation_time * self.pulse_speed * 0.7)
        outer_color = self.interpolate_color(self.bg_color, self.accent_color, outer_alpha)
        self.canvas.create_oval(
            center_x - outer_radius, center_y - outer_radius,
            center_x + outer_radius, center_y + outer_radius,
            outline=outer_color, width=1, fill=""
        )

        # Draw clean status text
        self._draw_status_text(message)
        
    def draw_transcribing_state(self, message: str = "Transcribing..."):
        """Draw elegant flowing wave animation."""
        if not self.canvas:
            return

        self.clear_canvas()
        self._draw_clean_background()

        center_x = self.width // 2
        center_y = self.height // 2 - 8

        # Draw flowing wave pattern
        wave_width = self.width * 0.7
        start_x = (self.width - wave_width) // 2

        # Create smooth wave points
        points = []
        point_count = 20
        for i in range(point_count):
            x = start_x + (i / (point_count - 1)) * wave_width

            # Flowing wave calculation
            wave_phase = (i / point_count) * 2 * math.pi + self.animation_time * 2.5
            wave_amplitude = 8
            y = center_y + math.sin(wave_phase) * wave_amplitude

            points.extend([x, y])

        # Draw main wave
        if len(points) >= 4:
            self.canvas.create_line(
                points,
                fill=self.accent_color,
                width=2,
                smooth=True,
                capstyle="round"
            )

        # Draw secondary wave with offset
        points2 = []
        for i in range(point_count):
            x = start_x + (i / (point_count - 1)) * wave_width
            wave_phase = (i / point_count) * 2 * math.pi + self.animation_time * 2.5 + math.pi / 3
            y = center_y + math.sin(wave_phase) * 4  # Smaller amplitude
            points2.extend([x, y])

        if len(points2) >= 4:
            secondary_color = self.interpolate_color(self.bg_color, self.accent_color, 0.5)
            self.canvas.create_line(
                points2,
                fill=secondary_color,
                width=1,
                smooth=True,
                capstyle="round"
            )

        # Draw clean status text
        self._draw_status_text(message)
    
    def _draw_clean_background(self):
        """Draw clean, minimal background."""
        # Pure background
        self.canvas.create_rectangle(
            0, 0, self.width, self.height,
            fill=self.bg_color, outline=""
        )

        # Subtle border for definition
        border_color = self.interpolate_color(self.bg_color, self.muted_color, 0.3)
        self.canvas.create_rectangle(
            1, 1, self.width - 1, self.height - 1,
            fill="", outline=border_color, width=1
        )

    def _draw_status_text(self, message: str):
        """Draw clean, readable status text."""
        if message:
            # Position text at bottom with proper spacing
            text_y = self.height - 12
            self.draw_text(
                message,
                self.width // 2,
                text_y,
                self.text_color,
                ("Segoe UI", 9, "normal")  # Modern, clean font
            )
    
    def draw_canceling_state(self, message: str = "Cancelled"):
        """Draw elegant fade-out animation for canceling state."""
        if not self.canvas:
            return

        self.clear_canvas()
        self._draw_clean_background()

        # Get cancellation progress (0.0 to 1.0)
        progress = self.get_cancellation_progress()
        fade_factor = 1.0 - progress

        center_x = self.width // 2
        center_y = self.height // 2 - 8

        # Draw fading circle
        if fade_factor > 0:
            radius = 20 * fade_factor
            circle_color = self.interpolate_color(self.bg_color, self.accent_color, fade_factor * 0.7)

            self.canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                outline=circle_color, width=2, fill=""
            )

            # Inner dot that fades out
            dot_radius = 3 * fade_factor
            if dot_radius > 0.5:
                dot_color = self.interpolate_color(self.bg_color, self.primary_color, fade_factor)
                self.canvas.create_oval(
                    center_x - dot_radius, center_y - dot_radius,
                    center_x + dot_radius, center_y + dot_radius,
                    fill=dot_color, outline=""
                )

        # Draw fading bars
        total_width = (self.bar_count - 1) * self.bar_spacing
        start_x = (self.width - total_width) // 2

        for i in range(self.bar_count):
            if fade_factor <= 0:
                break

            x = start_x + i * self.bar_spacing

            # Use last known levels or create pattern
            if i < len(self.audio_levels) and len(self.audio_levels) > 0:
                level = self.audio_levels[i]
            else:
                level = 0.3 + 0.2 * math.sin(i * 0.8)  # Gentle pattern

            # Apply fade
            bar_height = (8 + level * 20) * fade_factor
            if bar_height <= 1:
                continue

            y1 = center_y + 25 - bar_height // 2
            y2 = y1 + bar_height

            # Fade color
            bar_color = self.interpolate_color(self.bg_color, self.primary_color, fade_factor * 0.6)

            self.canvas.create_rectangle(
                x - self.bar_width // 2, y1,
                x + self.bar_width // 2, y2,
                fill=bar_color, outline=""
            )

        # Draw fading status text
        if fade_factor > 0.1:
            text_color = self.interpolate_color(self.bg_color, self.text_color, fade_factor)
            self._draw_status_text_with_color(message, text_color)
    
    def draw_idle_state(self, message: str = ""):
        """Draw clean, minimal idle state."""
        if not self.canvas:
            return

        self.clear_canvas()

        # Only draw if we have a message
        if message:
            self._draw_clean_background()

            center_x = self.width // 2
            center_y = self.height // 2 - 8

            # Draw simple, elegant circle
            circle_radius = 12
            circle_color = self.interpolate_color(self.bg_color, self.accent_color, 0.4)

            self.canvas.create_oval(
                center_x - circle_radius, center_y - circle_radius,
                center_x + circle_radius, center_y + circle_radius,
                outline=circle_color, width=1, fill=""
            )

            # Central dot for focus
            dot_radius = 2
            self.canvas.create_oval(
                center_x - dot_radius, center_y - dot_radius,
                center_x + dot_radius, center_y + dot_radius,
                fill=self.primary_color, outline=""
            )

            # Simple static bars below
            total_width = (self.bar_count - 1) * self.bar_spacing
            start_x = (self.width - total_width) // 2

            for i in range(self.bar_count):
                x = start_x + i * self.bar_spacing

                # Gentle height variation
                bar_height = 6 + (i % 3) * 2
                y1 = center_y + 20 - bar_height // 2
                y2 = y1 + bar_height

                # Very muted color for idle state
                bar_color = self.interpolate_color(self.bg_color, self.muted_color, 0.6)

                self.canvas.create_rectangle(
                    x - self.bar_width // 2, y1,
                    x + self.bar_width // 2, y2,
                    fill=bar_color, outline=""
                )

            # Draw clean status text
            self._draw_status_text(message)

    def _draw_status_text_with_color(self, message: str, color: str):
        """Draw status text with specific color."""
        if message:
            text_y = self.height - 12
            self.draw_text(
                message,
                self.width // 2,
                text_y,
                color,
                ("Segoe UI", 9, "normal")
            )
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration for minimalist style."""
        return {
            'bar_count': 7,
            'bar_width': 3,
            'bar_spacing': 12,
            'bg_color': '#ffffff',
            'primary_color': '#2c3e50',
            'accent_color': '#3498db',
            'muted_color': '#bdc3c7',
            'text_color': '#2c3e50',
            'breathing_speed': 1.5,
            'pulse_speed': 2.0,
            'fade_speed': 1.0,
            'smoothing': 0.15
        }

    @classmethod
    def get_preview_config(cls) -> Dict[str, Any]:
        """Get configuration optimized for preview display."""
        config = cls.get_default_config()
        # Make preview more responsive and compact
        config.update({
            'bar_count': 5,
            'bar_spacing': 10,
            'breathing_speed': 2.0,
            'pulse_speed': 2.5,
            'fade_speed': 1.2
        })
        return config