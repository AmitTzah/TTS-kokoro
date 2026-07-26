"""Pygame-based audio playback wrapper with seek and speed support.

Speed control uses WSOLA time stretching (via the lightweight, pure-python
``audiotsm`` package), so playback rate changes without shifting pitch or
adding the hollow artifacts of a phase vocoder.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import pygame
import soundfile as sf
from audiotsm import wsola
from audiotsm.io.array import ArrayReader, ArrayWriter


class AudioPlayer:
    """Manages playback of generated audio via pygame.mixer.

    Speed control is implemented by resampling the source WAV into a
    temporary file at load time (pygame has no native tempo control).
    Positions are always reported on the original audio timeline.
    """

    def __init__(self, frequency: int = 24000) -> None:
        self._frequency = frequency
        self._duration: float = 0.0
        # pygame's music.get_pos() does not include the start offset passed
        # to play(start=...), so track it ourselves to report absolute time.
        self._start_offset: float = 0.0
        self._speed: float = 1.0
        self._temp_wav: Path | None = None
        pygame.mixer.init(frequency=frequency)

    # ── playback control ──────────────────────────────────────

    def load(self, path: Path | str) -> None:
        """Load an audio file for playback (resampled if speed != 1x)."""
        pygame.mixer.music.unload()
        self._remove_temp()
        self._start_offset = 0.0
        # Read duration from the original WAV header (original timeline)
        try:
            self._duration = sf.info(str(path)).duration
        except Exception:
            self._duration = 0.0
        load_path = str(path)
        if self._speed != 1.0:
            try:
                load_path = self._write_stretched(str(path))
            except Exception:
                load_path = str(path)  # fall back to normal-speed playback
        pygame.mixer.music.load(load_path)

    def play(self, start: float = 0.0) -> None:
        """Start playback, optionally from a position in seconds."""
        pygame.mixer.music.play()
        if start > 0:
            pygame.mixer.music.set_pos(start / self._speed)
        self._start_offset = start

    def stop(self) -> None:
        """Stop playback."""
        pygame.mixer.music.stop()
        self._start_offset = 0.0

    def pause(self) -> None:
        """Pause playback (can be resumed with :meth:`unpause`)."""
        pygame.mixer.music.pause()

    def unpause(self) -> None:
        """Resume paused playback."""
        pygame.mixer.music.unpause()

    def seek(self, seconds: float) -> None:
        """Jump to a position in seconds (original timeline)."""
        pygame.mixer.music.play(start=seconds / self._speed)
        self._start_offset = seconds

    def unload(self) -> None:
        """Stop playback and release the audio file handle."""
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        self._remove_temp()
        self._duration = 0.0
        self._start_offset = 0.0

    # ── speed ─────────────────────────────────────────────────

    def set_speed(self, speed: float) -> None:
        """Set playback rate (applies on the next :meth:`load`)."""
        self._speed = max(0.25, min(float(speed), 4.0))

    @property
    def speed(self) -> float:
        return self._speed

    # ── state queries ─────────────────────────────────────────

    @property
    def is_playing(self) -> bool:
        """``True`` while audio is actively playing."""
        return pygame.mixer.music.get_busy()

    @property
    def position(self) -> float:
        """Current playback position in seconds (original timeline)."""
        pos = self._start_offset + pygame.mixer.music.get_pos() / 1000.0 * self._speed
        if self._duration > 0:
            pos = min(pos, self._duration)
        return max(0.0, pos)

    @property
    def duration(self) -> float:
        """Total duration in seconds (original timeline)."""
        return self._duration

    # ── internal ──────────────────────────────────────────────

    def _write_stretched(self, path: str) -> str:
        """Write a pitch-preserving stretched copy of *path* to a temp WAV."""
        data, rate = sf.read(path, dtype="float32")
        stretched = time_stretch(data, self._speed)
        fd, tmp = tempfile.mkstemp(prefix="tts_speed_", suffix=".wav")
        os.close(fd)
        sf.write(tmp, stretched, rate)
        self._temp_wav = Path(tmp)
        return tmp

    def _remove_temp(self) -> None:
        if self._temp_wav is not None:
            try:
                self._temp_wav.unlink()
            except OSError:
                pass
            self._temp_wav = None


def time_stretch(data: np.ndarray, speed: float) -> np.ndarray:
    """Change playback duration by 1/speed WITHOUT shifting pitch.

    WSOLA (Waveform Similarity Overlap-Add): a time-domain algorithm that
    preserves waveform shape, avoiding the hollow/phasy artifacts of
    frequency-domain phase vocoders. *speed* > 1 shortens (faster),
    < 1 lengthens (slower). Mono or (samples, channels) input.
    """
    channels = data.reshape(1, -1) if data.ndim == 1 else data.T
    n_channels, n_samples = channels.shape
    # WSOLA discards the trailing partial frame (up to frame_length +
    # tolerance samples); pad the input so no real content is lost, then
    # normalize the output to the exact target length.
    pad = 1536
    channels = np.ascontiguousarray(
        np.pad(channels, ((0, 0), (0, max(pad, 4096 - n_samples))))
    )

    reader = ArrayReader(channels)
    writer = ArrayWriter(n_channels)
    wsola(n_channels, speed=speed).run(reader, writer)
    out = writer.data

    target = int(round(n_samples / speed))
    if out.shape[1] >= target:
        out = out[:, :target]
    else:
        out = np.pad(out, ((0, 0), (0, target - out.shape[1])))

    result = out[0] if data.ndim == 1 else out.T
    return np.ascontiguousarray(result, dtype=np.float32)
