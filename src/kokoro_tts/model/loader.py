"""Model loading wrapper."""

from __future__ import annotations

import torch

from kokoro_tts.config import MODEL_PATH

# These are imported from the vendored Kokoro-82M directory (added to
# sys.path by config.py).
from models import build_model as _build_model  # type: ignore[import-untyped]


def load_model(device: str) -> torch.nn.Module:
    """Load the Kokoro-82M TTS model.

    Args:
        device: ``'cuda'`` or ``'cpu'``.

    Returns:
        The loaded model on the specified device.

    Raises:
        FileNotFoundError: If the model file doesn't exist.
        RuntimeError: If the model fails to load.
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    return _build_model(str(MODEL_PATH), device)
