"""
Modern Hotkey Configuration Dialog for PyQt6 UI.
"""
import logging
from typing import Optional, Callable, Dict
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QKeySequence

from config import config
from ui_qt.widgets import PrimaryButton, ModernButton, HeaderCard


class HotkeyDialog(QDialog):
    """Modern hotkey configuration dialog."""

    hotkeys_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        """Initialize hotkey dialog."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("Hotkey Configuration")
        self.setMinimumSize(500, 400)

        # State
        self.current_hotkeys: Dict[str, str] = {}
        self.capturing = None
        self.capture_timer = QTimer()
        self.capture_timer.setSingleShot(True)

        # Callbacks
        self.on_hotkeys_save: Optional[Callable] = None

        self._setup_ui()
        self._load_hotkeys()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        title = QLabel("Hotkey Configuration")
        title_font = QFont("Segoe UI", 14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e0e0ff;")
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "Click on a field and press the key combination you want to use.\n"
            "Press ESC to reset a field."
        )
        instructions.setStyleSheet("color: #a0a0c0;")
        instructions.setFont(QFont("Segoe UI", 10))
        layout.addWidget(instructions)

        layout.addSpacing(12)

        # Record toggle hotkey
        record_label = QLabel("Record Toggle:")
        record_label.setStyleSheet("color: #e0e0ff;")
        record_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(record_label)

        self.record_input = self._create_hotkey_input()
        self.record_input.clicked.connect(lambda: self._start_capture("record_toggle", self.record_input))
        layout.addWidget(self.record_input)

        layout.addSpacing(12)

        # Cancel hotkey
        cancel_label = QLabel("Cancel Recording:")
        cancel_label.setStyleSheet("color: #e0e0ff;")
        cancel_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(cancel_label)

        self.cancel_input = self._create_hotkey_input()
        self.cancel_input.clicked.connect(lambda: self._start_capture("cancel", self.cancel_input))
        layout.addWidget(self.cancel_input)

        layout.addSpacing(12)

        # Enable/Disable hotkey
        enable_label = QLabel("Enable/Disable:")
        enable_label.setStyleSheet("color: #e0e0ff;")
        enable_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(enable_label)

        self.enable_input = self._create_hotkey_input()
        self.enable_input.clicked.connect(lambda: self._start_capture("enable_disable", self.enable_input))
        layout.addWidget(self.enable_input)

        layout.addSpacing(16)

        # Reset button
        reset_btn = ModernButton("Reset to Defaults")
        reset_btn.setMaximumWidth(200)
        reset_btn.clicked.connect(self._reset_to_defaults)
        layout.addWidget(reset_btn)

        layout.addStretch()

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        button_layout.addStretch()

        cancel_btn = ModernButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = PrimaryButton("Save Hotkeys")
        save_btn.clicked.connect(self._save_hotkeys)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        # Apply styling
        self.setStyleSheet("""
            HotkeyDialog {
                background-color: #1e1e2e;
                border-radius: 8px;
            }
        """)

    def _create_hotkey_input(self) -> QLineEdit:
        """Create a hotkey input field."""
        input_field = QLineEdit()
        input_field.setReadOnly(True)
        input_field.setMinimumHeight(36)
        input_field.setFont(QFont("Segoe UI", 10))
        input_field.setPlaceholderText("Click to set hotkey")
        input_field.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d44;
                color: #00d4ff;
                border: 1px solid #404060;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border: 2px solid #00d4ff;
            }
        """)
        return input_field

    def _start_capture(self, hotkey_type: str, input_field: QLineEdit):
        """Start capturing a hotkey."""
        self.capturing = hotkey_type
        input_field.setText("Waiting for input...")
        input_field.setStyleSheet("""
            QLineEdit {
                background-color: #6366f1;
                color: #ffffff;
                border: 2px solid #00d4ff;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
        """)

        # For now, this is a placeholder. In a real implementation,
        # you would use a low-level keyboard hook like the existing one
        self.logger.info(f"Capturing hotkey for: {hotkey_type}")

    def _reset_to_defaults(self):
        """Reset hotkeys to default values."""
        self.current_hotkeys = config.DEFAULT_HOTKEYS.copy()
        self._update_displays()
        self.logger.info("Hotkeys reset to defaults")

    def _load_hotkeys(self):
        """Load current hotkey settings."""
        self.current_hotkeys = config.DEFAULT_HOTKEYS.copy()
        self._update_displays()

    def _update_displays(self):
        """Update the input field displays."""
        self.record_input.setText(self.current_hotkeys.get("record_toggle", "*"))
        self.cancel_input.setText(self.current_hotkeys.get("cancel", "-"))
        self.enable_input.setText(self.current_hotkeys.get("enable_disable", "ctrl+alt+*"))

    def _save_hotkeys(self):
        """Save hotkey settings."""
        hotkeys_data = {
            "record_toggle": self.record_input.text(),
            "cancel": self.cancel_input.text(),
            "enable_disable": self.enable_input.text(),
        }

        if self.on_hotkeys_save:
            self.on_hotkeys_save(hotkeys_data)

        self.hotkeys_changed.emit(hotkeys_data)
        self.logger.info("Hotkeys saved")
        self.accept()

    def keyPressEvent(self, event):
        """Handle key press events for hotkey capture."""
        if self.capturing:
            # Get the key sequence
            key_sequence = QKeySequence(event.key() + int(event.modifiers()))
            key_text = key_sequence.toString()

            if event.key() == Qt.Key.Key_Escape:
                # Clear the current hotkey
                if self.capturing == "record_toggle":
                    self.record_input.setText("")
                elif self.capturing == "cancel":
                    self.cancel_input.setText("")
                elif self.capturing == "enable_disable":
                    self.enable_input.setText("")
            else:
                # Update the appropriate field
                if self.capturing == "record_toggle":
                    self.record_input.setText(key_text)
                    self.current_hotkeys["record_toggle"] = key_text
                elif self.capturing == "cancel":
                    self.cancel_input.setText(key_text)
                    self.current_hotkeys["cancel"] = key_text
                elif self.capturing == "enable_disable":
                    self.enable_input.setText(key_text)
                    self.current_hotkeys["enable_disable"] = key_text

            # Reset input field styling
            self._update_displays()
            self.capturing = None
