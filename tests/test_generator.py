"""Tests for kokoro_tts.tts.generator — v1.0 KPipeline-based generation."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kokoro_tts.tts.generator import generate_audio


class TestGenerateAudio:
    def test_concatenates_multiple_chunks(self) -> None:
        """Multiple pipeline chunks are concatenated into one WAV."""
        fake_audio1 = np.zeros(12000, dtype=np.float32)
        fake_audio2 = np.ones(12000, dtype=np.float32)

        mock_pipeline = MagicMock()
        mock_pipeline.return_value = iter([
            ("Hello", "həˈloʊ", fake_audio1),
            (" world", " wɜːld", fake_audio2),
        ])

        wav_path, phonemes = generate_audio(mock_pipeline, "Hello world", "af_heart")

        assert wav_path.suffix == ".wav"
        assert wav_path.exists()
        assert "həˈloʊ" in (phonemes or "")
        assert "wɜːld" in (phonemes or "")

        # Verify concatenation
        import soundfile as sf

        data, sr = sf.read(str(wav_path))
        assert len(data) == 24000  # 12000 + 12000
        wav_path.unlink()

    def test_empty_output_raises(self) -> None:
        """When pipeline yields no audio, raises ValueError."""
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = iter([
            ("text", "ps", None),
        ])

        with pytest.raises(ValueError, match="no output"):
            generate_audio(mock_pipeline, "test", "af_heart")

    def test_single_chunk_no_concat(self) -> None:
        """Single chunk is written directly without concatenation."""
        fake_audio = np.arange(1000, dtype=np.float32)

        mock_pipeline = MagicMock()
        mock_pipeline.return_value = iter([
            ("text", "ps", fake_audio),
        ])

        wav_path, _ = generate_audio(mock_pipeline, "test", "af_heart")
        assert wav_path.exists()

        import soundfile as sf

        data, _ = sf.read(str(wav_path))
        assert len(data) == 1000
        wav_path.unlink()
