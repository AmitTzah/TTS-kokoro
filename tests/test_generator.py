"""Tests for kokoro_tts.tts.generator — audio generation logic."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kokoro_tts.tts.generator import generate_audio


class TestGenerateAudio:
    def test_returns_none_raises_value_error(self) -> None:
        """When the underlying generate() returns (None, None), raise ValueError."""
        with patch("kokoro.generate", return_value=(None, None)):
            with pytest.raises(ValueError, match="no output"):
                generate_audio(MagicMock(), "hello", {}, "a")

    def test_success_writes_temp_wav(self) -> None:
        """Happy path: audio array is written to a temp .wav file."""
        import numpy as np

        fake_audio = np.zeros(24000, dtype=np.float32)

        with patch("kokoro.generate", return_value=(fake_audio, "həˈloʊ")):
            wav_path, phonemes = generate_audio(MagicMock(), "hello", {}, "a")

        assert wav_path.suffix == ".wav"
        assert wav_path.exists()
        assert phonemes == "həˈloʊ"

        # Cleanup
        wav_path.unlink()

    def test_temp_file_is_different_each_call(self) -> None:
        """Each call produces a unique temp file."""
        import numpy as np

        fake_audio = np.zeros(100, dtype=np.float32)

        with patch("kokoro.generate", return_value=(fake_audio, "")):
            p1, _ = generate_audio(MagicMock(), "a", {}, "a")
            p2, _ = generate_audio(MagicMock(), "b", {}, "b")

        assert p1 != p2
        p1.unlink()
        p2.unlink()
