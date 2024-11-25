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
        
        # Settings variables
        self.use_api = tk.BooleanVar(value=False)
        self.api_key = os.getenv('OPENAI_API_KEY')
        
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
        
        # Create GUI elements
        self.setup_gui()
        
        # Initialize local Whisper model
        print("Loading Whisper model...")
        self.model = whisper.load_model("base")
        print("Model loaded!")
        
        # Setup keyboard listener
        keyboard.on_press_key('num *', self.handle_shortcut, suppress=True)
        keyboard.on_press_key('esc', self.handle_escape, suppress=True)
    
    def handle_escape(self, event):
        """Handle the escape key press"""
        if self.is_recording or self.is_transcribing:
            self.cancel_transcription()
    
    def handle_shortcut(self, event):
        """Handle the shortcut key press"""
        # Only toggle if we're not currently transcribing
        if not self.is_transcribing:
            self.toggle_recording()
    
    def toggle_recording(self):
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
        settings_menu.add_checkbutton(label="Use Whisper API", variable=self.use_api)
        
        # Create and pack widgets
        self.status_label = tk.Label(self.root, text="Status: Ready", pady=10)
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
            
            if self.use_api.get():
                print("\n=== Using OpenAI Whisper API ===")
                if not self.api_key:
                    print("Error: No API key found!")
                    raise ValueError("OpenAI API key not found in environment variables (OPENAI_API_KEY)")
                
                print("Sending audio file to OpenAI API...")
                # Updated API call using the new client
                with open("recorded_audio.wav", "rb") as audio_file:
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
                # Local Whisper transcription remains the same
                result = self.model.transcribe("recorded_audio.wav")
                transcribed_text = result['text'].strip()
                print(f"Local transcription complete. Length: {len(transcribed_text)} characters")
            
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
    
    def run(self):
        # Make window stay on top
        self.root.attributes('-topmost', True)
        self.root.mainloop()
        # Clean up keyboard hook before exiting
        keyboard.unhook_all()
        self.audio.terminate()

if __name__ == "__main__":
    app = AudioRecorder()
    app.run()