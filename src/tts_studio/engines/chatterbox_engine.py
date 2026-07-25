"""Chatterbox TTS engine via the `chatterbox-tts` pip package."""

from __future__ import annotations

import io
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any


@contextmanager
def _suppress_stdout():
    """Suppress stdout/stderr during model calls.

    Chatterbox emits emoji/Unicode that breaks on Windows cp1252 console.
    """
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        yield
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr


# ── Monkeypatch perth before chatterbox touches it ──────────
import perth as _perth

if _perth.PerthImplicitWatermarker is None:

    class _FakeWatermarker:
        def apply_watermark(self, wav, *args, **kwargs):
            return wav

        def get_watermark(self, *args, **kwargs):
            return None

    _perth.PerthImplicitWatermarker = _FakeWatermarker

from tts_studio.engines.base import ModelInfo, TTSEngine, VoiceInfo


class ChatterboxEngine(TTSEngine):
    """Chatterbox engine wrapping ChatterboxTTS / ChatterboxMultilingualTTS."""

    def __init__(self) -> None:
        self._model: Any = None
        self._model_id: str = ""
        self._is_multilingual: bool = False

    def list_models(self) -> list[ModelInfo]:
        from tts_studio.models.registry import get_models_by_provider

        return get_models_by_provider("chatterbox")

    def load_model(self, model_id: str) -> None:
        if "multilingual" in model_id:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS

            self._model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")
            self._is_multilingual = True
        else:
            from chatterbox.tts_turbo import ChatterboxTurboTTS

            self._model = ChatterboxTurboTTS.from_pretrained(device="cuda")
            self._is_multilingual = False
        self._model_id = model_id

    # ── Voice management ───────────────────────────────────

    @property
    def supports_cloning(self) -> bool:
        return True

    def _refs_dir(self) -> Path:
        from tts_studio.config import MODELS_DIR

        d = MODELS_DIR / "references"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def list_voices(self) -> list[VoiceInfo]:
        voices = [
            VoiceInfo(id="default", name="Default", language="en"),
        ]
        # Scan saved reference clips
        refs_dir = self._refs_dir()
        for meta_file in sorted(refs_dir.glob("*.json")):
            try:
                import json

                meta = json.loads(meta_file.read_text())
                ref_path = refs_dir / meta.get("reference_file", "")
                voices.append(
                    VoiceInfo(
                        id=meta["id"],
                        name=meta["name"],
                        language=meta.get("language", "en"),
                        is_custom=True,
                        reference_path=str(ref_path) if ref_path.exists() else "",
                    )
                )
            except Exception:
                continue
        return voices

    def add_voice(self, name: str, reference_path: str) -> VoiceInfo:
        import json
        import shutil
        import uuid

        src = Path(reference_path)
        if not src.exists():
            raise FileNotFoundError(f"Reference audio not found: {reference_path}")

        voice_id = f"clone-{uuid.uuid4().hex[:8]}"
        refs_dir = self._refs_dir()

        # Copy reference clip
        ext = src.suffix or ".wav"
        dest_name = f"{voice_id}{ext}"
        shutil.copy2(src, refs_dir / dest_name)

        # Save metadata
        meta = {
            "id": voice_id,
            "name": name,
            "language": "en",
            "reference_file": dest_name,
        }
        (refs_dir / f"{voice_id}.json").write_text(json.dumps(meta, indent=2))

        return VoiceInfo(
            id=voice_id,
            name=name,
            language="en",
            is_custom=True,
            reference_path=str(refs_dir / dest_name),
        )

    def delete_voice(self, voice_id: str) -> None:
        refs_dir = self._refs_dir()
        for f in refs_dir.glob(f"{voice_id}.*"):
            f.unlink()

    # ── Generation ─────────────────────────────────────────

    def generate(
        self, text: str, voice_id: str, **kwargs: Any
    ) -> tuple[Path, str | None]:
        if self._model is None:
            raise RuntimeError("No model loaded")

        import tempfile

        import soundfile as sf

        # Look up reference path for custom voices
        audio_prompt = kwargs.get("audio_prompt_path")
        if audio_prompt is None and voice_id != "default":
            for v in self.list_voices():
                if v.id == voice_id and v.reference_path:
                    audio_prompt = v.reference_path
                    break

        # Reload on default voice switch to clear cached conditionals
        if voice_id == "default":
            self._last_voice = getattr(self, "_last_voice", None)
            if self._last_voice != "default":
                self._reload_model()
            self._last_voice = "default"

        with _suppress_stdout():
            if self._is_multilingual:
                lang = kwargs.get("language_id", "en")
                wav = self._model.generate(
                    text, language_id=lang, audio_prompt_path=audio_prompt
                )
            else:
                wav = self._model.generate(text, audio_prompt_path=audio_prompt)

        wav = wav.cpu() if wav.is_cuda else wav
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, wav.numpy().squeeze(), self._model.sr)
            return Path(tmp.name), None

    def _reload_model(self) -> None:
        """Reload the model to clear cached voice conditionals."""
        model_id = self._model_id
        self.unload()
        self.load_model(model_id)

    def unload(self) -> None:
        import torch

        self._model = None
        torch.cuda.empty_cache()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def device(self) -> str:
        return "cuda" if self._model is not None else "cpu"

    @property
    def sample_rate(self) -> int:
        if self._model is not None:
            return self._model.sr
        return 24000
