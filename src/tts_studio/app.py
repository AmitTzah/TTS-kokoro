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
from tts_studio.models.manager import get_downloaded_models
from tts_studio.models.registry import AVAILABLE_MODELS
from tts_studio.ui.events import (
    set_generating,
    set_generation_done,
    set_loading,
    set_ready,
)
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

        self.player = AudioPlayer(frequency=SAMPLE_RATE)

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
        )

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
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
        self._refresh_voices()
        self._loading = False
        set_ready(
            widgets,
            f"Ready — {len(voice_ids)} voices on {self.engine.device}.",
        )

    # ── voice cloning ────────────────────────────────────────

    def _on_clone_voice(self) -> None:
        if self.engine is None or not self.engine.supports_cloning:
            return
        from tkinter import filedialog, simpledialog

        path = filedialog.askopenfilename(
            title="Select Reference Audio (10s clip)",
            filetypes=[("Audio files", "*.wav *.mp3 *.flac *.ogg"), ("All files", "*.*")],
        )
        if not path:
            return
        name = simpledialog.askstring(
            "Voice Name", "Name for this cloned voice:"
        )
        if not name:
            return
        try:
            voice = self.engine.add_voice(name, path)
            self._refresh_voices()
            # Select the new voice by display name
            if voice.name in self._voice_map:
                self._widgets["voice_var"].set(voice.name)
        except Exception as exc:
            self._show_error("Clone Failed", str(exc))

    def _on_delete_voice(self) -> None:
        if self.engine is None or not self.engine.supports_cloning:
            return
        voice_name = self._widgets["voice_var"].get()
        voice_id = self._voice_map.get(voice_name, voice_name)
        voices = self.engine.list_voices()
        target = next((v for v in voices if v.id == voice_id), None)
        if target is None or not target.is_custom:
            return
        from tkinter import messagebox

        if messagebox.askyesno("Delete Voice", f"Delete '{target.name}'?"):
            self.engine.delete_voice(voice_id)
            self._refresh_voices()

    def _refresh_voices(self) -> None:
        if self.engine is None:
            return
        voices = self.engine.list_voices()
        # Build display-name → id mapping, show names in dropdown
        self._voice_map = {v.name: v.id for v in voices}
        set_voices(self._widgets, list(self._voice_map.keys()))
        # Show/hide clone/delete buttons based on engine capability
        if self.engine.supports_cloning:
            self._widgets["clone_btn"].config(state=tk.NORMAL)
        else:
            self._widgets["clone_btn"].config(state=tk.DISABLED)
        # Delete button enabled only for custom voices
        self._update_delete_btn()
        # Bind dropdown change to update delete button
        self._widgets["voice_dropdown"].bind(
            "<<ComboboxSelected>>", lambda e: self._update_delete_btn(), add="+"
        )

    def _update_delete_btn(self) -> None:
        voice_name = self._widgets["voice_var"].get()
        voice_id = self._voice_map.get(voice_name, voice_name)
        if self.engine and self.engine.supports_cloning:
            voices = self.engine.list_voices()
            target = next((v for v in voices if v.id == voice_id), None)
            if target and target.is_custom:
                self._widgets["delete_btn"].config(state=tk.NORMAL)
            else:
                self._widgets["delete_btn"].config(state=tk.DISABLED)

    # ── model manager ────────────────────────────────────────

    def _open_model_manager(self) -> None:
        dialog = tk.Toplevel(self.root)
        ModelManager(dialog)

    # ── generate ─────────────────────────────────────────────

    def _on_generate(self) -> None:
        if self._loading:
            self._widgets["status_label"].config(text="Still loading...")
            return
        if self.engine is None or not self.engine.is_loaded:
            self._widgets["status_label"].config(text="No engine loaded.")
            return

        text = self._widgets["text_entry"].get("1.0", tk.END).strip()
        voice_name = self._widgets["voice_var"].get()
        voice_id = self._voice_map.get(voice_name, voice_name)

        if not text:
            set_generation_done(self._widgets, False, "Please enter some text.")
            return

        split_mode = self._widgets["split_var"].get()
        pause_sec = float(self._widgets["pause_var"].get())
        set_generating(self._widgets)
        threading.Thread(
            target=self._generate, args=(text, voice_id, split_mode, pause_sec), daemon=True
        ).start()

    def _generate(self, text: str, voice_id: str, split_mode: str = "paragraphs", pause_sec: float = 0.35) -> None:
        import re

        import numpy as np
        import soundfile as sf
        import tempfile

        try:
            chunks = TTSApp._split_text(text, split_mode)

            all_wavs = []
            for chunk in chunks:
                if not chunk.strip():
                    continue
                wav_path, _ = self.engine.generate(chunk, voice_id)
                data, _ = sf.read(str(wav_path))
                all_wavs.append(data)
                # Clean up intermediate temp file immediately
                wav_path.unlink()

            if not all_wavs:
                self._dispatch(set_generation_done, False, "No audio generated.")
                return

            # Get sample rate from engine (not hardcoded — varies per engine)
            sr = getattr(self.engine, "sample_rate", 24000)
            gap = np.zeros(int(pause_sec * sr), dtype=np.float32)
            combined = all_wavs[0]
            for w in all_wavs[1:]:
                combined = np.concatenate([combined, gap, w])

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, combined, sr)
                wav_path = tmp.name

            if self._audio_file is not None:
                self.player.unload()
                try:
                    if self._audio_file.exists():
                        self._audio_file.unlink()
                except OSError:
                    pass
            self._audio_file = Path(wav_path)
            self._dispatch(set_generation_done, True, "Audio generated.")
        except Exception as exc:
            self._dispatch(set_generation_done, False, f"Error: {exc}")

    @staticmethod
    def _split_text(text: str, mode: str = "paragraphs") -> list[str]:
        """Split text by paragraphs, sentences, or not at all."""
        import re

        if mode == "off":
            return [text]

        if mode == "sentences":
            return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]

        # mode == "paragraphs"
        # Split on double newlines. If text only has single newlines,
        # treat each line as a paragraph.
        paragraphs = re.split(r"\n\s*\n", text.strip())
        if len(paragraphs) <= 1:
            paragraphs = [p.strip() for p in text.strip().split("\n") if p.strip()]
        return [p.strip() for p in paragraphs if p.strip()] or [text]

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

    def _dispatch(self, fn: Any, *args: Any) -> None:
        self.root.after(0, lambda: fn(self._widgets, *args))

    @staticmethod
    def _show_error(title: str, message: str) -> None:
        from tkinter import messagebox

        messagebox.showerror(title, message)
