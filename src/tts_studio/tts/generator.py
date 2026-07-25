"""TTS generation via Kokoro v1.0 KPipeline.

Replaces the vendored v0.19 ``build_model()``/``generate()`` approach.
Audio chunks from the pipeline are concatenated and saved as a temp WAV.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from tts_studio.config import SAMPLE_RATE

__all__ = ["SAMPLE_RATE", "generate_audio"]


def generate_audio(
    pipeline,
    text: str,
    voice: str,
    speed: float = 1.0,
    split_pattern: str = r"\n+",
) -> tuple[Path, str | None]:
    """Generate speech audio from text using a Kokoro v1.0 pipeline.

    Args:
        pipeline: A :class:`kokoro.KPipeline` instance (already initialised
                  with the desired language code).
        text: Input text to synthesise.
        voice: Voice name (e.g. ``'af_heart'``).
        speed: Playback speed multiplier.
        split_pattern: Regex for chunk boundary detection.

    Returns:
        ``(wav_path, phonemes)`` where *wav_path* is a temporary ``.wav``
        file and *phonemes* is a concatenation of all chunk phonemes.

    Raises:
        ValueError: If the pipeline produces no audio output.
    """
    chunks: list[np.ndarray] = []
    all_phonemes: list[str] = []

    for _gs, ps, audio in pipeline(
        text, voice=voice, speed=speed, split_pattern=split_pattern
    ):
        if audio is None:
            continue
        chunks.append(audio)
        if ps:
            all_phonemes.append(ps)

    if not chunks:
        raise ValueError(
            "Audio generation produced no output — "
            "the text may be empty after processing."
        )

    combined = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, combined, SAMPLE_RATE)
        return Path(tmp.name), " | ".join(all_phonemes) if all_phonemes else None
