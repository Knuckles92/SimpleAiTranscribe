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
    LOADING_WINDOW_SIZE: str = "300x300"
    HOTKEY_DIALOG_SIZE: str = "400x300"
    OVERLAY_SIZE: str = "200x30"
    
    # Waveform overlay settings
    WAVEFORM_OVERLAY_WIDTH: int = 300
    WAVEFORM_OVERLAY_HEIGHT: int = 80
    WAVEFORM_BAR_COUNT: int = 20
    WAVEFORM_BAR_WIDTH: int = 8
    WAVEFORM_BAR_SPACING: int = 2
    WAVEFORM_FRAME_RATE: int = 30
    WAVEFORM_LEVEL_SMOOTHING: float = 0.7
    
    # Waveform colors (hex format)
    WAVEFORM_BG_COLOR: str = "#1a1a1a"
    WAVEFORM_ACCENT_COLOR: str = "#00d4ff"
    WAVEFORM_SECONDARY_COLOR: str = "#0099cc"
    WAVEFORM_TEXT_COLOR: str = "#ffffff"
    
    # Timing settings
    HOTKEY_DEBOUNCE_MS: int = 300
    OVERLAY_HIDE_DELAY_MS: int = 1500
    CANCELLATION_ANIMATION_DURATION_MS: int = 800
    PROGRESS_BAR_INTERVAL_MS: int = 10
    # Continue capturing this many ms after stop to avoid end cut-offs
    POST_ROLL_MS: int = 1200
    
    # Audio splitting settings
    MAX_FILE_SIZE_MB: int = 23  # Maximum file size before splitting
    SILENCE_THRESHOLD: float = 0.01  # Volume threshold to detect silence
    MIN_CHUNK_DURATION_SEC: int = 30  # Minimum duration for each chunk in seconds
    SILENCE_DURATION_SEC: float = 0.5  # Duration of silence needed for split point
    OVERLAP_DURATION_SEC: float = 2.0  # Overlap between chunks to avoid word cutoffs
    
    # Whisper model
    DEFAULT_WHISPER_MODEL: str = "base"
    
    # Waveform style settings
    CURRENT_WAVEFORM_STYLE: str = "modern"
    WAVEFORM_STYLE_CONFIGS: Dict[str, Dict] = None
    
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
        
        if self.WAVEFORM_STYLE_CONFIGS is None:
            self.WAVEFORM_STYLE_CONFIGS = {
                'modern': {
                    'bar_count': 20,
                    'bar_width': 8,
                    'bar_spacing': 2,
                    'bg_color': '#1a1a1a',
                    'accent_color': '#00d4ff',
                    'secondary_color': '#0099cc',
                    'text_color': '#ffffff',
                    'danger_color': '#ff4444',
                    'pulse_speed': 2.0,
                    'pulse_amplitude': 0.3,
                    'wave_speed': 3.0,
                    'smoothing_factor': 0.1
                },
                'retro': {
                    'bar_count': 16,
                    'bar_width': 10,
                    'bar_spacing': 3,
                    'bg_color': '#0a0a0a',
                    'neon_pink': '#ff00ff',
                    'neon_cyan': '#00ffff',
                    'neon_purple': '#8000ff',
                    'neon_green': '#00ff00',
                    'text_color': '#ffffff',
                    'grid_speed': 1.5,
                    'scanline_speed': 8.0,
                    'glitch_intensity': 0.05,
                    'glow_intensity': 1.5,
                    'chromatic_aberration': True,
                    'scanlines_enabled': True,
                    'vhs_noise': True
                },
                'minimalist': {
                    'line_count': 18,
                    'line_width': 2,
                    'line_spacing': 8,
                    'bg_color': '#f8f8f8',
                    'primary_color': '#4a4a4a',
                    'accent_color': '#6b9bd2',
                    'subtle_color': '#c0c0c0',
                    'text_color': '#333333',
                    'breathing_speed': 0.8,
                    'ripple_speed': 1.2,
                    'fade_speed': 0.6,
                    'smoothing': 0.05
                },
                'spectrum': {
                    'spectrum_bars': 24,
                    'inner_radius': 25,
                    'outer_radius': 45,
                    'bar_width': 4,
                    'bg_color': '#000000',
                    'center_color': '#ffffff',
                    'text_color': '#ffffff',
                    'use_rainbow': True,
                    'rainbow_saturation': 0.9,
                    'rainbow_brightness': 1.0,
                    'rotation_speed': 1.0,
                    'spiral_speed': 2.0,
                    'pulse_speed': 1.5,
                    'decay_rate': 0.95
                },
                'particle': {
                    'max_particles': 150,
                    'emission_rate': 30,
                    'particle_life': 2.0,
                    'gravity': 20,
                    'damping': 0.98,
                    'wind_strength': 5,
                    'audio_response': 1.5,
                    'bg_color': '#0a0a0a',
                    'text_color': '#ffffff',
                    'particle_trail': True,
                    'glow_effect': True,
                    'turbulence_strength': 10,
                    'color_shift_speed': 50
                },
                'neonmatrix': {
                    'bg_color': '#0a0f14',
                    'primary': '#39ff14',
                    'secondary': '#00e5ff',
                    'alert': '#ff2a6d',
                    'text_color': '#d0f5ff',
                    'bar_count': 18,
                    'bar_width': 7,
                    'bar_spacing': 3,
                    'rain_columns': 24,
                    'rain_speed': 110.0,
                    'glow_intensity': 0.4,
                },
                'galaxywarp': {
                    'bg_color': '#050510',
                    'star_color': '#b0d8ff',
                    'accent': '#7a5cff',
                    'accent2': '#ff9d00',
                    'text_color': '#e8f0ff',
                    'star_count': 120,
                    'star_speed': 1.6,
                    'star_depth': 0.995,
                    'ring_count': 4,
                    'ring_thickness': 3,
                    'ripple_speed': 1.8,
                    'ripple_gain': 22.0,
                }
            }


# Global config instance
config = AppConfig() 