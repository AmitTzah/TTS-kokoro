"""Tkinter widget construction for the main window.

This module is purely declarative — it builds widgets and returns
references.  Voice list is populated dynamically after model load.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


def build_ui(
    root: tk.Tk,
    *,
    on_generate: Callable[[], None],
    on_play: Callable[[], None],
    on_pause_resume: Callable[[], None],
    on_save: Callable[[], None],
) -> dict[str, tk.Widget | tk.StringVar]:
    """Build all widgets and return references keyed by name.

    The voice dropdown starts empty — call :func:`set_voices` after
    the model is loaded to populate it.
    """
    # ── Voice Selection ───────────────────────────────────────
    voice_frame = ttk.LabelFrame(root, text="Voice Selection")
    voice_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

    voice_var = tk.StringVar(value="")
    voice_dropdown = ttk.Combobox(voice_frame, textvariable=voice_var, values=[])
    voice_dropdown.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    # ── Text Input ────────────────────────────────────────────
    text_frame = ttk.LabelFrame(root, text="Text Input")
    text_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    text_entry = tk.Text(text_frame, wrap=tk.WORD, height=10)
    text_entry.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

    # ── Generate Button ───────────────────────────────────────
    generate_button = ttk.Button(root, text="Generate Audio", command=on_generate)
    generate_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    # ── Status Label ──────────────────────────────────────────
    status_label = ttk.Label(root, text="")
    status_label.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

    # ── Audio Controls ────────────────────────────────────────
    audio_frame = ttk.LabelFrame(root, text="Generated Audio")
    audio_frame.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

    play_button = ttk.Button(audio_frame, text="Play", command=on_play, state=tk.DISABLED)
    play_button.grid(row=0, column=0, padx=5, pady=5)

    pause_resume_button = ttk.Button(
        audio_frame, text="Pause", command=on_pause_resume, state=tk.DISABLED
    )
    pause_resume_button.grid(row=0, column=1, padx=5, pady=5)

    save_button = ttk.Button(audio_frame, text="Save", command=on_save, state=tk.DISABLED)
    save_button.grid(row=0, column=2, padx=5, pady=5)

    # ── Progress Bar ──────────────────────────────────────────
    progress_bar = ttk.Progressbar(root, orient="horizontal", mode="indeterminate")

    # ── Grid Weights ──────────────────────────────────────────
    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)

    return {
        "voice_var": voice_var,
        "voice_dropdown": voice_dropdown,
        "text_entry": text_entry,
        "generate_button": generate_button,
        "status_label": status_label,
        "play_button": play_button,
        "pause_resume_button": pause_resume_button,
        "save_button": save_button,
        "progress_bar": progress_bar,
    }


def set_voices(widgets: dict, voices: list[str]) -> None:
    """Populate the voice dropdown with the given voice names."""
    widgets["voice_dropdown"]["values"] = voices
    if voices:
        # Default to af_heart (v1.0) or first available
        default = "af_heart" if "af_heart" in voices else voices[0]
        widgets["voice_var"].set(default)
