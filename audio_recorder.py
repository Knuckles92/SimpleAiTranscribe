import tkinter as tk
from tkinter import messagebox
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

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("audio_recorder.log"),
                        logging.StreamHandler()
                    ])

class AudioRecorder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Audio Recorder")
        self.root.geometry("300x200")
        
        # Initialize recording variables
        self.is_recording = False
        self.is_transcribing = False
        self.should_cancel = False
        self.frames = []
        self.audio = pyaudio.PyAudio()
        
        # Program enabled state
        self.program_enabled = True
        
        # Settings variables
        self.use_api = tk.BooleanVar(value=False)
        self.model_choice = tk.StringVar(value="local_whisper")  # Default to local whisper
        self.model_choice.trace_add("write", self.on_model_changed)  # Add trace to update use_api
        
        # Try system environment variables first
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        # If no API key in system env, try loading from .env file
        if not self.api_key:
            try:
                from dotenv import load_dotenv
                # Load .env file from the same directory as the script
                env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
                load_dotenv(env_path)
                self.api_key = os.getenv('OPENAI_API_KEY')
            except ImportError:
                logging.warning("python-dotenv not installed. Skipping .env file loading.")
            except Exception as e:
                logging.warning(f"Failed to load .env file: {e}")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        
        # Create status overlay window
        self.overlay = tk.Toplevel(self.root)
        self.overlay.title("")
        self.overlay.geometry("200x30")
        self.overlay.attributes('-topmost', True)
        self.overlay.overrideredirect(True)  # Remove window decorations
        self.overlay.withdraw()  # Hide initially
        
        # Create overlay label
        self.overlay_label = tk.Label(self.overlay, text="", bg='black', fg='white', pady=5)
        self.overlay_label.pack(fill=tk.BOTH, expand=True)
        
        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        
        # Setup system tray
        self.setup_system_tray()
        
        # Handle window close event
        self.root.protocol('WM_DELETE_WINDOW', self.on_closing)
        
        # Create GUI elements
        self.setup_gui()
        
        # Create transcription display
        self.transcription_text = tk.Text(self.root, height=3, wrap=tk.WORD, relief=tk.FLAT,
                                        font=('TkDefaultFont', 9), bg=self.root.cget('bg'))
        self.transcription_text.pack(padx=10, pady=(0, 10), fill=tk.X)
        self.transcription_text.config(state=tk.DISABLED)  # Make it read-only
        
        # Initialize local Whisper model
        logging.info("Loading Whisper model...")
        self.model = whisper.load_model("base")
        logging.info("Model loaded!")
        
        # Setup keyboard suppression for specific keys
        keyboard.hook(self._handle_keyboard_event, suppress=True)
        
    def _handle_keyboard_event(self, event):
        """Global keyboard event handler with suppression"""
        if event.event_type == keyboard.KEY_DOWN:
            # Handle CTRL+ALT+* for enable/disable
            if (event.name == '*' and
                keyboard.is_pressed('ctrl') and
                keyboard.is_pressed('alt')):
                self.program_enabled = not self.program_enabled
                if not self.program_enabled:
                    self.show_status_overlay("STT Disabled")
                    # Schedule overlay to hide after 1.5 seconds
                    self.root.after(1500, self.show_status_overlay, "")
                    # Unhook all keys except CTRL+ALT+*
                    keyboard.unhook_all()
                    keyboard.hook(self._handle_keyboard_event, suppress=True)
                else:
                    # Re-enable all key listeners
                    keyboard.unhook_all()
                    keyboard.hook(self._handle_keyboard_event, suppress=True)
                    self.show_status_overlay("STT Enabled")
                    # Schedule overlay to hide after 1.5 seconds
                    self.root.after(1500, self.show_status_overlay, "")
                return False  # Suppress the key combination
            
            # If program is disabled, only allow CTRL+ALT+*
            if not self.program_enabled:
                # Check if the exact CTRL+ALT+* combination is pressed
                if not (event.name == '*' and
                       keyboard.is_pressed('ctrl') and
                       keyboard.is_pressed('alt')):
                    return True
                
            if event.name == '*' and not self.is_transcribing:
                if not hasattr(self, '_last_trigger_time'):
                    self._last_trigger_time = 0
                
                # Debounce to prevent double triggers
                current_time = time.time()
                if current_time - self._last_trigger_time > 0.3:  # 300ms debounce
                    self._last_trigger_time = current_time
                    self.toggle_recording()
                return False  # Always suppress * key
                
            elif event.name == '-':
                if self.is_recording or self.is_transcribing:
                    self.cancel_transcription()
                    return False  # Suppress - key when handling
        
        # Let all other keys pass through
        return True
    
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def setup_gui(self):
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Create File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.quit_app)
        
        # Create Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_checkbutton(label="Use API", variable=self.use_api, command=self.on_api_checkbox_changed)
        
        # Create model selection submenu
        model_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label="Transcription Model", menu=model_menu)
        
        # Add model options
        model_menu.add_radiobutton(label="Local Whisper", variable=self.model_choice, value="local_whisper")
        model_menu.add_radiobutton(label="API: Whisper", variable=self.model_choice, value="api_whisper")
        model_menu.add_radiobutton(label="API: GPT-4o Transcribe", variable=self.model_choice, value="api_gpt4o")
        model_menu.add_radiobutton(label="API: GPT-4o Mini Transcribe", variable=self.model_choice, value="api_gpt4o_mini")
        
        # Create and pack widgets
        self.status_label = tk.Label(self.root, text="Status: Ready", pady=10)
        self.status_label.pack()
        
        # Add model status label
        self.model_status_label = tk.Label(self.root, text="Model: Local Whisper", pady=5, font=('TkDefaultFont', 8))
        self.model_status_label.pack()
        
        self.start_button = tk.Button(self.root, text="Start Recording",
                                    command=self.start_recording)
        self.start_button.pack(pady=5)
        
        self.stop_button = tk.Button(self.root, text="Stop Recording",
                                   command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.pack(pady=5)
        
        self.cancel_button = tk.Button(self.root, text="Cancel Transcription",
                                     command=self.cancel_transcription, state=tk.DISABLED)
        self.cancel_button.pack(pady=5)
    
    def start_recording(self):
        self.frames = []  # Initialize empty list to store audio frames
        self.is_recording = True
        self.start_button.config(state=tk.DISABLED)  # Disable the start button while recording
        self.stop_button.config(state=tk.NORMAL)  # Enable the stop button
        self.cancel_button.config(state=tk.NORMAL)  # Enable the cancel button
        self.status_label.config(text="Status: Recording...")  # Update status label to show recording state
        
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
                logging.error(f"Error recording: {e}")
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
    
    def transcribe_audio(self):
        try:
            self.is_transcribing = True
            self.should_cancel = False
            
            self.show_status_overlay("Transcribing...")
            
            # Determine if we should use API based on model selection
            use_api = self.model_choice.get().startswith("api_")
            
            if use_api:
                logging.info("\n=== Using OpenAI API ===")
                if not self.api_key:
                    logging.error("Error: No API key found!")
                    raise ValueError("OpenAI API key not found in environment variables (OPENAI_API_KEY)")
                
                logging.info(f"Using model: {self.model_choice.get()}")
                
                # Select API model based on choice
                api_model = "whisper-1"  # Default to whisper API
                
                if self.model_choice.get() == "api_gpt4o":
                    api_model = "gpt-4o-transcribe"
                elif self.model_choice.get() == "api_gpt4o_mini":
                    api_model = "gpt-4o-mini-transcribe"
                
                logging.info(f"Selected API model: {api_model}")
                logging.info("Sending audio file to OpenAI API...")
                
                # Updated API call using the new client
                with open("recorded_audio.wav", "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=api_model,
                        file=audio_file,
                        response_format="text"
                    )
                transcribed_text = response.strip()
                logging.info(f"API Response received. Length: {len(transcribed_text)} characters")
            else:
                logging.info("\n=== Using Local Whisper Model ===")
                logging.info("Processing audio with local model...")
                # Local Whisper transcription remains the same
                result = self.model.transcribe("recorded_audio.wav")
                transcribed_text = result['text'].strip()
                logging.info(f"Local transcription complete. Length: {len(transcribed_text)} characters")
            
                if self.should_cancel:
                    logging.info("Transcription cancelled by user")
                    self.show_status_overlay("")
                    self.status_label.config(text="Status: Ready")
                    self.cancel_button.config(state=tk.DISABLED)
                    self.is_transcribing = False
                    return
            
            logging.info(f"Final transcription: {transcribed_text}")
            # Update the transcription display
            self.transcription_text.config(state=tk.NORMAL)  # Temporarily enable for editing
            self.transcription_text.delete(1.0, tk.END)
            self.transcription_text.insert(tk.END, f"Transcription: {transcribed_text}")
            self.transcription_text.config(state=tk.DISABLED)  # Make read-only again
            
            # Auto-paste the final transcription
            logging.info("Pasting transcription to active window...")
            self.clear_and_paste(transcribed_text)
            self.show_status_overlay("")
            self.status_label.config(text="Status: Ready (Pasted)")
            logging.info("Transcription process complete\n")
            
        except Exception as e:
            logging.error(f"\nError during transcription: {str(e)}")
            self.show_status_overlay("")
            messagebox.showerror("Error", f"Transcription failed: {str(e)}")
            self.status_label.config(text="Status: Ready")
        finally:
            self.is_transcribing = False
            self.should_cancel = False
            self.cancel_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)
    
    
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
        """Setup the system tray icon and menu"""
        # Create a simple icon (you might want to replace this with a proper icon file)
        icon_data = Image.new('RGB', (64, 64), color='red')
        menu = (
            pystray.MenuItem('Show', self.show_window),
            pystray.MenuItem('Exit', self.quit_app)
        )
        self.tray_icon = pystray.Icon("audio_recorder", icon_data, "Audio Recorder", menu)
        
    def show_window(self, icon=None, item=None):
        """Show the main window"""
        self.root.deiconify()
        self.root.state('normal')
        
    def hide_window(self):
        """Hide the main window"""
        self.root.withdraw()
        if not self.tray_icon.visible:
            self.tray_icon_thread = threading.Thread(target=self.tray_icon.run)
            self.tray_icon_thread.start()
            
    def on_closing(self):
        """Handle window closing event"""
        self.hide_window()  # Hide window
        
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        if self.tray_icon and self.tray_icon.visible:
            self.tray_icon.stop()
        self.root.quit()
        # Clean up keyboard hook before exiting
        keyboard.unhook_all()
        self.audio.terminate()

    def run(self):
        # Make window stay on top
        self.root.attributes('-topmost', True)
        # Remove the self.root.withdraw() line to show window on startup
        self.root.mainloop()
        # Clean up keyboard hook before exiting
        keyboard.unhook_all()
        self.audio.terminate()

    def on_model_changed(self, *args):
        """Update the use_api variable when model choice changes"""
        # If model starts with "api_", it's an API model
        self.use_api.set(self.model_choice.get().startswith("api_"))
        
        # Update model status label
        model_text = "Model: "
        choice = self.model_choice.get()
        
        if choice == "local_whisper":
            model_text += "Local Whisper"
        elif choice == "api_whisper":
            model_text += "API: Whisper"
        elif choice == "api_gpt4o":
            model_text += "API: GPT-4o Transcribe"
        elif choice == "api_gpt4o_mini":
            model_text += "API: GPT-4o Mini Transcribe"
            
        self.model_status_label.config(text=model_text)

    def on_api_checkbox_changed(self):
        """Update model choice when the API checkbox is toggled"""
        if self.use_api.get():
            # If API is checked and current model is local, set to default API model
            if self.model_choice.get() == "local_whisper":
                self.model_choice.set("api_whisper")
        else:
            # If API is unchecked, set to local model
            self.model_choice.set("local_whisper")

if __name__ == "__main__":
    app = AudioRecorder()
    app.run()