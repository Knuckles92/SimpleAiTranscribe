# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a desktop application for recording and transcribing audio using either local Whisper models or OpenAI API-based transcription. The core functionality is contained in `audio.py`, which implements:

1. Audio recording capabilities using PyAudio
2. Local transcription with OpenAI Whisper (base model)
3. API-based transcription options (Whisper API, GPT-4o Transcribe, GPT-4o Mini Transcribe)
4. Text-to-Speech (TTS) functionality using OpenAI's TTS models
5. System tray integration via pystray
6. Global keyboard shortcut handling with keyboard library

## Development Commands

### Setup and Installation

```bash
# Install required dependencies
pip install -r requirements.txt

# Set OpenAI API key (for API-based features)
# Option 1: Environment variable
export OPENAI_API_KEY='your-api-key'

# Option 2: .env file
echo "OPENAI_API_KEY=your-api-key" > .env
```

### Running the Application

```bash
# Run with default settings (local Whisper model)
python audio.py

# Run with specific model selection
python audio.py --model local_whisper
python audio.py --model api_whisper
python audio.py --model api_gpt4o
python audio.py --model api_gpt4o_mini

# Force API usage (with any model)
python audio.py --use-api
```

## Technical Details

### Application Structure

- **Main Class**: `AudioRecorder` in `audio.py` handles all core functionality
- **Audio Player**: `StoppableAudio` class uses pygame for audio playback with stop capability
- **Configuration**: Supports both CLI arguments and environment variables/`.env` file

### Key Features and Components

1. **Audio Recording System**:
   - Uses PyAudio for capturing audio input
   - Records to temporary WAV file before processing

2. **Transcription System**:
   - Local: Uses Whisper library directly
   - API-based: Uses OpenAI client library with various models

3. **TTS System**:
   - Uses OpenAI's TTS API
   - Reads text from clipboard
   - Supports custom speaking style from `style.txt`

4. **Keyboard Management**:
   - Global keyboard hooks for shortcuts
   - Custom key suppression to prevent key propagation
   - Debounce mechanism for triggers

5. **System Integration**:
   - System tray icon with menu
   - Background operation support

### Important Files

- `audio.py`: Main application file
- `requirements.txt`: Project dependencies
- `style.txt`: Configuration file for TTS speaking style
- `speech.mp3`: Temporary file for TTS output
- `recorded_audio.wav`: Temporary file for audio recording
- `audio_recorder.log`: Application log file

## Best Practices When Modifying Code

1. Maintain the existing keyboard hook system when adding new shortcuts
2. Always implement proper cleanup in error handling blocks
3. Use the logging system for debugging and status messages
4. Run UI-related operations in the main thread, offload processing to worker threads
5. Keep the TTS and STT features properly isolated but functionally integrated