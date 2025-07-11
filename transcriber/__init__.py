"""
Transcription backends for the Audio Recorder application.
"""
from .base import TranscriptionBackend
from .local_backend import LocalWhisperBackend
from .openai_backend import OpenAIBackend

__all__ = ['TranscriptionBackend', 'LocalWhisperBackend', 'OpenAIBackend'] 