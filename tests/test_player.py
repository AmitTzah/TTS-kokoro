"""Tests for kokoro_tts.audio.player — AudioPlayer."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tts_studio.audio.player import AudioPlayer, time_stretch


class TestAudioPlayer:
    def test_init_succeeds(self) -> None:
        """AudioPlayer can be created with the default sample rate."""
        player = AudioPlayer(frequency=24000)
        assert player is not None

    def test_is_playing_returns_bool(self) -> None:
        """is_playing returns False when nothing is loaded."""
        player = AudioPlayer(frequency=24000)
        assert player.is_playing is False

    def test_position_includes_seek_offset(self) -> None:
        """position must report absolute time after seek().

        Regression test: pygame's music.get_pos() does NOT include the
        start offset passed to play(start=...). After a seek the position
        would snap back near 0, making the seek bar jump on the next poll.
        """
        player = AudioPlayer(frequency=24000)
        player._duration = 60.0
        with (
            patch("pygame.mixer.music.play"),
            patch("pygame.mixer.music.get_pos", return_value=2000),
        ):
            player.seek(30.0)
            assert player.position == 32.0

    def test_position_clamped_to_duration(self) -> None:
        """position never exceeds the loaded duration."""
        player = AudioPlayer(frequency=24000)
        player._duration = 10.0
        with patch("pygame.mixer.music.get_pos", return_value=15_000):
            assert player.position == 10.0

    def test_stop_resets_seek_offset(self) -> None:
        """stop() clears the offset so the next play starts at 0."""
        player = AudioPlayer(frequency=24000)
        with (
            patch("pygame.mixer.music.play"),
            patch("pygame.mixer.music.stop"),
            patch("pygame.mixer.music.get_pos", return_value=1000),
        ):
            player.seek(30.0)
            player.stop()
            assert player.position == 1.0

    def test_seek_scales_start_by_speed(self) -> None:
        """seek() converts original-timeline seconds to file position."""
        player = AudioPlayer(frequency=24000)
        player._duration = 60.0
        player.set_speed(2.0)
        with (
            patch("pygame.mixer.music.play") as mock_play,
            patch("pygame.mixer.music.get_pos", return_value=2000),
        ):
            player.seek(30.0)
            mock_play.assert_called_once_with(start=15.0)
            # 2 real seconds at 2x from position 30 → 34 on the original timeline
            assert player.position == 34.0

    def test_set_speed_clamped(self) -> None:
        player = AudioPlayer(frequency=24000)
        player.set_speed(10.0)
        assert player.speed == 4.0
        player.set_speed(0.1)
        assert player.speed == 0.25

    def test_time_stretch_length(self) -> None:
        """Stretched output length scales by ~1/speed (mono and stereo)."""
        rate = 24000
        mono = np.zeros(rate, dtype=np.float32)
        out_fast = time_stretch(mono, 2.0)
        out_slow = time_stretch(mono, 0.5)
        # Output length is normalized to exactly n/speed
        assert len(out_fast) == rate // 2
        assert len(out_slow) == rate * 2

        stereo = np.zeros((rate, 2), dtype=np.float32)
        out = time_stretch(stereo, 1.5)
        assert out.ndim == 2 and out.shape[1] == 2
        assert out.shape[0] == rate * 2 // 3

    def test_time_stretch_preserves_pitch(self) -> None:
        """Dominant frequency of a tone is unchanged after stretching.

        Regression test: the previous implementation used plain resampling,
        which shifted pitch with speed (chipmunk effect) and made the speed
        control unusable.
        """
        rate = 24000
        freq = 440.0
        t = np.arange(rate, dtype=np.float32) / rate
        tone = np.sin(2 * np.pi * freq * t).astype(np.float32)

        stretched = time_stretch(tone, 2.0)

        spectrum = np.abs(np.fft.rfft(stretched))
        peak_hz = np.argmax(spectrum) * rate / len(stretched)
        assert abs(peak_hz - freq) < 20.0

    def test_load_stretches_into_temp_when_speed_not_1(self) -> None:
        """load() writes a temp WAV and loads it when speed != 1x."""
        player = AudioPlayer(frequency=24000)
        player.set_speed(2.0)
        with (
            patch("pygame.mixer.music.unload"),
            patch("pygame.mixer.music.load") as mock_load,
            patch("soundfile.info") as mock_info,
            patch("soundfile.read", return_value=(np.zeros(24000, dtype=np.float32), 24000)),
            patch("soundfile.write") as mock_write,
        ):
            mock_info.return_value.duration = 1.0
            player.load("fake.wav")

        assert player._temp_wav is not None
        mock_write.assert_called_once()
        mock_load.assert_called_once_with(str(player._temp_wav))
        # Original-timeline duration is preserved
        assert player.duration == 1.0

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
