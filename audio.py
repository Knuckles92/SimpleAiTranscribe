import argparse
import pyaudio
import wave
import threading
import whisper
import os
import numpy as np
import pyperclip
import keyboard
from openai import OpenAI
import pystray
from PIL import Image
import time
import logging
import dotenv
from pathlib import Path
import pydub
import pygame
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.text import Text
from rich.style import Style
from rich.live import Live
from rich.table import Table

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("audio_recorder.log")
                        # Removed console handler since we'll use Rich for display
                    ])

# Initialize Rich console
console = Console()

# Load speaking style from file
try:
    with open('style.txt', 'r', encoding='utf-8') as file:
        speaking_style = file.read()
except FileNotFoundError:
    speaking_style = "You are a helpful assistant that speaks clearly and naturally."
    # Create the style file with default content
    with open('style.txt', 'w', encoding='utf-8') as file:
        file.write(speaking_style)

# Custom audio playback class that can always be stopped using pygame
class StoppableAudio:
    def __init__(self):
        self.playing = False
        self.initialized = False
        self.temp_file = "temp_audio.wav"

        # Initialize pygame mixer
        self._init_pygame()

    def _init_pygame(self):
        """Initialize pygame mixer with retry logic"""
        if not self.initialized:
            try:
                pygame.mixer.init()
                self.initialized = True
                logging.info("Using pygame for audio playback")
            except Exception as e:
                logging.error(f"Failed to initialize pygame mixer: {e}")
                # Try again with different parameters
                try:
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
                    self.initialized = True
                    logging.info("Using pygame for audio playback (with fallback parameters)")
                except Exception as e2:
                    logging.error(f"Failed to initialize pygame mixer with fallback parameters: {e2}")

    def play(self, audio_segment):
        """Play audio with the ability to stop it"""
        # Always try to initialize pygame if not already initialized
        if not self.initialized:
            self._init_pygame()

        # If still not initialized after trying, log error and return
        if not self.initialized:
            logging.error("Cannot play audio: pygame mixer could not be initialized")
            return False

        try:
            # Export audio to a temporary file that pygame can read
            audio_segment.export(self.temp_file, format="wav")

            # Stop any currently playing sound
            pygame.mixer.music.stop()

            # Load and play the audio
            pygame.mixer.music.load(self.temp_file)
            pygame.mixer.music.play()

            self.playing = True
            return True
        except Exception as e:
            logging.error(f"Error playing audio with pygame: {e}")
            return False

    def stop(self):
        """Stop audio playback"""
        self.playing = False

        if self.initialized:
            try:
                pygame.mixer.music.stop()
                return True
            except Exception as e:
                logging.error(f"Error stopping pygame playback: {e}")

        return False  # Couldn't stop playback

