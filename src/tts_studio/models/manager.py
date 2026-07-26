"""Model management — list, download, delete models."""

from __future__ import annotations

from tts_studio.models.downloader import (
    delete_model,
    get_downloaded_models,
    is_downloaded,
)
from tts_studio.models.registry import AVAILABLE_MODELS, get_model

__all__ = [
    "AVAILABLE_MODELS",
    "get_model",
    "is_downloaded",
    "get_downloaded_models",
    "delete_model",
]
