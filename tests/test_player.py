"""Tests for kokoro_tts.audio.player — AudioPlayer."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kokoro_tts.audio.player import AudioPlayer


class TestAudioPlayer:
    def test_init_succeeds(self) -> None:
        """AudioPlayer can be created with the default sample rate."""
        player = AudioPlayer(frequency=24000)
        assert player is not None

    def test_is_playing_returns_bool(self) -> None:
        """is_playing returns False when nothing is loaded."""
        player = AudioPlayer(frequency=24000)
        assert player.is_playing is False
