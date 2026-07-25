"""Tests for tts_studio.config."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tts_studio.config import SAMPLE_RATE


class TestConfig:
    def test_sample_rate(self) -> None:
        assert SAMPLE_RATE == 24000
