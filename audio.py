import tkinter as tk
from tkinter import messagebox, ttk
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
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
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
        self.model_choice = tk.StringVar(value="local_whisper")  # Default to local whisper
        self.model_choice.trace_add("write", self.on_model_changed)  # Add trace for model changes
        
        # Hotkey configuration
        self.settings_file = "audio_recorder_settings.json"
        self.hotkeys = self.load_hotkey_settings()

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
            # Log all keyboard events for debugging
            #logging.info(f"Keyboard event: {event.name}, event_type: {event.event_type}, scan_code: {event.scan_code}")

            # Check enable/disable hotkey
            if self._matches_hotkey(event, self.hotkeys['enable_disable']):
                self.program_enabled = not self.program_enabled
                if not self.program_enabled:
                    self.show_status_overlay("STT Disabled")
                    # Schedule overlay to hide after 1.5 seconds
                    self.root.after(1500, self.show_status_overlay, "")
                    # Unhook all keys except enable/disable
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

            # If program is disabled, only allow enable/disable hotkey
            if not self.program_enabled:
                if not self._matches_hotkey(event, self.hotkeys['enable_disable']):
                    return True

            # Check record toggle hotkey
            elif self._matches_hotkey(event, self.hotkeys['record_toggle']) and not self.is_transcribing:
                if not hasattr(self, '_last_trigger_time'):
                    self._last_trigger_time = 0

                # Debounce to prevent double triggers
                current_time = time.time()
                if current_time - self._last_trigger_time > 0.3:  # 300ms debounce
                    self._last_trigger_time = current_time
                    self.toggle_recording()
                return False  # Always suppress record toggle key

            # Check cancel hotkey
            elif self._matches_hotkey(event, self.hotkeys['cancel']):
                # Always call cancel_transcription to stop any ongoing process
                # This makes the cancel key a universal stop button
                self.cancel_transcription()
                return False  # Suppress cancel key when handling

        # Let all other keys pass through
        return True

    def _matches_hotkey(self, event, hotkey_string):
        """Check if the current event matches a hotkey string"""
        if not hotkey_string:
            return False
            
        # Parse hotkey string (e.g., "ctrl+alt+*", "*", "shift+f1")
        parts = hotkey_string.lower().split('+')
        main_key = parts[-1]  # Last part is the main key
        modifiers = parts[:-1]  # Everything else are modifiers
        
        # Check if main key matches
        if event.name.lower() != main_key:
            return False
            
        # Check modifiers
        for modifier in modifiers:
            if modifier == 'ctrl' and not keyboard.is_pressed('ctrl'):
                return False
            elif modifier == 'alt' and not keyboard.is_pressed('alt'):
                return False
            elif modifier == 'shift' and not keyboard.is_pressed('shift'):
                return False
            elif modifier == 'win' and not keyboard.is_pressed('win'):
                return False
                
        # Check that no extra modifiers are pressed
        if 'ctrl' not in modifiers and keyboard.is_pressed('ctrl'):
            return False
        if 'alt' not in modifiers and keyboard.is_pressed('alt'):
            return False
        if 'shift' not in modifiers and keyboard.is_pressed('shift'):
            return False
        if 'win' not in modifiers and keyboard.is_pressed('win'):
            return False
            
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
        settings_menu.add_command(label="Configure Hotkeys", command=self.open_hotkey_settings)

        # Create and pack widgets
        self.status_label = tk.Label(self.root, text="Status: Ready", pady=10)
        self.status_label.pack()

        # Add model selection dropdown
        model_frame = tk.Frame(self.root)
        model_frame.pack(pady=5)
        
        tk.Label(model_frame, text="Model:", font=('TkDefaultFont', 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.model_combobox = ttk.Combobox(model_frame, textvariable=self.model_choice, width=25, state="readonly")
        self.model_combobox['values'] = (
            'Local Whisper',
            'API: Whisper', 
            'API: GPT-4o Transcribe',
            'API: GPT-4o Mini Transcribe'
        )
        # Map display names to internal values
        self.model_value_map = {
            'Local Whisper': 'local_whisper',
            'API: Whisper': 'api_whisper',
            'API: GPT-4o Transcribe': 'api_gpt4o',
            'API: GPT-4o Mini Transcribe': 'api_gpt4o_mini'
        }
        self.model_display_map = {v: k for k, v in self.model_value_map.items()}
        
        # Set initial display value
        self.model_combobox.set(self.model_display_map[self.model_choice.get()])
        self.model_combobox.bind('<<ComboboxSelected>>', self.on_model_combobox_changed)
        self.model_combobox.pack(side=tk.LEFT)

        self.start_button = tk.Button(self.root, text="Start Recording",
                                    command=self.start_recording)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(self.root, text="Stop Recording",
                                   command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.cancel_button = tk.Button(self.root, text="Stop",
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
        """Universal stop button that cancels transcription"""
        self.should_cancel = True

        # Handle recording state
        if self.is_recording:
            self.is_recording = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="Status: Cancelled")
            self.show_status_overlay("Recording Cancelled")
            self.root.after(1500, self.show_status_overlay, "")
        # Handle transcribing state
        elif self.is_transcribing:
            self.status_label.config(text="Status: Canceling...")
            self.show_status_overlay("Canceling Transcription...")
            self.root.after(1500, self.show_status_overlay, "")

        # Always disable the cancel button after stopping
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
                api_model = "gpt-4o-mini-transcribe"  # Default to mini model

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

    def show_window(self, *_):
        """Show the main window (parameters needed for system tray callback)"""
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

    def quit_app(self, *_):
        """Quit the application"""
        if self.tray_icon and self.tray_icon.visible:
            self.tray_icon.stop()

        # Clean up keyboard hooks before exiting
        try:
            keyboard.unhook_all()
        except Exception as e:
            logging.error(f"Error cleaning up keyboard hooks: {e}")

        self.audio.terminate()
        self.root.quit()

    def run(self):
        # Make window stay on top
        self.root.attributes('-topmost', True)
        # Remove the self.root.withdraw() line to show window on startup

        try:
            self.root.mainloop()
        finally:
            # Clean up keyboard hooks before exiting
            try:
                keyboard.unhook_all()
            except Exception as e:
                logging.error(f"Error cleaning up keyboard hooks: {e}")

            self.audio.terminate()

    def on_model_combobox_changed(self, event=None):
        """Handle combobox selection change"""
        display_value = self.model_combobox.get()
        internal_value = self.model_value_map.get(display_value)
        if internal_value:
            self.model_choice.set(internal_value)

    def on_model_changed(self, *_):
        """Called when model choice changes - now only for logging purposes"""
        choice = self.model_choice.get()
        logging.info(f"Model changed to: {choice}")

    def open_hotkey_settings(self):
        """Open hotkey configuration dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configure Hotkeys")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Main frame
        main_frame = tk.Frame(dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="Hotkey Configuration", font=('TkDefaultFont', 12, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Hotkey entries
        self.hotkey_vars = {}
        
        # Record Toggle
        record_frame = tk.Frame(main_frame)
        record_frame.pack(fill=tk.X, pady=5)
        tk.Label(record_frame, text="Record Toggle:", width=15, anchor='w').pack(side=tk.LEFT)
        self.hotkey_vars['record_toggle'] = tk.StringVar(value=self.hotkeys['record_toggle'])
        record_entry = tk.Entry(record_frame, textvariable=self.hotkey_vars['record_toggle'], width=20)
        record_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Cancel
        cancel_frame = tk.Frame(main_frame)
        cancel_frame.pack(fill=tk.X, pady=5)
        tk.Label(cancel_frame, text="Cancel:", width=15, anchor='w').pack(side=tk.LEFT)
        self.hotkey_vars['cancel'] = tk.StringVar(value=self.hotkeys['cancel'])
        cancel_entry = tk.Entry(cancel_frame, textvariable=self.hotkey_vars['cancel'], width=20)
        cancel_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Enable/Disable
        enable_frame = tk.Frame(main_frame)
        enable_frame.pack(fill=tk.X, pady=5)
        tk.Label(enable_frame, text="Enable/Disable:", width=15, anchor='w').pack(side=tk.LEFT)
        self.hotkey_vars['enable_disable'] = tk.StringVar(value=self.hotkeys['enable_disable'])
        enable_entry = tk.Entry(enable_frame, textvariable=self.hotkey_vars['enable_disable'], width=20)
        enable_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Instructions
        instructions = tk.Label(main_frame, text=
            "Instructions:\n"
            "• Single keys: a, b, *, -, etc.\n"
            "• Combinations: ctrl+alt+*, shift+f1, etc.\n"
            "• Special keys: space, enter, esc, f1-f12\n"
            "• Current defaults: * (record), - (cancel), ctrl+alt+* (enable/disable)",
            justify=tk.LEFT, wraplength=360, font=('TkDefaultFont', 9))
        instructions.pack(pady=20, fill=tk.X)
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        tk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(button_frame, text="Apply", command=lambda: self.apply_hotkey_settings(dialog)).pack(side=tk.RIGHT)
        tk.Button(button_frame, text="Reset to Defaults", command=self.reset_hotkeys_to_defaults).pack(side=tk.LEFT)
        
    def reset_hotkeys_to_defaults(self):
        """Reset hotkeys to default values"""
        defaults = {
            'record_toggle': '*',
            'cancel': '-',
            'enable_disable': 'ctrl+alt+*'
        }
        for key, default_value in defaults.items():
            if key in self.hotkey_vars:
                self.hotkey_vars[key].set(default_value)
    
    def apply_hotkey_settings(self, dialog):
        """Apply the new hotkey settings"""
        try:
            # Update hotkeys dictionary
            for key, var in self.hotkey_vars.items():
                new_value = var.get().strip()
                if new_value:
                    self.hotkeys[key] = new_value
            
            # Save settings to file
            self.save_hotkey_settings()
            
            # Restart keyboard hook with new hotkeys
            keyboard.unhook_all()
            keyboard.hook(self._handle_keyboard_event, suppress=True)
            
            messagebox.showinfo("Success", "Hotkeys updated successfully!")
            dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update hotkeys: {str(e)}")

    def load_hotkey_settings(self):
        """Load hotkey settings from file, return defaults if file doesn't exist"""
        defaults = {
            'record_toggle': '*',
            'cancel': '-',
            'enable_disable': 'ctrl+alt+*'
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get('hotkeys', defaults)
        except Exception as e:
            logging.warning(f"Failed to load settings: {e}")
        
        return defaults
    
    def save_hotkey_settings(self):
        """Save hotkey settings to file"""
        try:
            settings = {'hotkeys': self.hotkeys}
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            logging.info("Hotkey settings saved successfully")
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
            raise

if __name__ == "__main__":
    app = AudioRecorder()
    app.run()