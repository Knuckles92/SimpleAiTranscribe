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
from settings import settings_manager
from ui_qt.loading_screen_qt import ModernLoadingScreen
from ui_qt.widgets import (
    HeaderCard, Card, PrimaryButton, DangerButton,
    SuccessButton, ControlPanel, ModernButton, HotkeyDisplay
)


class ModernMainWindow(QMainWindow):
    """Modern PyQt6 main window with clean, professional design."""

    # Signals for application events
    record_toggled = pyqtSignal(bool)
    model_changed = pyqtSignal(str)
    transcription_ready = pyqtSignal(str)
    settings_requested = pyqtSignal()
    hotkeys_requested = pyqtSignal()
    overlay_toggle_requested = pyqtSignal()
    about_requested = pyqtSignal()

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
        self.test_loading_screen_instance = None  # Keep reference to prevent GC

        # Callbacks (will be set by controller)
        self.on_record_start: Optional[Callable] = None
        self.on_record_stop: Optional[Callable] = None
        self.on_record_cancel: Optional[Callable] = None
        self.on_model_changed: Optional[Callable] = None

        # Setup UI
        self._setup_ui()
        self._setup_menu()
        self._connect_signals()
        self._load_saved_settings()

    def _setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout (root)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Content Container (Centered)
        content_container = QWidget()
        content_container.setObjectName("contentContainer")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(24, 24, 24, 24) # Reduced margins
        content_layout.setSpacing(16) # Reduced spacing for compactness
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Wrapper to center the content container horizontally
        center_wrapper = QHBoxLayout()
        center_wrapper.addStretch()
        center_wrapper.addWidget(content_container, stretch=1)
        center_wrapper.addStretch()
        
        # Limit max width of content
        content_container.setMaximumWidth(700) # Slightly narrower for cleaner look
        content_container.setMinimumWidth(500)

        root_layout.addLayout(center_wrapper)

        # Model selection card
        model_card = Card()
        # Layout margins handled by Card class

        model_label = QLabel("Transcription Model")
        model_label.setObjectName("headerLabel")
        model_label.setFont(QFont("Segoe UI", 13)) # Adjusted font size
        model_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.model_combo = QComboBox()
        self.model_combo.addItems(config.MODEL_CHOICES)
        self.model_combo.setMinimumHeight(40) # Slightly reduced height
        self.model_combo.setFont(QFont("Segoe UI", 12))

        model_card.layout.addWidget(model_label)
        model_card.layout.addWidget(self.model_combo)

        content_layout.addWidget(model_card)

        # Status label
        self.status_label = QLabel("Ready to record")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 13))
        content_layout.addWidget(self.status_label)

        # Control buttons
        control_panel = ControlPanel()
        control_panel.layout.setSpacing(12) # Reduced spacing

        self.record_button = PrimaryButton("Start Recording")
        self.cancel_button = DangerButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.stop_button = SuccessButton("Stop")
        self.stop_button.setEnabled(False)

        control_panel.layout.addStretch()
        control_panel.layout.addWidget(self.record_button)
        control_panel.layout.addWidget(self.stop_button)
        control_panel.layout.addWidget(self.cancel_button)
        control_panel.layout.addStretch()

        content_layout.addWidget(control_panel)

        # Transcription display card
        transcription_card = HeaderCard("Transcription")

        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setMinimumHeight(250) # Adjusted height
        self.transcription_text.setFont(QFont("Segoe UI", 13))
        self.transcription_text.setPlaceholderText(
            "Transcription will appear here...\n"
            "Start recording to begin."
        )

        transcription_card.layout.addWidget(self.transcription_text)

        content_layout.addWidget(transcription_card)
        
        # Hotkey display at the bottom, centered
        hotkey_layout = QHBoxLayout()
        hotkey_layout.setSpacing(12)
        
        # Modern hotkey display
        self.hotkey_display = HotkeyDisplay()
        
        hotkey_layout.addStretch()
        hotkey_layout.addWidget(self.hotkey_display)
        hotkey_layout.addStretch()
        
        content_layout.addLayout(hotkey_layout)
        content_layout.addStretch() # Push everything up

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
        view_menu.addAction("Show Loading Screen", self.test_loading_screen)

        # Help menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self.show_about)

    def _connect_signals(self):
        """Connect button signals to slots."""
        self.record_button.clicked.connect(self._on_record_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)

    def _load_saved_settings(self):
        """Load saved settings and apply to UI."""
        try:
            # Load the saved model selection
            saved_model = settings_manager.load_model_selection()
            
            # Find the display name for the saved model
            for display_name, internal_value in config.MODEL_VALUE_MAP.items():
                if internal_value == saved_model:
                    index = self.model_combo.findText(display_name)
                    if index >= 0:
                        # Block signals temporarily to avoid triggering on_model_changed
                        self.model_combo.blockSignals(True)
                        self.model_combo.setCurrentIndex(index)
                        self.current_model = display_name
                        self.model_combo.blockSignals(False)
                        self.logger.info(f"Loaded saved model selection: {display_name}")
                    break
        except Exception as e:
            self.logger.error(f"Failed to load saved settings: {e}")
            # Use default (already set)

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
        self.settings_requested.emit()

    def open_hotkey_settings(self):
        """Open hotkey settings dialog."""
        self.logger.info("Opening hotkey settings")
        self.hotkeys_requested.emit()

    def toggle_overlay(self):
        """Toggle the overlay visibility."""
        self.logger.info("Toggling overlay")
        self.overlay_toggle_requested.emit()

    def test_loading_screen(self):
        """Show the loading screen for testing purposes."""
        self.logger.info("Testing loading screen")
        
        if self.test_loading_screen_instance:
            self.test_loading_screen_instance.destroy()
            self.test_loading_screen_instance = None
            
        self.test_loading_screen_instance = ModernLoadingScreen()
        self.test_loading_screen_instance.show()
        
        # Simulate some activity
        QTimer.singleShot(1000, lambda: self.test_loading_screen_instance.update_status("Loading resources..."))
        QTimer.singleShot(2000, lambda: self.test_loading_screen_instance.update_progress("Connecting to services..."))
        QTimer.singleShot(3000, lambda: self.test_loading_screen_instance.update_status("Almost ready..."))
        
        # Auto close after 5 seconds
        QTimer.singleShot(5000, lambda: self.test_loading_screen_instance.destroy())
        
        # Allow click to close
        original_mouse_press = self.test_loading_screen_instance.mousePressEvent
        
        def close_on_click(event):
            self.test_loading_screen_instance.destroy()
            self.test_loading_screen_instance = None
            
        self.test_loading_screen_instance.mousePressEvent = close_on_click

    def show_about(self):
        """Show about dialog."""
        self.logger.info("Showing about dialog")
        self.about_requested.emit()

    def closeEvent(self, event):
        """Handle window close event."""
        self.logger.info("Main window closing")
        try:
            if self.test_loading_screen_instance:
                self.test_loading_screen_instance.destroy()
        except Exception as e:
            self.logger.debug(f"Error destroying loading screen: {e}")
        
        # Check if minimize to tray is enabled (default: True)
        try:
            settings = settings_manager.load_all_settings()
            minimize_tray = settings.get('minimize_tray', True)  # Default to True
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            minimize_tray = True  # Default to True on error
        
        if minimize_tray:
            # Hide window instead of closing
            event.ignore()
            try:
                self.hide()
                self.logger.info("Window hidden to system tray")
            except Exception as e:
                self.logger.debug(f"Error hiding window: {e}")
                # If hiding fails, accept the close event
                event.accept()
        else:
            # Close normally
            event.accept()
