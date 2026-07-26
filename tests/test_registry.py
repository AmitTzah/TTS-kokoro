"""Tests for tts_studio.models.registry — model catalog."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tts_studio.models.registry import AVAILABLE_MODELS, get_model, get_models_by_provider


class TestRegistry:
    def test_has_kokoro_and_chatterbox(self) -> None:
        providers = {m.provider for m in AVAILABLE_MODELS}
        assert "kokoro" in providers
        assert "chatterbox" in providers

    def test_get_models_by_provider(self) -> None:
        kokoro = get_models_by_provider("kokoro")
        assert len(kokoro) >= 1
        assert all(m.provider == "kokoro" for m in kokoro)

        chatterbox = get_models_by_provider("chatterbox")
        assert len(chatterbox) >= 2
        assert all(m.provider == "chatterbox" for m in chatterbox)

    def test_get_model_found(self) -> None:
        m = get_model("kokoro-v1.0-en")
        assert m is not None
        assert m.provider == "kokoro"

    def test_get_model_not_found(self) -> None:
        assert get_model("nonexistent") is None
