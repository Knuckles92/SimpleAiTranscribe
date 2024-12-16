import tkinter as tk
from tkinter import messagebox
import pyaudio
import wave
import threading
import os
import numpy as np
import pyperclip
import keyboard
from openai import OpenAI
from pathlib import Path
import whisper  # This will now use the openai-whisper package
from dotenv import load_dotenv  # Import load_dotenv
import pystray
from PIL import Image

# Load environment variables from .env file
load_dotenv()  # This will load variables from .env into the environment

# Add ffmpeg to PATH - updated to include bin directory
os.environ["PATH"] = "C:/ffmpeg/bin" + os.pathsep + os.environ["PATH"]

class AudioRecorder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Audio Recorder")
        self.root.geometry("215x175")

        # Initialize recording variables
        self.is_recording = False
        self.is_transcribing = False
        self.should_cancel = False
        self.frames = []
        self.audio = pyaudio.PyAudio()

        # Initialize system tray variables
        self.icon = None
        self.icon_running = False
        self.icon_image = Image.new('RGB', (64, 64), color='red')
        self.setup_system_tray()

        # Settings variables
        self.use_api = tk.BooleanVar(value=False)
        self.api_key = os.getenv('OPENAI_API_KEY')  # Retrieve API key

        # Initialize OpenAI client
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            print("OpenAI client initialized with API key from environment variables.")
        else:
            self.client = None
            print("OpenAI API key not found in environment variables or .env file.")

        # Create status overlay window
        self.overlay = tk.Toplevel(self.root)
        self.overlay.title("")
        self.overlay.geometry("200x30")
        self.overlay.attributes('-topmost', True)
        self.overlay.overrideredirect(True)  # Remove window decorations
        self.overlay.withdraw()  # Initially hide the overlay

        # Create overlay label
        self.overlay_label = tk.Label(self.overlay, text="", bg='black', fg='white', pady=5)
        self.overlay_label.pack(fill=tk.BOTH, expand=True)

        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100

        # Set audio file path to be in the same directory as the script
        script_dir = Path(__file__).parent.absolute()
        self.audio_file_path = str(script_dir / "recorded_audio.wav")
        print(f"Audio file will be saved to: {self.audio_file_path}")

        # Verify ffmpeg is available
        try:
            import subprocess
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            print("ffmpeg is available in PATH")
        except Exception as e:
            print(f"Warning: ffmpeg check failed: {e}")
            messagebox.showwarning("Warning", "ffmpeg not found in PATH. Audio transcription may fail.")

        # Create GUI elements
        self.setup_gui()

        # Initialize model asynchronously
        self.model = None
        threading.Thread(target=self.initialize_model).start()

        # Setup keyboard shortcuts
        keyboard.add_hotkey('num *', self.toggle_recording, suppress=True)
        keyboard.add_hotkey('esc', self.cancel_transcription, suppress=True)

        # Handle window close button
        self.root.protocol('WM_DELETE_WINDOW', self.minimize_to_tray)

    def handle_global_keypress(self, event):
        """This method is no longer used as we're using keyboard.add_hotkey instead"""
        pass

    def toggle_recording(self):
        """Handle toggle recording with model loading check"""
        if not self.model:
            messagebox.showinfo("Please wait", "Model is still loading...")
            return
        if not self.is_transcribing:
            if not self.is_recording:
                self.start_recording()
            else:
                self.stop_recording()

    def setup_gui(self):
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Create Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_checkbutton(label="Use Whisper API", variable=self.use_api, 
                                      command=self.switch_version)

        # Create model indicator
        self.model_indicator = tk.Label(self.root, text="Model: Loading...", pady=5)
        self.model_indicator.pack()

        # Create and pack widgets
        self.status_label = tk.Label(self.root, text="Status: Initializing...", pady=5)
        self.status_label.pack()

        self.start_button = tk.Button(self.root, text="Start Recording", 
                                     command=self.start_recording)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(self.root, text="Stop Recording", 
                                    command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.cancel_button = tk.Button(self.root, text="Cancel Transcription", 
                                      command=self.cancel_transcription, state=tk.DISABLED)
        self.cancel_button.pack(pady=5)

        self.transcription_label = tk.Label(self.root, text="", wraplength=250)
        self.transcription_label.pack(pady=10)

    def initialize_model(self):
        """Initialize the Whisper model in a separate thread"""
        self.status_label.config(text="Status: Loading Whisper model...")
        print("Loading Whisper model...")
        try:
            self.model = whisper.load_model("base")
            print("Model loaded successfully!")
            self.status_label.config(text="Status: Ready")
            self.update_model_indicator()
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            self.status_label.config(text="Status: Error loading model")
            messagebox.showerror("Error", f"Failed to load Whisper model: {e}")

    def update_model_indicator(self):
        """Update the model indicator text"""
        model_text = "API" if self.use_api.get() else "Local"
        self.model_indicator.config(text=f"Model: {model_text}")

    def start_recording(self):
        self.frames = []  # Initialize empty list to store audio frames
        self.is_recording = True
        self.start_button.config(state=tk.DISABLED)  # Disable the start button while recording
        self.stop_button.config(state=tk.NORMAL)  # Enable the stop button
        self.cancel_button.config(state=tk.NORMAL)  # Enable the cancel button
        self.status_label.config(text="Status: Recording...")  # Update status label to show recording state
        self.transcription_label.config(text="")  # Clear any previous transcription text

        # Show recording status
        self.show_status_overlay("Recording...")

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
                print(f"Error recording: {e}")
                break

        stream.stop_stream()
        stream.close()

    def stop_recording(self):
        self.is_recording = False
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Processing...")

        # Update status overlay
        self.show_status_overlay("Processing...")

        # Save the recording
        self.save_recording()

        # Transcribe in a separate thread
        threading.Thread(target=self.transcribe_audio).start()

    def save_recording(self):
        try:
            print(f"Saving audio to: {self.audio_file_path}")
            with wave.open(self.audio_file_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.frames))

            # Verify the file was saved correctly
            if not os.path.exists(self.audio_file_path):
                raise FileNotFoundError(f"Failed to save audio file at: {self.audio_file_path}")

            file_size = os.path.getsize(self.audio_file_path)
            print(f"Audio saved successfully. File size: {file_size} bytes")

            if file_size == 0:
                raise ValueError("Audio file was saved but is empty")

        except Exception as e:
            print(f"Error saving audio file: {e}")
            raise

    def cancel_transcription(self):
        self.should_cancel = True
        if self.is_recording:
            self.is_recording = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="Status: Cancelled")
            self.show_status_overlay("")
        elif self.is_transcribing:
            self.status_label.config(text="Status: Canceling...")

        self.cancel_button.config(state=tk.DISABLED)

    def clear_and_paste(self, text):
        """Paste text at current cursor position."""
        pyperclip.copy(text)
        keyboard.send('ctrl+v')  # Paste new text

    def validate_audio_file(self):
        """Validate the audio file before transcription"""
        if not os.path.exists(self.audio_file_path):
            raise FileNotFoundError(f"Audio file not found at: {self.audio_file_path}")

        file_size = os.path.getsize(self.audio_file_path)
        if file_size == 0:
            raise ValueError("Audio file exists but is empty")

        print(f"Audio file validation passed. Size: {file_size} bytes")
        return True

    def transcribe_audio(self):
        try:
            self.is_transcribing = True
            self.should_cancel = False

            self.show_status_overlay("Transcribing...")

            # Validate audio file
            self.validate_audio_file()

            if self.use_api.get():
                print("\n=== Using OpenAI Whisper API ===")
                if not self.api_key:
                    print("Error: No API key found!")
                    raise ValueError("OpenAI API key not found in environment variables (OPENAI_API_KEY)")

                print("Sending audio file to OpenAI API...")
                with open(self.audio_file_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )
                transcribed_text = response.strip()
                print(f"API Response received. Length: {len(transcribed_text)} characters")
            else:
                print("\n=== Using Local Whisper Model ===")
                print("Processing audio with local model...")
                try:
                    # Use absolute path and disable fp16
                    abs_path = str(Path(self.audio_file_path).resolve())
                    print(f"Using absolute path: {abs_path}")

                    # Verify ffmpeg is available before transcription
                    import subprocess
                    subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
                    print("ffmpeg verified before transcription")

                    # Try transcription with more explicit options
                    result = self.model.transcribe(
                        abs_path,
                        fp16=False,
                        language='en',  # Explicitly set language to English
                        task='transcribe'
                    )

                    transcribed_text = result['text'].strip()
                    print(f"Local transcription complete. Length: {len(transcribed_text)} characters")
                except Exception as e:
                    print(f"Error during local transcription: {e}")
                    print(f"Current working directory: {os.getcwd()}")
                    print(f"Audio file path: {abs_path}")
                    print(f"Audio file exists: {os.path.exists(abs_path)}")
                    # Try to get more detailed ffmpeg error
                    try:
                        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
                    except Exception as ffmpeg_e:
                        print(f"ffmpeg error: {ffmpeg_e}")
                    raise

            if self.should_cancel:
                print("Transcription cancelled by user")
                self.show_status_overlay("")
                self.status_label.config(text="Status: Ready")
                self.cancel_button.config(state=tk.DISABLED)
                self.is_transcribing = False
                return

            print(f"Final transcription: {transcribed_text}")
            self.transcription_label.config(text=f"Transcription: {transcribed_text}")

            # Auto-paste the final transcription
            print("Pasting transcription to active window...")
            self.clear_and_paste(transcribed_text)
            self.show_status_overlay("")
            self.status_label.config(text="Status: Ready (Pasted)")
            print("Transcription process complete\n")

        except Exception as e:
            print(f"\nError during transcription: {str(e)}")
            self.show_status_overlay("")
            messagebox.showerror("Error", f"Transcription failed: {str(e)}")
            self.status_label.config(text="Status: Ready")
        finally:
            self.is_transcribing = False
            self.should_cancel = False
            self.cancel_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def show_status_overlay(self, message):
        """Show status overlay with given message"""
        if message:
            # Position overlay near mouse cursor
            x = self.root.winfo_pointerx() + 10
            y = self.root.winfo_pointery() + 10
            self.overlay.geometry(f"+{x}+{y}")

            self.overlay_label.config(text=message)
            self.overlay.deiconify()
        else:
            self.overlay.withdraw()

    def setup_system_tray(self):
        # Create the system tray menu
        menu = (
            pystray.MenuItem('Show', self.show_window),
            pystray.MenuItem('Exit', self.quit_app)
        )
        
        # Create a new icon instance
        self.icon = pystray.Icon("audio_recorder", self.icon_image, "Audio Recorder", menu)
        
    def show_window(self, icon=None, item=None):
        if self.icon_running:
            self.icon.stop()
            self.icon_running = False
            self.icon = None  # Clear the icon reference
        self.root.after(0, self.root.deiconify)
        
    def minimize_to_tray(self):
        self.root.withdraw()
        # Create a new icon instance each time we minimize
        self.setup_system_tray()
        threading.Thread(target=self.run_icon, daemon=True).start()
            
    def run_icon(self):
        if not self.icon_running and self.icon is not None:
            self.icon_running = True
            self.icon.run()
            self.icon_running = False
            
    def quit_app(self, icon=None, item=None):
        if self.icon_running and self.icon is not None:
            self.icon.stop()
            self.icon_running = False
            self.icon = None
        self.root.quit()

    def switch_version(self):
        """Switch between API and local model version"""
        if self.use_api.get() and not self.api_key:
            messagebox.showerror("Error", "API key not found. Please check your .env file.")
            self.use_api.set(False)
        self.update_model_indicator()

    def run(self):
        # Make window stay on top
        self.root.attributes('-topmost', True)
        self.root.mainloop()
        if self.icon is not None:
            self.icon.stop()
        # Clean up keyboard hook before exiting
        keyboard.unhook_all()
        self.audio.terminate()

if __name__ == "__main__":
    app = AudioRecorder()
    app.run()
