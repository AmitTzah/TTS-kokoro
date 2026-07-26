"""Audio generation with chunking, progress, and cancellation."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from tts_studio.config import SAMPLE_RATE
from tts_studio.settings import get_engine_settings
from tts_studio.text_utils import split_text
from tts_studio.ui.events import (
    set_generating,
    set_generation_done,
    update_progress,
)


class GenerationManager:
    """Handles text-to-speech generation with chunking and cancellation."""

    def __init__(self, app: Any):
        self._app = app
        self._cancel_event = threading.Event()

    @property
    def _widgets(self):
        return self._app._widgets

    @property
    def _engine(self):
        return self._app.engine

    # ── public API ───────────────────────────────────────────

    def generate(self) -> None:
        if self._app._loading:
            self._widgets["status_label"].config(text="Still loading...")
            return
        if self._engine is None or not self._engine.is_loaded:
            self._widgets["status_label"].config(text="No engine loaded.")
            return

        text = self._widgets["text_entry"].get("1.0", "end").strip()
        voice_name = self._widgets["voice_var"].get()
        voice_id = self._app._voice_map.get(voice_name, voice_name)

        if not text:
            set_generation_done(self._widgets, False, "Please enter some text.")
            return

        split_mode = self._widgets["split_var"].get()
        pause_sec = float(self._widgets["pause_var"].get().rstrip("s"))
        chunk_count = len(split_text(text, split_mode)) if split_mode != "off" else 1
        self._cancel_event.clear()
        set_generating(self._widgets, chunk_count=chunk_count)
        threading.Thread(
            target=self._run, args=(text, voice_id, split_mode, pause_sec), daemon=True
        ).start()

    def cancel(self) -> None:
        self._cancel_event.set()
        self._widgets["cancel_button"].config(state="disabled", text="Cancelling...")

    # ── generation thread ────────────────────────────────────

    def _run(self, text: str, voice_id: str, split_mode: str, pause_sec: float) -> None:
        import numpy as np
        import soundfile as sf
        import tempfile

        try:
            chunks = split_text(text, split_mode)
            all_wavs = []
            total = len(chunks)
            failed_count = 0
            sr = getattr(self._engine, "sample_rate", SAMPLE_RATE)

            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                if self._cancel_event.is_set():
                    break

                try:
                    engine_name = self._widgets["provider_var"].get()
                    settings = get_engine_settings(engine_name)
                    wav_path, _ = self._engine.generate(chunk, voice_id, **settings)
                    data, _ = sf.read(str(wav_path))
                    all_wavs.append(data)
                    wav_path.unlink()
                except Exception as exc:
                    print(f"[WARN] Chunk {i} failed: {exc}")
                    failed_count += 1
                    all_wavs.append(np.zeros(int(0.3 * sr), dtype=np.float32))

                pct = int((i + 1) / total * 100) if total > 0 else 100
                self._dispatch_progress(pct)

            if not all_wavs:
                self._dispatch(set_generation_done, False, "No audio generated.")
                return

            gap = np.zeros(int(pause_sec * sr), dtype=np.float32)
            combined = all_wavs[0]
            for w in all_wavs[1:]:
                combined = np.concatenate([combined, gap, w])

            with tempfile.NamedTemporaryFile(prefix="tts_gen_", suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, combined, sr)
                wav_path = tmp.name

            self._app._replace_audio(Path(wav_path))

            cancelled = self._cancel_event.is_set()
            if cancelled and failed_count > 0:
                msg = f"Cancelled — {failed_count} of {total} chunks failed."
            elif cancelled:
                msg = f"Audio generated ({len(all_wavs)}/{total} chunks)."
            elif failed_count > 0:
                msg = f"Audio generated ({failed_count} of {total} chunks failed)."
            else:
                msg = "Audio generated."
            self._dispatch(set_generation_done, True, msg)
        except Exception as exc:
            self._dispatch(set_generation_done, False, f"Error: {exc}")

    # ── helpers ──────────────────────────────────────────────

    def _dispatch_progress(self, pct: float) -> None:
        self._app.root.after(0, lambda: update_progress(self._widgets, pct))

    def _dispatch(self, fn: Any, *args: Any) -> None:
        self._app.root.after(0, lambda: fn(self._widgets, *args))
