"""Tests for kokoro_tts.config — constants and path validation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure src/ is on the path for test runs
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kokoro_tts.config import ALL_VOICES, VOICE_CATEGORIES, VOICE_LANG, SAMPLE_RATE


class TestVoiceDefinitions:
    def test_all_voices_is_flat_list(self) -> None:
        assert isinstance(ALL_VOICES, list)
        assert len(ALL_VOICES) == 11
        assert ALL_VOICES[0] == "af"

    def test_voice_categories_contains_all_voices(self) -> None:
        flat = [v for voices in VOICE_CATEGORIES.values() for v in voices]
        assert sorted(flat) == sorted(ALL_VOICES)

    def test_voice_lang_only_valid_prefixes(self) -> None:
        for voice_name in ALL_VOICES:
            prefix = voice_name[0]
            assert prefix in VOICE_LANG, (
                f"Voice '{voice_name}' has unknown language prefix '{prefix}'"
            )

    def test_sample_rate_is_positive(self) -> None:
        assert SAMPLE_RATE > 0
        assert SAMPLE_RATE == 24000
