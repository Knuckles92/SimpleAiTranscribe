"""
UI Controller for PyQt6 Application.
Manages the main window, overlay, and dialogs.
Bridges between UI and application logic.
"""
import logging
from typing import Optional, Callable, List
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import QMessageBox

from ui_qt.main_window_qt import ModernMainWindow
from ui_qt.overlay_qt import ModernWaveformOverlay
from ui_qt.system_tray_qt import SystemTrayManager
from ui_qt.dialogs.settings_dialog import SettingsDialog
from ui_qt.dialogs.hotkey_dialog import HotkeyDialog


class UIController(QObject):
    """Controls the UI components and manages their interactions."""

    # Signals
    record_started = pyqtSignal()
    record_stopped = pyqtSignal()
    record_canceled = pyqtSignal()
    model_changed = pyqtSignal(str)
    transcription_received = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    audio_levels_updated = pyqtSignal(list)

    def __init__(self):
        """Initialize UI controller."""
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Create UI components
        self.main_window = ModernMainWindow()
        self.overlay = ModernWaveformOverlay()
        self.tray_manager = SystemTrayManager(self.main_window)

        # State
        self.is_recording = False
        self.audio_levels: List[float] = [0.0] * 20

        # Callbacks for external handlers
        self.on_record_start: Optional[Callable] = None
        self.on_record_stop: Optional[Callable] = None
        self.on_record_cancel: Optional[Callable] = None
        self.on_model_changed: Optional[Callable] = None
        self.on_hotkeys_changed: Optional[Callable] = None

        self._setup_connections()

    def _setup_connections(self):
        """Setup signal connections between UI components."""
        # Main window signals
        self.main_window.record_toggled.connect(self._on_record_toggled)
        self.main_window.model_changed.connect(self._on_model_changed)
        self.main_window.settings_requested.connect(self.open_settings_dialog)
        self.main_window.hotkeys_requested.connect(self.open_hotkey_dialog)
        self.main_window.overlay_toggle_requested.connect(self.toggle_overlay)
        self.main_window.about_requested.connect(self.show_about_dialog)

        # Tray manager signals
        self.tray_manager.show_requested.connect(self._on_tray_show)
        self.tray_manager.hide_requested.connect(self._on_tray_hide)
        self.tray_manager.exit_requested.connect(self._on_tray_exit)
        self.tray_manager.toggle_recording.connect(self._on_tray_toggle_recording)

        # Overlay signals
        self.overlay.state_changed.connect(self._on_overlay_state_changed)

        # Internal signals
        self.record_started.connect(self._on_internal_record_started)
        self.record_stopped.connect(self._on_internal_record_stopped)
        self.transcription_received.connect(self._on_internal_transcription)
        self.status_changed.connect(self._on_internal_status_changed)
        self.audio_levels_updated.connect(self._on_internal_audio_levels)

    def _on_record_toggled(self, is_recording: bool):
        """Handle record button toggle from main window."""
        if is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def _on_model_changed(self, model_name: str):
        """Handle model selection change."""
        self.logger.info(f"Model changed to: {model_name}")
        if self.on_model_changed:
            self.on_model_changed(model_name)
        self.model_changed.emit(model_name)

    def _on_tray_show(self):
        """Handle show from tray."""
        self.main_window.showNormal()
        self.logger.debug("Window shown from tray")

    def _on_tray_hide(self):
        """Handle hide from tray."""
        self.main_window.hide()
        self.logger.debug("Window hidden to tray")

    def _on_tray_exit(self):
        """Handle exit from tray."""
        self.logger.info("Exit requested from tray")

    def _on_tray_toggle_recording(self):
        """Handle toggle recording from tray."""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def _on_overlay_state_changed(self, state: str):
        """Handle overlay state change."""
        self.logger.debug(f"Overlay state changed to: {state}")

    def _on_internal_record_started(self):
        """Handle internal record started signal."""
        self.tray_manager.set_recording(True)
        # Show overlay with recording state if not already visible
        if not self.overlay.isVisible():
            self.overlay.show_at_cursor(self.overlay.STATE_RECORDING)
        else:
            self.overlay.set_state(self.overlay.STATE_RECORDING)

    def _on_internal_record_stopped(self):
        """Handle internal record stopped signal."""
        self.tray_manager.set_recording(False)
        # Show overlay with processing state if not already visible
        if not self.overlay.isVisible():
            self.overlay.show_at_cursor(self.overlay.STATE_PROCESSING)
        else:
            self.overlay.set_state(self.overlay.STATE_PROCESSING)

    def _on_internal_transcription(self, text: str):
        """Handle transcription received."""
        self.main_window.set_transcription(text)
        # Hide overlay when transcription is complete
        self.hide_overlay()

    def _on_internal_status_changed(self, status: str):
        """Handle status change."""
        self.main_window.set_status(status)

    def _on_internal_audio_levels(self, levels: List[float]):
        """Handle audio levels update."""
        self.overlay.update_audio_levels(levels)

    def start_recording(self):
        """Start recording."""
        self.is_recording = True
        self.logger.info("Recording started")

        if self.on_record_start:
            self.on_record_start()

        self.record_started.emit()

    def stop_recording(self):
        """Stop recording."""
        self.is_recording = False
        self.logger.info("Recording stopped")

        if self.on_record_stop:
            self.on_record_stop()

        self.record_stopped.emit()

    def cancel_recording(self):
        """Cancel recording."""
        self.is_recording = False
        self.logger.info("Recording canceled")

        if self.on_record_cancel:
            self.on_record_cancel()

        self.record_canceled.emit()
        self.main_window.clear_transcription()
        self.overlay.set_state(self.overlay.STATE_CANCELING)

    def set_transcription(self, text: str):
        """Set transcription text."""
        self.transcription_received.emit(text)

    def set_status(self, status: str):
        """Set status message and update overlay state based on status."""
        self.status_changed.emit(status)

        # Map status messages to overlay states (similar to old Tkinter app)
        # This ensures overlay visibility is automatically managed
        if "Recording" in status:
            if not self.overlay.isVisible():
                self.overlay.show_at_cursor(self.overlay.STATE_RECORDING)
            else:
                self.overlay.set_state(self.overlay.STATE_RECORDING)
        elif "Processing" in status:
            if not self.overlay.isVisible():
                self.overlay.show_at_cursor(self.overlay.STATE_PROCESSING)
            else:
                self.overlay.set_state(self.overlay.STATE_PROCESSING)
        elif "Transcribing" in status:
            if not self.overlay.isVisible():
                self.overlay.show_at_cursor(self.overlay.STATE_TRANSCRIBING)
            else:
                self.overlay.set_state(self.overlay.STATE_TRANSCRIBING)
        elif "STT Enabled" in status:
            if not self.overlay.isVisible():
                self.overlay.show_at_cursor(self.overlay.STATE_STT_ENABLE)
            else:
                self.overlay.set_state(self.overlay.STATE_STT_ENABLE)
        elif "STT Disabled" in status:
            if not self.overlay.isVisible():
                self.overlay.show_at_cursor(self.overlay.STATE_STT_DISABLE)
            else:
                self.overlay.set_state(self.overlay.STATE_STT_DISABLE)
        elif any(keyword in status.lower() for keyword in ["complete", "ready", "failed", "error"]):
            # Hide overlay when task is complete or failed
            self.hide_overlay()

    def update_audio_levels(self, levels: List[float]):
        """Update audio level display."""
        self.audio_levels = levels
        self.audio_levels_updated.emit(levels)

    def show_overlay(self):
        """Show the overlay."""
        self.overlay.show_at_cursor()

    def hide_overlay(self):
        """Hide the overlay."""
        self.overlay.hide()

    def toggle_overlay(self):
        """Toggle the overlay visibility."""
        if self.overlay.isVisible():
            self.hide_overlay()
        else:
            self.show_overlay()

    def show_main_window(self):
        """Show the main window."""
        self.main_window.showNormal()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def hide_main_window(self):
        """Hide the main window."""
        self.main_window.hide()

    def open_settings_dialog(self):
        """Open the settings dialog."""
        dialog = SettingsDialog(self.main_window)
        # Connect hotkey button in settings to hotkey dialog
        dialog.tabs.setCurrentIndex(0) # Default to general
        dialog.exec()

    def open_hotkey_dialog(self):
        """Open the hotkey configuration dialog."""
        dialog = HotkeyDialog(self.main_window)
        
        def on_hotkeys_save(hotkeys):
            if self.on_hotkeys_changed:
                self.on_hotkeys_changed(hotkeys)
                
        dialog.on_hotkeys_save = on_hotkeys_save
        dialog.exec()

    def show_about_dialog(self):
        """Show the about dialog."""
        QMessageBox.about(
            self.main_window,
            "About Audio Recorder",
            "Audio Recorder with Whisper Integration\n\n"
            "A modern PyQt6 interface for local and API-based transcription.\n\n"
            "© 2024"
        )

    def get_model_value(self) -> str:
        """Get the selected model value."""
        return self.main_window.get_model_value()

    def cleanup(self):
        """Cleanup resources."""
        self.overlay.close()
        self.main_window.close()
        self.logger.info("UI Controller cleaned up")

