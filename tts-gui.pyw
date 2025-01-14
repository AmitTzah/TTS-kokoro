import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import torch
import soundfile as sf
import tempfile
import threading
import sys

# --- Configure eSpeak-NG Path (if needed for phonemizer) ---
ESPEAK_LIBRARY_PATH = r"C:\Program Files\eSpeak NG\libespeak-ng.dll"
ESPEAK_EXECUTABLE_PATH = r"C:\Program Files\eSpeak NG\espeak-ng.exe"

if not os.path.exists(ESPEAK_LIBRARY_PATH):
    raise FileNotFoundError(f"Could not find espeak library at {ESPEAK_LIBRARY_PATH}")
if not os.path.exists(ESPEAK_EXECUTABLE_PATH):
    raise FileNotFoundError(f"Could not find espeak executable at {ESPEAK_EXECUTABLE_PATH}")

os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = ESPEAK_LIBRARY_PATH
os.environ["PHONEMIZER_ESPEAK_PATH"] = ESPEAK_EXECUTABLE_PATH

# --- Set up Kokoro-82M Path ---
# Get the absolute path to the 'Kokoro-82M' directory
KOKORO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Kokoro-82M')

# Add the 'Kokoro-82M' directory to the Python path
sys.path.append(KOKORO_DIR)

# --- NOW import models and kokoro ---
from models import build_model
from kokoro import generate
import pygame

# --- Model and Voices Setup ---
MODEL_PATH = os.path.join(KOKORO_DIR, 'kokoro-v0_19.pth')
VOICES_DIR = os.path.join(KOKORO_DIR, 'voices')

VOICE_CATEGORIES = {
    'American Female': ['af', 'af_bella', 'af_nicole', 'af_sarah', 'af_sky'],
    'American Male': ['am_adam', 'am_michael'],
    'British Female': ['bf_emma', 'bf_isabella'],
    'British Male': ['bm_george', 'bm_lewis']
}

