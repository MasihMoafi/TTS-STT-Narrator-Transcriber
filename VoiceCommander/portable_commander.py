import os
import subprocess
import tempfile
import uuid
import threading
import sounddevice as sd
from scipy.io.wavfile import write as write_wav
import numpy as np
import pyperclip
from pynput import keyboard

# --- CONFIGURATION ---
# This script is designed to be portable. It assumes the following directory structure:
# /Your_Portable_Folder/
# ├── whisper.cpp/
# │   ├── ... (whisper.cpp contents)
# │   └── models/
# │       └── ggml-medium.en.bin
# └── VoiceCommander/
#     └── portable_commander.py

# Get the directory of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory of the script's directory (e.g., /Your_Portable_Folder/)
BASE_DIR = os.path.dirname(SCRIPT_DIR)

WHISPER_CPP_DIR = os.path.join(BASE_DIR, "whisper.cpp")
WHISPER_EXECUTABLE = os.path.join(WHISPER_CPP_DIR, "build", "bin", "whisper-cli")
WHISPER_MODEL_PATH = os.path.join(WHISPER_CPP_DIR, "models", "ggml-medium.en.bin")
HOTKEY = keyboard.Key.f9
SAMPLERATE = 16000

# --- STATE MANAGEMENT ---
class Recorder:
    def __init__(self):
        self.recording = False
        self.audio_data = []
        self.lock = threading.Lock()

    def start(self):
        with self.lock:
            if self.recording:
                return
            print(">>> Recording started. Press F9 to stop.")
            self.recording = True
            self.audio_data = []
            # Start the recording stream in a separate thread
            threading.Thread(target=self._record_loop, daemon=True).start()

    def stop_and_process(self):
        with self.lock:
            if not self.recording:
                return
            print(">>> Recording stopped. Processing...")
            self.recording = False
        
        # Process the audio in a separate thread to keep the hotkey listener responsive
        threading.Thread(target=self._process_audio_data, daemon=True).start()

    def _record_loop(self):
        """Continuously records audio in chunks while recording is active."""
        with sd.InputStream(samplerate=SAMPLERATE, channels=1, dtype='int16') as stream:
            while self.recording:
                audio_chunk, overflowed = stream.read(SAMPLERATE) # Read 1-second chunks
                if overflowed:
                    print("Warning: Audio buffer overflowed")
                with self.lock:
                    if self.recording:
                        self.audio_data.append(audio_chunk)

    def _process_audio_data(self):
        """Transcribes the recorded audio and pastes it."""
        with self.lock:
            if not self.audio_data:
                print("No audio recorded.")
                return
            recording = np.concatenate(self.audio_data, axis=0)

        print("Transcribing...")
        tmp_audio_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.wav")
        write_wav(tmp_audio_path, SAMPLERATE, recording)

        command = [WHISPER_EXECUTABLE, "-m", WHISPER_MODEL_PATH, "-f", tmp_audio_path, "-nt"]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            transcribed_text = result.stdout.strip()
            print(f"Transcribed: {transcribed_text}")
            pyperclip.copy(transcribed_text)
            print("Text copied to clipboard. Pasting for all applications...")
            
            controller = keyboard.Controller()

            # Standard Paste (Ctrl+V)
            with controller.pressed(keyboard.Key.ctrl):
                controller.press('v')
                controller.release('v')

            # Terminal Paste (Ctrl+Shift+V)
            with controller.pressed(keyboard.Key.ctrl, keyboard.Key.shift):
                controller.press('v')
                controller.release('v')

            print("Paste command sent.")
        else:
            print("Whisper.cpp failed:")
            print(result.stderr)
        
        os.remove(tmp_audio_path)

# --- HOTKEY LISTENER ---
recorder = Recorder()

def on_press(key):
    if key == HOTKEY:
        if recorder.recording:
            recorder.stop_and_process()
        else:
            recorder.start()

def main():
    print(f"VoiceCommander is active. Press '{HOTKEY}' to start/stop recording.")
    print("The transcribed text will be pasted at your cursor's location.")
    print("Close this window or press Ctrl+C to exit.")
    
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()