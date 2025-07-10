# Audio Recorder with Speech-to-Text

A desktop application for recording audio and transcribing it to text using either local Whisper models or OpenAI API. Features a minimal Tkinter GUI, system tray integration, global keyboard shortcuts, and real-time status overlay with automatic text pasting.

## Features

### 🎙️ Audio Recording
- High-quality mono audio recording (44.1kHz, 16-bit)
- Real-time audio capture using PyAudio
- Automatic WAV file generation

### 🔄 Multiple Transcription Options
- **Local Whisper**: Uses OpenAI's Whisper "base" model locally (~150MB download on first use)
- **API Options**:
  - Whisper API (standard model)
  - GPT-4o Transcribe (premium accuracy)
  - GPT-4o Mini Transcribe (fast and cost-effective)

### ⌨️ Global Keyboard Shortcuts
- `*` (asterisk): Start/stop recording
- `-` (minus): Universal stop/cancel button
- `Ctrl+Alt+*`: Enable/disable the entire program globally

### 🖥️ User Interface
- **Main Window**: Model selection dropdown, recording controls, and transcription display
- **System Tray**: Minimize to tray with show/hide controls
- **Status Overlay**: Real-time status window that follows mouse cursor
- **Auto-paste**: Automatically pastes transcriptions to the active window

### 🔧 Advanced Features
- Global keyboard hooks that work across all applications
- Program can be completely disabled while running
- Debounce protection (300ms) to prevent accidental double-triggers
- Comprehensive logging to file and console
- Support for environment variables and .env files

## Prerequisites

### System Requirements
- **Python 3.8+**
- **Windows** (due to keyboard library requirements)

### Required Dependencies
```
tkinter (usually included with Python)
pyaudio
wave (built-in)
whisper
numpy
pyperclip
keyboard
openai
pystray
Pillow
python-dotenv (optional, for .env file support)
```

### API Setup (Optional)
- OpenAI API key for cloud transcription features
- Set as `OPENAI_API_KEY` environment variable or in `.env` file

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd whisper_local
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API key (for cloud features):**
   
   Option A - Environment variable:
   ```bash
   set OPENAI_API_KEY=your-api-key-here
   ```
   
   Option B - Create .env file:
   ```bash
   echo OPENAI_API_KEY=your-api-key-here > .env
   ```

## Usage

### Starting the Application
```bash
python audio.py
```

The application window will appear and stay on top. You can minimize it to system tray by closing the window.

### Basic Workflow
1. **Select Model**: Choose your preferred transcription method from the dropdown
2. **Record**: Press `*` to start recording, press `*` again to stop
3. **Wait**: The app will process and transcribe your audio
4. **Auto-paste**: Transcribed text is automatically pasted to your active window

### Keyboard Controls
- **Start/Stop Recording**: Press `*` (works globally in any application)
- **Cancel Operation**: Press `-` to stop recording or cancel transcription
- **Disable Program**: Press `Ctrl+Alt+*` to temporarily disable all functionality

### Model Selection
- **Local Whisper**: Runs entirely offline, good accuracy, ~2-5 second processing time
- **API: Whisper**: Standard OpenAI Whisper via API, requires internet
- **API: GPT-4o Transcribe**: Highest accuracy, premium model, requires API key
- **API: GPT-4o Mini Transcribe**: Fast and cost-effective, requires API key

### System Tray
- **Right-click tray icon**: Show/hide window or exit application
- **Closing main window**: Sends app to system tray (doesn't exit)

## Configuration

### Audio Settings
The application uses these fixed audio settings:
- **Sample Rate**: 44,100 Hz
- **Channels**: Mono (1 channel)
- **Format**: 16-bit PCM
- **Chunk Size**: 1024 frames

### Log Files
- **Log File**: `audio_recorder.log` (created in application directory)
- **Temporary Files**: `recorded_audio.wav` (overwritten each recording)

## Troubleshooting

### Common Issues

**"No API key found" error:**
- Ensure `OPENAI_API_KEY` is set in environment variables or `.env` file
- API key is only required for cloud transcription options

**Keyboard shortcuts not working:**
- Run the application as administrator if needed
- Check if the program is disabled (press `Ctrl+Alt+*` to re-enable)

**Recording fails:**
- Check microphone permissions
- Ensure no other applications are exclusively using the microphone
- Review `audio_recorder.log` for detailed error information

**Application won't start:**
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version is 3.8 or higher

### Performance Notes
- **First Local Run**: Whisper model download (~150MB) may take a few minutes
- **Local vs API**: Local processing takes 2-5 seconds, API is usually faster but requires internet
- **Memory Usage**: Local Whisper model uses ~500MB RAM when loaded

## Technical Details

### Architecture
- **GUI Framework**: Tkinter with ttk components
- **Audio Processing**: PyAudio for capture, Wave for file handling
- **Speech Recognition**: OpenAI Whisper (local) or OpenAI API (cloud)
- **System Integration**: Keyboard hooks, clipboard operations, system tray

### Security & Privacy
- **Local Mode**: Audio never leaves your computer
- **API Mode**: Audio is sent to OpenAI servers for processing
- **No Data Storage**: Recordings are temporarily saved and overwritten
- **Logging**: Only application events are logged, not audio content

## License

Just use the thing.

## Contributing

Do whatever you want.
