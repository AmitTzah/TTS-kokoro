"""Tests for kokoro_tts.voice.loader — voice pack loading."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kokoro_tts.voice.loader import load_voices


class TestLoadVoices:
    def test_loads_all_voices_when_no_errors(self) -> None:
        """All 11 voices are loaded successfully."""
        with patch("kokoro_tts.voice.loader.torch.load", return_value={"mock": True}):
            voicepacks = load_voices("cpu")

        from kokoro_tts.voice import ALL_VOICES

        assert len(voicepacks) == len(ALL_VOICES)
        for name in ALL_VOICES:
            assert name in voicepacks

    def test_failed_voice_is_omitted(self) -> None:
        """A voice that fails to load is silently excluded."""
        call_count = [0]
        failed_on = 3  # Fail on the 4th voice

        def failing_load(path, **kwargs):
            call_count[0] += 1
            if call_count[0] == failed_on:
                raise FileNotFoundError("missing.pt")
            return {"mock": True}

        errors: list[tuple[str, str]] = []

        with patch("kokoro_tts.voice.loader.torch.load", side_effect=failing_load):
            voicepacks = load_voices(
                "cpu",
                on_error=lambda name, msg: errors.append((name, msg)),
            )

        from kokoro_tts.voice import ALL_VOICES

        assert len(voicepacks) == len(ALL_VOICES) - 1
        assert len(errors) == 1
        assert errors[0][0] == ALL_VOICES[failed_on - 1]
        assert errors[0][1] == "missing.pt"

    def test_on_progress_called_for_each_success(self) -> None:
        """on_progress fires with (current, total) after each successful load."""
        progress: list[tuple[int, int]] = []

        with patch("kokoro_tts.voice.loader.torch.load", return_value={"mock": True}):
            load_voices("cpu", on_progress=lambda c, t: progress.append((c, t)))

        from kokoro_tts.voice import ALL_VOICES

        assert len(progress) == len(ALL_VOICES)
        assert progress[-1] == (len(ALL_VOICES), len(ALL_VOICES))
