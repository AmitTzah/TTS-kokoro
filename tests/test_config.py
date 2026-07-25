"""Tests for kokoro_tts.config — constants and validation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kokoro_tts.config import LANG_CODES, SAMPLE_RATE


class TestConfig:
    def test_lang_codes_has_english(self) -> None:
        """English (a, b) is present."""
        assert "a" in LANG_CODES
        assert "b" in LANG_CODES
        assert LANG_CODES["a"] == "American English"

    def test_lang_codes_count(self) -> None:
        """v1.0 has 9 language codes."""
        assert len(LANG_CODES) == 9

    def test_sample_rate(self) -> None:
        """Sample rate is 24000 Hz."""
        assert SAMPLE_RATE == 24000
