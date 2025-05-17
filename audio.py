import argparse
import pyaudio
import wave
import threading
import whisper
import os
import pyperclip
import keyboard
from openai import OpenAI
import pystray
from PIL import Image
import time
import logging
import pygame  
import tkinter as tk
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.text import Text
from rich.style import Style
from rich.live import Live
from rich.table import Table

# Ensure res directory exists
os.makedirs('res', exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join("res", "audio_recorder.log"))
                    ])

console = Console()

class StoppableAudio:
    def __init__(self):
        self.playing = False
        self.initialized = False
        # Ensure res directory exists
        os.makedirs('res', exist_ok=True)
        self.temp_file = os.path.join("res", "temp_audio.wav")

        self._init_pygame()

    def _init_pygame(self):
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
        if not self.initialized:
            self._init_pygame()

        if not self.initialized:
            logging.error("Cannot play audio: pygame mixer could not be initialized")
            return False

        try:
            audio_segment.export(self.temp_file, format="wav")

            pygame.mixer.music.stop()

            pygame.mixer.music.load(self.temp_file)
            pygame.mixer.music.play()

            self.playing = True
            return True
        except Exception as e:
            logging.error(f"Error playing audio with pygame: {e}")
            return False

    def stop(self):
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
        parser = argparse.ArgumentParser(description="Audio Recorder CLI")
        parser.add_argument('--model', choices=['local', 'api', '4o', '4om'], default='local', 
                         help='Transcription model: local=local_whisper, api=api_whisper, 4o=gpt-4o, 4om=gpt-4o-mini')
        args = parser.parse_args()

        self.model_mapping = {
            'local': 'local_whisper',
            'api': 'api_whisper',
            '4o': 'api_gpt4o',
            '4om': 'api_gpt4o_mini'
        }
        self.model_choice = self.model_mapping[args.model]

        self.is_recording = False
        self.is_transcribing = False
        self.is_playing_audio = False
        self.should_cancel = False
        self.frames = []
        self.audio = pyaudio.PyAudio()

        self.audio_player = StoppableAudio()

        self.program_enabled = True
        
        # Create status overlay window
        self.overlay = tk.Tk()
        self.overlay.title("")
        self.overlay.geometry("200x30")
        self.overlay.attributes('-topmost', True)
        self.overlay.overrideredirect(True)  # Remove window decorations
        self.overlay.withdraw()  # Hide initially
        
        # Create overlay label
        self.overlay_label = tk.Label(self.overlay, text="", bg='black', fg='white', pady=5)
        self.overlay_label.pack(fill=tk.BOTH, expand=True)

        self.use_api = self.model_choice.startswith('api_')

        self.api_key = os.getenv('OPENAI_API_KEY')

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

        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100

        self.setup_system_tray()

        logging.info("Loading Whisper model...")
        self.model = whisper.load_model("base")
        logging.info("Model loaded!")

        keyboard.hook(self._handle_keyboard_event, suppress=True)
        keyboard.add_hotkey('f9', lambda: None, suppress=True)

        welcome_panel = Panel(
            Text(f"Audio Recorder", style="bold white on blue", justify="center"),
            subtitle=Text(f"Version 1.0", style="italic", justify="center"),
            border_style="blue"
        )
        console.print(welcome_panel)

        table = Table(show_header=True, header_style="bold cyan", border_style="blue")
        table.add_column("Setting", style="dim")
        table.add_column("Value", style="green")
        
        table.add_row("Model", self.model_choice)
        table.add_row("API Mode", "✅ Enabled" if self.use_api else "❌ Disabled")
        
        
        console.print(table)
        
        shortcuts = Table(show_header=True, header_style="bold magenta", title="Keyboard Shortcuts", border_style="magenta")
        shortcuts.add_column("Key", style="cyan")
        shortcuts.add_column("Action", style="yellow")
        
        shortcuts.add_row("*", "Start/Stop Recording")
        shortcuts.add_row("-", "Cancel/Stop Any Process")
        shortcuts.add_row("Ctrl+Alt+*", "Enable/Disable Program")
        
        console.print(shortcuts)
        console.print("", Text("▶ Ready", style="bold green"), "\n")

    def _handle_keyboard_event(self, event):
        if event.event_type == keyboard.KEY_DOWN:
            logging.info(f"Keyboard event: {event.name}, event_type: {event.event_type}, scan_code: {event.scan_code}")
            if (event.name == '*' and
                keyboard.is_pressed('ctrl') and
                keyboard.is_pressed('alt')):
                self.program_enabled = not self.program_enabled
                if not self.program_enabled:
                    self.show_status_overlay("STT Disabled")
                    # Schedule overlay to hide after 1.5 seconds
                    self.overlay.after(1500, self.show_status_overlay, "")
                    keyboard.unhook_all()
                    keyboard.hook(self._handle_keyboard_event, suppress=True)
                else:
                    keyboard.unhook_all()
                    keyboard.hook(self._handle_keyboard_event, suppress=True)
                    self.show_status_overlay("STT Enabled")
                    # Schedule overlay to hide after 1.5 seconds
                    self.overlay.after(1500, self.show_status_overlay, "")
                return False

            if not self.program_enabled:
                if not (event.name == '*' and
                       keyboard.is_pressed('ctrl') and
                       keyboard.is_pressed('alt')):
                    return True

            elif event.name == '*' and not self.is_transcribing:
                if not hasattr(self, '_last_trigger_time'):
                    self._last_trigger_time = 0

                current_time = time.time()
                if current_time - self._last_trigger_time > 0.3:
                    self._last_trigger_time = current_time
                    self.toggle_recording()
                return False

            elif event.name == '-':
                self.cancel_transcription()
                return False
        return True

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.frames = []
        self.is_recording = True
        self.status_label = "Recording..."
        
        # Show recording status in overlay
        self.show_status_overlay("Recording...")

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
        
        # Update status overlay
        self.show_status_overlay("Processing...")
        
        with console.status("[bold blue]Processing audio...", spinner="dots"):
            self.save_recording()
        
        # Update status overlay
        self.show_status_overlay("Transcribing...")

        transcription_thread = threading.Thread(target=self.transcribe_audio, daemon=True)
        transcription_thread.start()

    def save_recording(self):
        # Ensure res directory exists
        os.makedirs('res', exist_ok=True)
        
        # Use the res directory for audio files
        file_path = os.path.join('res', "recorded_audio.wav")
        
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
        return file_path

    def cancel_transcription(self):
        self.should_cancel = True

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

        if self.is_recording:
            self.is_recording = False
            self.status_label = "Recording Cancelled"
            self.show_status_overlay("Recording Cancelled")
            # Schedule overlay to hide after 1.5 seconds
            self.overlay.after(1500, self.show_status_overlay, "")
            console.print(Panel(
                Text("⏹️ Recording Cancelled", style="bold red"),
                border_style="red",
                expand=False
            ))
            time.sleep(1.5)
        elif self.is_transcribing:
            self.status_label = "Canceling..."
            self.show_status_overlay("Canceling...")
            # Schedule overlay to hide after 1.5 seconds
            self.overlay.after(1500, self.show_status_overlay, "")
            console.print(Panel(
                Text("⏹️ Cancelling Process...", style="bold red"),
                border_style="red",
                expand=False
            ))
            time.sleep(1.5)
        
        console.print("", Text("▶ Ready", style="bold green"), "\n")

    def transcribe_audio(self):
        try:
            self.is_transcribing = True
            self.should_cancel = False

            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[bold]{task.percentage:.0f}%"),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                transcribe_task = progress.add_task("[cyan]Transcribing audio...", total=100)
                progress.update(transcribe_task, advance=10)
                
                use_api = self.model_choice.startswith("api_")

                if use_api:
                    if self.model_choice == "api_whisper":
                        api_model = "whisper-1"
                    elif self.model_choice == "api_gpt4o":
                        api_model = "gpt-4o-transcribe"
                    elif self.model_choice == "api_gpt4o_mini":
                        api_model = "gpt-4o-mini-transcribe"

                    logging.info("\n=== Using OpenAI API ===")
                    if not self.api_key:
                        logging.error("Error: No API key found!")
                        raise ValueError("OpenAI API key not found in environment variables (OPENAI_API_KEY)")

                    logging.info(f"Using model: {self.model_choice}")

                    logging.info(f"Selected API model: {api_model}")
                    logging.info("Sending audio file to OpenAI API...")
                    progress.update(transcribe_task, description="[magenta]Sending to OpenAI API...", advance=20)

                    with open(os.path.join("res", "recorded_audio.wav"), "rb") as audio_file:
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
                    progress.update(transcribe_task, description="[magenta]Processing with local Whisper model...", advance=20)
                    result = self.model.transcribe(os.path.join("res", "recorded_audio.wav"))
                    transcribed_text = result['text'].strip()
                    logging.info(f"Local transcription complete. Length: {len(transcribed_text)} characters")
                    progress.update(transcribe_task, description="[green]Finalizing transcription...", advance=60)

                    if self.should_cancel:
                        logging.info("Transcription cancelled by user")
                        console.print("", Text("▶ Ready", style="bold green"), "\n")
                        self.status_label = "Ready"
                        return

                logging.info(f"Final transcription: {transcribed_text}")
                
                if 'progress' in locals():
                    progress.update(transcribe_task, description="[bold green]Transcription complete!", advance=10)
                
                console.print(Panel(
                    Text(transcribed_text, style="white"),
                    title="[bold green]Transcription Result[/bold green]",
                    border_style="green",
                    expand=True
                ))

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

    def show_status_overlay(self, message):
        """Show status overlay with given message"""
        if message:
            # Position overlay near mouse cursor
            x = self.overlay.winfo_pointerx() + 10
            y = self.overlay.winfo_pointery() + 10
            self.overlay.geometry(f"+{x}+{y}")
            
            self.overlay_label.config(text=message)
            self.overlay.deiconify()
            self.overlay.update()
            
            # Also print to console for CLI mode
            console.print(Text(f"▶ {message}", style="bold blue"))
        else:
            self.overlay.withdraw()

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
        except Exception as e:
            logging.error(f"Error cleaning up keyboard hooks: {e}")
        if self.audio_player.initialized:
            try:
                pygame.mixer.quit()
                pygame.quit()
            except Exception as e:
                logging.error(f"Error cleaning up pygame: {e}")
        self.audio.terminate()
        # Destroy the overlay window
        try:
            self.overlay.destroy()
        except Exception as e:
            logging.error(f"Error destroying overlay: {e}")
        console.print(Panel(
            Text("Goodbye! Thank you for using Audio Recorder CLI", style="bold white"),
            border_style="blue", 
            expand=False
        ))
        os._exit(0)

    def run(self):
        try:
            # Update the overlay position periodically when visible
            def update_overlay_position():
                if self.overlay.state() == 'normal':  # If overlay is visible
                    x = self.overlay.winfo_pointerx() + 10
                    y = self.overlay.winfo_pointery() + 10
                    self.overlay.geometry(f"+{x}+{y}")
                self.overlay.after(100, update_overlay_position)  # Schedule next update
            
            # Start the position update loop
            update_overlay_position()
            
            # Start the tkinter main loop
            self.overlay.mainloop()
        except KeyboardInterrupt:
            self.quit_app()

if __name__ == "__main__":
    app = AudioRecorder()
    app.run()