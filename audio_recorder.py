import pyaudio
import wave
import threading
import logging
import time
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

class AudioRecorder:
    def __init__(self):
        """Initialize the audio recorder"""
        self.is_recording = False
        self.frames = []
        self.audio = pyaudio.PyAudio()
        
        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        
    def start_recording(self, status_callback=None):
        """Start recording audio"""
        self.frames = []
        self.is_recording = True
        
        if status_callback:
            status_callback("Recording...")
            
        threading.Thread(target=self._record).start()
        
    def _record(self):
        """Record audio in a separate thread"""
        stream = self.audio.open(format=self.format, channels=self.channels,
                            rate=self.rate, input=True,
                            frames_per_buffer=self.chunk)
        
        while self.is_recording:
            try:
                data = stream.read(self.chunk)
                self.frames.append(data)
            except Exception as e:
                logging.error(f"Error recording: {e}")
                break
                
        stream.stop_stream()
        stream.close()
        
    def stop_recording(self, status_callback=None):
        """Stop recording audio"""
        self.is_recording = False
        
        if status_callback:
            status_callback("Processing...")
            
        with console.status("[bold blue]Processing audio...", spinner="dots"):
            self.save_recording()
            
        if status_callback:
            status_callback("Transcribing...")
            
        return True
        
    def save_recording(self, output_file="recorded_audio.wav"):
        """Save recorded audio to a WAV file"""
        # Ensure res directory exists
        os.makedirs('res', exist_ok=True)
        
        # Use the res directory for audio files
        file_path = os.path.join('res', output_file)
        
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
        return file_path
        
    def cancel_recording(self, status_callback=None):
        """Cancel ongoing recording"""
        if self.is_recording:
            self.is_recording = False
            
            if status_callback:
                status_callback("Recording Cancelled")
                
            console.print(Panel(
                Text("⏹️ Recording Cancelled", style="bold red"),
                border_style="red",
                expand=False
            ))
            time.sleep(1.5)
            return True
        return False
        
    def cleanup(self):
        """Clean up resources"""
        self.audio.terminate()
