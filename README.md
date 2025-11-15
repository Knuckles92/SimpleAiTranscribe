# Audio Recorder with Speech-to-Text

A modular desktop application for recording audio and transcribing it to text using either local Whisper models or OpenAI API. Features a clean Tkinter GUI, system tray integration, global keyboard shortcuts, and real-time status overlay with automatic text pasting.


![Cursor_oltUG9lVTm](https://github.com/user-attachments/assets/ffe3f51e-3faf-4f31-a661-a1de6bcd0bc9)


## Features

### 🎙️ Audio Recording
- High-quality mono audio recording (44.1kHz, 16-bit)
- Real-time audio capture using PyAudio
- Automatic WAV file generation
- **Smart Audio Splitting**: Automatically splits large audio files (>23MB) using silence detection to prevent API timeouts
- **Post-roll Recording**: Continues recording for 1.2 seconds after stop to prevent word cutoffs

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
- **Customizable**: All hotkeys can be remapped via the hotkey configuration dialog

### 🖥️ User Interface
- **Main Window**: Model selection dropdown, recording controls, and transcription display
- **System Tray**: Minimize to tray with show/hide controls
- **Status Overlay**: Real-time status window that follows mouse cursor with **7 customizable waveform styles**
- **Auto-paste**: Automatically pastes transcriptions to the active window
- **Loading Screen**: Shows initialization progress during startup

### 🎨 Waveform Visualization Styles
Choose from 7 distinct real-time visualization styles for the status overlay:
- **Modern**: Clean gradient bars with smooth animations and pulsing effects
- **Retro**: Classic VU meter style with analog warmth and needle movement
- **Minimalist**: Subtle, elegant line-based visualization with zen-like simplicity
- **Spectrum**: Circular frequency analyzer with vibrant rainbow colors and pulsing center
- **Particle**: Physics-based particle system that dynamically responds to audio input
- **Neon Matrix**: Cyberpunk-inspired code rain with neon equalizer bars and glitch effects
- **Galaxy Warp**: Hypnotic space-themed visualization with orbiting particles and warp effects

### 🔧 Advanced Features
- Global keyboard hooks that work across all applications
- Program can be completely disabled while running
- Debounce protection (300ms) to prevent accidental double-triggers
- Comprehensive logging to file and console
- Support for environment variables and .env files
- **Persistent Settings**: Remembers your model selection, hotkey preferences, and waveform style
- **Audio Level Monitoring**: Real-time audio level display during recording
- **FFmpeg Integration**: Advanced audio processing with automatic detection and configuration. Features include:
  - Automatic FFmpeg binary detection in system PATH
  - Fallback to built-in audio processing if FFmpeg is not available
  - Support for various audio codecs and formats
  - Configurable audio processing parameters
  - Seamless integration with the recording pipeline

## Prerequisites

### System Requirements
- **Python 3.8+**
- **Windows** (due to keyboard library requirements)

### Required Dependencies
See `requirements.txt` for a complete list of dependencies.

### API Setup (Optional)
- OpenAI API key for cloud transcription features
- Set as `OPENAI_API_KEY` environment variable or in `.env` file

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Knuckles92/SimpleAiTranscribe
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
   
   Option B - Create .env file and set:
   ```bash
   OPENAI_API_KEY=your-api-key-here
   ```

## Usage

### Starting the Application
```bash
python app.py
```

The application will show a loading screen while initializing components, then display the main window. You can minimize it to system tray by closing the window.

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

### Configuration

#### Audio Settings
The application uses these optimized audio settings:
- **Sample Rate**: 44,100 Hz
- **Channels**: Mono (1 channel)
- **Format**: 16-bit PCM
- **Chunk Size**: 1024 frames
- **Post-roll Buffer**: 1.2 seconds of additional recording

#### File Size Management
- **Maximum File Size**: 23MB before automatic splitting
- **Split Detection**: Uses silence detection with 0.5-second minimum silence
- **Chunk Overlap**: 2-second overlap between chunks to prevent word cutoffs
- **Minimum Chunk Duration**: 30 seconds per chunk

#### Waveform Styles
- **Available Styles**: 7 distinct visualization themes
- **Live Preview**: Real-time style preview in selection dialog
- **Persistent Selection**: Remembers your chosen style across sessions
- **Customizable Colors**: Each style has configurable color schemes

#### Settings Files
- **Main Settings**: `audio_recorder_settings.json` (persistent configuration)
- **Log File**: `audio_recorder.log` (application events and errors)
- **Temporary Files**: `recorded_audio.wav` (current recording, overwritten each time)
- **Environment**: `.env` file support for API keys and configuration

## Troubleshooting

### Common Issues

**"No API key found" error:**
- Ensure `OPENAI_API_KEY` is set in environment variables or `.env` file
- API key is only required for cloud transcription options
- Check that the key has proper permissions for your selected API model

**Keyboard shortcuts not working:**
- Run the application as administrator if needed
- Check if the program is disabled (press `Ctrl+Alt+*` to re-enable)
- Verify hotkey settings haven't been changed in the hotkey configuration dialog

**Recording fails:**
- Check microphone permissions in Windows settings
- Ensure no other applications are exclusively using the microphone
- Review `audio_recorder.log` for detailed error information
- Try restarting the application if audio device enumeration fails

**Application won't start:**
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version is 3.8 or higher
- Ensure PyAudio can access your audio devices
- Check for missing Visual C++ redistributables on Windows

**Waveform overlay not appearing:**
- Verify the overlay is enabled in settings
- Check if it's positioned off-screen (resets to cursor position on next use)
- Ensure your graphics drivers support the required transparency features

**Large file transcription issues:**
- Files over 23MB are automatically split using silence detection
- Ensure sufficient disk space for temporary chunk files
- Check `audio_recorder.log` for splitting progress and any errors

### Performance Notes
- **First Local Run**: Whisper model download (~150MB) may take a few minutes depending on internet speed
- **Local vs API**: Local processing takes 2-5 seconds, API is usually faster but requires internet
- **Memory Usage**: Local Whisper model uses ~500MB RAM when loaded
- **Audio Splitting**: Large files may take additional time for silence analysis and chunk processing
- **Waveform Styles**: More complex styles (Particle, Retro) may use slightly more CPU during recording

## Technical Details

### Architecture
- **GUI Framework**: Tkinter with ttk components
- **Audio Processing**: PyAudio for capture, Wave for file handling
- **Speech Recognition**: OpenAI Whisper (local) or OpenAI API (cloud)
- **System Integration**: Keyboard hooks, clipboard operations, system tray
- **Concurrency**: ThreadPoolExecutor for background tasks
- **Configuration**: Centralized config management with dataclasses
- **Testing**: Unit tests with mocking for hardware dependencies

### Security & Privacy
- **Local Mode**: Audio never leaves your computer
- **API Mode**: Audio is sent to OpenAI servers for processing
- **No Data Storage**: Recordings are temporarily saved and overwritten
- **Logging**: Only application events are logged, not audio content

## License

Just use the thing.

## Contributing

Do whatever you want.

## Architecture

The application has been refactored into a modular architecture for better maintainability and extensibility:

### Core Modules
- **`app.py`**: Main application bootstrap and initialization
- **`config.py`**: Centralized configuration and constants
- **`settings.py`**: Settings persistence and management
- **`recorder.py`**: Audio recording functionality
- **`hotkey_manager.py`**: Global keyboard hook management

### Transcription Backends
- **`transcriber/`**: Pluggable transcription backend system
  - `base.py`: Abstract base class for all backends
  - `local_backend.py`: Local Whisper model implementation
  - `openai_backend.py`: OpenAI API implementation

### User Interface
- **`ui/`**: Modular UI components
  - `loading_screen.py`: Application startup screen
  - `main_window.py`: Primary application window with model selection and status display
  - `hotkey_dialog.py`: Hotkey configuration dialog with visual key capture
  - `tray.py`: System tray integration
  - `waveform_overlay.py`: Real-time audio visualization overlay with 7 customizable styles
  - `waveform_style_dialog.py`: Style selection dialog with live previews
  - `ffmpeg_dialog.py`: FFmpeg configuration and detection dialog
  - `waveform_styles/`: Pluggable visualization style system
    - `base_style.py`: Abstract base class for waveform styles
    - `modern_style.py`: Clean modern bars with smooth animations
    - `retro_style.py`: Neon matrix-style with glitch effects
    - `minimalist_style.py`: Subtle line-based visualization
    - `spectrum_style.py`: Circular spectrum analyzer
    - `particle_style.py`: Dynamic particle system
    - `style_factory.py`: Style registration and creation

### Testing
- **`tests/`**: Unit tests for core functionality
  - `test_settings.py`: Settings management tests
  - `test_recorder.py`: Audio recording tests

### Extensibility Points
- **Add New Transcription Backends**: Implement `TranscriptionBackend` interface
- **Custom UI Components**: Extend the `ui/` package
- **Configuration Options**: Add settings to `config.py`
- **New Hotkey Actions**: Extend `HotkeyManager` callbacks
