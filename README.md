# Audio Recorder

A desktop application for recording and transcribing audio with multiple transcription options. It supports both local Whisper models and OpenAI API transcription (including GPT-4o variants). The app features a minimal Tkinter GUI, system tray integration, keyboard shortcuts, and a real-time status overlay.

---

## Features

- **Audio Recording**:
  - High-quality audio recording using PyAudio
  - Configurable sample rate (44.1kHz default) and channels
  - Automatic saving as WAV file

- **Transcription Options**:
  - Local transcription using OpenAI Whisper (base model)
  - API-based transcription with:
    - Whisper API
    - GPT-4o Transcribe
    - GPT-4o Mini Transcribe
  - Model selection via Settings menu

- **Keyboard Shortcuts**:
  - Start/Stop recording: `*` (asterisk)
  - Cancel transcription: `-` (minus)
  - Enable/Disable program: `CTRL+ALT+*`

- **System Integration**:
  - System tray icon with show/hide controls
  - Real-time status overlay window that follows mouse cursor
  - Auto-paste transcriptions to active window
  - Program can be globally enabled/disabled

- **UI Features**:
  - Status indicators showing current operation and selected model
  - Transcription display showing recent transcription result
  - Minimizes to system tray when closed

- **Settings**:
  - Toggle between local and API transcription
  - Select from multiple transcription models
  - Supports API key via environment variables or .env file

- **Error Handling**:
  - Comprehensive logging to file and console
  - Error messages for failed transcriptions
  - Debounce mechanism to prevent accidental double triggers

---

## Prerequisites

- **Python 3.8+**
- Required Python libraries (see requirements.txt):
  - `tkinter`
  - `pyaudio`
  - `wave`
  - `whisper`
  - `numpy`
  - `pyperclip`
  - `keyboard`
  - `openai`
  - `pystray`
  - `Pillow`
  - `python-dotenv` (optional for .env support)

- For API transcription:
  - OpenAI API key (set as OPENAI_API_KEY environment variable or in .env file)

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/knuckles92/audio-recorder.git
   cd audio-recorder
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. For API usage, set your OpenAI API key:
   - Option 1: Environment variable
     ```bash
     export OPENAI_API_KEY='your-api-key'
     ```
   - Option 2: .env file
     ```bash
     echo "OPENAI_API_KEY=your-api-key" > .env
     ```

---

## Usage

1. Run the application:
   ```bash
   python audio.py
   ```

2. Basic Controls:
   - Press `*` to start/stop recording
   - Press `-` to cancel current operation
   - Use `CTRL+ALT+*` to enable/disable the program globally

3. Settings:
   - Access via the menu bar
   - Toggle between local and API transcription
   - Select your preferred transcription model

4. System Tray:
   - Right-click the tray icon to show/hide the window or exit
   - Closing the main window sends the app to system tray instead of exiting

---

## Notes

- The application creates a log file (`audio_recorder.log`) for troubleshooting
- First run with local Whisper will download the model (approx. 150MB)
- For best API results, use GPT-4o models when available
- Keyboard hooks operate globally, allowing for use with any application
