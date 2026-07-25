"""Kokoro TTS application controller.

Wires together the splash screen, model, voices, TTS generator, audio
player, and Tkinter UI.  This module contains the orchestration logic
that was previously mixed into the monolithic ``tts-gui.pyw``.
"""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from typing import Any

import torch

from kokoro_tts.audio.player import AudioPlayer
from kokoro_tts.audio.saver import save_audio_dialog
from kokoro_tts.config import SAMPLE_RATE
from kokoro_tts.model.loader import load_model
from kokoro_tts.tts.generator import generate_audio
from kokoro_tts.ui.events import (
    set_generating,
    set_generation_done,
    set_loading,
    set_ready,
)
from kokoro_tts.ui.main_window import build_ui
from kokoro_tts.voice import ALL_VOICES, VOICE_LANG
from kokoro_tts.voice.loader import load_voices


class TTSApp:
    """Main application controller."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Text-to-Speech Generator")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model: torch.nn.Module | None = None
        self.voicepacks: dict[str, dict] = {}
        self._loading = True  # Guard against generation during startup
        self._audio_file: Path | None = None
        self._paused = False

        # Audio player (initialised here so errors show in the visible window)
        self.player = AudioPlayer(frequency=SAMPLE_RATE)

        # Build widgets
        self._widgets = build_ui(
            root,
            on_generate=self._on_generate,
            on_play=self._on_play,
            on_pause_resume=self._on_pause_resume,
            on_save=self._on_save,
        )

        # Clean up temp files when the user closes the window
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Show UI immediately, defer heavy loading
        self.root.update()
        self.root.after(50, self._start_loading)

    # ── startup pipeline ──────────────────────────────────────

    def _start_loading(self) -> None:
        """Phase 1: load the Kokoro model."""
        set_loading(self._widgets, "Loading model...")

        try:
            self.model = load_model(self.device)
        except Exception as exc:
            set_ready(self._widgets, f"Model loading failed: {exc}")
            self._loading = False
            return

        self._widgets["status_label"].config(
            text=f"Model loaded on {self.device}. Loading voices..."
        )
        self.root.after(10, self._finish_loading_voices)

    def _finish_loading_voices(self) -> None:
        """Phase 2: load voice packs with per-voice progress."""
        self._widgets["generate_button"].config(state=tk.DISABLED)

        self.voicepacks = load_voices(
            self.device,
            on_progress=lambda current, total: self._widgets[
                "status_label"
            ].config(text=f"Loading voices... ({current}/{total})"),
            on_error=lambda name, err: self._show_error(
                "Voice Load Error", f"Failed to load '{name}': {err}"
            ),
            root=self.root,
        )

        # Remove failed voices from the dropdown
        loaded = set(self.voicepacks.keys())
        failed = [v for v in ALL_VOICES if v not in loaded]
        if failed:
            available = [v for v in ALL_VOICES if v in loaded]
            self._widgets["voice_dropdown"]["values"] = available
            if self._widgets["voice_var"].get() in failed:
                self._widgets["voice_var"].set(available[0] if available else "")

        self._loading = False
        set_ready(
            self._widgets,
            f"Ready — model on {self.device}, {len(self.voicepacks)} voices loaded.",
        )

    # ── generate ───────────────────────────────────────────────

    def _on_generate(self) -> None:
        """Button handler — validate and launch generation thread."""
        if self._loading:
            self._widgets["status_label"].config(
                text="Still loading voices — please wait."
            )
            return
        if self.model is None:
            self._widgets["status_label"].config(
                text="Model not loaded. Please restart the application."
            )
            return

        # Read widget values on the MAIN thread (tkinter is not thread-safe)
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
        """Run TTS generation on a background thread."""
        lang = voice_name[0] if voice_name else ""
        if not lang or lang not in VOICE_LANG:
            self._dispatch(
                set_generation_done,
                False,
                f"Unsupported voice prefix '{lang}' for '{voice_name}'.",
            )
            return

        try:
            voicepack = self.voicepacks[voice_name]
            wav_path, _phonemes = generate_audio(
                self.model, text, voicepack, lang=lang
            )
            # Clean up previous temp file.
            # player.unload() stops playback AND releases the file handle
            # (pygame.mixer.music.stop() alone keeps it locked on Windows).
            if self._audio_file is not None:
                self.player.unload()
                try:
                    if self._audio_file.exists():
                        self._audio_file.unlink()
                except OSError:
                    pass  # Already gone or still locked — not critical
            self._audio_file = wav_path
            self._dispatch(set_generation_done, True, "Audio generated successfully.")
        except Exception as exc:
            self._dispatch(set_generation_done, False, f"Error: {exc}")

    # ── playback ───────────────────────────────────────────────

    def _on_play(self) -> None:
        """Play / Stop toggle."""
        if self.player.is_playing or self._paused:
            self.player.stop()
            self._widgets["play_button"].config(
                text="Play", command=self._on_play
            )
            self._widgets["pause_resume_button"].config(
                state=tk.DISABLED, text="Pause"
            )
            self._paused = False
        else:
            try:
                self.player.load(str(self._audio_file))
                self.player.play()
                self._widgets["play_button"].config(
                    text="Stop", command=self._on_play
                )
                self._widgets["pause_resume_button"].config(
                    state=tk.NORMAL, text="Pause"
                )
                self._paused = False
                # Poll for natural playback end so the button reverts
                self._poll_playback_end()
            except Exception as exc:
                self._show_error("Playback Error", str(exc))

    def _poll_playback_end(self) -> None:
        """Periodically check if playback finished; revert button when done.

        Keeps polling while paused — pygame may report ``get_busy() == False``
        for paused audio on some SDL versions, but we must not reset the
        button state while the user has intentionally paused.
        """
        if self._paused or self.player.is_playing:
            self.root.after(200, self._poll_playback_end)
        else:
            self._widgets["play_button"].config(
                text="Play", command=self._on_play
            )
            self._widgets["pause_resume_button"].config(
                state=tk.DISABLED, text="Pause"
            )
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

    # ── cleanup ────────────────────────────────────────────────

    def _on_close(self) -> None:
        """Clean up temp files and destroy the window."""
        self.player.unload()
        if self._audio_file is not None and self._audio_file.exists():
            try:
                self._audio_file.unlink()
            except OSError:
                pass
        self.root.destroy()

    # ── helpers ────────────────────────────────────────────────

    def _dispatch(self, fn: Any, *args: Any) -> None:
        """Schedule a UI update on the main thread."""
        self.root.after(0, lambda: fn(self._widgets, *args))

    @staticmethod
    def _show_error(title: str, message: str) -> None:
        """Show an error dialog (must be called from main thread)."""
        from tkinter import messagebox

        messagebox.showerror(title, message)
