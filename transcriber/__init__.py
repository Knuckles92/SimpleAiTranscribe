"""
Transcription backends for the Audio Recorder application.
"""
from .base import TranscriptionBackend
from .local_backend import LocalWhisperBackend

__all__ = ['TranscriptionBackend', 'LocalWhisperBackend'] 