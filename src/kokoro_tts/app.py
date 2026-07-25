"""Kokoro TTS v1.0 application controller.

Uses the ``kokoro`` pip package (KPipeline) instead of the vendored
v0.19 model files.
"""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from typing import Any

import requests
from kokoro import KPipeline

from kokoro_tts.audio.player import AudioPlayer
from kokoro_tts.audio.saver import save_audio_dialog
from kokoro_tts.config import ICON_PATH, LANG_CODES, SAMPLE_RATE
from kokoro_tts.tts.generator import generate_audio
from kokoro_tts.ui.events import (
    set_generating,
    set_generation_done,
    set_loading,
    set_ready,
)
from kokoro_tts.ui.main_window import build_ui, set_voices


class TTSApp:
    """Main application controller."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Text-to-Speech Generator — Kokoro v1.0")

        if ICON_PATH.exists():
            self.root.iconbitmap(str(ICON_PATH))

        self._pipeline: KPipeline | None = None
        self._loading = True
        self._audio_file: Path | None = None
        self._paused = False

        # Audio player
        self.player = AudioPlayer(frequency=SAMPLE_RATE)

        # Build widgets with v1.0 voice list
        self._widgets = build_ui(
            root,
            on_generate=self._on_generate,
            on_play=self._on_play,
            on_pause_resume=self._on_pause_resume,
            on_save=self._on_save,
        )

        # Clean up on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Show UI, defer model init
        self.root.update()
        self.root.after(50, self._start_loading)

    # ── startup ──────────────────────────────────────────────────

    def _start_loading(self) -> None:
        """Initialise the KPipeline and fetch available voices."""
        set_loading(self._widgets, "Loading Kokoro v1.0 model...")

        try:
            self._pipeline = KPipeline(lang_code="a")
        except Exception as exc:
            set_ready(self._widgets, f"Model loading failed: {exc}")
            self._loading = False
            return

        # Fetch voice list from Hugging Face
        self._widgets["status_label"].config(text="Fetching voice list...")
        self.root.after(10, self._load_voice_list)

    def _load_voice_list(self) -> None:
        """Query HF API for available voices and populate dropdown."""
        try:
            resp = requests.get(
                "https://huggingface.co/api/models/hexgrad/Kokoro-82M",
                timeout=10,
            )
            resp.raise_for_status()
            siblings = resp.json().get("siblings", [])
        except Exception:
            # Offline fallback — use known English voices
            siblings = []

        voices: list[str] = []
        en_voices: list[str] = []
        for sib in siblings:
            fname = sib.get("rfilename", "")
            if fname.startswith("voices/") and fname.endswith(".pt"):
                name = fname.replace("voices/", "").replace(".pt", "")
                voices.append(name)
                # English voices start with a or b
                if name.startswith(("a", "b")):
                    en_voices.append(name)

        # Prefer English voices; fall back to all if offline
        display = sorted(en_voices) if en_voices else ["af_heart", "af_bella"]

        set_voices(self._widgets, display)
        self._loading = False
        set_ready(
            self._widgets,
            f"Ready — Kokoro v1.0 ({len(display)} voices).",
        )

    # ── generate ──────────────────────────────────────────────────

    def _on_generate(self) -> None:
        """Validate and launch generation thread."""
        if self._loading:
            self._widgets["status_label"].config(text="Still loading — please wait.")
            return
        if self._pipeline is None:
            self._widgets["status_label"].config(text="Model not loaded.")
            return

        text = self._widgets["text_entry"].get("1.0", tk.END).strip()
        voice_name: str = self._widgets["voice_var"].get()

        if not text:
            set_generation_done(self._widgets, False, "Please enter some text.")
            return

        set_generating(self._widgets)
        threading.Thread(
            target=self._generate, args=(text, voice_name), daemon=True
        ).start()

    def _generate(self, text: str, voice_name: str) -> None:
        """Run TTS generation on background thread."""
        try:
            wav_path, _phonemes = generate_audio(
                self._pipeline, text, voice_name
            )
            # Clean up previous temp file
            if self._audio_file is not None:
                self.player.unload()
                try:
                    if self._audio_file.exists():
                        self._audio_file.unlink()
                except OSError:
                    pass
            self._audio_file = wav_path
            self._dispatch(set_generation_done, True, "Audio generated successfully.")
        except Exception as exc:
            self._dispatch(set_generation_done, False, f"Error: {exc}")

    # ── playback ──────────────────────────────────────────────────

    def _on_play(self) -> None:
        """Play / Stop toggle."""
        if self.player.is_playing or self._paused:
            self.player.stop()
            self._widgets["play_button"].config(text="Play", command=self._on_play)
            self._widgets["pause_resume_button"].config(state=tk.DISABLED, text="Pause")
            self._paused = False
        else:
            try:
                self.player.load(str(self._audio_file))
                self.player.play()
                self._widgets["play_button"].config(text="Stop", command=self._on_play)
                self._widgets["pause_resume_button"].config(state=tk.NORMAL, text="Pause")
                self._paused = False
                self._poll_playback_end()
            except Exception as exc:
                self._show_error("Playback Error", str(exc))

    def _poll_playback_end(self) -> None:
        """Periodically check if playback finished."""
        if self._paused or self.player.is_playing:
            self.root.after(200, self._poll_playback_end)
        else:
            self._widgets["play_button"].config(text="Play", command=self._on_play)
            self._widgets["pause_resume_button"].config(state=tk.DISABLED, text="Pause")
            self._paused = False

    def _on_pause_resume(self) -> None:
        """Pause / Resume toggle."""
        if self._paused:
            self.player.unpause()
            self._widgets["pause_resume_button"].config(text="Pause")
        else:
            self.player.pause()
            self._widgets["pause_resume_button"].config(text="Resume")
        self._paused = not self._paused

    def _on_save(self) -> None:
        """Save dialog."""
        if self._audio_file is None:
            return
        dest = save_audio_dialog(self._audio_file)
        if dest:
            self._widgets["status_label"].config(text=f"Audio saved to {dest}")

    # ── cleanup ───────────────────────────────────────────────────

    def _on_close(self) -> None:
        """Clean up temp files and destroy the window."""
        self.player.unload()
        if self._audio_file is not None and self._audio_file.exists():
            try:
                self._audio_file.unlink()
            except OSError:
                pass
        self.root.destroy()

    # ── helpers ───────────────────────────────────────────────────

    def _dispatch(self, fn: Any, *args: Any) -> None:
        """Schedule a UI update on the main thread."""
        self.root.after(0, lambda: fn(self._widgets, *args))

    @staticmethod
    def _show_error(title: str, message: str) -> None:
        """Show an error dialog."""
        from tkinter import messagebox

        messagebox.showerror(title, message)
