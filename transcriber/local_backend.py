"""
Local Whisper transcription backend.
"""
import whisper
import logging
from typing import Optional
from .base import TranscriptionBackend
from config import config


class LocalWhisperBackend(TranscriptionBackend):
    """Local Whisper model transcription backend."""
    
    def __init__(self, model_name: str = None):
        """Initialize the local Whisper backend.
        
        Args:
            model_name: Whisper model name to use. Uses config default if None.
        """
        super().__init__()
        self.model_name = model_name or config.DEFAULT_WHISPER_MODEL
        self.model: Optional[whisper.Whisper] = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            logging.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logging.info("Whisper model loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load Whisper model: {e}")
            self.model = None
    
    def transcribe(self, audio_file_path: str) -> str:
        """Transcribe audio file using local Whisper model.
        
        Args:
            audio_file_path: Path to the audio file to transcribe.
            
        Returns:
            Transcribed text.
            
        Raises:
            Exception: If transcription fails or model is not available.
        """
        if not self.is_available():
            raise Exception("Local Whisper model is not available")
        
        try:
            self.is_transcribing = True
            self.reset_cancel_flag()
            
            logging.info("Processing audio with local Whisper model...")
            result = self.model.transcribe(audio_file_path)
            
            if self.should_cancel:
                logging.info("Transcription cancelled by user")
                raise Exception("Transcription cancelled")
            
            transcribed_text = result['text'].strip()
            logging.info(f"Local transcription complete. Length: {len(transcribed_text)} characters")
            
            return transcribed_text
            
        except Exception as e:
            logging.error(f"Local transcription failed: {e}")
            raise
        finally:
            self.is_transcribing = False
    
    def is_available(self) -> bool:
        """Check if the local Whisper model is available.
        
        Returns:
            True if model is loaded and available, False otherwise.
        """
        return self.model is not None
    
    def reload_model(self, model_name: str = None):
        """Reload the Whisper model with a different model name.
        
        Args:
            model_name: New model name to load. Uses current if None.
        """
        if model_name:
            self.model_name = model_name
        self._load_model()
    
    @property
    def name(self) -> str:
        """Get the backend name with model info."""
        return f"LocalWhisper ({self.model_name})" 