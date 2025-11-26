"""
Local Whisper transcription backend with ffmpeg detection and configuration.
"""
import whisper
import logging
import os
import subprocess
import platform
from typing import Optional, List
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from .base import TranscriptionBackend
from config import config
from settings import settings_manager


class FFmpegManager:
    """Manages ffmpeg detection and configuration."""
    
    @staticmethod
    def detect_ffmpeg() -> Optional[str]:
        """Detect if ffmpeg is available in PATH.
        
        Returns:
            Path to ffmpeg executable if found, None otherwise.
        """
        try:
            # Try to run ffmpeg -version
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                # ffmpeg found in PATH
                return 'ffmpeg'
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Check common installation paths on Windows
        if platform.system() == "Windows":
            common_paths = [
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
                r"C:\tools\ffmpeg\bin\ffmpeg.exe",
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return path
        
        return None
    
    @staticmethod
    def prompt_for_ffmpeg_path() -> Optional[str]:
        """Prompt user to select ffmpeg executable location.
        
        Returns:
            Path to selected ffmpeg executable, or None if cancelled.
        """
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Show informative message first
        message = ("FFmpeg was not found in your system PATH.\n\n"
                  "FFmpeg is required for local Whisper transcription.\n"
                  "Please locate your ffmpeg.exe file.\n\n"
                  "Common locations:\n"
                  "• C:\\ffmpeg\\bin\\ffmpeg.exe\n"
                  "• C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe\n"
                  "• Or wherever you installed FFmpeg")
        
        messagebox.showinfo("FFmpeg Not Found", message)
        
        # Open file dialog to select ffmpeg.exe
        if platform.system() == "Windows":
            file_types = [("Executable files", "*.exe"), ("All files", "*.*")]
            initial_name = "ffmpeg.exe"
        else:
            file_types = [("All files", "*.*")]
            initial_name = "ffmpeg"
        
        ffmpeg_path = filedialog.askopenfilename(
            title="Select FFmpeg Executable",
            filetypes=file_types,
            initialfile=initial_name
        )
        
        root.destroy()
        
        if ffmpeg_path and os.path.exists(ffmpeg_path):
            # Verify it's actually ffmpeg
            try:
                result = subprocess.run([ffmpeg_path, '-version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0 and 'ffmpeg' in result.stdout.lower():
                    return ffmpeg_path
                else:
                    messagebox.showerror("Invalid FFmpeg", 
                                       "The selected file does not appear to be a valid FFmpeg executable.")
            except Exception as e:
                messagebox.showerror("FFmpeg Test Failed", 
                                   f"Could not verify FFmpeg executable: {e}")
        
        return None
    
    @staticmethod
    def configure_whisper_ffmpeg(ffmpeg_path: str):
        """Configure whisper to use specific ffmpeg path.
        
        Args:
            ffmpeg_path: Path to ffmpeg executable.
        """
        # Set environment variable for ffmpeg
        os.environ['FFMPEG_BINARY'] = ffmpeg_path
        
        # Also add the directory to PATH if it's not there
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        current_path = os.environ.get('PATH', '')
        if ffmpeg_dir not in current_path:
            os.environ['PATH'] = f"{ffmpeg_dir}{os.pathsep}{current_path}"


class LocalWhisperBackend(TranscriptionBackend):
    """Local Whisper model transcription backend with ffmpeg handling."""
    
    def __init__(self, model_name: str = None):
        """Initialize the local Whisper backend.
        
        Args:
            model_name: Whisper model name to use. Uses config default if None.
        """
        super().__init__()
        self.model_name = model_name or config.DEFAULT_WHISPER_MODEL
        self.model: Optional[whisper.Whisper] = None
        self.ffmpeg_configured = False
        self._setup_ffmpeg()
        self._load_model()
    
    def _setup_ffmpeg(self):
        """Setup ffmpeg configuration."""
        # Check if we already have a saved ffmpeg path
        settings = settings_manager.load_all_settings()
        saved_ffmpeg_path = settings.get('ffmpeg_path')
        
        if saved_ffmpeg_path and os.path.exists(saved_ffmpeg_path):
            logging.info(f"Using saved ffmpeg path: {saved_ffmpeg_path}")
            FFmpegManager.configure_whisper_ffmpeg(saved_ffmpeg_path)
            self.ffmpeg_configured = True
            return
        
        # Try to detect ffmpeg automatically
        detected_path = FFmpegManager.detect_ffmpeg()
        if detected_path:
            logging.info(f"FFmpeg detected at: {detected_path}")
            if detected_path != 'ffmpeg':  # If it's a full path, configure it
                FFmpegManager.configure_whisper_ffmpeg(detected_path)
            self.ffmpeg_configured = True
            return
        
        logging.warning("FFmpeg not detected automatically")
        self.ffmpeg_configured = False
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            logging.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logging.info("Whisper model loaded successfully")
        except Exception as e:
            error_msg = str(e).lower()
            if 'winerror 2' in error_msg or 'file not found' in error_msg:
                logging.error("Whisper model loading failed due to missing ffmpeg")
                self._handle_ffmpeg_missing()
            else:
                logging.error(f"Failed to load Whisper model: {e}")
                self.model = None
    
    def _handle_ffmpeg_missing(self):
        """Handle the case when ffmpeg is missing."""
        if not self.ffmpeg_configured:
            logging.info("Prompting user for ffmpeg location...")
            ffmpeg_path = FFmpegManager.prompt_for_ffmpeg_path()
            
            if ffmpeg_path:
                # Save the path for future use
                settings = settings_manager.load_all_settings()
                settings['ffmpeg_path'] = ffmpeg_path
                settings_manager.save_all_settings(settings)
                
                # Configure whisper to use this path
                FFmpegManager.configure_whisper_ffmpeg(ffmpeg_path)
                self.ffmpeg_configured = True
                
                logging.info(f"FFmpeg configured at: {ffmpeg_path}")
                
                # Try loading the model again
                try:
                    self.model = whisper.load_model(self.model_name)
                    logging.info("Whisper model loaded successfully after ffmpeg configuration")
                except Exception as e:
                    logging.error(f"Model loading still failed after ffmpeg configuration: {e}")
                    self.model = None
            else:
                logging.warning("User cancelled ffmpeg selection. Local Whisper will not be available.")
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
            raise Exception("Local Whisper model is not available. Please check ffmpeg installation.")
        
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
            error_msg = str(e).lower()
            if 'winerror 2' in error_msg or 'file not found' in error_msg:
                logging.error("Transcription failed due to ffmpeg issue")
                # Try to reconfigure ffmpeg
                self._handle_ffmpeg_missing()
                if self.is_available():
                    # If model is now available, retry once
                    logging.info("Retrying transcription after ffmpeg reconfiguration...")
                    return self.transcribe(audio_file_path)
            
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
    
    def transcribe_chunks(self, chunk_files: List[str]) -> str:
        """Transcribe multiple audio chunk files efficiently with local Whisper.
        
        Args:
            chunk_files: List of paths to audio chunk files.
            
        Returns:
            Combined transcribed text from all chunks.
            
        Raises:
            Exception: If transcription fails or model is not available.
        """
        if not self.is_available():
            raise Exception("Local Whisper model is not available. Please check ffmpeg installation.")
        
        try:
            self.is_transcribing = True
            self.reset_cancel_flag()
            
            transcriptions = []
            
            for i, chunk_file in enumerate(chunk_files):
                if self.should_cancel:
                    logging.info("Chunked transcription cancelled by user")
                    raise Exception("Transcription cancelled")
                
                logging.info(f"Processing chunk {i+1}/{len(chunk_files)} with local Whisper: {chunk_file}")
                
                # Transcribe individual chunk
                result = self.model.transcribe(chunk_file)
                chunk_text = result['text'].strip()
                transcriptions.append(chunk_text)
                
                logging.info(f"Chunk {i+1}/{len(chunk_files)} completed. Length: {len(chunk_text)} characters")
            
            # Combine transcriptions
            from audio_processor import audio_processor
            combined_text = audio_processor.combine_transcriptions(transcriptions)
            
            logging.info(f"Local chunked transcription complete. Total length: {len(combined_text)} characters")
            return combined_text
            
        except Exception as e:
            logging.error(f"Local chunked transcription failed: {e}")
            raise
        finally:
            self.is_transcribing = False

    def reset_ffmpeg_config(self):
        """Reset ffmpeg configuration and prompt user again."""
        # Remove saved ffmpeg path
        settings = settings_manager.load_all_settings()
        if 'ffmpeg_path' in settings:
            del settings['ffmpeg_path']
            settings_manager.save_all_settings(settings)
        
        # Reset configuration state
        self.ffmpeg_configured = False
        self.model = None
        
        # Try setup again
        self._setup_ffmpeg()
        self._load_model()
    
    def cleanup(self):
        """Clean up Whisper model and release resources.
        
        This unloads the model from memory (including GPU memory if applicable).
        """
        try:
            if self.model is not None:
                logging.info("Cleaning up LocalWhisperBackend - unloading model...")
                
                # Cancel any ongoing transcription
                self.should_cancel = True
                
                # Delete the model to free memory
                del self.model
                self.model = None
                
                # Force garbage collection to release GPU memory
                import gc
                gc.collect()
                
                # If using CUDA, clear GPU cache
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        logging.info("Cleared CUDA cache")
                except ImportError:
                    pass  # torch not available, skip GPU cleanup
                except Exception as e:
                    logging.debug(f"Error clearing CUDA cache: {e}")
                
                logging.info("LocalWhisperBackend cleaned up successfully")
        except Exception as e:
            logging.debug(f"Error during LocalWhisperBackend cleanup: {e}")
    
    @property
    def name(self) -> str:
        """Get the backend name with model info."""
        status = "Ready" if self.is_available() else "FFmpeg Required"
        return f"LocalWhisper ({self.model_name}) - {status}"