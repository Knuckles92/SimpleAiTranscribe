# Audio Recorder

A simple desktop application for recording and transcribing audio. It leverages **OpenAI Whisper** for transcription and supports both local and API-based transcription methods. The app is built using `Tkinter` for minimal GUI and integrates seamlessly with system keyboard shortcuts, and cleanly sits in the system tray.

---
![notepad_xQrbAMoXs2](https://github.com/user-attachments/assets/2bc2186b-3166-40ba-a104-fa1c4a527853)

## Features

- **Audio Recording**:
  - High-quality audio recording using PyAudio.
  - Configurable sample rate and channels.

- **Transcription**:
  - Local transcription using a pretrained Whisper model.
  - Optional API-based transcription with OpenAI Whisper for enhanced accuracy.
  
- **Keyboard Shortcuts**:
  - Start/Stop recording: `*` (asterisk)
  - Cancel transcription: `-` (minus)
  - Enable/Disable program: `CTRL+ALT+*`

- **Real-time Status Overlay**:
  - Displays the current state (e.g., Recording, Transcribing).

- **Auto-Paste Transcriptions**:
  - Automatically pastes the transcription into the active window after processing.

- **User-Friendly GUI**:
  - Intuitive controls for starting/stopping recordings and managing transcriptions.

---

## Prerequisites

- **Python 3.8+**
- Required Python libraries:
  - `tkinter`
  - `pyaudio`
  - `wave`
  - `whisper`
  - `numpy`
  - `pyperclip`
  - `keyboard`
  - `openai`

- Optional:
  - OpenAI API key for API-based transcription (`OPENAI_API_KEY` environment variable).

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/audio-recorder.git
   cd audio-recorder
