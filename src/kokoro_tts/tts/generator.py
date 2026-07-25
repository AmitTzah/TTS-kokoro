"""Audio generation wrapper around the Kokoro pipeline."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import soundfile as sf
import torch

from kokoro_tts.config import SAMPLE_RATE

# Public re-export so callers don't need to know the internal name
__all__ = ["SAMPLE_RATE", "generate_audio"]


def generate_audio(
    model: torch.nn.Module,
    text: str,
    voicepack: dict[str, Any],
    lang: str,
) -> tuple[Path, str | None]:
    """Generate speech audio from text.

    Args:
        model: The loaded Kokoro TTS model.
        text: Input text to synthesize.
        voicepack: Voice tensor from :func:`kokoro_tts.voice.loader.load_voices`.
        lang: Phonemizer language code (``'a'`` or ``'b'``).

    Returns:
        ``(wav_path, phonemes)`` where *wav_path* is a temporary ``.wav`` file
        and *phonemes* is the phoneme string (or ``None`` if unavailable).

    Raises:
        ValueError: If *audio* is ``None`` (empty text after tokenization).
    """
    # Lazy import — kokoro.py initialises espeak at module level which
    # may not be available in test / CI environments
    from kokoro import generate as _generate  # type: ignore[import-untyped]

    audio, phonemes = _generate(model, text, voicepack, lang=lang)

    if audio is None:
        raise ValueError(
            "Audio generation produced no output — "
            "the text may be empty after processing."
        )

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, audio, SAMPLE_RATE)
        return Path(tmp.name), phonemes
