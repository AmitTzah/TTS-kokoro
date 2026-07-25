"""UI state-management helpers.

Keeps widget manipulation logic separate from widget construction
so :mod:`kokoro_tts.ui.main_window` can stay purely declarative.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any


def set_loading(
    widgets: dict[str, Any],
    message: str = "Loading model...",
) -> None:
    """Show the indeterminate progress bar and status message."""
    _status(widgets, message)
    _progress_show(widgets)


def set_ready(
    widgets: dict[str, Any],
    message: str,
) -> None:
    """Hide the progress bar, show a ready message, enable Generate."""
    _progress_hide(widgets)
    _status(widgets, message)
    _button_state(widgets["generate_button"], tk.NORMAL)


def set_generating(widgets: dict[str, Any]) -> None:
    """Enter 'generating' state: disable Generate, show progress."""
    _button_state(widgets["generate_button"], tk.DISABLED)
    _status(widgets, "Generating audio...")
    _progress_show(widgets)


def set_generation_done(
    widgets: dict[str, Any],
    success: bool,
    message: str,
) -> None:
    """Return from 'generating' state.

    On success: enable playback controls.  On failure: keep them disabled.
    """
    _progress_hide(widgets)
    _status(widgets, message)
    _button_state(widgets["generate_button"], tk.NORMAL)

    if success:
        _button_state(widgets["play_button"], tk.NORMAL)
        _button_state(widgets["pause_resume_button"], tk.DISABLED)
        widgets["pause_resume_button"].config(text="Pause")
        _button_state(widgets["save_button"], tk.NORMAL)
    else:
        _button_state(widgets["play_button"], tk.DISABLED)
        _button_state(widgets["pause_resume_button"], tk.DISABLED)
        _button_state(widgets["save_button"], tk.DISABLED)


# ── internal helpers ──────────────────────────────────────────

def _status(w: dict[str, Any], text: str) -> None:
    w["status_label"].config(text=text)


def _progress_show(w: dict[str, Any]) -> None:
    w["progress_bar"].grid(row=5, column=0, padx=10, pady=5, sticky="ew")
    w["progress_bar"].start()


def _progress_hide(w: dict[str, Any]) -> None:
    w["progress_bar"].stop()
    w["progress_bar"].grid_forget()


def _button_state(btn: ttk.Button, state: str) -> None:
    btn.config(state=state)
