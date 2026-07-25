"""Kokoro TTS engine via the `kokoro` pip package (KPipeline)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kokoro import KPipeline

from tts_studio.engines.base import ModelInfo, TTSEngine, VoiceInfo


class KokoroEngine(TTSEngine):
    """Kokoro v1.0 engine wrapping KPipeline."""

    def __init__(self) -> None:
        self._pipeline: KPipeline | None = None
        self._model_id: str = ""

    # ── TTSEngine interface ──────────────────────────────────

    def list_models(self) -> list[ModelInfo]:
        from tts_studio.models.registry import get_models_by_provider

        return get_models_by_provider("kokoro")

    def load_model(self, model_id: str) -> None:
        self._pipeline = KPipeline(lang_code="a")
        self._model_id = model_id

    def list_voices(self) -> list[VoiceInfo]:
        if self._pipeline is None:
            return []
        # Fetch voice list from HF
        import requests

        try:
            resp = requests.get(
                "https://huggingface.co/api/models/hexgrad/Kokoro-82M",
                timeout=10,
            )
            resp.raise_for_status()
            siblings = resp.json().get("siblings", [])
        except Exception:
            siblings = []

        voices: list[VoiceInfo] = []
        for sib in siblings:
            fname = sib.get("rfilename", "")
            if fname.startswith("voices/") and fname.endswith(".pt"):
                name = fname.replace("voices/", "").replace(".pt", "")
                lang = "en" if name[0] in ("a", "b") else name[0]
                voices.append(VoiceInfo(id=name, name=name, language=lang))

        if not voices:
            # Offline fallback
            voices = [
                VoiceInfo(id="af_heart", name="af_heart", language="en"),
                VoiceInfo(id="af_bella", name="af_bella", language="en"),
            ]
        return sorted(voices, key=lambda v: v.id)

    def generate(
        self, text: str, voice_id: str, **kwargs: Any
    ) -> tuple[Path, str | None]:
        if self._pipeline is None:
            raise RuntimeError("No model loaded")

        from tts_studio.tts.generator import generate_audio

        return generate_audio(self._pipeline, text, voice_id)

    def unload(self) -> None:
        import torch

        self._pipeline = None
        torch.cuda.empty_cache()

    @property
    def is_loaded(self) -> bool:
        return self._pipeline is not None

    @property
    def device(self) -> str:
        if self._pipeline and self._pipeline.model:
            return str(self._pipeline.model.device)
        return "cpu"
