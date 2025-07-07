# Juliette AI - Portable Voice Assistant

This is a personal, local, and fast voice assistant built with Streamlit. It uses `whisper.cpp` for speech-to-text and a custom text-to-speech engine to provide a seamless voice interaction experience.

This version is configured to be portable and easily shareable.

## Features

*   **Dynamic Recording:** Start and stop recording with button clicks, allowing for variable-length audio input.
*   **Local STT:** Transcription is performed locally using a `whisper.cpp` model.
*   **Local TTS:** Speech is generated locally using the Kokoro TTS engine.
*   **Portable:** Configuration is handled via environment variables, not hardcoded paths.

## Setup

### 1. Prerequisites
- Python 3.8+
- `whisper.cpp` built and ready. (https://github.com/ggml-org/whisper.cpp)
- Kokoro TTS scripts available.

### 2. Installation
Clone this repository and install the required Python packages:
```bash
git clone <your-repo-url>
cd <your-repo-name>
pip install -r requirements.txt
```

### 3. Configuration
This application uses environment variables to locate necessary external projects. You must set these variables before running the app.

**On Linux/macOS:**
```bash
export WHISPER_CPP_DIR="/path/to/your/whisper.cpp"
export KOKORO_SCRIPT_DIR="/path/to/your/My_freelance_website/scripts"
```

**On Windows (Command Prompt):**
```cmd
set WHISPER_CPP_DIR="C:\path\to\your\whisper.cpp"
set KOKORO_SCRIPT_DIR="C:\path\to\your\My_freelance_website\scripts"
```

**On Windows (PowerShell):**
```powershell
$env:WHISPER_CPP_DIR="C:\path\to\your\whisper.cpp"
$env:KOKORO_SCRIPT_DIR="C:\path\to\your\My_freelance_website\scripts"
```
*Note: You may want to add these to your shell's profile file (`.bashrc`, `.zshrc`, etc.) or your system's environment variables for persistence.*

## Usage

Once the environment variables are set and dependencies are installed, run the Streamlit application:
```bash
streamlit run audio.py
```

### How to Interact:
1.  Click **"Start Recording"** to begin capturing audio.
2.  The application will show a "Recording..." status.
3.  When you are finished speaking, click **"Stop Recording"**.
4.  The app will then transcribe the audio and display the text.
5.  You can use the "Generate Speech" button to have the transcribed text read aloud.

```