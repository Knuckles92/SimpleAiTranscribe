"""
Main application bootstrap for Audio Recorder using modern PyQt6 UI.
This is the new entry point for the refactored application.
"""
import logging
import os
import sys
import pyperclip
import keyboard
from pathlib import Path
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtCore import QObject, pyqtSignal

from config import config
from ui_qt.app import QtApplication
from ui_qt.loading_screen_qt import ModernLoadingScreen
from ui_qt.ui_controller import UIController
from recorder import AudioRecorder
from hotkey_manager import HotkeyManager
from settings import settings_manager
from transcriber import TranscriptionBackend, LocalWhisperBackend, OpenAIBackend
from audio_processor import audio_processor


def setup_logging():
    """Setup application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler()
        ]
    )


class ApplicationController(QObject):
    """Main application controller integrating UI and logic."""

    # Qt signals for thread-safe UI updates
    transcription_completed = pyqtSignal(str)
    transcription_failed = pyqtSignal(str)
    status_update = pyqtSignal(str)
    stt_state_changed = pyqtSignal(bool)  # True = enabled, False = disabled

    def __init__(self, ui_controller: UIController):
        """Initialize the application controller."""
        super().__init__()
        self.ui_controller = ui_controller
        self.recorder = AudioRecorder()
        self.hotkey_manager: Optional[HotkeyManager] = None
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Transcription backends
        self.transcription_backends: Dict[str, TranscriptionBackend] = {}
        self.current_backend: Optional[TranscriptionBackend] = None

        # Setup components
        self._setup_transcription_backends()
        self._setup_hotkeys()
        self._setup_ui_callbacks()
        self._setup_audio_level_callback()
        self._connect_signals()

    def _setup_transcription_backends(self):
        """Initialize transcription backends."""
        logging.info("Setting up transcription backends...")

        # Local Whisper backend
        self.transcription_backends['local_whisper'] = LocalWhisperBackend()

        # OpenAI backends
        self.transcription_backends['api_whisper'] = OpenAIBackend('api_whisper')
        self.transcription_backends['api_gpt4o'] = OpenAIBackend('api_gpt4o')
        self.transcription_backends['api_gpt4o_mini'] = OpenAIBackend('api_gpt4o_mini')

        # Load saved model selection and set backend
        saved_model = settings_manager.load_model_selection()
        self.current_backend = self.transcription_backends.get(
            saved_model, self.transcription_backends['local_whisper']
        )
        logging.info(f"Using transcription backend: {saved_model}")

    def _setup_hotkeys(self):
        """Setup hotkey management."""
        logging.info("Setting up hotkeys...")
        hotkeys = settings_manager.load_hotkey_settings()
        self.hotkey_manager = HotkeyManager(hotkeys)
        self.hotkey_manager.set_callbacks(
            on_record_toggle=self.toggle_recording,
            on_cancel=self.cancel_recording,
            on_status_update=self.update_status_with_auto_hide,
            on_status_update_auto_hide=self.update_status_with_auto_hide
        )
        # Initialize the hotkey display with current settings
        self.ui_controller.update_hotkey_display(hotkeys)

    def _setup_ui_callbacks(self):
        """Setup UI event callbacks."""
        self.ui_controller.on_record_start = self.start_recording
        self.ui_controller.on_record_stop = self.stop_recording
        self.ui_controller.on_record_cancel = self.cancel_recording
        self.ui_controller.on_model_changed = self.on_model_changed
        self.ui_controller.on_hotkeys_changed = self.update_hotkeys

    def update_hotkeys(self, hotkeys: Dict[str, str]):
        """Update application hotkeys."""
        logging.info(f"Updating hotkeys: {hotkeys}")
        if self.hotkey_manager:
            self.hotkey_manager.update_hotkeys(hotkeys)
            settings_manager.save_hotkey_settings(hotkeys)
            self.ui_controller.set_status("Hotkeys updated")

    def _setup_audio_level_callback(self):
        """Setup audio level callback for waveform display."""
        def audio_level_callback(level: float):
            # Convert single level to list for compatibility
            levels = [level] * 20  # Duplicate for all bars
            self.ui_controller.update_audio_levels(levels)

        self.recorder.set_audio_level_callback(audio_level_callback)

    def _connect_signals(self):
        """Connect Qt signals to UI controller methods."""
        self.transcription_completed.connect(self._on_transcription_complete)
        self.transcription_failed.connect(self._on_transcription_error)
        self.status_update.connect(self.ui_controller.set_status)
        self.stt_state_changed.connect(self._on_stt_state_changed)

    def _on_stt_state_changed(self, enabled: bool):
        """Handle STT state change on main thread."""
        if enabled:
            self.ui_controller.overlay.show_at_cursor(self.ui_controller.overlay.STATE_STT_ENABLE)
        else:
            self.ui_controller.overlay.show_at_cursor(self.ui_controller.overlay.STATE_STT_DISABLE)

    def start_recording(self):
        """Start audio recording."""
        if self.recorder.start_recording():
            logging.info("Recording started")
            # Emit status to trigger overlay display
            self.status_update.emit("Recording...")
        else:
            self.status_update.emit("Failed to start recording")

    def stop_recording(self):
        """Stop audio recording and start transcription."""
        if not self.recorder.stop_recording():
            self.status_update.emit("Failed to stop recording")
            return

        # Emit processing status to show overlay
        self.status_update.emit("Processing...")

        # Ensure the recorder thread has flushed the post-roll before saving
        if not self.recorder.wait_for_stop_completion():
            logging.warning("Proceeding without confirmed post-roll completion; tail of recording may be short")

        # Check if we have recording data
        if not self.recorder.has_recording_data():
            logging.error("No recording data available")
            self._on_transcription_error("No audio data recorded")
            return

        # Save recording
        if not self.recorder.save_recording():
            logging.error("Failed to save recording")
            self._on_transcription_error("Failed to save audio file")
            return

        # Verify audio file
        if not os.path.exists(config.RECORDED_AUDIO_FILE):
            logging.error(f"Audio file not found: {config.RECORDED_AUDIO_FILE}")
            self._on_transcription_error("Audio file not created")
            return

        file_size = os.path.getsize(config.RECORDED_AUDIO_FILE)
        logging.info(f"Audio file size: {file_size} bytes")
        if file_size < 100:
            logging.error(f"Audio file too small: {file_size} bytes")
            self._on_transcription_error("Audio file is empty or corrupted")
            return

        # Start transcription in background
        try:
            needs_splitting, file_size_mb = audio_processor.check_file_size(
                config.RECORDED_AUDIO_FILE
            )

            if needs_splitting:
                logging.info(f"Large file ({file_size_mb:.2f} MB), using split workflow")
                self.status_update.emit(f"Processing large file ({file_size_mb:.1f} MB)...")
                self.executor.submit(self._transcribe_large_audio)
            else:
                self.executor.submit(self._transcribe_audio)

            logging.info(f"Transcription started. Duration: {self.recorder.get_recording_duration():.2f}s")

        except Exception as e:
            logging.error(f"Failed to start transcription: {e}")
            self._on_transcription_error(f"Failed to process audio: {e}")

    def toggle_recording(self):
        """Toggle between starting and stopping recording."""
        logging.info(f"Toggle recording. Current state: {self.recorder.is_recording}")
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def cancel_recording(self):
        """Cancel recording or transcription."""
        logging.info(f"Cancel called. Recording: {self.recorder.is_recording}")

        if self.recorder.is_recording:
            self.recorder.stop_recording()
            self.recorder.clear_recording_data()
            self.ui_controller.set_status("Recording cancelled")
            # Show canceling state in overlay, then hide
            self.ui_controller.overlay.set_state(self.ui_controller.overlay.STATE_CANCELING)
            logging.info("Recording cancelled")
        elif self.current_backend and self.current_backend.is_transcribing:
            self.current_backend.cancel_transcription()
            self.ui_controller.set_status("Transcription cancelled")
            # Show canceling state in overlay, then hide
            self.ui_controller.overlay.set_state(self.ui_controller.overlay.STATE_CANCELING)
            logging.info("Transcription cancelled")
        else:
            self.ui_controller.set_status("Cancelled")
            self.ui_controller.hide_overlay()

    def _transcribe_audio(self):
        """Transcribe audio in background thread."""
        try:
            self.status_update.emit("Transcribing...")
            transcribed_text = self.current_backend.transcribe(config.RECORDED_AUDIO_FILE)

            # Emit signal to update UI on main thread
            self.transcription_completed.emit(transcribed_text)

        except Exception as e:
            logging.error(f"Transcription failed: {e}")
            self.transcription_failed.emit(str(e))

    def _transcribe_large_audio(self):
        """Transcribe large audio file by splitting into chunks."""
        chunk_files = []
        try:
            def progress_callback(message):
                self.status_update.emit(message)

            chunk_files = audio_processor.split_audio_file(
                config.RECORDED_AUDIO_FILE, progress_callback
            )

            if not chunk_files:
                raise Exception("Failed to split audio file")

            # Transcribe chunks
            if hasattr(self.current_backend, 'transcribe_chunks'):
                self.status_update.emit(f"Transcribing {len(chunk_files)} chunks...")
                transcribed_text = self.current_backend.transcribe_chunks(chunk_files)
            else:
                transcriptions = []
                for i, chunk_file in enumerate(chunk_files):
                    self.status_update.emit(
                        f"Transcribing chunk {i+1}/{len(chunk_files)}..."
                    )
                    transcriptions.append(self.current_backend.transcribe(chunk_file))

                transcribed_text = audio_processor.combine_transcriptions(transcriptions)

            # Emit signal to update UI on main thread
            self.transcription_completed.emit(transcribed_text)

        except Exception as e:
            logging.error(f"Large audio transcription failed: {e}")
            self.transcription_failed.emit(str(e))
        finally:
            try:
                audio_processor.cleanup_temp_files()
            except Exception as cleanup_error:
                logging.warning(f"Failed to cleanup temp files: {cleanup_error}")

    def _on_transcription_complete(self, transcribed_text: str):
        """Handle transcription completion."""
        self.ui_controller.set_transcription(transcribed_text)
        self.ui_controller.set_status("Transcription complete!")

        # Hide overlay after completion
        self.ui_controller.hide_overlay()

        # Load settings
        settings = settings_manager.load_all_settings()
        copy_clipboard = settings.get('copy_clipboard', True)
        auto_paste = settings.get('auto_paste', True)

        # Copy to clipboard if enabled
        if copy_clipboard:
            try:
                pyperclip.copy(transcribed_text)
                logging.info("Transcription copied to clipboard")
            except Exception as e:
                logging.error(f"Failed to copy to clipboard: {e}")

        # Auto-paste if enabled
        if auto_paste:
            try:
                keyboard.send('ctrl+v')
                logging.info("Transcription auto-pasted")
                self.ui_controller.set_status("Ready (Pasted)")
            except Exception as e:
                logging.error(f"Failed to auto-paste: {e}")
                self.ui_controller.set_status("Transcription complete (paste failed)")
        else:
            self.ui_controller.set_status("Ready")

    def _on_transcription_error(self, error_message: str):
        """Handle transcription error."""
        self.ui_controller.set_status(f"Error: {error_message}")
        self.ui_controller.set_transcription(f"Error: {error_message}")

        # Hide overlay on error
        self.ui_controller.hide_overlay()

    def on_model_changed(self, model_name: str):
        """Handle model selection change."""
        # Convert display name to internal value
        model_value = config.MODEL_VALUE_MAP.get(model_name)
        if model_value and model_value in self.transcription_backends:
            self.current_backend = self.transcription_backends[model_value]
            settings_manager.save_model_selection(model_value)
            logging.info(f"Switched to model: {model_value}")

    def update_status_with_auto_hide(self, status: str):
        """Update status with auto-hide after delay."""
        # Use signals for thread-safe UI updates (called from hotkey thread)
        self.status_update.emit(status)

        # Show overlay for STT enable/disable states
        if status == "STT Enabled":
            self.stt_state_changed.emit(True)
        elif status == "STT Disabled":
            self.stt_state_changed.emit(False)

    def cleanup(self):
        """Cleanup resources."""
        try:
            if self.hotkey_manager:
                self.hotkey_manager.cleanup()
        except Exception as e:
            logging.debug(f"Error during hotkey cleanup: {e}")
        
        try:
            if self.recorder:
                self.recorder.cleanup()
        except Exception as e:
            logging.debug(f"Error during recorder cleanup: {e}")
        
        try:
            self.executor.shutdown(wait=False)
        except Exception as e:
            logging.debug(f"Error during executor shutdown: {e}")
        
        try:
            self.ui_controller.cleanup()
        except Exception as e:
            logging.debug(f"Error during UI controller cleanup: {e}")
        logging.info("Application controller cleaned up")


def main():
    """Main application entry point with modern PyQt6 UI."""
    # Setup logging
    setup_logging()
    logging.info("=" * 60)
    logging.info("Starting Audio Recorder with Modern PyQt6 UI")
    logging.info("=" * 60)

    # Create Qt application
    qt_app = QtApplication()

    loading_screen = None
    ui_controller = None
    app_controller = None

    try:
        # Show loading screen
        loading_screen = ModernLoadingScreen()
        loading_screen.show()

        # Simulate initialization steps
        loading_screen.update_status("Initializing components...")
        loading_screen.update_progress("Loading theme...")
        loading_screen.repaint()

        # Give Qt time to render
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.processEvents()

        # Create UI controller
        loading_screen.update_status("Creating interface...")
        loading_screen.update_progress("Setting up windows...")
        QCoreApplication.processEvents()

        ui_controller = UIController()

        # Create application controller (integrates logic with UI)
        loading_screen.update_status("Initializing audio system...")
        loading_screen.update_progress("Loading transcription models...")
        QCoreApplication.processEvents()

        app_controller = ApplicationController(ui_controller)

        # Hide loading screen and show main window
        loading_screen.destroy()
        loading_screen = None

        # Show main window
        ui_controller.show_main_window()

        logging.info("Application initialization complete")
        logging.info("Starting event loop")

        # Run the application
        return qt_app.run(ui_controller.main_window)

    except Exception as e:
        logging.exception("Application startup failed")
        # Re-raise after logging
        raise

    finally:
        # Cleanup
        try:
            if loading_screen is not None:
                loading_screen.destroy()
        except Exception as e:
            logging.exception("Failed to cleanup loading screen")

        try:
            if app_controller is not None:
                app_controller.cleanup()
            elif ui_controller is not None:
                ui_controller.cleanup()
        except Exception as e:
            logging.exception("Failed to cleanup controllers")

        logging.info("=" * 60)
        logging.info("Application shutdown complete")
        logging.info("=" * 60)


if __name__ == "__main__":
    sys.exit(main())
