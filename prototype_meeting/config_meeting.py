"""
Configuration constants for the Meeting Transcription feature.
"""
from dataclasses import dataclass
from typing import Dict, List
import os
from datetime import datetime


@dataclass
class MeetingConfig:
    """Configuration for meeting transcription system."""
    
    # Meeting-specific file paths
    MEETINGS_BASE_DIR: str = "meetings"
    MEETING_AUDIO_TEMPLATE: str = "meeting_{timestamp}.wav"
    MEETING_TRANSCRIPT_TEMPLATE: str = "meeting_{timestamp}.txt"
    MEETING_METADATA_TEMPLATE: str = "meeting_{timestamp}_meta.json"
    MEETING_CHUNKS_DIR: str = "chunks"
    
    # Meeting recording settings (different from short-form)
    MAX_MEETING_DURATION_HOURS: int = 8  # 8 hour meeting limit
    MEETING_CHUNK_SIZE: int = 2048  # Larger buffer for longer recordings
    MEETING_SAMPLE_RATE: int = 44100  # High quality for long meetings
    MEETING_CHANNELS: int = 1  # Mono for better processing
    
    # Meeting file management (no size limits like short-form)
    DISABLE_FILE_SIZE_LIMIT: bool = True
    AUTO_SAVE_INTERVAL_MINUTES: int = 5  # Auto-save every 5 minutes
    BACKUP_CHUNKS_ON_SPLIT: bool = True
    
    # Enhanced chunking for meetings
    MEETING_MIN_CHUNK_MINUTES: int = 2  # Minimum 2-minute chunks
    MEETING_MAX_CHUNK_MINUTES: int = 15  # Maximum 15-minute chunks
    MEETING_SILENCE_THRESHOLD: float = 0.008  # More sensitive silence detection
    MEETING_SILENCE_DURATION_SEC: float = 2.0  # Longer silence for natural breaks
    MEETING_OVERLAP_SECONDS: float = 5.0  # More overlap to prevent word cutoffs
    
    # Speaker detection settings (future enhancement)
    ENABLE_SPEAKER_DETECTION: bool = False
    MIN_SPEAKER_SEGMENT_SEC: float = 10.0
    SPEAKER_CHANGE_THRESHOLD: float = 0.6
    
    # Meeting-specific hotkeys
    MEETING_HOTKEYS: Dict[str, str] = None
    
    # Meeting UI settings
    MEETING_WINDOW_SIZE: str = "800x600"
    WAVEFORM_EDITOR_HEIGHT: int = 200
    CHUNK_LIST_HEIGHT: int = 300
    MEETING_CONTROL_HEIGHT: int = 100
    
    # Meeting session settings
    AUTO_PAUSE_ON_SILENCE_MINUTES: int = 10  # Auto-pause after 10min silence
    POST_ROLL_MEETING_MS: int = 3000  # 3 second post-roll for meetings
    ENABLE_MEETING_NOTIFICATIONS: bool = True
    
    # Export formats
    EXPORT_FORMATS: List[str] = None
    DEFAULT_EXPORT_FORMAT: str = "txt"
    INCLUDE_TIMESTAMPS: bool = True
    INCLUDE_CHUNK_MARKERS: bool = True
    
    # Meeting analytics
    TRACK_MEETING_STATISTICS: bool = True
    STATISTICS_FILE: str = "meeting_statistics.json"
    
    def __post_init__(self):
        """Initialize computed fields after dataclass creation."""
        if self.MEETING_HOTKEYS is None:
            self.MEETING_HOTKEYS = {
                'start_meeting': 'ctrl+alt+m',
                'pause_resume_meeting': 'ctrl+alt+p',
                'stop_meeting': 'ctrl+alt+s',
                'add_chunk_marker': 'ctrl+alt+c',
                'save_meeting': 'ctrl+alt+v'
            }
        
        if self.EXPORT_FORMATS is None:
            self.EXPORT_FORMATS = [
                'txt',      # Plain text
                'docx',     # Word document
                'pdf',      # PDF document
                'json',     # JSON with metadata
                'srt',      # Subtitle format
                'vtt'       # WebVTT format
            ]
    
    def get_meeting_timestamp(self) -> str:
        """Generate timestamp for meeting files."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def get_meeting_audio_path(self, timestamp: str = None) -> str:
        """Get full path for meeting audio file."""
        if timestamp is None:
            timestamp = self.get_meeting_timestamp()
        filename = self.MEETING_AUDIO_TEMPLATE.format(timestamp=timestamp)
        return os.path.join(self.MEETINGS_BASE_DIR, filename)
    
    def get_meeting_transcript_path(self, timestamp: str = None) -> str:
        """Get full path for meeting transcript file."""
        if timestamp is None:
            timestamp = self.get_meeting_timestamp()
        filename = self.MEETING_TRANSCRIPT_TEMPLATE.format(timestamp=timestamp)
        return os.path.join(self.MEETINGS_BASE_DIR, filename)
    
    def get_meeting_metadata_path(self, timestamp: str = None) -> str:
        """Get full path for meeting metadata file."""
        if timestamp is None:
            timestamp = self.get_meeting_timestamp()
        filename = self.MEETING_METADATA_TEMPLATE.format(timestamp=timestamp)
        return os.path.join(self.MEETINGS_BASE_DIR, filename)
    
    def get_meeting_chunks_dir(self, timestamp: str) -> str:
        """Get directory path for meeting chunks."""
        return os.path.join(self.MEETINGS_BASE_DIR, f"meeting_{timestamp}_chunks")
    
    def ensure_meetings_directory(self):
        """Ensure the meetings directory exists."""
        os.makedirs(self.MEETINGS_BASE_DIR, exist_ok=True)


# Global meeting config instance
meeting_config = MeetingConfig()