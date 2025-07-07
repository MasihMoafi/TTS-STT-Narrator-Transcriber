import streamlit as st
import os
import tempfile
import sounddevice as sd
from scipy.io.wavfile import write as write_wav
import uuid
import subprocess
import numpy as np

# --- CONFIGURATION ---
# Use environment variables for paths, making the app portable
WHISPER_CPP_DIR = os.environ.get("WHISPER_CPP_DIR")
KOKORO_SCRIPT_DIR = os.environ.get("KOKORO_SCRIPT_DIR")

# Construct full paths, handling potential None values
if WHISPER_CPP_DIR:
    WHISPER_EXECUTABLE = os.path.join(WHISPER_CPP_DIR, "build", "bin", "whisper-cli")
    WHISPER_MODEL_PATH = os.path.join(WHISPER_CPP_DIR, "models", "ggml-medium.en.bin")
else:
    WHISPER_EXECUTABLE = None
    WHISPER_MODEL_PATH = None

if KOKORO_SCRIPT_DIR:
    KOKORO_SCRIPT_PATH = os.path.join(KOKORO_SCRIPT_DIR, "kokoro_tts.py")
else:
    KOKORO_SCRIPT_PATH = None

# --- HELPER FUNCTIONS ---
def run_subprocess_sync(command, cwd=None):
    """Runs a subprocess synchronously and returns stdout, stderr."""
    result = subprocess.run(command, capture_output=True, text=True, cwd=cwd)
    return result.stdout, result.stderr, result.returncode

def paths_are_valid():
    """Check if all required paths are configured and valid."""
    if not WHISPER_CPP_DIR or not os.path.isdir(WHISPER_CPP_DIR):
        st.error("WHISPER_CPP_DIR is not configured or not a valid directory.")
        return False
    if not KOKORO_SCRIPT_DIR or not os.path.isdir(KOKORO_SCRIPT_DIR):
        st.error("KOKORO_SCRIPT_DIR is not configured or not a valid directory.")
        return False
    if not os.path.isfile(WHISPER_EXECUTABLE):
        st.error(f"Whisper executable not found at: {WHISPER_EXECUTABLE}")
        return False
    if not os.path.isfile(WHISPER_MODEL_PATH):
        st.error(f"Whisper model not found at: {WHISPER_MODEL_PATH}")
        return False
    if not os.path.isfile(KOKORO_SCRIPT_PATH):
        st.error(f"Kokoro TTS script not found at: {KOKORO_SCRIPT_PATH}")
        return False
    return True

# --- PAGE SETUP ---
st.set_page_config(page_title="Juliette AI", layout="centered")
st.title("Juliette AI 🎙️")
st.caption("Your personal, local, lightning-fast voice assistant.")

# --- MAIN APP ---
if not paths_are_valid():
    st.warning("Please configure the WHISPER_CPP_DIR and KOKORO_SCRIPT_DIR environment variables.")
    st.stop()

# --- SESSION STATE ---
if "recording" not in st.session_state:
    st.session_state.recording = False
if "audio_data" not in st.session_state:
    st.session_state.audio_data = []
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = ""
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# --- UI & LOGIC ---
st.subheader("1. Listen (STT)")

if not st.session_state.recording:
    if st.button("Start Recording"):
        st.session_state.recording = True
        st.session_state.audio_data = []
        st.rerun()
else:
    st.info("🔴 Recording... Press 'Stop Recording' when you are finished.")
    if st.button("Stop Recording"):
        st.session_state.recording = False
        
        with st.spinner("Transcribing..."):
            if not st.session_state.audio_data:
                st.warning("No audio recorded.")
            else:
                samplerate = 16000
                recording = np.concatenate(st.session_state.audio_data, axis=0)
                
                tmp_audio_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.wav")
                write_wav(tmp_audio_path, samplerate, recording)

                command = [WHISPER_EXECUTABLE, "-m", WHISPER_MODEL_PATH, "-f", tmp_audio_path, "-nt"]
                stdout, stderr, returncode = run_subprocess_sync(command)

                if returncode == 0:
                    st.session_state.transcribed_text = stdout.strip()
                else:
                    st.error("Whisper.cpp failed:")
                    st.code(stderr)
                
                os.remove(tmp_audio_path)
        st.rerun()

if st.session_state.recording:
    with st.spinner("Recording..."):
        samplerate = 16000
        chunk = sd.rec(int(1 * samplerate), samplerate=samplerate, channels=1, dtype='int16')
        sd.wait()
        st.session_state.audio_data.append(chunk)
        st.rerun()

st.text_area("Transcribed Text", value=st.session_state.transcribed_text, height=150, key="transcribed_text_area")

st.subheader("2. Speak (TTS)")
if st.button("Generate Speech"):
    text_to_speak = st.session_state.transcribed_text_area
    if text_to_speak:
        with st.spinner("Generating speech..."):
            tmp_input_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.txt")
            tmp_output_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.wav")

            with open(tmp_input_path, 'w') as f:
                f.write(text_to_speak)

            command = ["python", KOKORO_SCRIPT_PATH, tmp_input_path, tmp_output_path]
            stdout, stderr, returncode = run_subprocess_sync(command, cwd=KOKORO_SCRIPT_DIR)

            if returncode == 0 and os.path.exists(tmp_output_path):
                with open(tmp_output_path, 'rb') as f:
                    st.session_state.last_audio = f.read()
            else:
                st.error("Kokoro TTS failed:")
                st.code(stderr)
            
            os.remove(tmp_input_path)
            if os.path.exists(tmp_output_path):
                os.remove(tmp_output_path)
            st.rerun()
    else:
        st.warning("There is no text to speak.")

if st.session_state.last_audio:
    st.audio(st.session_state.last_audio, format='audio/wav')
