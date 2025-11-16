"""
Audio recording functionality for the Audio Recorder application.
"""
import sounddevice as sd
import wave
import threading
import logging
import numpy as np
import time

from typing import List, Optional, Callable
from config import config


class AudioRecorder:
    """Handles audio recording using SoundDevice."""

    def __init__(self):
        """Initialize the audio recorder."""
        self.is_recording = False
        self.frames: List[bytes] = []
        self.stream: Optional[sd.InputStream] = None
        self.recording_thread: Optional[threading.Thread] = None
        self._stop_requested: bool = False
        self._post_roll_until: float = 0.0

        # Audio settings from config
        self.chunk = config.CHUNK_SIZE
        self.dtype = config.AUDIO_FORMAT
        self.channels = config.CHANNELS
        self.rate = config.SAMPLE_RATE

        # Audio level callback
        self.audio_level_callback: Optional[Callable[[float], None]] = None

        # Audio level calculation
        self.current_level = 0.0
        self.level_smoothing = config.WAVEFORM_LEVEL_SMOOTHING  # Smoothing factor for level changes

        # Thread safety for callback
        self._callback_lock = threading.Lock()

        logging.info("Audio recorder initialized")

    def set_audio_level_callback(self, callback: Callable[[float], None]):
        """Set callback function for real-time audio level updates.

        Args:
            callback: Function that will be called with audio level (0.0 to 1.0)
        """
        self.audio_level_callback = callback

    def start_recording(self) -> bool:
        """Start audio recording.

        Returns:
            True if recording started successfully, False otherwise.
        """
        if self.is_recording:
            logging.warning("Recording already in progress")
            return False

        try:
            # Clear any old recording data
            self.frames = []
            logging.info(f"Cleared recording frames. Old frame count: {len(self.frames)}")

            # Delete old audio file if it exists
            import os
            if os.path.exists(config.RECORDED_AUDIO_FILE):
                try:
                    os.remove(config.RECORDED_AUDIO_FILE)
                    logging.info(f"Deleted old audio file: {config.RECORDED_AUDIO_FILE}")
                except Exception as e:
                    logging.warning(f"Could not delete old audio file: {e}")

            self.is_recording = True
            self._stop_requested = False
            self._post_roll_until = 0.0

            # Start recording in a separate thread
            self.recording_thread = threading.Thread(target=self._record_audio, daemon=True)
            self.recording_thread.start()

            logging.info("Recording started - frames cleared, old file removed")
            return True

        except Exception as e:
            logging.error(f"Failed to start recording: {e}")
            self.is_recording = False
            return False

    def stop_recording(self) -> bool:
        """Stop audio recording.

        Returns:
            True if recording stopped successfully, False otherwise.
        """
        if not self.is_recording:
            logging.warning("No recording in progress")
            return False

        try:
            # Request stop and allow a short post-roll to capture trailing speech
            self._stop_requested = True
            self._post_roll_until = time.time() + (config.POST_ROLL_MS / 1000.0)

            # Don't wait for recording thread to finish - let post-roll happen in background
            # The thread will naturally finish after the post-roll period
            logging.info("Recording stop requested, post-roll continuing in background")
            return True

        except Exception as e:
            logging.error(f"Failed to stop recording: {e}")
            return False

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Callback function for sounddevice to process incoming audio data.

        Args:
            indata: Input audio data as numpy array
            frames: Number of frames
            time_info: Time information
            status: Stream status
        """
        if status:
            logging.warning(f"Audio stream status: {status}")

        try:
            # Thread-safe frame appending
            with self._callback_lock:
                # Store as bytes for WAV file compatibility
                self.frames.append(indata.copy().tobytes())

                # Calculate audio level for waveform display
                if self.audio_level_callback:
                    self._calculate_and_report_level(indata.copy())

        except Exception as e:
            logging.error(f"Error in audio callback: {e}")

    def _record_audio(self):
        """Record audio data in a separate thread until recording is stopped."""
        try:
            # Create input stream with callback
            self.stream = sd.InputStream(
                samplerate=self.rate,
                channels=self.channels,
                dtype=self.dtype,
                blocksize=self.chunk,
                callback=self._audio_callback
            )

            # Start the stream
            self.stream.start()
            logging.info("Audio stream started")

            # Wait until stop is requested and post-roll window has elapsed
            while True:
                time.sleep(0.01)  # Small sleep to avoid busy-waiting

                # Evaluate exit condition
                if self._stop_requested and time.time() >= self._post_roll_until:
                    break

        except Exception as e:
            logging.error(f"Error opening audio stream: {e}")
        finally:
            if self.stream:
                try:
                    self.stream.stop()
                    self.stream.close()
                    logging.info("Audio stream stopped and closed")
                except Exception as e:
                    logging.error(f"Error closing audio stream: {e}")
            # Mark not recording and clear internal flags
            self.is_recording = False
            self._stop_requested = False
            self._post_roll_until = 0.0

    def _calculate_and_report_level(self, audio_data: np.ndarray):
        """Calculate audio level from numpy audio data and report it via callback.

        Args:
            audio_data: Audio data as numpy array
        """
        try:
            # Calculate RMS level
            if len(audio_data) > 0:
                # Normalize to 0.0-1.0 range
                if self.dtype == np.int16:
                    # For 16-bit audio, max value is 32767
                    rms_level = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2)) / 32767.0
                elif self.dtype == np.float32:
                    # For float32, assume range is -1.0 to 1.0
                    rms_level = np.sqrt(np.mean(audio_data ** 2))
                else:
                    return  # Unsupported format

                # Apply smoothing
                self.current_level = (
                    self.level_smoothing * self.current_level +
                    (1.0 - self.level_smoothing) * rms_level
                )

                # Clamp to valid range
                self.current_level = max(0.0, min(1.0, self.current_level))

                # Call the callback with the calculated level
                if self.audio_level_callback:
                    self.audio_level_callback(self.current_level)

        except Exception as e:
            logging.debug(f"Error calculating audio level: {e}")

    def save_recording(self, filename: str = None) -> bool:
        """Save the recorded audio frames to a WAV file.

        Args:
            filename: Output filename. Uses config default if None.

        Returns:
            True if saved successfully, False otherwise.
        """
        if not self.frames:
            logging.warning("No audio data to save")
            return False

        filename = filename or config.RECORDED_AUDIO_FILE
        frame_count = len(self.frames)
        total_bytes = sum(len(frame) for frame in self.frames)

        try:
            # Create a temporary file first, then rename for atomic operation
            import tempfile
            import os
            temp_fd, temp_path = tempfile.mkstemp(suffix='.wav', dir=os.path.dirname(filename))

            try:
                with os.fdopen(temp_fd, 'wb') as temp_file:
                    with wave.open(temp_file, 'wb') as wf:
                        wf.setnchannels(self.channels)
                        # Get sample width from numpy dtype
                        wf.setsampwidth(np.dtype(self.dtype).itemsize)
                        wf.setframerate(self.rate)
                        wf.writeframes(b''.join(self.frames))

                # Atomically replace the old file
                if os.path.exists(filename):
                    os.remove(filename)
                os.rename(temp_path, filename)

                import time
                logging.info(f"Audio saved to {filename} at {time.strftime('%Y-%m-%d %H:%M:%S')} - {frame_count} frames, {total_bytes} bytes, {self.get_recording_duration():.2f}s")
                return True

            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise

        except Exception as e:
            logging.error(f"Failed to save audio to {filename}: {e}")
            return False

    def get_recording_duration(self) -> float:
        """Get the duration of the current recording in seconds.

        Returns:
            Duration in seconds, or 0 if no recording data.
        """
        if not self.frames:
            return 0.0

        total_frames = len(self.frames) * self.chunk
        return total_frames / self.rate

    def has_recording_data(self) -> bool:
        """Check if there is recorded audio data available.

        Returns:
            True if recording data is available, False otherwise.
        """
        return bool(self.frames)

    def clear_recording_data(self):
        """Clear the recorded audio data."""
        self.frames = []
        logging.info("Recording data cleared")

    def cleanup(self):
        """Clean up audio resources."""
        try:
            if self.is_recording:
                self.stop_recording()

            # SoundDevice doesn't require explicit termination like PyAudio
            logging.info("Audio recorder cleaned up")

        except Exception as e:
            logging.error(f"Error during audio recorder cleanup: {e}")
