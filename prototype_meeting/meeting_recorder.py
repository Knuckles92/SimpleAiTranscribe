"""
Meeting-specific audio recording functionality that extends the base AudioRecorder.
Designed for longer recording sessions with pause/resume, auto-save, and session management.
"""
import pyaudio
import wave
import threading
import logging
import numpy as np
import time
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Callable, Dict, Any

# Import the base AudioRecorder and meeting configuration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from recorder import AudioRecorder
from prototype_meeting.config_meeting import meeting_config


class MeetingSessionInfo:
    """Container for meeting session information and statistics."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.total_duration = 0.0
        self.recording_duration = 0.0
        self.pause_count = 0
        self.pause_times: List[datetime] = []
        self.resume_times: List[datetime] = []
        self.auto_save_count = 0
        self.last_auto_save: Optional[datetime] = None
        self.audio_file_path: Optional[str] = None
        self.metadata_file_path: Optional[str] = None
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive session statistics."""
        now = datetime.now()
        total_time = (self.end_time or now) - self.start_time
        
        # Calculate pause time
        total_pause_time = timedelta()
        for i, pause_time in enumerate(self.pause_times):
            resume_time = self.resume_times[i] if i < len(self.resume_times) else now
            total_pause_time += resume_time - pause_time
        
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_session_time': total_time.total_seconds(),
            'recording_duration': self.recording_duration,
            'pause_count': self.pause_count,
            'total_pause_time': total_pause_time.total_seconds(),
            'auto_save_count': self.auto_save_count,
            'last_auto_save': self.last_auto_save.isoformat() if self.last_auto_save else None,
            'audio_file_path': self.audio_file_path,
            'metadata_file_path': self.metadata_file_path,
            'is_completed': self.end_time is not None
        }


