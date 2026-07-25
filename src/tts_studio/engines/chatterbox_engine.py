"""Chatterbox TTS engine via the `chatterbox-tts` pip package.

Known upstream issue: perth 1.0.1 on PyPI uses pkg_resources which
was removed in setuptools>=81.  The fix is on perth master but
unreleased.  We monkeypatch before importing chatterbox.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

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

    def list_voices(self) -> list[VoiceInfo]:
        # Chatterbox has a built-in default voice when no reference audio
        # is provided.  Voice cloning via audio_prompt_path is also available.
        return [
            VoiceInfo(id="default", name="Default", language="en"),
            VoiceInfo(id="clone", name="Clone (needs reference audio)", language="en"),
        ]

    def generate(
        self, text: str, voice_id: str, **kwargs: Any
    ) -> tuple[Path, str | None]:
        if self._model is None:
            raise RuntimeError("No model loaded")

        import io
        import sys
        import tempfile

        import soundfile as sf

        audio_prompt = kwargs.get("audio_prompt_path")

        # Suppress chatterbox stdout during generation — it may emit
        # emoji/Unicode that breaks on Windows console (cp1252).
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

        try:
            if self._is_multilingual:
                lang = kwargs.get("language_id", "en")
                wav = self._model.generate(
                    text, language_id=lang, audio_prompt_path=audio_prompt
                )
            else:
                wav = self._model.generate(text, audio_prompt_path=audio_prompt)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        # wav is a torch tensor; save to temp file
        wav = wav.cpu() if wav.is_cuda else wav
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, wav.numpy().squeeze(), self._model.sr)
            return Path(tmp.name), None

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