# --- Initialize Pygame for Audio Playback ---
pygame.mixer.init(frequency=24000)  # Match the Kokoro model's sample rate

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Text-to-Speech Generator")

        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'  # Use CUDA if available
        self.model = None
        self.voicepacks = {}

        self.create_widgets()
        self.load_model()
        self.load_voices()

    def create_widgets(self):
        # --- Voice Selection ---
        voice_frame = ttk.LabelFrame(self.root, text="Voice Selection")
        voice_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.selected_voice = tk.StringVar(value='af')
        voice_options = []
        for category, voices in VOICE_CATEGORIES.items():
            for voice in voices:
                voice_options.append(voice)

        self.voice_dropdown = ttk.Combobox(voice_frame, textvariable=self.selected_voice, values=voice_options)
        self.voice_dropdown.current(0)
        self.voice_dropdown.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # --- Text Input ---
        text_frame = ttk.LabelFrame(self.root, text="Text Input")
        text_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.text_entry = tk.Text(text_frame, wrap=tk.WORD, height=10)
        self.text_entry.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # --- Generate Button ---
        self.generate_button = ttk.Button(self.root, text="Generate Audio", command=self.generate_audio_thread)
        self.generate_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # --- Status Label ---
        self.status_label = ttk.Label(self.root, text="")
        self.status_label.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        # --- Audio Controls ---
        audio_frame = ttk.LabelFrame(self.root, text="Generated Audio")
        audio_frame.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

        self.play_button = ttk.Button(audio_frame, text="Play", command=self.play_audio, state=tk.DISABLED)
        self.play_button.grid(row=0, column=0, padx=5, pady=5)

        self.pause_resume_button = ttk.Button(audio_frame, text="Pause", command=self.toggle_pause_resume, state=tk.DISABLED)
        self.pause_resume_button.grid(row=0, column=1, padx=5, pady=5)

        self.save_button = ttk.Button(audio_frame, text="Save", command=self.save_audio, state=tk.DISABLED)
        self.save_button.grid(row=0, column=2, padx=5, pady=5)

        self.is_paused = False

        # --- Progress Bar ---
        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", mode="indeterminate")

        # --- Configure Grid ---
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)  # Allow text area to expand

    def load_model(self):
        self.status_label.config(text="Loading model...")
        self.progress_bar.grid(row=5, column=0, padx=10, pady=5, sticky="ew") # Show progress bar
        self.progress_bar.start()

        try:
            self.model = build_model(MODEL_PATH, self.device)  # Load model to specified device
            self.status_label.config(text=f"Model loaded successfully on {self.device}.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {e}")
            self.status_label.config(text="Model loading failed.")
        finally:
            self.progress_bar.stop()
            self.progress_bar.grid_forget()  # Hide progress bar

    def load_voices(self):
        for voice_name in [voice for category in VOICE_CATEGORIES.values() for voice in category]:
            try:
                voice_path = os.path.join(VOICES_DIR, f'{voice_name}.pt')
                self.voicepacks[voice_name] = torch.load(voice_path, map_location=self.device) # Load to specified device
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load voice {voice_name}: {e}")

    def generate_audio_thread(self):
        self.generate_button.config(state=tk.DISABLED)
        self.status_label.config(text="Generating audio...")
        self.progress_bar.grid(row=5, column=0, padx=10, pady=5, sticky="ew")  # Show progress bar
        self.progress_bar.start()

        thread = threading.Thread(target=self.generate_audio)
        thread.start()

    def generate_audio(self):
        text = self.text_entry.get("1.0", tk.END).strip()
        voice_name = self.selected_voice.get()

        if not text:
            self.update_ui_after_generation(False, "Please enter some text.")
            return

        try:
            voicepack = self.voicepacks[voice_name]
            audio, phonemes = generate(self.model, text, voicepack, lang=voice_name[0])

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                sf.write(temp_file.name, audio, 24000)
                self.audio_file = temp_file.name

            self.update_ui_after_generation(True, "Audio generated successfully.")

        except Exception as e:
            self.update_ui_after_generation(False, f"Error generating audio: {e}")

    def update_ui_after_generation(self, success, message):
        self.root.after(0, lambda: self._update_ui(success, message))

    def _update_ui(self, success, message):
        self.status_label.config(text=message)
        self.generate_button.config(state=tk.NORMAL)
        self.progress_bar.stop()
        self.progress_bar.grid_forget()

        if success:
            self.play_button.config(state=tk.NORMAL)
            self.pause_resume_button.config(state=tk.DISABLED)
            self.pause_resume_button.config(text="Pause")
            self.save_button.config(state=tk.NORMAL)
        else:
            self.play_button.config(state=tk.DISABLED)
            self.pause_resume_button.config(state=tk.DISABLED)
            self.save_button.config(state=tk.DISABLED)

    def play_audio(self):
        try:
            pygame.mixer.music.load(self.audio_file)
            pygame.mixer.music.play()
            self.play_button.config(text="Stop", command=self.stop_audio)
            self.pause_resume_button.config(state=tk.NORMAL)
            self.pause_resume_button.config(text="Pause")
            self.is_paused = False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play audio: {e}")

    def stop_audio(self):
        try:
            pygame.mixer.music.stop()
            self.play_button.config(text="Play", command=self.play_audio)
            self.pause_resume_button.config(state=tk.DISABLED)
            self.pause_resume_button.config(text="Pause")
            self.is_paused = False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop audio: {e}")

    def toggle_pause_resume(self):
        try:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.pause_resume_button.config(text="Pause")
                self.is_paused = False
            else:
                pygame.mixer.music.pause()
                self.pause_resume_button.config(text="Resume")
                self.is_paused = True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle pause/resume: {e}")

    def save_audio(self):
        try:
            # Open a file dialog for the user to choose where to save
            file_path = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
                title="Save Audio As"
            )
            if not file_path:
                return  # User cancelled

            # Copy the temporary audio file to the chosen location
            with open(self.audio_file, 'rb') as temp_file, open(file_path, 'wb') as save_file:
                save_file.write(temp_file.read())

            self.status_label.config(text=f"Audio saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save audio: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TTSApp(root)
    root.mainloop()