class AudioRecorder:
    def __init__(self):
        # Parse CLI arguments for model selection
        parser = argparse.ArgumentParser(description="Audio Recorder CLI")
        parser.add_argument('--model', choices=['local_whisper', 'api_whisper', 'api_gpt4o', 'api_gpt4o_mini'], default='local_whisper', help='Transcription model to use')
        parser.add_argument('--use-api', action='store_true', help='Use OpenAI API for transcription')
        args = parser.parse_args()

        # Initialize recording variables
        self.is_recording = False
        self.is_transcribing = False
        self.is_playing_audio = False
        self.should_cancel = False
        self.frames = []
        self.audio = pyaudio.PyAudio()

        # Initialize audio player
        self.audio_player = StoppableAudio()

        # Program enabled state
        self.program_enabled = True
        self.tts_enabled = True  # TTS feature enabled state

        # Settings variables
        self.use_api = args.use_api or args.model.startswith('api_')
        self.model_choice = args.model

        # Try system environment variables first
        self.api_key = os.getenv('OPENAI_API_KEY')

        # If no API key in system env, try loading from .env file
        if not self.api_key:
            try:
                from dotenv import load_dotenv
                env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
                load_dotenv(env_path)
                self.api_key = os.getenv('OPENAI_API_KEY')
            except ImportError:
                logging.warning("python-dotenv not installed. Skipping .env file loading.")
            except Exception as e:
                logging.warning(f"Failed to load .env file: {e}")

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100

        # Setup system tray
        self.setup_system_tray()

        # Initialize local Whisper model
        logging.info("Loading Whisper model...")
        self.model = whisper.load_model("base")
        logging.info("Model loaded!")

        # Setup keyboard suppression for specific keys
        keyboard.hook(self._handle_keyboard_event, suppress=True)
        keyboard.add_hotkey('f9', lambda: self._f9_pressed(), suppress=True)

        # Display beautiful welcome banner
        welcome_panel = Panel(
            Text(f"Audio Recorder", style="bold white on blue", justify="center"),
            subtitle=Text(f"Version 1.0", style="italic", justify="center"),
            border_style="blue"
        )
        console.print(welcome_panel)

        # Show key info in a table
        table = Table(show_header=True, header_style="bold cyan", border_style="blue")
        table.add_column("Setting", style="dim")
        table.add_column("Value", style="green")
        
        table.add_row("Model", self.model_choice)
        table.add_row("API Mode", "✅ Enabled" if self.use_api else "❌ Disabled")
        table.add_row("TTS Feature", "✅ Enabled" if self.tts_enabled else "❌ Disabled")
        
        console.print(table)
        
        # Print keyboard shortcuts help
        shortcuts = Table(show_header=True, header_style="bold magenta", title="Keyboard Shortcuts", border_style="magenta")
        shortcuts.add_column("Key", style="cyan")
        shortcuts.add_column("Action", style="yellow")
        
        shortcuts.add_row("*", "Start/Stop Recording")
        shortcuts.add_row("-", "Cancel/Stop Any Process")
        shortcuts.add_row("F9", "Text-to-Speech (from clipboard)")
        shortcuts.add_row("Ctrl+Shift+T", "Text-to-Speech (alternative)")
        shortcuts.add_row("Ctrl+Alt+*", "Enable/Disable Program")
        
        console.print(shortcuts)
        console.print("", Text("▶ Ready", style="bold green"), "\n")

    def _handle_keyboard_event(self, event):
        """Global keyboard event handler with suppression"""
        if event.event_type == keyboard.KEY_DOWN:
            # Log all keyboard events for debugging
            #logging.info(f"Keyboard event: {event.name}, event_type: {event.event_type}, scan_code: {event.scan_code}")

            # Handle CTRL+ALT+* for enable/disable
            if (event.name == '*' and
                keyboard.is_pressed('ctrl') and
                keyboard.is_pressed('alt')):
                self.program_enabled = not self.program_enabled
                if not self.program_enabled:
                    print("STT Disabled")
                    # Schedule overlay to hide after 1.5 seconds
                    time.sleep(1.5)
                    # Unhook all keys except CTRL+ALT+*
                    keyboard.unhook_all()
                    keyboard.hook(self._handle_keyboard_event, suppress=True)
                else:
                    # Re-enable all key listeners
                    keyboard.unhook_all()
                    keyboard.hook(self._handle_keyboard_event, suppress=True)
                    print("STT Enabled")
                    # Schedule overlay to hide after 1.5 seconds
                    time.sleep(1.5)
                return False  # Suppress the key combination

            # If program is disabled, only allow CTRL+ALT+*
            if not self.program_enabled:
                # Check if the exact CTRL+ALT+* combination is pressed
                if not (event.name == '*' and
                       keyboard.is_pressed('ctrl') and
                       keyboard.is_pressed('alt')):
                    return True

            # TTS feature shortcut (F9)
            # F9 scan code is typically 67 on most keyboards
            if (event.name == 'f9' or event.scan_code == 67) and self.tts_enabled:
                print("F9 key detected (name: {event.name}, scan_code: {event.scan_code}) - starting text-to-speech")
                # Use the same method as the dedicated hotkey handler
                time.sleep(0.01)
                self._run_tts_in_main_thread()
                return False  # Suppress F9 key

            # Add alternative key for TTS (Ctrl+Shift+T) since F9 might be problematic on some systems
            elif event.name == 't' and keyboard.is_pressed('ctrl') and keyboard.is_pressed('shift') and self.tts_enabled:
                print("Ctrl+Shift+T detected - starting text-to-speech")
                # Use the same method as the dedicated hotkey handler
                time.sleep(0.01)
                self._run_tts_in_main_thread()
                return False  # Suppress the key combination

            elif event.name == '*' and not self.is_transcribing:
                if not hasattr(self, '_last_trigger_time'):
                    self._last_trigger_time = 0

                # Debounce to prevent double triggers
                current_time = time.time()
                if current_time - self._last_trigger_time > 0.3:  # 300ms debounce
                    self._last_trigger_time = current_time
                    self.toggle_recording()
                return False  # Always suppress * key

            elif event.name == '-':
                # Always call cancel_transcription to stop any ongoing process
                # This makes the "-" key a universal stop button
                self.cancel_transcription()
                return False  # Suppress - key when handling

        # Let all other keys pass through
        return True

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.frames = []  # Initialize empty list to store audio frames
        self.is_recording = True
        self.status_label = "Recording..."
        
        # Show recording panel with animation
        console.print(Panel(
            Text("🎙️ Recording...", style="bold red blink"),
            border_style="red",
            expand=False
        ))

        # Start recording in a separate thread
        threading.Thread(target=self._record).start()

    def _record(self):
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

    def stop_recording(self):
        self.is_recording = False
        self.status_label = "Processing..."
        
        # Show processing animation
        with console.status("[bold blue]Processing audio...", spinner="dots"):
            # Save the recording
            self.save_recording()
        
        console.print(Panel(
            Text("🔍 Transcribing audio...", style="bold yellow"),
            border_style="yellow",
            expand=False
        ))

        # Use daemon thread to prevent console flash
        transcription_thread = threading.Thread(target=self.transcribe_audio, daemon=True)
        transcription_thread.start()

    def save_recording(self):
        # Save recorded audio to WAV file
        with wave.open("recorded_audio.wav", 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))

    def cancel_transcription(self):
        """Universal stop button that cancels transcription and stops audio playback"""
        self.should_cancel = True

        # Stop audio playback regardless of current state
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

        # Handle recording state
        if self.is_recording:
            self.is_recording = False
            self.status_label = "Recording Cancelled"
            console.print(Panel(
                Text("⏹️ Recording Cancelled", style="bold red"),
                border_style="red",
                expand=False
            ))
            time.sleep(1.5)
        # Handle transcribing state
        elif self.is_transcribing:
            self.status_label = "Canceling..."
            console.print(Panel(
                Text("⏹️ Cancelling Process...", style="bold red"),
                border_style="red",
                expand=False
            ))
            time.sleep(1.5)
        
        # Always show ready status after cancellation
        console.print("", Text("▶ Ready", style="bold green"), "\n")

    def clear_and_paste(self, text):
        """Paste text at current cursor position."""
        pyperclip.copy(text)
        keyboard.send('ctrl+v')  # Paste new text

    def transcribe_audio(self):
        try:
            self.is_transcribing = True
            self.should_cancel = False

            # Create a progress context for the transcription process
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[bold]{task.percentage:.0f}%"),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                # Add the main task
                transcribe_task = progress.add_task("[cyan]Transcribing audio...", total=100)

                # Update progress to 10% to show we're starting
                progress.update(transcribe_task, advance=10)
                
                # Determine if we should use API based on model selection
                use_api = self.model_choice.startswith("api_")

            if use_api:
                logging.info("\n=== Using OpenAI API ===")
                if not self.api_key:
                    logging.error("Error: No API key found!")
                    raise ValueError("OpenAI API key not found in environment variables (OPENAI_API_KEY)")

                logging.info(f"Using model: {self.model_choice}")

                # Select API model based on choice
                api_model = "gpt-4o-mini-transcribe"  # Default to mini model

                if self.model_choice == "api_gpt4o":
                    api_model = "gpt-4o-transcribe"
                elif self.model_choice == "api_gpt4o_mini":
                    api_model = "gpt-4o-mini-transcribe"

                logging.info(f"Selected API model: {api_model}")
                logging.info("Sending audio file to OpenAI API...")
                progress.update(transcribe_task, description="[magenta]Sending to OpenAI API...", advance=20)

                # Updated API call using the new client
                with open("recorded_audio.wav", "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=api_model,
                        file=audio_file,
                        response_format="text"
                    )
                transcribed_text = response.strip()
                logging.info(f"API Response received. Length: {len(transcribed_text)} characters")
                progress.update(transcribe_task, description="[green]Processing API response...", advance=60)
            else:
                logging.info("\n=== Using Local Whisper Model ===")
                logging.info("Processing audio with local model...")
                # Local Whisper transcription remains the same
                progress.update(transcribe_task, description="[magenta]Processing with local Whisper model...", advance=20)
                result = self.model.transcribe("recorded_audio.wav")
                transcribed_text = result['text'].strip()
                logging.info(f"Local transcription complete. Length: {len(transcribed_text)} characters")
                progress.update(transcribe_task, description="[green]Finalizing transcription...", advance=60)

                if self.should_cancel:
                    logging.info("Transcription cancelled by user")
                    console.print("", Text("▶ Ready", style="bold green"), "\n")
                    self.status_label = "Ready"
                    return

            logging.info(f"Final transcription: {transcribed_text}")
            
            # Complete the progress
            if 'progress' in locals():
                progress.update(transcribe_task, description="[bold green]Transcription complete!", advance=10)
            
            # Show the transcription result in a nice panel
            console.print(Panel(
                Text(transcribed_text, style="white"),
                title="[bold green]Transcription Result[/bold green]",
                border_style="green",
                expand=True
            ))

            # Auto-paste the final transcription
            console.print("[yellow]Pasting transcription to active window...[/yellow]")
            self.clear_and_paste(transcribed_text)
            console.print("", Text("✅ Ready (Pasted to clipboard)", style="bold green"), "\n")
            self.status_label = "Ready (Pasted)"
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
        finally:
            self.is_transcribing = False
            self.should_cancel = False
            self.status_label = "Ready"
            console.print("", Text("▶ Ready", style="bold green"), "\n")

    def show_status_overlay(self, message):
        if message:
            console.print(Text(f"▶ {message}", style="bold blue"))
        # Our beautiful CLI already handles status messages nicely

    def setup_system_tray(self):
        icon_data = Image.new('RGB', (64, 64), color='red')
        menu = (
            pystray.MenuItem('Show', self.show_window),
            pystray.MenuItem('Exit', self.quit_app)
        )
        self.tray_icon = pystray.Icon("audio_recorder", icon_data, "Audio Recorder", menu)
        self.tray_icon_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_icon_thread.start()

    def show_window(self, *_):
        console.print("[dim][Tray] Show called (running in CLI mode)[/dim]")

    def hide_window(self):
        console.print("[dim][Tray] Hide called (running in CLI mode)[/dim]")

    def on_closing(self):
        self.hide_window()

    def quit_app(self, *_):
        if self.tray_icon and self.tray_icon.visible:
            self.tray_icon.stop()
        try:
            keyboard.unhook_all()
            keyboard.remove_hotkey('f9')
        except Exception as e:
            logging.error(f"Error cleaning up keyboard hooks: {e}")
        if self.audio_player.initialized:
            try:
                pygame.mixer.quit()
                pygame.quit()
            except Exception as e:
                logging.error(f"Error cleaning up pygame: {e}")
        self.audio.terminate()
        console.print(Panel(
            Text("Goodbye! Thank you for using Audio Recorder CLI", style="bold white"),
            border_style="blue", 
            expand=False
        ))
        os._exit(0)

    def run(self):
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.quit_app()

    def _f9_pressed(self):
        """Dedicated handler for F9 key press"""
        console.print("[dim]F9 hotkey triggered directly[/dim]")
        if self.tts_enabled:
            # Use root.after to ensure this runs in the main thread
            time.sleep(0.01)
            self._run_tts_in_main_thread()

    def _run_tts_in_main_thread(self):
        """Run TTS in the main thread first to ensure UI updates, then spawn thread for API call"""
        console.print(Panel(
            Text("🔊 Starting Text-to-Speech...", style="bold cyan"),
            border_style="cyan",
            expand=False
        ))
        # Now spawn thread for the actual TTS processing
        threading.Thread(target=self.text_to_speech, daemon=True).start()

    # TTS methods from clip.py
    def text_to_speech(self):
        """Convert clipboard text to speech and play it"""
        try:
            # Get clipboard content
            clipboard_text = pyperclip.paste()
            console.print(Panel(
                Text(clipboard_text[:100] + ("..." if len(clipboard_text) > 100 else ""), style="italic"),
                title="[bold cyan]Clipboard Content[/bold cyan]",
                subtitle=f"[dim]Length: {len(clipboard_text)} characters[/dim]",
                border_style="cyan",
                expand=False
            ))

            if not clipboard_text:
                console.print(Panel(
                    Text("Nothing to speak - clipboard is empty", style="bold yellow"),
                    border_style="yellow",
                    expand=False
                ))
                time.sleep(1.5)
                return

            # Check if API key is available
            if not self.api_key:
                console.print(Panel(
                    Text("No API key available for TTS", style="bold red"),
                    border_style="red",
                    expand=False
                ))
                time.sleep(1.5)
                return

            # Initialize OpenAI client if needed
            if not self.client:
                console.print("[cyan]Initializing OpenAI client for TTS...[/cyan]")
                self.client = OpenAI(api_key=self.api_key)

            # Create TTS
            speech_file_path = Path(os.path.dirname(os.path.abspath(__file__))) / "speech.mp3"

            # Create a nice progress display
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold cyan]{task.description}"),
                BarColumn(),
                TextColumn("[bold]{task.percentage:.0f}%"),
                console=console
            ) as progress:
                tts_task = progress.add_task("[cyan]Generating speech...", total=100)
                
                console.print(f"[cyan]Model:[/cyan] [yellow]gpt-4o-mini-tts[/yellow], [cyan]Voice:[/cyan] [yellow]ash[/yellow]")
                progress.update(tts_task, advance=20)

            try:
                with self.client.audio.speech.with_streaming_response.create(
                    model="gpt-4o-mini-tts",
                    voice="ash",
                    input=clipboard_text,
                    instructions=speaking_style,
                ) as response:
                    # Update progress as we go
                    progress.update(tts_task, description="[magenta]Receiving audio stream...", advance=30)
                    response.stream_to_file(speech_file_path)
                    progress.update(tts_task, description="[green]TTS generation complete!", advance=50)
                
                console.print(Panel(
                    Text(f"Audio saved to {speech_file_path}", style="green"),
                    title="[bold green]TTS Complete[/bold green]",
                    border_style="green",
                    expand=False
                ))
                console.print("[cyan]Playing audio...[/cyan]")

                # Set the flag that audio is playing
                self.is_playing_audio = True

                try:
                    # Load the audio
                    audio = pydub.AudioSegment.from_file(speech_file_path)

                    # Play the audio with our stoppable player
                    if not self.audio_player.play(audio):
                        # If playback failed, show error
                        print("Failed to play audio with pygame")
                        self.is_playing_audio = False
                        time.sleep(1.5)
                        return

                    # Start a thread to monitor when playback finishes naturally
                    def check_playback_finished():
                        # Check if music is playing using pygame
                        while self.is_playing_audio and pygame.mixer.music.get_busy():
                            time.sleep(0.1)

                        # Only update UI if playback wasn't cancelled but finished naturally
                        if self.is_playing_audio:  # If we didn't cancel it
                            self.is_playing_audio = False
                            time.sleep(0)
                            console.print(Panel(
                                Text("Audio playback completed", style="bold green"),
                                border_style="green",
                                expand=False
                            ))
                            time.sleep(1.5)
                            console.print("", Text("▶ Ready", style="bold green"), "\n")

                    # Start monitoring thread
                    threading.Thread(target=check_playback_finished, daemon=True).start()

                except Exception as e:
                    console.print(Panel(
                        Text(f"Error: {str(e)}", style="bold red"),
                        title="[bold red]Playback Error[/bold red]",
                        border_style="red",
                        expand=False
                    ))
                    self.is_playing_audio = False
                    time.sleep(1.5)
                    console.print("", Text("▶ Ready", style="bold green"), "\n")
            except Exception as api_error:
                console.print(Panel(
                    Text(f"Error: {str(api_error)}", style="bold red"),
                    title="[bold red]OpenAI API Error[/bold red]",
                    border_style="red",
                    expand=False
                ))
                time.sleep(3)
                console.print("", Text("▶ Ready", style="bold green"), "\n")

        except Exception as e:
            console.print(Panel(
                Text(f"Error: {str(e)}", style="bold red"),
                title="[bold red]TTS Processing Error[/bold red]",
                border_style="red",
                expand=False
            ))
            time.sleep(3)
            console.print("", Text("▶ Ready", style="bold green"), "\n")

if __name__ == "__main__":
    app = AudioRecorder()
    app.run()