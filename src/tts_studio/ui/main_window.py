"""Tkinter widget construction for the main window."""

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
    on_provider_change: Callable[[str], None],
    on_model_change: Callable[[str], None],
    on_model_manager: Callable[[], None],
    on_clone_voice: Callable[[], None],
    on_delete_voice: Callable[[], None],
) -> dict[str, tk.Widget | tk.StringVar]:
    """Build all widgets."""

    # ── Toolbar ──────────────────────────────────────────────
    toolbar = ttk.Frame(root)
    toolbar.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

    ttk.Button(
        toolbar, text="Manage Models", command=on_model_manager
    ).pack(side="left")

    # ── Provider + Model selection ───────────────────────────
    config_frame = ttk.LabelFrame(root, text="Engine")
    config_frame.grid(row=1, column=0, padx=10, pady=(10, 5), sticky="ew")

    ttk.Label(config_frame, text="Provider:").grid(row=0, column=0, padx=(5, 2), pady=5, sticky="w")
    provider_var = tk.StringVar(value="kokoro")
    provider_dropdown = ttk.Combobox(
        config_frame,
        textvariable=provider_var,
        values=["kokoro", "chatterbox"],
        state="readonly",
        width=15,
    )
    provider_dropdown.grid(row=0, column=1, padx=2, pady=5, sticky="w")
    provider_dropdown.bind("<<ComboboxSelected>>", lambda e: on_provider_change(provider_var.get()))

    ttk.Label(config_frame, text="Model:").grid(row=0, column=2, padx=(15, 2), pady=5, sticky="w")
    model_var = tk.StringVar(value="")
    model_dropdown = ttk.Combobox(
        config_frame,
        textvariable=model_var,
        values=[],
        state="readonly",
        width=35,
    )
    model_dropdown.grid(row=0, column=3, padx=2, pady=5, sticky="w")
    model_dropdown.bind("<<ComboboxSelected>>", lambda e: on_model_change(model_var.get()))

    # ── Voice Selection ──────────────────────────────────────
    voice_frame = ttk.LabelFrame(root, text="Voice Selection")
    voice_frame.grid(row=2, column=0, padx=10, pady=(5, 5), sticky="ew")

    voice_var = tk.StringVar(value="")
    voice_dropdown = ttk.Combobox(
        voice_frame, textvariable=voice_var, values=[], state="readonly"
    )
    voice_dropdown.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    clone_btn = ttk.Button(voice_frame, text="＋", width=3, command=on_clone_voice)
    clone_btn.grid(row=0, column=1, padx=(2, 2), pady=5)

    delete_btn = ttk.Button(voice_frame, text="✕", width=3, command=on_delete_voice)
    delete_btn.grid(row=0, column=2, padx=(0, 5), pady=5)

    voice_frame.columnconfigure(0, weight=1)

    # ── Text Input ───────────────────────────────────────────
    text_frame = ttk.LabelFrame(root, text="Text Input")
    text_frame.grid(row=3, column=0, padx=10, pady=(5, 5), sticky="nsew")

    text_entry = tk.Text(text_frame, wrap=tk.WORD, height=10)
    text_entry.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    text_frame.columnconfigure(0, weight=1)
    text_frame.rowconfigure(0, weight=1)

    # ── Options + Generate ───────────────────────────────────
    options_frame = ttk.Frame(root)
    options_frame.grid(row=4, column=0, padx=10, pady=(5, 0), sticky="ew")

    ttk.Label(options_frame, text="Split:").pack(side="left")
    split_var = tk.StringVar(value="paragraphs")
    split_combo = ttk.Combobox(
        options_frame,
        textvariable=split_var,
        values=["paragraphs", "sentences", "off"],
        state="readonly",
        width=12,
    )
    split_combo.pack(side="left", padx=(2, 10))

    ttk.Label(options_frame, text="Pause:").pack(side="left")
    pause_var = tk.StringVar(value="0.75")
    pause_combo = ttk.Combobox(
        options_frame,
        textvariable=pause_var,
        values=["0.15", "0.35", "0.5", "0.75", "1.0", "1.5", "2.0", "3.0", "5.0"],
        state="readonly",
        width=5,
    )
    pause_combo.pack(side="left", padx=(2, 0))
    pause_label = ttk.Label(options_frame, text="s")
    pause_label.pack(side="left")

    # Grey out pause when split is off
    def _on_split_change(*args):
        if split_var.get() == "off":
            pause_combo.config(state="disabled")
        else:
            pause_combo.config(state="readonly")

    split_var.trace_add("write", _on_split_change)

    generate_button = ttk.Button(root, text="Generate Audio", command=on_generate)
    generate_button.grid(row=5, column=0, padx=10, pady=(5, 5), sticky="ew")

    # ── Status Label ─────────────────────────────────────────
    status_label = ttk.Label(root, text="")
    status_label.grid(row=6, column=0, padx=10, pady=5, sticky="ew")

    # ── Audio Controls ───────────────────────────────────────
    audio_frame = ttk.LabelFrame(root, text="Generated Audio")
    audio_frame.grid(row=7, column=0, padx=10, pady=(5, 10), sticky="ew")

    play_button = ttk.Button(audio_frame, text="Play", command=on_play, state=tk.DISABLED)
    play_button.grid(row=0, column=0, padx=5, pady=5)

    pause_resume_button = ttk.Button(
        audio_frame, text="Pause", command=on_pause_resume, state=tk.DISABLED
    )
    pause_resume_button.grid(row=0, column=1, padx=5, pady=5)

    save_button = ttk.Button(audio_frame, text="Save", command=on_save, state=tk.DISABLED)
    save_button.grid(row=0, column=2, padx=5, pady=5)

    # ── Progress Bar ─────────────────────────────────────────
    progress_bar = ttk.Progressbar(root, orient="horizontal", mode="indeterminate")

    # ── Grid Weights ─────────────────────────────────────────
    root.columnconfigure(0, weight=1)
    root.rowconfigure(3, weight=1)

    return {
        "provider_var": provider_var,
        "provider_dropdown": provider_dropdown,
        "model_var": model_var,
        "model_dropdown": model_dropdown,
        "voice_var": voice_var,
        "voice_dropdown": voice_dropdown,
        "clone_btn": clone_btn,
        "delete_btn": delete_btn,
        "text_entry": text_entry,
        "generate_button": generate_button,
        "status_label": status_label,
        "play_button": play_button,
        "pause_resume_button": pause_resume_button,
        "save_button": save_button,
        "split_var": split_var,
        "pause_var": pause_var,
        "progress_bar": progress_bar,
    }


def set_voices(widgets: dict, voices: list[str]) -> None:
    widgets["voice_dropdown"]["values"] = voices
    if voices:
        widgets["voice_var"].set(voices[0])


def set_models(widgets: dict, models: list[str]) -> None:
    widgets["model_dropdown"]["values"] = models
    if models:
        widgets["model_var"].set(models[0])
