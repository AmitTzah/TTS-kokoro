"""TTS Studio — multi-engine controller."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from typing import Any

from tts_studio.audio.player import AudioPlayer
from tts_studio.audio.saver import save_audio_dialog
from tts_studio.config import ICON_PATH, SAMPLE_RATE
from tts_studio.engines.base import TTSEngine
from tts_studio.engines.kokoro_engine import KokoroEngine
from tts_studio.generation import GenerationManager
from tts_studio.models.manager import get_downloaded_models
from tts_studio.models.registry import AVAILABLE_MODELS
from tts_studio.ui.events import set_loading, set_ready
from tts_studio.voice_manager import VoiceManager
from tts_studio.ui.main_window import build_ui, set_models, set_voices
from tts_studio.ui.model_manager import ModelManager


class TTSApp:
    """Main application controller."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("TTS Studio")

        if ICON_PATH.exists():
            self.root.iconbitmap(str(ICON_PATH))

        self.engine: TTSEngine | None = None
        self._loading = True
        self._audio_file: Path | None = None
        self._paused = False
        self._voice_map: dict[str, str] = {}  # display_name → voice_id
        self._settings_dialog: tk.Toplevel | None = None
        self._model_manager_dialog: tk.Toplevel | None = None

        self.player = AudioPlayer(frequency=SAMPLE_RATE)

        self.voice_manager = VoiceManager(self)
        self.generation = GenerationManager(self)

        self._widgets = build_ui(
            root,
            on_generate=self._on_generate,
            on_play=self._on_play,
            on_pause_resume=self._on_pause_resume,
            on_save=self._on_save,
            on_provider_change=self._on_provider_change,
            on_model_change=self._on_model_change,
            on_model_manager=self._open_model_manager,
            on_clone_voice=self._on_clone_voice,
            on_delete_voice=self._on_delete_voice,
            on_settings=self._on_settings,
        )

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Wire cancel button to generation manager
        self._widgets["cancel_button"].config(command=self.generation.cancel)

        self.root.update()
        self.root.after(50, self._startup)

    # ── startup ──────────────────────────────────────────────

    def _startup(self) -> None:
        set_loading(self._widgets, "Loading...")
        # Populate model list for default provider
        self._on_provider_change("kokoro")

    # ── provider / model switching ───────────────────────────

    def _on_provider_change(self, provider: str) -> None:
        downloaded = get_downloaded_models()
        # Only show installed models for this provider
        models = [
            m for m in AVAILABLE_MODELS
            if m.provider == provider and m.id in downloaded
        ]
        model_names = [m.name for m in models]
        set_models(self._widgets, model_names)

        if model_names:
            self._on_model_change(model_names[0])
        else:
            set_voices(self._widgets, [])
            set_ready(
                self._widgets,
                f"No {provider} models installed. Use Manage Models to download one.",
            )
            self._loading = False

    def _on_model_change(self, model_name: str) -> None:
        # Find model info
        model = next((m for m in AVAILABLE_MODELS if m.name == model_name), None)
        if model is None:
            return

        set_loading(self._widgets, f"Loading {model.name}...")

        # Unload previous engine
        if self.engine is not None:
            self.engine.unload()

        # Create engine for this provider
        if model.provider == "kokoro":
            self.engine = KokoroEngine()
        elif model.provider == "chatterbox":
            try:
                from tts_studio.engines.chatterbox_engine import ChatterboxEngine
                self.engine = ChatterboxEngine()
            except ImportError:
                set_ready(self._widgets, "Chatterbox not installed. pip install chatterbox-tts")
                self._loading = False
                return
        else:
            return

        # Load model in background
        threading.Thread(target=self._load_engine, args=(model.id,), daemon=True).start()

    def _load_engine(self, model_id: str) -> None:
        try:
            self.engine.load_model(model_id)
        except Exception as exc:
            self._dispatch(set_ready, f"Failed to load: {exc}")
            self._loading = False
            return

        # Get voices
        voices = self.engine.list_voices()
        voice_ids = [v.id for v in voices]

        self._dispatch(self._on_engine_ready, voice_ids)

    def _on_engine_ready(self, widgets: dict, voice_ids: list[str]) -> None:
        self.voice_manager.refresh()
        self._loading = False
        set_ready(
            widgets,
            f"Ready — {len(voice_ids)} voices on {self.engine.device}.",
        )

    # ── voice cloning (delegates) ────────────────────────────

    def _on_clone_voice(self) -> None:
        self.voice_manager.clone_voice()

    def _on_delete_voice(self) -> None:
        self.voice_manager.delete_voice()

    # ── settings ─────────────────────────────────────────────

    def _on_settings(self) -> None:
        if self._settings_dialog is not None and self._settings_dialog.winfo_exists():
            self._settings_dialog.lift()
            return

        from tts_studio.ui.settings_dialog import SettingsDialog

        self._settings_dialog = tk.Toplevel(self.root)
        SettingsDialog(self._settings_dialog, parent=self.root)
        self._settings_dialog.protocol("WM_DELETE_WINDOW", self._on_settings_closed)

    def _on_settings_closed(self) -> None:
        self._settings_dialog.destroy()
        self._settings_dialog = None

    # ── model manager ────────────────────────────────────────

    def _open_model_manager(self) -> None:
        if self._model_manager_dialog is not None and self._model_manager_dialog.winfo_exists():
            self._model_manager_dialog.lift()
            return

        self._model_manager_dialog = tk.Toplevel(self.root)
        ModelManager(self._model_manager_dialog, parent=self.root)
        self._model_manager_dialog.protocol("WM_DELETE_WINDOW", self._on_model_manager_closed)

    def _on_model_manager_closed(self) -> None:
        self._model_manager_dialog.destroy()
        self._model_manager_dialog = None

    # ── generate (delegates) ─────────────────────────────────

    def _on_generate(self) -> None:
        self.generation.generate()

    def _replace_audio(self, path: Path) -> None:
        """Called by GenerationManager to swap in new audio."""
        if self._audio_file is not None:
            self.player.unload()
            try:
                if self._audio_file.exists():
                    self._audio_file.unlink()
            except OSError:
                pass
        self._audio_file = path

    # ── playback ─────────────────────────────────────────────

    def _on_play(self) -> None:
        if self.player.is_playing or self._paused:
            self.player.stop()
            self._widgets["play_button"].config(text="Play", command=self._on_play)
            self._widgets["pause_resume_button"].config(state=tk.DISABLED, text="Pause")
            self._paused = False
        else:
            try:
                if self._audio_file is None:
                    return
                self.player.load(str(self._audio_file))
                self.player.play()
                self._widgets["play_button"].config(text="Stop", command=self._on_play)
                self._widgets["pause_resume_button"].config(state=tk.NORMAL, text="Pause")
                self._paused = False
                self._poll_playback_end()
            except Exception as exc:
                self._show_error("Playback Error", str(exc))

    def _poll_playback_end(self) -> None:
        if self._paused or self.player.is_playing:
            self.root.after(200, self._poll_playback_end)
        else:
            self._widgets["play_button"].config(text="Play", command=self._on_play)
            self._widgets["pause_resume_button"].config(state=tk.DISABLED, text="Pause")
            self._paused = False

    def _on_pause_resume(self) -> None:
        if self._paused:
            self.player.unpause()
            self._widgets["pause_resume_button"].config(text="Pause")
        else:
            self.player.pause()
            self._widgets["pause_resume_button"].config(text="Resume")
        self._paused = not self._paused

    def _on_save(self) -> None:
        if self._audio_file is None:
            return
        dest = save_audio_dialog(self._audio_file)
        if dest:
            self._widgets["status_label"].config(text=f"Saved to {dest}")

    # ── cleanup ──────────────────────────────────────────────

    def _on_close(self) -> None:
        self.player.unload()
        if self._audio_file is not None and self._audio_file.exists():
            try:
                self._audio_file.unlink()
            except OSError:
                pass
        self.root.destroy()

    def _dispatch_progress(self, pct: float) -> None:
        self.root.after(0, lambda: update_progress(self._widgets, pct))

    def _dispatch(self, fn: Any, *args: Any) -> None:
        self.root.after(0, lambda: fn(self._widgets, *args))

    @staticmethod
    def _show_error(title: str, message: str) -> None:
        from tkinter import messagebox

        messagebox.showerror(title, message)
