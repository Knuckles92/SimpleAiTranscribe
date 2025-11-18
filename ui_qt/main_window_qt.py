"""
Modern PyQt6 Main Window.
Main application window with recording controls and transcription display.
"""
import logging
from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap

from config import config
from ui_qt.widgets import (
    HeaderCard, Card, PrimaryButton, DangerButton,
    SuccessButton, ControlPanel, ModernButton
)


class ModernMainWindow(QMainWindow):
    """Modern PyQt6 main window with clean, professional design."""

    # Signals for application events
    record_toggled = pyqtSignal(bool)
    model_changed = pyqtSignal(str)
    transcription_ready = pyqtSignal(str)

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("Audio Recorder - Modern Interface")
        self.setMinimumSize(500, 600)
        self.setMaximumWidth(900)

        # State
        self.is_recording = False
        self.current_model = config.MODEL_CHOICES[0]

        # Callbacks (will be set by controller)
        self.on_record_start: Optional[Callable] = None
        self.on_record_stop: Optional[Callable] = None
        self.on_record_cancel: Optional[Callable] = None
        self.on_model_changed: Optional[Callable] = None

        # Setup UI
        self._setup_ui()
        self._setup_menu()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Header section
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Title
        title_label = QLabel("Audio Recorder")
        title_font = QFont("Segoe UI", 16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setObjectName("accentLabel")

        header_layout.addWidget(title_label)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # Model selection card
        model_card = Card()
        model_card.layout.setContentsMargins(12, 12, 12, 12)

        model_label = QLabel("Transcription Model")
        model_label.setObjectName("headerLabel")
        model_label.setFont(QFont("Segoe UI", 11))

        self.model_combo = QComboBox()
        self.model_combo.addItems(config.MODEL_CHOICES)
        self.model_combo.setMinimumHeight(36)
        self.model_combo.setFont(QFont("Segoe UI", 10))

        model_card.layout.addWidget(model_label)
        model_card.layout.addWidget(self.model_combo)

        main_layout.addWidget(model_card)

        # Status label
        self.status_label = QLabel("Ready to record")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Control buttons
        control_panel = ControlPanel()

        self.record_button = PrimaryButton("Start Recording")
        self.record_button.setMinimumHeight(44)
        self.record_button.setMinimumWidth(150)

        self.cancel_button = DangerButton("Cancel")
        self.cancel_button.setMinimumHeight(44)
        self.cancel_button.setMinimumWidth(120)
        self.cancel_button.setEnabled(False)

        self.stop_button = SuccessButton("Stop")
        self.stop_button.setMinimumHeight(44)
        self.stop_button.setMinimumWidth(120)
        self.stop_button.setEnabled(False)

        control_panel.layout.addWidget(self.record_button)
        control_panel.layout.addWidget(self.stop_button)
        control_panel.layout.addWidget(self.cancel_button)
        control_panel.layout.addStretch()

        main_layout.addWidget(control_panel)

        # Transcription display card
        transcription_card = HeaderCard("Transcription")

        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setMinimumHeight(200)
        self.transcription_text.setFont(QFont("Segoe UI", 10))
        self.transcription_text.setPlaceholderText(
            "Transcription will appear here...\n"
            "Start recording to begin."
        )

        transcription_card.layout.addWidget(self.transcription_text)

        main_layout.addWidget(transcription_card)

        # Footer info
        footer_label = QLabel("© 2024 Audio Recorder. Global hotkeys: * (record), - (cancel)")
        footer_label.setObjectName("statusLabel")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setFont(QFont("Segoe UI", 9))

        main_layout.addWidget(footer_label)

    def _setup_menu(self):
        """Setup the menu bar."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #2d2d44;
                color: #e0e0ff;
                border-bottom: 1px solid #404060;
            }
            QMenuBar::item:selected {
                background-color: #6366f1;
            }
            QMenu {
                background-color: #2d2d44;
                color: #e0e0ff;
            }
            QMenu::item:selected {
                background-color: #6366f1;
            }
        """)

        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Settings", self.open_settings)
        file_menu.addAction("Hotkeys", self.open_hotkey_settings)
        file_menu.addAction("Exit", self.close)

        # View menu
        view_menu = menubar.addMenu("View")
        view_menu.addAction("Show Overlay", self.toggle_overlay)

        # Help menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self.show_about)

    def _connect_signals(self):
        """Connect button signals to slots."""
        self.record_button.clicked.connect(self._on_record_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)

    def _on_record_clicked(self):
        """Handle record button click."""
        self.is_recording = True
        self._update_recording_state()

        if self.on_record_start:
            self.on_record_start()

        self.record_toggled.emit(True)

    def _on_stop_clicked(self):
        """Handle stop button click."""
        self.is_recording = False
        self._update_recording_state()

        if self.on_record_stop:
            self.on_record_stop()

        self.record_toggled.emit(False)

    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self.is_recording = False
        self._update_recording_state()

        if self.on_record_cancel:
            self.on_record_cancel()

        self.record_toggled.emit(False)

    def _on_model_changed(self, model_name: str):
        """Handle model selection change."""
        self.current_model = model_name
        if self.on_model_changed:
            self.on_model_changed(model_name)
        self.model_changed.emit(model_name)

    def _update_recording_state(self):
        """Update button states based on recording status."""
        if self.is_recording:
            self.record_button.setEnabled(False)
            self.record_button.setText("Recording...")
            self.stop_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            self.model_combo.setEnabled(False)
            self.status_label.setText("Recording in progress...")
        else:
            self.record_button.setEnabled(True)
            self.record_button.setText("Start Recording")
            self.stop_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.model_combo.setEnabled(True)
            self.status_label.setText("Ready to record")

    def set_status(self, status_text: str):
        """Update the status label."""
        self.status_label.setText(status_text)

    def set_transcription(self, text: str):
        """Set the transcription text."""
        self.transcription_text.setText(text)

    def append_transcription(self, text: str):
        """Append text to the transcription."""
        cursor = self.transcription_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.transcription_text.setTextCursor(cursor)
        self.transcription_text.insertPlainText(text)

    def clear_transcription(self):
        """Clear the transcription text."""
        self.transcription_text.clear()

    def get_model_value(self) -> str:
        """Get the model value key."""
        return config.MODEL_VALUE_MAP.get(self.current_model, "local_whisper")

    def open_settings(self):
        """Open settings dialog."""
        self.logger.info("Opening settings dialog")
        # Will be implemented in settings dialog module

    def open_hotkey_settings(self):
        """Open hotkey settings dialog."""
        self.logger.info("Opening hotkey settings")
        # Will be implemented in hotkey dialog module

    def toggle_overlay(self):
        """Toggle the overlay visibility."""
        self.logger.info("Toggling overlay")
        # Will be implemented in overlay module

    def show_about(self):
        """Show about dialog."""
        self.logger.info("Showing about dialog")
        # Will be implemented

    def closeEvent(self, event):
        """Handle window close event."""
        self.logger.info("Main window closing")
        event.accept()
