"""Pygame-based audio playback wrapper."""

from __future__ import annotations

from pathlib import Path

import pygame


class AudioPlayer:
    """Manages playback of generated audio via pygame.mixer.

    Usage::

        player = AudioPlayer()
        player.load(wav_path)
        player.play()
        player.pause()
        player.stop()
    """

    def __init__(self, frequency: int = 24000) -> None:
        """Initialise the pygame mixer.

        Args:
            frequency: Sample rate in Hz (must match the audio file).
        """
        self._frequency = frequency
        pygame.mixer.init(frequency=frequency)

    # ── playback control ──────────────────────────────────────

    def load(self, path: Path | str) -> None:
        """Load an audio file for playback."""
        pygame.mixer.music.load(str(path))

    def play(self) -> None:
        """Start (or restart) playback."""
        pygame.mixer.music.play()

    def stop(self) -> None:
        """Stop playback."""
        pygame.mixer.music.stop()

    def pause(self) -> None:
        """Pause playback (can be resumed with :meth:`unpause`)."""
        pygame.mixer.music.pause()

    def unpause(self) -> None:
        """Resume paused playback."""
        pygame.mixer.music.unpause()

    # ── state queries ─────────────────────────────────────────

    @property
    def is_playing(self) -> bool:
        """``True`` while audio is actively playing."""
        return pygame.mixer.music.get_busy()

