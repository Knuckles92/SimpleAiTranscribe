"""
OpenAI API transcription backend.
"""
import os
import logging
from typing import Optional
from openai import OpenAI
from .base import TranscriptionBackend
from config import config


class OpenAIBackend(TranscriptionBackend):
    """OpenAI API transcription backend."""
    
    def __init__(self, model_type: str = "api_whisper", api_key: str = None):
        """Initialize the OpenAI backend.
        
        Args:
            model_type: Type of OpenAI model to use (api_whisper, api_gpt4o, api_gpt4o_mini).
            api_key: OpenAI API key. Uses environment variable if None.
        """
        super().__init__()
        self.model_type = model_type
        self.api_key = api_key or self._get_api_key()
        self.client: Optional[OpenAI] = None
        self._initialize_client()
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables or .env file."""
        # Try system environment variables first
        api_key = os.getenv('OPENAI_API_KEY')
        
        # If no API key in system env, try loading from .env file
        if not api_key:
            try:
                from dotenv import load_dotenv
                env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', config.ENV_FILE)
                load_dotenv(env_path)
                api_key = os.getenv('OPENAI_API_KEY')
            except ImportError:
                logging.warning("python-dotenv not installed. Skipping .env file loading.")
            except Exception as e:
                logging.warning(f"Failed to load .env file: {e}")
        
        return api_key
    
    def _initialize_client(self):
        """Initialize the OpenAI client."""
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logging.info("OpenAI client initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logging.warning("No OpenAI API key found")
            self.client = None
    
    def _get_api_model_name(self) -> str:
        """Get the API model name based on model type."""
        if self.model_type == "api_gpt4o":
            return "gpt-4o-transcribe"
        elif self.model_type == "api_gpt4o_mini":
            return "gpt-4o-mini-transcribe"
        else:  # api_whisper or default
            return "whisper-1"
    
    def transcribe(self, audio_file_path: str) -> str:
        """Transcribe audio file using OpenAI API.
        
        Args:
            audio_file_path: Path to the audio file to transcribe.
            
        Returns:
            Transcribed text.
            
        Raises:
            Exception: If transcription fails or API is not available.
        """
        if not self.is_available():
            raise Exception("OpenAI API is not available (no API key or client initialization failed)")
        
        try:
            self.is_transcribing = True
            self.reset_cancel_flag()
            
            api_model = self._get_api_model_name()
            logging.info(f"Using OpenAI API model: {api_model}")
            logging.info("Sending audio file to OpenAI API...")
            
            with open(audio_file_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=api_model,
                    file=audio_file,
                    response_format="text"
                )
            
            if self.should_cancel:
                logging.info("Transcription cancelled by user")
                raise Exception("Transcription cancelled")
            
            transcribed_text = response.strip()
            logging.info(f"API transcription complete. Length: {len(transcribed_text)} characters")
            
            return transcribed_text
            
        except Exception as e:
            logging.error(f"OpenAI API transcription failed: {e}")
            raise
        finally:
            self.is_transcribing = False
    
    def is_available(self) -> bool:
        """Check if the OpenAI API is available.
        
        Returns:
            True if API key is set and client is initialized, False otherwise.
        """
        return self.client is not None and self.api_key is not None
    
    def update_api_key(self, api_key: str):
        """Update the API key and reinitialize the client.
        
        Args:
            api_key: New API key to use.
        """
        self.api_key = api_key
        self._initialize_client()
    
    def change_model_type(self, model_type: str):
        """Change the model type.
        
        Args:
            model_type: New model type to use.
        """
        self.model_type = model_type
        logging.info(f"Model type changed to: {model_type}")
    
    @property
    def name(self) -> str:
        """Get the backend name with model info."""
        return f"OpenAI ({self.model_type})" 