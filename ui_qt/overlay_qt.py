"""
Modern PyQt6 Waveform Overlay.
Real-time audio visualization overlay with blur effects and animations.
"""
import logging
import time
from typing import Optional, List
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRect, pyqtSignal, QPoint
from PyQt6.QtGui import (
    QPainter, QPainterPath, QColor, QBrush, QPen,
    QLinearGradient, QFont, QCursor
)
from config import config
from settings import settings_manager
from ui_qt.waveform_styles import style_factory
from ui_qt.waveform_styles.base_style import BaseWaveformStyle


class ModernWaveformOverlay(QWidget):
    """Modern waveform overlay with smooth animations."""

    state_changed = pyqtSignal(str)

    # States
    STATE_IDLE = "idle"
    STATE_RECORDING = "recording"
    STATE_PROCESSING = "processing"
    STATE_TRANSCRIBING = "transcribing"
    STATE_CANCELING = "canceling"
    STATE_STT_ENABLE = "stt_enable"
    STATE_STT_DISABLE = "stt_disable"

    def __init__(self):
        """Initialize the overlay."""
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Window properties
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set fixed size from config
        self.overlay_width = config.WAVEFORM_OVERLAY_WIDTH
        self.overlay_height = config.WAVEFORM_OVERLAY_HEIGHT
        self.setFixedSize(self.overlay_width, self.overlay_height)

        # State
        self.current_state = self.STATE_IDLE
        self.audio_levels: List[float] = [0.0] * 20
        self.animation_time = 0.0
        self.cancel_progress = 0.0

        # Load waveform style
        current_style, style_configs = settings_manager.load_waveform_style_settings()
        try:
            style_config = style_configs.get(current_style, config.WAVEFORM_STYLE_CONFIGS.get('modern', {}))
            self.style: BaseWaveformStyle = style_factory.create_style(
                current_style,
                self.overlay_width,
                self.overlay_height,
                style_config
            )
        except (ValueError, KeyError):
            # Fallback to modern style if loading fails
            self.logger.warning(f"Failed to load style '{current_style}', using modern")
            self.style = style_factory.create_style('modern', self.overlay_width, self.overlay_height)

        # Animation
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_animation)
        self.frame_rate = 30
        self.animation_duration = 0
        self.last_frame_time = time.time()

        # Hide by default
        self.hidden_timer = QTimer()
        self.hidden_timer.setSingleShot(True)
        self.hidden_timer.timeout.connect(self.hide)

    def paintEvent(self, event):
        """Paint the overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background with blur effect
        self._draw_background(painter)

        # Get drawing rect
        rect = self.rect()

        # Draw state-specific content using style
        if self.current_state == self.STATE_RECORDING:
            self.style.draw_recording_state(painter, rect, "Recording...")
        elif self.current_state == self.STATE_PROCESSING:
            self.style.draw_processing_state(painter, rect, "Processing...")
        elif self.current_state == self.STATE_TRANSCRIBING:
            self.style.draw_transcribing_state(painter, rect, "Transcribing...")
        elif self.current_state == self.STATE_CANCELING:
            self.style.draw_canceling_state(painter, rect, "Cancelled")
        elif self.current_state == self.STATE_STT_ENABLE:
            self.style.draw_stt_enable_state(painter, rect, "STT Enabled")
        elif self.current_state == self.STATE_STT_DISABLE:
            self.style.draw_stt_disable_state(painter, rect, "STT Disabled")

    def _draw_background(self, painter: QPainter):
        """Draw the background with frosted glass effect."""
        rect = self.rect()

        # Draw semi-transparent background
        painter.fillRect(rect, QColor(45, 45, 68, 200))

        # Draw border
        painter.setPen(QPen(QColor(64, 64, 96, 150), 1))
        painter.drawRoundedRect(rect, 12, 12)

    def _draw_recording_state(self, painter: QPainter):
        """Draw recording state visualization."""
        rect = self.rect()
        w, h = rect.width(), rect.height()

        # Draw waveform bars
        bar_count = 20
        bar_width = (w - 40) / bar_count
        start_x = 20

        for i in range(bar_count):
            x = start_x + i * bar_width
            level = self.audio_levels[i] if i < len(self.audio_levels) else 0.0
            bar_height = max(10, level * (h - 40))

            # Color gradient based on level
            if level > 0.7:
                color = QColor(239, 68, 68)  # Red
            elif level > 0.4:
                color = QColor(99, 102, 241)  # Indigo
            else:
                color = QColor(139, 92, 246)  # Purple

            painter.fillRect(
                int(x + bar_width * 0.2),
                int(h / 2 - bar_height / 2),
                int(bar_width * 0.6),
                int(bar_height),
                color
            )

        # Draw status text
        painter.setPen(QPen(QColor(224, 224, 255)))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(rect.adjusted(0, h - 25, 0, 0), Qt.AlignmentFlag.AlignCenter, "Recording...")

    def _draw_processing_state(self, painter: QPainter):
        """Draw processing state."""
        rect = self.rect()
        w, h = rect.width(), rect.height()

        # Draw rotating spinner
        painter.setPen(QPen(QColor(99, 102, 241), 3))
        spinner_rect = QRect(w // 2 - 20, h // 2 - 20, 40, 40)
        angle = int((self.animation_time * 360) % 360)
        painter.drawArc(spinner_rect, angle * 16, 200 * 16)

        # Status text
        painter.setPen(QPen(QColor(224, 224, 255)))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(rect.adjusted(0, h - 25, 0, 0), Qt.AlignmentFlag.AlignCenter, "Processing...")

    def _draw_transcribing_state(self, painter: QPainter):
        """Draw transcribing state."""
        rect = self.rect()
        w, h = rect.width(), rect.height()

        # Draw pulsing circles
        progress = (self.animation_time * 2) % 1.0
        for i in range(3):
            offset = (progress + i * 0.3) % 1.0
            radius = int(15 + offset * 15)
            alpha = int(200 * (1 - offset))
            color = QColor(0, 212, 255, alpha)

            painter.setPen(QPen(color, 2))
            painter.drawEllipse(w // 2 - radius, h // 2 - radius, radius * 2, radius * 2)

        # Status text
        painter.setPen(QPen(QColor(224, 224, 255)))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(rect.adjusted(0, h - 25, 0, 0), Qt.AlignmentFlag.AlignCenter, "Transcribing...")

    def _draw_canceling_state(self, painter: QPainter):
        """Draw canceling state with shrinking X."""
        rect = self.rect()
        w, h = rect.width(), rect.height()

        # Draw shrinking X
        progress = self.cancel_progress  # 0.0 to 1.0
        size = int(40 * (1 - progress * 0.8))

        # X lines
        painter.setPen(QPen(QColor(239, 68, 68), 4))
        painter.drawLine(
            w // 2 - size,
            h // 2 - size,
            w // 2 + size,
            h // 2 + size
        )
        painter.drawLine(
            w // 2 + size,
            h // 2 - size,
            w // 2 - size,
            h // 2 + size
        )

        # Status text
        painter.setPen(QPen(QColor(224, 224, 255)))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(rect.adjusted(0, h - 25, 0, 0), Qt.AlignmentFlag.AlignCenter, "Canceling...")

    def _draw_stt_enable_state(self, painter: QPainter):
        """Draw STT enable state."""
        rect = self.rect()
        w, h = rect.width(), rect.height()

        # Draw checkmark animation
        progress = min(1.0, self.animation_time / 0.5)

        painter.setPen(QPen(QColor(16, 185, 129), 4))
        if progress > 0.0:
            # Checkmark path
            painter.drawLine(int(w // 2 - 15), int(h // 2), int(w // 2 - 5), int(h // 2 + 10))
            painter.drawLine(int(w // 2 - 5), int(h // 2 + 10), int(w // 2 + 15), int(h // 2 - 10))

        # Status text
        painter.setPen(QPen(QColor(224, 224, 255)))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(rect.adjusted(0, h - 25, 0, 0), Qt.AlignmentFlag.AlignCenter, "Enabled")

    def _draw_stt_disable_state(self, painter: QPainter):
        """Draw STT disable state."""
        rect = self.rect()
        w, h = rect.width(), rect.height()

        # Draw X animation
        progress = min(1.0, self.animation_time / 0.5)

        painter.setPen(QPen(QColor(239, 68, 68), 4))
        if progress > 0.0:
            size = int(20 * progress)
            painter.drawLine(w // 2 - size, h // 2 - size, w // 2 + size, h // 2 + size)
            painter.drawLine(w // 2 + size, h // 2 - size, w // 2 - size, h // 2 + size)

        # Status text
        painter.setPen(QPen(QColor(224, 224, 255)))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(rect.adjusted(0, h - 25, 0, 0), Qt.AlignmentFlag.AlignCenter, "Disabled")

    def _update_animation(self):
        """Update animation time and redraw."""
        # Calculate delta time
        current_time = time.time()
        delta_time = current_time - self.last_frame_time
        self.last_frame_time = current_time

        self.animation_time += delta_time

        # Update style animation
        if self.style:
            self.style.update_animation_time(delta_time)

        if self.current_state == self.STATE_CANCELING:
            self.cancel_progress = min(1.0, self.animation_time / 0.8)
            if self.cancel_progress >= 1.0:
                self.set_state(self.STATE_IDLE)
                self.timer.stop()

        self.update()

    def set_state(self, state: str):
        """Set the overlay state."""
        if self.current_state != state:
            self.current_state = state
            self.animation_time = 0.0
            self.cancel_progress = 0.0

            # Set canceling start time for style
            if state == self.STATE_CANCELING and self.style:
                self.style.set_canceling_start_time(time.time())

            if state == self.STATE_IDLE:
                self.timer.stop()
            else:
                self.timer.start(1000 // self.frame_rate)

            self.state_changed.emit(state)
            self.logger.debug(f"Overlay state changed to: {state}")

            # Auto-hide after delay for certain states
            if state in [self.STATE_STT_ENABLE, self.STATE_STT_DISABLE]:
                self.hidden_timer.start(1500)

    def update_audio_levels(self, levels: List[float]):
        """Update audio level data."""
        self.audio_levels = levels[:20]  # Keep only 20 levels

        # Update style with audio levels
        if self.style:
            current_level = sum(levels) / len(levels) if levels else 0.0
            self.style.update_audio_levels(self.audio_levels, current_level)

    def show_at_cursor(self):
        """Show overlay near the cursor."""
        # Get global cursor position
        cursor_pos = QCursor.pos()

        # Position overlay near cursor (offset slightly)
        x = cursor_pos.x() + 10
        y = cursor_pos.y() + 10

        self.move(x, y)
        self.show()
        self.set_state(self.STATE_RECORDING)

    def closeEvent(self, event):
        """Handle closing."""
        self.timer.stop()
        self.hidden_timer.stop()
        event.accept()
