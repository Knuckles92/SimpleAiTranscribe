"""
Configuration constants for the Audio Recorder application.
"""
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class AppConfig:
    """Centralized configuration for the Audio Recorder application."""
    
    # File paths
    SETTINGS_FILE: str = "audio_recorder_settings.json"
    RECORDED_AUDIO_FILE: str = "recorded_audio.wav"
    LOG_FILE: str = "audio_recorder.log"
    ENV_FILE: str = ".env"
    
    # Audio settings
    CHUNK_SIZE: int = 1024
    AUDIO_FORMAT: str = "paInt16"  # Will be converted to pyaudio constant
    CHANNELS: int = 1
    SAMPLE_RATE: int = 44100
    
    # Default hotkeys
    DEFAULT_HOTKEYS: Dict[str, str] = None
    
    # Model configurations
    MODEL_CHOICES: Tuple[str, ...] = (
        'Local Whisper',
        'API: Whisper',
        'API: GPT-4o Transcribe',
        'API: GPT-4o Mini Transcribe'
    )
    
    MODEL_VALUE_MAP: Dict[str, str] = None
    
    # UI settings
    MAIN_WINDOW_SIZE: str = "300x200"
    LOADING_WINDOW_SIZE: str = "300x150"
    HOTKEY_DIALOG_SIZE: str = "400x300"
    OVERLAY_SIZE: str = "200x30"
    
    # Timing settings
    HOTKEY_DEBOUNCE_MS: int = 300
    OVERLAY_HIDE_DELAY_MS: int = 1500
    PROGRESS_BAR_INTERVAL_MS: int = 10
    
    # Whisper model
    DEFAULT_WHISPER_MODEL: str = "base"
    
    def __post_init__(self):
        """Initialize computed fields after dataclass creation."""
        if self.DEFAULT_HOTKEYS is None:
            self.DEFAULT_HOTKEYS = {
                'record_toggle': '*',
                'cancel': '-',
                'enable_disable': 'ctrl+alt+*'
            }
        
        if self.MODEL_VALUE_MAP is None:
            self.MODEL_VALUE_MAP = {
                'Local Whisper': 'local_whisper',
                'API: Whisper': 'api_whisper',
                'API: GPT-4o Transcribe': 'api_gpt4o',
                'API: GPT-4o Mini Transcribe': 'api_gpt4o_mini'
            }


# Global config instance
config = AppConfig() 