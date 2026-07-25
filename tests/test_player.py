"""Tests for kokoro_tts.audio.player — AudioPlayer."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tts_studio.audio.player import AudioPlayer


class TestAudioPlayer:
    def test_init_succeeds(self) -> None:
        """AudioPlayer can be created with the default sample rate."""
        player = AudioPlayer(frequency=24000)
        assert player is not None

    def test_is_playing_returns_bool(self) -> None:
        """is_playing returns False when nothing is loaded."""
        player = AudioPlayer(frequency=24000)
        assert player.is_playing is False

    def test_unload_calls_stop_and_unload(self) -> None:
        """unload() calls both mixer.stop() and mixer.unload().

        Regression test: on Windows, mixer.stop() alone keeps the file
        handle open, causing WinError 32 when deleting the WAV on the
        next generation.  unload() must call both.
        """
        player = AudioPlayer(frequency=24000)
        with (
            patch("pygame.mixer.music.stop") as mock_stop,
            patch("pygame.mixer.music.unload") as mock_unload,
        ):
            player.unload()

        mock_stop.assert_called_once()
        mock_unload.assert_called_once()