class MeetingRecorder(AudioRecorder):
    """
    Extended AudioRecorder for longer meeting sessions with enhanced features:
    - No file size limitations
    - Pause/resume functionality
    - Persistent file storage
    - Auto-save capability
    - Session state tracking
    - Meeting-specific settings
    """
    
    def __init__(self):
        """Initialize the meeting recorder with meeting-specific settings."""
        # Don't call super().__init__() yet, we need to override settings first
        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        self.is_paused = False
        self.frames: List[bytes] = []
        self.stream: Optional[pyaudio.Stream] = None
        self.recording_thread: Optional[threading.Thread] = None
        self._stop_requested: bool = False
        self._post_roll_until: float = 0.0
        
        # Meeting-specific audio settings
        self.chunk = meeting_config.MEETING_CHUNK_SIZE
        self.format = pyaudio.paInt16  # Fixed format for consistency
        self.channels = meeting_config.MEETING_CHANNELS
        self.rate = meeting_config.MEETING_SAMPLE_RATE
        
        # Audio level callback and calculation (from parent)
        self.audio_level_callback: Optional[Callable[[float], None]] = None
        self.current_level = 0.0
        self.level_smoothing = 0.8  # Default smoothing for meetings
        
        # Meeting-specific properties
        self.session_info: Optional[MeetingSessionInfo] = None
        self.auto_save_thread: Optional[threading.Thread] = None
        self._auto_save_stop_event = threading.Event()
        self.pause_lock = threading.Lock()
        self.last_frame_count_at_save = 0
        self._completion_callback: Optional[Callable[[], None]] = None
        
        # Ensure meetings directory exists
        meeting_config.ensure_meetings_directory()
        
        logging.info("Meeting recorder initialized with meeting-specific settings")
    
    def start_meeting_recording(self, session_id: str = None) -> bool:
        """
        Start a meeting recording with session-based filename.
        
        Args:
            session_id: Optional session identifier. If None, generates timestamp-based ID.
            
        Returns:
            True if recording started successfully, False otherwise.
        """
        if self.is_recording:
            logging.warning("Meeting recording already in progress")
            return False
        
        try:
            # Generate session ID if not provided
            if session_id is None:
                session_id = meeting_config.get_meeting_timestamp()
            
            # Initialize session info
            self.session_info = MeetingSessionInfo(session_id)
            
            # Set up file paths using meeting config
            self.session_info.audio_file_path = meeting_config.get_meeting_audio_path(session_id)
            self.session_info.metadata_file_path = meeting_config.get_meeting_metadata_path(session_id)
            
            # Clear any old recording data (but don't delete files)
            self.frames = []
            self.last_frame_count_at_save = 0
            
            # Start recording
            self.is_recording = True
            self.is_paused = False
            self._stop_requested = False
            self._post_roll_until = 0.0
            
            # Start recording in a separate thread
            self.recording_thread = threading.Thread(target=self._record_meeting_audio, daemon=True)
            self.recording_thread.start()
            
            # Start auto-save thread
            self._auto_save_stop_event.clear()
            self.auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
            self.auto_save_thread.start()
            
            logging.info(f"Meeting recording started - Session ID: {session_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to start meeting recording: {e}")
            self.is_recording = False
            self.session_info = None
            return False
    
    def pause_recording(self) -> bool:
        """
        Pause the current meeting recording.
        
        Returns:
            True if successfully paused, False otherwise.
        """
        if not self.is_recording or self.is_paused:
            logging.warning("Cannot pause - not recording or already paused")
            return False
        
        try:
            with self.pause_lock:
                self.is_paused = True
                if self.session_info:
                    self.session_info.pause_times.append(datetime.now())
                    self.session_info.pause_count += 1
                    
            logging.info("Meeting recording paused")
            return True
            
        except Exception as e:
            logging.error(f"Failed to pause recording: {e}")
            return False
    
    def resume_recording(self) -> bool:
        """
        Resume a paused meeting recording.
        
        Returns:
            True if successfully resumed, False otherwise.
        """
        if not self.is_recording or not self.is_paused:
            logging.warning("Cannot resume - not recording or not paused")
            return False
        
        try:
            with self.pause_lock:
                self.is_paused = False
                if self.session_info:
                    self.session_info.resume_times.append(datetime.now())
                    
            logging.info("Meeting recording resumed")
            return True
            
        except Exception as e:
            logging.error(f"Failed to resume recording: {e}")
            return False
    
    def stop_meeting_recording(self, completion_callback: Optional[Callable[[], None]] = None) -> bool:
        """
        Stop the meeting recording and save with metadata.
        
        Args:
            completion_callback: Optional callback to invoke after file is saved.
            
        Returns:
            True if recording stopped and saved successfully, False otherwise.
        """
        if not self.is_recording:
            logging.warning("No meeting recording in progress")
            return False
        
        try:
            # Store the completion callback
            self._completion_callback = completion_callback
            
            # Request stop with enhanced post-roll
            self._stop_requested = True
            # Use MEETING_POST_ROLL_MS instead of POST_ROLL_MS
            post_roll_ms = getattr(meeting_config, 'POST_ROLL_MEETING_MS', 3000)
            self._post_roll_until = time.time() + (post_roll_ms / 1000.0)
            
            # Stop auto-save thread
            if self.auto_save_thread and self.auto_save_thread.is_alive():
                self._auto_save_stop_event.set()
                self.auto_save_thread.join(timeout=2.0)
            
            # Wait a moment for post-roll to complete, then save
            threading.Timer(post_roll_ms / 1000.0 + 0.5, self._finalize_meeting_recording).start()
            
            logging.info("Meeting recording stop requested, post-roll and finalization in progress")
            return True
            
        except Exception as e:
            logging.error(f"Failed to stop meeting recording: {e}")
            return False
    
    def _finalize_meeting_recording(self):
        """Finalize the meeting recording by saving audio and metadata."""
        try:
            if self.session_info:
                self.session_info.end_time = datetime.now()
                self.session_info.recording_duration = self.get_recording_duration()
                
                # Save the final audio file
                if self.save_meeting_recording():
                    # Save session metadata
                    self._save_session_metadata()
                    logging.info(f"Meeting recording finalized - Session: {self.session_info.session_id}")
                    
                    # Invoke completion callback if provided
                    if hasattr(self, '_completion_callback') and self._completion_callback:
                        try:
                            self._completion_callback()
                        except Exception as callback_error:
                            logging.error(f"Error in completion callback: {callback_error}")
                        finally:
                            self._completion_callback = None
                else:
                    logging.error("Failed to save final meeting recording")
                    
        except Exception as e:
            logging.error(f"Error finalizing meeting recording: {e}")
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive session information and statistics.
        
        Returns:
            Dictionary with session statistics, or None if no active session.
        """
        if not self.session_info:
            return None
        
        stats = self.session_info.get_statistics()
        # Add real-time recording duration
        stats['current_recording_duration'] = self.get_recording_duration()
        stats['is_paused'] = self.is_paused
        stats['frame_count'] = len(self.frames)
        
        return stats
    
    def auto_save_checkpoint(self) -> bool:
        """
        Manually trigger an auto-save checkpoint.
        
        Returns:
            True if checkpoint saved successfully, False otherwise.
        """
        if not self.is_recording or not self.session_info:
            logging.warning("Cannot save checkpoint - no active recording session")
            return False
        
        return self._perform_auto_save()
    
    def save_meeting_recording(self, filename: str = None) -> bool:
        """
        Save the recorded meeting audio to a WAV file (persistent storage).
        
        Args:
            filename: Optional custom filename. Uses session-based path if None.
            
        Returns:
            True if saved successfully, False otherwise.
        """
        if not self.frames:
            logging.warning("No meeting audio data to save")
            return False
        
        # Use session-based filename or provided filename
        if filename is None and self.session_info:
            filename = self.session_info.audio_file_path
        elif filename is None:
            # Fallback to timestamp-based filename
            timestamp = meeting_config.get_meeting_timestamp()
            filename = meeting_config.get_meeting_audio_path(timestamp)
        
        frame_count = len(self.frames)
        total_bytes = sum(len(frame) for frame in self.frames)
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Create a temporary file first, then rename for atomic operation
            import tempfile
            temp_fd, temp_path = tempfile.mkstemp(suffix='.wav', dir=os.path.dirname(filename))
            
            try:
                with os.fdopen(temp_fd, 'wb') as temp_file:
                    with wave.open(temp_file, 'wb') as wf:
                        wf.setnchannels(self.channels)
                        wf.setsampwidth(self.audio.get_sample_size(self.format))
                        wf.setframerate(self.rate)
                        wf.writeframes(b''.join(self.frames))
                
                # Atomically replace the old file (persistent storage - don't delete existing)
                if os.path.exists(filename):
                    # For meetings, we append or create versioned files rather than overwrite
                    base, ext = os.path.splitext(filename)
                    backup_filename = f"{base}_backup_{int(time.time())}{ext}"
                    os.rename(filename, backup_filename)
                    logging.info(f"Existing meeting file backed up to: {backup_filename}")
                
                os.rename(temp_path, filename)
                
                duration = self.get_recording_duration()
                logging.info(f"Meeting audio saved to {filename} at {time.strftime('%Y-%m-%d %H:%M:%S')} - {frame_count} frames, {total_bytes} bytes, {duration:.2f}s")
                
                # Update last save tracking
                self.last_frame_count_at_save = frame_count
                
                return True
                
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
            
        except Exception as e:
            logging.error(f"Failed to save meeting audio to {filename}: {e}")
            return False
    
    def _record_meeting_audio(self):
        """Record meeting audio data with pause/resume support."""
        stream = None
        try:
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            # Continue reading until stop is requested and post-roll window has elapsed
            while True:
                try:
                    # Respect pause state
                    if self.is_paused:
                        time.sleep(0.1)  # Small sleep to prevent busy waiting
                        continue
                    
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    self.frames.append(data)
                    
                    # Calculate audio level for waveform display
                    if self.audio_level_callback:
                        self._calculate_and_report_level(data)
                        
                except Exception as e:
                    logging.error(f"Error reading meeting audio data: {e}")
                    break
                
                # Evaluate exit condition after capturing this chunk
                if self._stop_requested and time.time() >= self._post_roll_until:
                    break
            
        except Exception as e:
            logging.error(f"Error opening meeting audio stream: {e}")
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception as e:
                    logging.error(f"Error closing meeting audio stream: {e}")
            # Mark not recording and clear internal flags
            self.is_recording = False
            self.is_paused = False
            self._stop_requested = False
            self._post_roll_until = 0.0
    
    def _auto_save_loop(self):
        """Auto-save loop that runs in a separate thread."""
        save_interval = meeting_config.AUTO_SAVE_INTERVAL_MINUTES * 60  # Convert to seconds
        
        while not self._auto_save_stop_event.wait(save_interval):
            if self.is_recording and not self.is_paused:
                self._perform_auto_save()
    
    def _perform_auto_save(self) -> bool:
        """Perform an auto-save operation."""
        try:
            # Only save if we have new data since last save
            current_frame_count = len(self.frames)
            if current_frame_count <= self.last_frame_count_at_save:
                logging.debug("No new audio data for auto-save")
                return True
            
            # Save current recording state
            if self.save_meeting_recording():
                if self.session_info:
                    self.session_info.auto_save_count += 1
                    self.session_info.last_auto_save = datetime.now()
                logging.info(f"Auto-save completed - {current_frame_count} frames saved")
                return True
            else:
                logging.warning("Auto-save failed")
                return False
                
        except Exception as e:
            logging.error(f"Error during auto-save: {e}")
            return False
    
    def _save_session_metadata(self):
        """Save session metadata to JSON file."""
        if not self.session_info:
            return
        
        try:
            metadata = self.session_info.get_statistics()
            
            # Add technical recording details
            metadata.update({
                'recording_settings': {
                    'chunk_size': self.chunk,
                    'sample_rate': self.rate,
                    'channels': self.channels,
                    'format': 'paInt16',
                    'meeting_config_version': '1.0'
                },
                'file_info': {
                    'frame_count': len(self.frames),
                    'total_bytes': sum(len(frame) for frame in self.frames),
                    'file_size_mb': os.path.getsize(self.session_info.audio_file_path) / (1024 * 1024) if os.path.exists(self.session_info.audio_file_path) else 0
                }
            })
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.session_info.metadata_file_path), exist_ok=True)
            
            with open(self.session_info.metadata_file_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Session metadata saved to: {self.session_info.metadata_file_path}")
            
        except Exception as e:
            logging.error(f"Failed to save session metadata: {e}")
    
    def get_recording_duration(self) -> float:
        """
        Get the duration of the current meeting recording in seconds.
        
        Returns:
            Duration in seconds, or 0 if no recording data.
        """
        if not self.frames:
            return 0.0
        
        total_frames = len(self.frames) * self.chunk
        return total_frames / self.rate
    
    def cleanup(self):
        """Clean up meeting recording resources."""
        try:
            # Stop auto-save thread
            if self.auto_save_thread and self.auto_save_thread.is_alive():
                self._auto_save_stop_event.set()
                self.auto_save_thread.join(timeout=2.0)
            
            # Stop recording if active
            if self.is_recording:
                self.stop_meeting_recording()
            
            # Clean up audio resources
            if self.audio:
                self.audio.terminate()
                
            logging.info("Meeting recorder cleaned up")
            
        except Exception as e:
            logging.error(f"Error during meeting recorder cleanup: {e}")