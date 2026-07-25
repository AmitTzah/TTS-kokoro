"""Tkinter UI components."""

from tts_studio.ui.main_window import build_ui, set_models, set_voices
from tts_studio.ui.events import (
    set_generating,
    set_generation_done,
    set_loading,
    set_ready,
)

__all__ = [
    "build_ui",
    "set_models",
    "set_voices",
    "set_generating",
    "set_generation_done",
    "set_loading",
    "set_ready",
]
