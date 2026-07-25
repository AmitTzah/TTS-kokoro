"""Voice pack loading with progress feedback and failure handling."""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable

import torch

from kokoro_tts.config import ALL_VOICES, VOICES_DIR


def load_voices(
    device: str,
    on_progress: Callable[[int, int], None] | None = None,
    on_error: Callable[[str, str], None] | None = None,
    root: tk.Tk | None = None,
) -> dict[str, Any]:
    """Load all voice packs and return a {name: tensor} dict.

    Args:
        device: ``'cuda'`` or ``'cpu'``.
        on_progress: Called as ``on_progress(loaded, total)`` after each
            **successfully** loaded voice.  Failed voices are not counted.
        on_error: Called as ``on_error(voice_name, error_message)`` for failures.
        root: If provided, ``root.update()`` is called between voices to keep
              the UI responsive.

    Returns:
        Dict mapping voice name to its loaded tensor.  Failed voices are
        silently omitted from the result (the caller receives ``on_error``).
    """
    voicepacks: dict[str, Any] = {}
    total = len(ALL_VOICES)
    loaded = 0

    for voice_name in ALL_VOICES:
        try:
            voice_path = VOICES_DIR / f"{voice_name}.pt"
            voicepacks[voice_name] = torch.load(
                str(voice_path), map_location=device, weights_only=True
            )
            loaded += 1
        except Exception as exc:
            if on_error:
                on_error(voice_name, str(exc))
            continue

        if on_progress:
            on_progress(loaded, total)
        if root is not None:
            root.update()

    return voicepacks
