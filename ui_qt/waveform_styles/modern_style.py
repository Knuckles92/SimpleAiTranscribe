"""
Modern waveform style - clean bars with gradient colors and smooth animations.
PyQt6 version of the modern style.
"""
import math
from typing import Dict, Any
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QPainterPath
from PyQt6.QtCore import QRect, QRectF, Qt
from .base_style import BaseWaveformStyle


class ModernStyle(BaseWaveformStyle):
    """Modern clean style with gradient bars and smooth animations."""

    def __init__(self, width: int, height: int, config: Dict[str, Any]):
        super().__init__(width, height, config)

        self._display_name = "Modern"
        self._description = "Clean gradient bars with smooth animations"

        # Style-specific settings
        self.bar_count = config.get('bar_count', 20)
        self.bar_width = config.get('bar_width', 8)
        self.bar_spacing = config.get('bar_spacing', 2)

        # Colors
        self.bg_color = config.get('bg_color', '#1a1a1a')
        self.accent_color = config.get('accent_color', '#00d4ff')
        self.secondary_color = config.get('secondary_color', '#0099cc')
        self.text_color = config.get('text_color', '#ffffff')
        self.danger_color = config.get('danger_color', '#ff4444')

        # Animation settings
        self.pulse_speed = config.get('pulse_speed', 2.0)
        self.pulse_amplitude = config.get('pulse_amplitude', 0.3)
        self.wave_speed = config.get('wave_speed', 3.0)
        self.smoothing_factor = config.get('smoothing_factor', 0.1)

    def _hex_to_qcolor(self, hex_color: str) -> QColor:
        """Convert hex color string to QColor."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return QColor(r, g, b)

    def _interpolate_color(self, color1: str, color2: str, t: float) -> QColor:
        """Interpolate between two hex colors.

        Args:
            color1: First color (hex string)
            color2: Second color (hex string)
            t: Interpolation factor (0.0 to 1.0)

        Returns:
            Interpolated QColor
        """
        c1 = self._hex_to_qcolor(color1)
        c2 = self._hex_to_qcolor(color2)

        r = int(c1.red() + t * (c2.red() - c1.red()))
        g = int(c1.green() + t * (c2.green() - c1.green()))
        b = int(c1.blue() + t * (c2.blue() - c1.blue()))

        return QColor(r, g, b)

    def _draw_rounded_bar(self, painter: QPainter, x: int, y1: int, width: int, height: int, color: QColor):
        """Draw a rounded rectangle bar.

        Args:
            painter: QPainter instance
            x: X position
            y1: Top Y position
            width: Bar width
            height: Bar height
            color: Fill color
        """
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        rect = QRectF(x, y1, width, height)
        painter.drawRoundedRect(rect, 3, 3)

    def draw_recording_state(self, painter: QPainter, rect: QRect, message: str = "Recording..."):
        """Draw real-time audio waveform for recording state."""
        # Calculate bar positions
        total_bar_width = self.bar_count * (self.bar_width + self.bar_spacing) - self.bar_spacing
        start_x = (rect.width() - total_bar_width) // 2

        # Draw waveform bars
        for i in range(self.bar_count):
            x = start_x + i * (self.bar_width + self.bar_spacing)

            # Get audio level for this bar
            if i < len(self.audio_levels):
                level = self.audio_levels[i]
            else:
                level = 0.0

            # Add some smoothing and noise for visual appeal
            smooth_level = level + self.smoothing_factor * math.sin(self.animation_time * 10 + i * 0.5)
            smooth_level = max(0.0, min(1.0, smooth_level))

            # Calculate bar height (minimum height for aesthetics)
            min_height = 4
            max_bar_height = rect.height() - 30
            bar_height = min_height + smooth_level * max_bar_height

            # Center the bar vertically
            y1 = (rect.height() - bar_height) // 2

            # Color gradient based on level
            if smooth_level > 0.7:
                color = self._interpolate_color(self.secondary_color, self.danger_color,
                                               (smooth_level - 0.7) / 0.3)
            else:
                color = self._interpolate_color(self.accent_color, self.secondary_color, smooth_level)

            # Draw bar with rounded edges
            self._draw_rounded_bar(painter, x, y1, self.bar_width, bar_height, color)

        # Draw status text
        painter.setPen(self._hex_to_qcolor(self.text_color))
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        text_rect = QRect(0, rect.height() - 25, rect.width(), 20)
        painter.drawText(text_rect, 0x0004 | 0x0080, message)  # AlignCenter | AlignBottom

    def draw_processing_state(self, painter: QPainter, rect: QRect, message: str = "Processing..."):
        """Draw pulsing animation for processing state."""
        # Pulsing circle animation
        pulse_factor = 1.0 + self.pulse_amplitude * math.sin(self.animation_time * self.pulse_speed)

        center_x = rect.width() // 2
        center_y = rect.height() // 2 - 5
        base_radius = 15
        radius = base_radius * pulse_factor

        # Draw pulsing circles with gradient effect
        for i in range(5):
            alpha = 1.0 - (i / 5.0)
            color = self._interpolate_color(self.accent_color, self.bg_color, 1.0 - alpha)
            current_radius = radius - i * 2

            if current_radius > 0:
                painter.setBrush(color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(
                    center_x - int(current_radius), center_y - int(current_radius),
                    int(current_radius * 2), int(current_radius * 2)
                )

        # Draw status text
        painter.setPen(self._hex_to_qcolor(self.text_color))
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        text_rect = QRect(0, rect.height() - 25, rect.width(), 20)
        painter.drawText(text_rect, 0x0004 | 0x0080, message)

    def draw_transcribing_state(self, painter: QPainter, rect: QRect, message: str = "Transcribing..."):
        """Draw wave animation for transcribing state."""
        # Flowing wave animation
        wave_count = 3
        center_y = rect.height() // 2 - 5

        for wave in range(wave_count):
            wave_offset = wave * (2 * math.pi / wave_count)

            # Calculate wave path
            path = QPainterPath()
            first_point = True

            for x in range(0, rect.width(), 4):
                y_offset = 10 * math.sin((x / 20.0) + (self.animation_time * self.wave_speed) + wave_offset)
                y = center_y + y_offset

                if first_point:
                    path.moveTo(x, y)
                    first_point = False
                else:
                    path.lineTo(x, y)

            # Draw wave line
            alpha = 1.0 - (wave * 0.3)
            color = self._interpolate_color(self.accent_color, self.bg_color, 1.0 - alpha)

            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.drawPath(path)

        # Draw status text
        painter.setPen(self._hex_to_qcolor(self.text_color))
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        text_rect = QRect(0, rect.height() - 25, rect.width(), 20)
        painter.drawText(text_rect, 0x0004 | 0x0080, message)
