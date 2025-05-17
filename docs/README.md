# Audio Recorder

A desktop application for recording and transcribing audio with multiple transcription options. It supports both local Whisper models and OpenAI API transcription (including GPT-4o variants). The app features a beautiful CLI interface with colors and progress bars, system tray integration, keyboard shortcuts, and status indicators.

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

- **Beautiful CLI Features**:
  - Colorful status panels and indicators showing current operation
  - Progress bars with spinners for real-time operation status
  - Rich text formatting and Unicode symbols for better readability
  - Elegant tables for displaying settings and transcription results
  - Animated processes with live updates

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
  - `rich` (for beautiful CLI interface)
  - `pygame` (for audio playback)

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
   - Press `-` to cancel current operation (universal stop button)
   - Press `F9` or `Ctrl+Shift+T` for text-to-speech from clipboard
   - Use `CTRL+ALT+*` to enable/disable the program globally

3. Command-line Arguments:
   - Specify transcription model: `python audio.py --model [local_whisper|api_whisper|api_gpt4o|api_gpt4o_mini]`
   - Force API usage: `python audio.py --use-api`
   - Example: `python audio.py --model api_gpt4o`

4. System Tray:
   - Right-click the tray icon to show/hide the window or exit
   - Closing the main window sends the app to system tray instead of exiting

---

## Notes

- The application creates a log file (`audio_recorder.log`) for troubleshooting
- First run with local Whisper will download the model (approx. 150MB)
- For best API results, use GPT-4o models when available
- Keyboard hooks operate globally, allowing for use with any application
- The Rich library powers the beautiful CLI interface
- You can customize speaking style for TTS by editing the `style.txt` file

## CLI Interface

The application features a beautiful command-line interface powered by the Rich library:

- **Colorful Status Panels**: Visual indicators of recording, transcription, and playback status
- **Progress Bars**: Real-time feedback for long-running operations
- **Formatted Output**: Clear, readable text with appropriate styling
- **Tables and Panels**: Well-organized information display
- **Unicode Symbols**: Visual indicators for statuses and actions
