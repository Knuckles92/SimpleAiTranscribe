"""
Audio recording functionality for the Audio Recorder application.
"""
import pyaudio
import wave
import threading
import logging
from typing import List, Optional
from config import config


class AudioRecorder:
    """Handles audio recording using PyAudio."""
    
    def __init__(self):
        """Initialize the audio recorder."""
        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        self.frames: List[bytes] = []
        self.stream: Optional[pyaudio.Stream] = None
        self.recording_thread: Optional[threading.Thread] = None
        
        # Audio settings from config
        self.chunk = config.CHUNK_SIZE
        self.format = getattr(pyaudio, config.AUDIO_FORMAT)
        self.channels = config.CHANNELS
        self.rate = config.SAMPLE_RATE
        
        logging.info("Audio recorder initialized")
    
    def start_recording(self) -> bool:
        """Start audio recording.
        
        Returns:
            True if recording started successfully, False otherwise.
        """
        if self.is_recording:
            logging.warning("Recording already in progress")
            return False
        
        try:
            self.frames = []
            self.is_recording = True
            
            # Start recording in a separate thread
            self.recording_thread = threading.Thread(target=self._record_audio, daemon=True)
            self.recording_thread.start()
            
            logging.info("Recording started")
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
            self.is_recording = False
            
            # Wait for recording thread to finish
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=2.0)
            
            logging.info("Recording stopped")
            return True
            
        except Exception as e:
            logging.error(f"Failed to stop recording: {e}")
            return False
    
    def _record_audio(self):
        """Record audio data in a separate thread until recording is stopped."""
        stream = None
        try:
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            while self.is_recording:
                try:
                    data = stream.read(self.chunk)
                    self.frames.append(data)
                except Exception as e:
                    logging.error(f"Error reading audio data: {e}")
                    break
                    
        except Exception as e:
            logging.error(f"Error opening audio stream: {e}")
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception as e:
                    logging.error(f"Error closing audio stream: {e}")
    
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
        
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.frames))
            
            logging.info(f"Audio saved to {filename}")
            return True
            
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
            
            if self.audio:
                self.audio.terminate()
                
            logging.info("Audio recorder cleaned up")
            
        except Exception as e:
            logging.error(f"Error during audio recorder cleanup: {e}") 