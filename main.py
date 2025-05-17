import argparse
import os
import logging
import pyperclip
import keyboard
import threading
import time

from audio_recorder import AudioRecorder
from audio_player import StoppableAudio
from transcription import Transcriber
from ui_components import StatusOverlay, SystemTray, print_welcome_message
from keyboard_handler import KeyboardHandler

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Set up logging
os.makedirs('res', exist_ok=True)  # Ensure res directory exists
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join("res", "audio_recorder.log"))
                    ])

console = Console()

class AudioTranscriptionApp:
    def __init__(self):
        # Parse command line arguments
        parser = argparse.ArgumentParser(description="Audio Recorder CLI")
        parser.add_argument('--model', choices=['local', 'api', '4o', '4om'], default='local', 
                         help='Transcription model: local=local_whisper, api=api_whisper, 4o=gpt-4o, 4om=gpt-4o-mini')
        args = parser.parse_args()

        # Map model choices to internal names
        self.model_mapping = {
            'local': 'local_whisper',
            'api': 'api_whisper',
            '4o': 'api_gpt4o',
            '4om': 'api_gpt4o_mini'
        }
        self.model_choice = self.model_mapping[args.model]
        self.use_api = self.model_choice.startswith('api_')

        # Initialize state variables
        self.is_recording = False
        self.is_transcribing = False
        self.is_playing_audio = False
        self.should_cancel = False
        self.program_enabled = True
        self.status_label = "Ready"

        # Initialize components
        self.audio_recorder = AudioRecorder()
        self.audio_player = StoppableAudio()
        self.transcriber = Transcriber(self.model_choice)
        self.overlay = StatusOverlay()
        
        # Set up system tray
        self.system_tray = SystemTray(self.show_window, self.quit_app)
        self.system_tray.setup()
        
        # Set up keyboard handler
        self.keyboard_handler = KeyboardHandler(
            self.toggle_recording,
            self.cancel_operation,
            self.toggle_program_enabled
        )
        self.keyboard_handler.setup()
        
        # Print welcome message
        print_welcome_message(self.model_choice, self.use_api)

    def toggle_recording(self):
        """Toggle recording state"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start recording audio"""
        self.is_recording = True
        self.audio_recorder.start_recording(self.show_status_overlay)

    def stop_recording(self):
        """Stop recording and start transcription"""
        self.is_recording = False
        self.status_label = "Processing..."
        
        # Update status overlay
        self.show_status_overlay("Processing...")
        
        # Stop recording and save the audio
        self.audio_recorder.stop_recording()
        
        # Update status overlay
        self.show_status_overlay("Transcribing...")

        # Start transcription in a separate thread
        transcription_thread = threading.Thread(target=self.transcribe_audio, daemon=True)
        transcription_thread.start()

    def transcribe_audio(self):
        """Transcribe the recorded audio"""
        try:
            self.is_transcribing = True
            self.should_cancel = False

            # Perform transcription
            audio_file_path = os.path.join("res", "recorded_audio.wav")
            transcribed_text = self.transcriber.transcribe(audio_file_path)
            
            if self.should_cancel or not transcribed_text:
                logging.info("Transcription cancelled or failed")
                console.print("", Text("▶ Ready", style="bold green"), "\n")
                self.status_label = "Ready"
                self.show_status_overlay("")
                self.is_transcribing = False
                return

            # Copy to clipboard and paste
            console.print("[yellow]Pasting transcription to active window...[/yellow]")
            pyperclip.copy(transcribed_text)
            keyboard.send('ctrl+v')
            console.print("", Text("✅ Ready (Pasted to clipboard)", style="bold green"), "\n")
            self.status_label = "Ready (Pasted)"
            
            # Hide the overlay
            self.show_status_overlay("")
            logging.info("Transcription process complete\n")

        except Exception as e:
            logging.error(f"\nError during transcription: {str(e)}")
            console.print(Panel(
                Text(f"Error: {str(e)}", style="bold red"),
                title="[bold red]Transcription Failed[/bold red]",
                border_style="red",
                expand=False
            ))
            self.status_label = "Ready"
            # Hide the overlay
            self.show_status_overlay("")
        finally:
            self.is_transcribing = False
            self.should_cancel = False
            self.status_label = "Ready"
            console.print("", Text("▶ Ready", style="bold green"), "\n")

    def cancel_operation(self):
        """Cancel any ongoing operation"""
        self.should_cancel = True

        # Stop audio playback if playing
        if self.is_playing_audio:
            self.is_playing_audio = False
            stopped = self.audio_player.stop()

            if stopped:
                logging.info("Audio playback stopped successfully")
            else:
                logging.error("Failed to stop audio playback")

            console.print(Panel(
                Text("⏹️ Audio Playback Stopped", style="bold red"),
                border_style="red",
                expand=False
            ))
            time.sleep(1.5)

        # Cancel recording if recording
        if self.is_recording:
            self.audio_recorder.cancel_recording(self.show_status_overlay)
            self.is_recording = False
        # Cancel transcription if transcribing
        elif self.is_transcribing:
            self.status_label = "Canceling..."
            self.show_status_overlay("Canceling...")
            # Schedule overlay to hide after 1.5 seconds
            threading.Timer(1.5, self.show_status_overlay, args=[""]).start()
            console.print(Panel(
                Text("⏹️ Cancelling Process...", style="bold red"),
                border_style="red",
                expand=False
            ))
            time.sleep(1.5)
        
        console.print("", Text("▶ Ready", style="bold green"), "\n")

    def toggle_program_enabled(self, enabled):
        """Toggle whether the program is enabled"""
        if not enabled:
            self.show_status_overlay("STT Disabled")
            # Schedule overlay to hide after 1.5 seconds
            threading.Timer(1.5, self.show_status_overlay, args=[""]).start()
        else:
            self.show_status_overlay("STT Enabled")
            # Schedule overlay to hide after 1.5 seconds
            threading.Timer(1.5, self.show_status_overlay, args=[""]).start()

    def show_status_overlay(self, message):
        """Show status overlay with given message"""
        self.overlay.show_status(message)

    def show_window(self, *_):
        """Show window (called from system tray)"""
        console.print("[dim][Tray] Show called (running in CLI mode)[/dim]")

    def hide_window(self):
        """Hide window (called when closing)"""
        console.print("[dim][Tray] Hide called (running in CLI mode)[/dim]")

    def on_closing(self):
        """Handle window closing"""
        self.hide_window()

    def quit_app(self, *_):
        """Quit the application"""
        # Clean up system tray
        self.system_tray.stop()
        
        # Clean up keyboard hooks
        self.keyboard_handler.cleanup()
        
        # Clean up audio player
        if self.audio_player.initialized:
            try:
                import pygame
                pygame.mixer.quit()
                pygame.quit()
            except Exception as e:
                logging.error(f"Error cleaning up pygame: {e}")
                
        # Clean up audio recorder
        self.audio_recorder.cleanup()
        
        # Destroy the overlay window
        self.overlay.destroy()
        
        console.print(Panel(
            Text("Goodbye! Thank you for using Audio Recorder CLI", style="bold white"),
            border_style="blue", 
            expand=False
        ))
        os._exit(0)

    def run(self):
        """Run the application"""
        try:
            # Start the overlay
            self.overlay.start()
            
            # Start the tkinter main loop
            self.overlay.run_mainloop()
        except KeyboardInterrupt:
            self.quit_app()


if __name__ == "__main__":
    app = AudioTranscriptionApp()
    app.run()
