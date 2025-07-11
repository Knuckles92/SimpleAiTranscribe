"""
Base transcription backend interface.
"""
from abc import ABC, abstractmethod
from typing import Optional


class TranscriptionBackend(ABC):
    """Abstract base class for transcription backends."""
    
    def __init__(self):
        """Initialize the transcription backend."""
        self.is_transcribing = False
        self.should_cancel = False
    
    @abstractmethod
    def transcribe(self, audio_file_path: str) -> str:
        """Transcribe audio file to text.
        
        Args:
            audio_file_path: Path to the audio file to transcribe.
            
        Returns:
            Transcribed text.
            
        Raises:
            Exception: If transcription fails.
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is available and ready to use.
        
        Returns:
            True if backend is available, False otherwise.
        """
        pass
    
    def cancel_transcription(self):
        """Cancel ongoing transcription."""
        self.should_cancel = True
    
    def reset_cancel_flag(self):
        """Reset the cancellation flag."""
        self.should_cancel = False
    
    @property
    def name(self) -> str:
        """Get the backend name."""
        return self.__class__.__name__ 