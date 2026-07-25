"""Tkinter UI components."""

from kokoro_tts.ui.main_window import build_ui
from kokoro_tts.ui.events import (
    set_generating,
    set_generation_done,
    set_loading,
    set_ready,
)

__all__ = [
    "build_ui",
    "set_generating",
    "set_generation_done",
    "set_loading",
    "set_ready",
]
