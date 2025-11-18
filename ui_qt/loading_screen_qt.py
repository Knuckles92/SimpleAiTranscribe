"""
Modern PyQt6 Loading Screen.
Shows a modern animated spinner with status messages during initialization.
"""
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QRect, QPropertyAnimation, QSequentialAnimationGroup
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QFont, QBrush, QPen
from PyQt6.QtCore import pyqtSignal


class AnimatedSpinner(QWidget):
    """Modern animated spinner widget."""

    def __init__(self, parent=None):
        """Initialize spinner."""
        super().__init__(parent)
        self.setMinimumSize(80, 80)
        self.setMaximumSize(80, 80)
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._rotate)

    def start(self):
        """Start the spinner animation."""
        self.timer.start(50)

    def stop(self):
        """Stop the spinner animation."""
        self.timer.stop()

    def _rotate(self):
        """Rotate the spinner."""
        self.angle = (self.angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        """Paint the spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Translate to center
        w = self.width()
        h = self.height()
        painter.translate(w / 2, h / 2)
        painter.rotate(self.angle)

        # Draw the spinning arc
        rect = QRect(-30, -30, 60, 60)

        # Outer circle
        painter.setPen(QPen(QColor("#6366f1"), 4))
        painter.drawArc(rect, 0, int(200 * 16))

        # Inner accent
        painter.rotate(120)
        painter.setPen(QPen(QColor("#8b5cf6"), 4))
        painter.drawArc(rect, 0, int(200 * 16))

        painter.rotate(120)
        painter.setPen(QPen(QColor("#00d4ff"), 4))
        painter.drawArc(rect, 0, int(200 * 16))


class ModernLoadingScreen(QWidget):
    """Modern loading screen with animated spinner."""

    # Signal to notify loading completion
    finished = pyqtSignal()

    def __init__(self):
        """Initialize loading screen."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("Audio Recorder")
        self.setMinimumSize(400, 350)
        self.setMaximumSize(400, 350)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Center on screen
        screen = self.screen().geometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2
        )

        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Title
        title = QLabel("Audio Recorder")
        title_font = QFont("Segoe UI", 18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #e0e0ff;")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Modern Speech-to-Text Application")
        subtitle_font = QFont("Segoe UI", 10)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #a0a0c0;")
        layout.addWidget(subtitle)

        # Spinner
        layout.addSpacing(20)
        self.spinner = AnimatedSpinner()
        spinner_container = QWidget()
        spinner_layout = QVBoxLayout(spinner_container)
        spinner_layout.setContentsMargins(0, 0, 0, 0)
        spinner_layout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(spinner_container)

        # Status label
        layout.addSpacing(20)
        self.status_label = QLabel("Initializing...")
        status_font = QFont("Segoe UI", 11)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #00d4ff;")
        layout.addWidget(self.status_label)

        # Progress label
        self.progress_label = QLabel("")
        progress_font = QFont("Segoe UI", 9)
        self.progress_label.setFont(progress_font)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("color: #a0a0c0;")
        layout.addWidget(self.progress_label)

        layout.addStretch()

        # Apply background styling
        self.setStyleSheet("""
            ModernLoadingScreen {
                background-color: #1e1e2e;
                border-radius: 12px;
                border: 1px solid #404060;
            }
        """)

    def show(self):
        """Show the loading screen and start animation."""
        super().show()
        self.spinner.start()
        self.logger.info("Loading screen displayed")

    def update_status(self, status_text: str):
        """Update the status message."""
        self.status_label.setText(status_text)

    def update_progress(self, progress_text: str):
        """Update the progress message."""
        self.progress_label.setText(progress_text)

    def closeEvent(self, event):
        """Handle closing."""
        self.spinner.stop()
        event.accept()
        self.logger.info("Loading screen closed")

    def destroy(self, destroyWindow=True, destroySubWindows=True):
        """Destroy the widget."""
        self.spinner.stop()
        super().destroy(destroyWindow, destroySubWindows)
