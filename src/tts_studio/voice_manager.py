"""Voice cloning and voice selection management."""

from __future__ import annotations

import tkinter as tk
from typing import Any

from tts_studio.settings import get_engine_settings, set_engine_setting
from tts_studio.ui.main_window import set_voices


class VoiceManager:
    """Handles voice cloning, deletion, refresh, and selection."""

    def __init__(self, app: Any):
        self._app = app

    @property
    def _widgets(self):
        return self._app._widgets

    @property
    def _engine(self):
        return self._app.engine

    # ── cloning ──────────────────────────────────────────────

    def clone_voice(self) -> None:
        if self._engine is None or not self._engine.supports_cloning:
            return
        from tkinter import filedialog, simpledialog

        path = filedialog.askopenfilename(
            title="Select Reference Audio (10s clip)",
            filetypes=[("Audio files", "*.wav *.mp3 *.flac *.ogg"), ("All files", "*.*")],
        )
        if not path:
            return
        name = simpledialog.askstring("Voice Name", "Name for this cloned voice:")
        if not name:
            return
        try:
            voice = self._engine.add_voice(name, path)
            self.refresh()
            if voice.name in self._app._voice_map:
                self._widgets["voice_var"].set(voice.name)
        except Exception as exc:
            self._app._show_error("Clone Failed", str(exc))

    def delete_voice(self) -> None:
        if self._engine is None or not self._engine.supports_cloning:
            return
        voice_name = self._widgets["voice_var"].get()
        voice_id = self._app._voice_map.get(voice_name, voice_name)
        voices = self._engine.list_voices()
        target = next((v for v in voices if v.id == voice_id), None)
        if target is None or not target.is_custom:
            return
        from tkinter import messagebox

        if messagebox.askyesno("Delete Voice", f"Delete '{target.name}'?"):
            self._engine.delete_voice(voice_id)
            self.refresh()

    # ── refresh / selection ──────────────────────────────────

    def refresh(self) -> None:
        if self._engine is None:
            return
        voices = self._engine.list_voices()
        self._app._voice_map = {v.name: v.id for v in voices}
        voice_names = list(self._app._voice_map.keys())
        set_voices(self._widgets, voice_names)

        # Restore last-used voice and pause for this engine
        engine_name = self._widgets["provider_var"].get()
        eng_settings = get_engine_settings(engine_name)
        last_voice = eng_settings.get("last_voice", "")
        if last_voice in self._app._voice_map:
            self._widgets["voice_var"].set(last_voice)
        elif voice_names:
            self._widgets["voice_var"].set(voice_names[0])
        # Restore pause
        last_pause = eng_settings.get("last_pause", "")
        if last_pause:
            self._widgets["pause_var"].set(last_pause)

        # Set default split mode based on engine capability
        from tts_studio.engines.kokoro_engine import KokoroEngine

        if isinstance(self._engine, KokoroEngine):
            self._widgets["split_var"].set("off")
            from tts_studio.ui.main_window import set_split_enabled
            set_split_enabled(self._widgets, False)
        else:
            self._widgets["split_var"].set("paragraphs")
            from tts_studio.ui.main_window import set_split_enabled
            set_split_enabled(self._widgets, True)

        # Show/hide clone/delete buttons
        if self._engine.supports_cloning:
            self._widgets["clone_btn"].config(state=tk.NORMAL)
        else:
            self._widgets["clone_btn"].config(state=tk.DISABLED)
        self._update_delete_btn()
        # Save pause on change
        self._widgets["pause_combo"].bind(
            "<<ComboboxSelected>>", lambda e: self._save_pause(), add="+"
        )

    def on_voice_selected(self) -> None:
        self._update_delete_btn()
        engine_name = self._widgets["provider_var"].get()
        voice_name = self._widgets["voice_var"].get()
        if voice_name:
            set_engine_setting(engine_name, "last_voice", voice_name)
        self._save_pause(engine_name)

    def _save_pause(self, engine_name: str | None = None) -> None:
        if engine_name is None:
            engine_name = self._widgets["provider_var"].get()
        pause_val = self._widgets["pause_var"].get()
        if pause_val:
            set_engine_setting(engine_name, "last_pause", pause_val)

    def _update_delete_btn(self) -> None:
        voice_name = self._widgets["voice_var"].get()
        voice_id = self._app._voice_map.get(voice_name, voice_name)
        if self._engine and self._engine.supports_cloning:
            voices = self._engine.list_voices()
            target = next((v for v in voices if v.id == voice_id), None)
            if target and target.is_custom:
                self._widgets["delete_btn"].config(state=tk.NORMAL)
            else:
                self._widgets["delete_btn"].config(state=tk.DISABLED)
