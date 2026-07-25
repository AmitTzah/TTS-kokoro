"""Kokoro TTS GUI — graphical interface for the Kokoro-82M text-to-speech model."""

import tkinter as tk
from tkinter import ttk
import os
import sys

# ═══════════════════════════════════════════════════════════════
# STEP 1 — Show a splash window IMMEDIATELY, before any heavy
# imports.  This gives the user instant feedback that the app is
# starting, rather than staring at a blank screen for 5-10 seconds.
# ═══════════════════════════════════════════════════════════════

_splash = tk.Tk()
_splash.title("Kokoro TTS — Starting...")
_splash.geometry("380x80")
_splash.resizable(False, False)
# Center on screen (approximate — exact centering comes later)
_splash.eval('tk::PlaceWindow . center')
_splash_label = ttk.Label(
    _splash,
    text="Loading Kokoro TTS...\nPlease wait.",
    font=("Segoe UI", 10),
)
_splash_label.pack(expand=True, padx=20, pady=15)
_splash.update()  # Force paint NOW — user sees this instantly

# ═══════════════════════════════════════════════════════════════
# STEP 2 — Heavy imports (torch, models, kokoro, pygame).
# The splash window is already visible so the user knows the app
# is starting.
# ═══════════════════════════════════════════════════════════════

import torch
import soundfile as sf
import tempfile
import threading

# --- Configure eSpeak-NG Path (if needed for phonemizer) ---
ESPEAK_LIBRARY_PATH = r"C:\Program Files\eSpeak NG\libespeak-ng.dll"
ESPEAK_EXECUTABLE_PATH = r"C:\Program Files\eSpeak NG\espeak-ng.exe"

if not os.path.exists(ESPEAK_LIBRARY_PATH):
    _splash.destroy()
    raise FileNotFoundError(f"Could not find espeak library at {ESPEAK_LIBRARY_PATH}")
if not os.path.exists(ESPEAK_EXECUTABLE_PATH):
    _splash.destroy()
    raise FileNotFoundError(f"Could not find espeak executable at {ESPEAK_EXECUTABLE_PATH}")

os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = ESPEAK_LIBRARY_PATH
os.environ["PHONEMIZER_ESPEAK_PATH"] = ESPEAK_EXECUTABLE_PATH

# --- Set up Kokoro-82M Path ---
KOKORO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Kokoro-82M')
sys.path.append(KOKORO_DIR)

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

# Flattened list derived from VOICE_CATEGORIES — single source of truth
ALL_VOICES = [voice for category in VOICE_CATEGORIES.values() for voice in category]

# Language prefix mapping: first char of voice name → phonemizer lang code
VOICE_LANG = {'a': 'a', 'b': 'b'}  # American English, British English

from tkinter import messagebox, filedialog

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Text-to-Speech Generator")

        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'  # Use CUDA if available
        self.model = None
        self.voicepacks = {}
        self._loading = True  # Guard: prevent generation during startup load

        # Initialize pygame mixer AFTER the window exists so any error
        # is shown to the user rather than crashing before the GUI appears
        try:
            pygame.mixer.init(frequency=24000)  # Match Kokoro model sample rate
        except Exception as e:
            messagebox.showerror(
                "Audio Error",
                f"Failed to initialize audio system: {e}\n\n"
                "Audio playback will not be available."
            )

        self.create_widgets()
        # Force the window to render NOW so the user sees immediate feedback
        # before the heavy model/voice loading begins
        self.root.update()
        # Defer heavy loading so the event loop is already running and the
        # window is visible with the status bar and progress indicator
        self.root.after(50, self.load_model)

    def create_widgets(self):
        # --- Voice Selection ---
        voice_frame = ttk.LabelFrame(self.root, text="Voice Selection")
        voice_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.selected_voice = tk.StringVar(value='af')
        self.voice_dropdown = ttk.Combobox(voice_frame, textvariable=self.selected_voice, values=ALL_VOICES)
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
        self.progress_bar.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
        self.progress_bar.start()

        try:
            self.model = build_model(MODEL_PATH, self.device)
            # Progress bar continues via _finish_loading_voices — do not stop yet
            self.status_label.config(text=f"Model loaded on {self.device}. Loading voices...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {e}")
            self.status_label.config(text="Model loading failed.")
            self.progress_bar.stop()
            self.progress_bar.grid_forget()
            self._loading = False
            return

        # Chain: load voices after model is ready, still via a deferred
        # callback so the UI remains responsive
        self.root.after(10, self._finish_loading_voices)

    def _finish_loading_voices(self):
        """Called via root.after() to keep UI responsive while loading voices."""
        # Prevent generation attempts while voices are still loading
        self.generate_button.config(state=tk.DISABLED)
        self.load_voices()
        self.progress_bar.stop()
        self.progress_bar.grid_forget()
        self._loading = False
        self.generate_button.config(state=tk.NORMAL)
        self.status_label.config(
            text=f"Ready — model on {self.device}, {len(self.voicepacks)} voices loaded."
        )

    def load_voices(self):
        failed = []
        for i, voice_name in enumerate(ALL_VOICES):
            try:
                voice_path = os.path.join(VOICES_DIR, f'{voice_name}.pt')
                self.voicepacks[voice_name] = torch.load(voice_path, map_location=self.device)
                # Keep the UI alive between each voice load so the progress
                # bar keeps animating and the window doesn't appear frozen
                self.status_label.config(
                    text=f"Loading voices... ({i + 1}/{len(ALL_VOICES)})"
                )
                self.root.update()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load voice {voice_name}: {e}")
                failed.append(voice_name)

        # Remove failed voices from the dropdown so users can't select them
        if failed:
            available = [v for v in ALL_VOICES if v not in failed]
            self.voice_dropdown['values'] = available
            if self.selected_voice.get() in failed:
                self.selected_voice.set(available[0] if available else '')

    def generate_audio_thread(self):
        if self._loading:
            self.status_label.config(text="Still loading voices — please wait.")
            return
        if self.model is None:
            self.status_label.config(text="Model not loaded. Please restart the application.")
            return

        self.generate_button.config(state=tk.DISABLED)
        self.status_label.config(text="Generating audio...")
        self.progress_bar.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
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
            # Validate language prefix — only 'a' (American) and 'b' (British) are supported
            lang = voice_name[0]
            if lang not in VOICE_LANG:
                self.update_ui_after_generation(
                    False, f"Unsupported voice language prefix '{lang}' for voice '{voice_name}'."
                )
                return

            voicepack = self.voicepacks[voice_name]
            audio, phonemes = generate(self.model, text, voicepack, lang=lang)

            # generate() returns (None, None) when tokenization produces no output
            if audio is None:
                self.update_ui_after_generation(
                    False, "Audio generation produced no output — the text may be empty after processing."
                )
                return

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
    # Repurpose the splash window (already visible since module load)
    # instead of creating a new Tk() — this avoids a second window flash
    _splash_label.destroy()
    _splash.geometry("")  # Clear fixed geometry so the main UI sizes naturally
    _splash.resizable(True, True)
    app = TTSApp(_splash)
    _splash.mainloop()
