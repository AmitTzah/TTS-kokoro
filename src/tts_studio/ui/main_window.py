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
    on_settings: Callable[[], None],
    on_speed_change: Callable[[str], None],
) -> dict[str, tk.Widget | tk.StringVar]:
    """Build all widgets."""

    # ── Toolbar ──────────────────────────────────────────────
    toolbar = ttk.Frame(root)
    toolbar.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

    ttk.Button(
        toolbar, text="Manage Models", command=on_model_manager
    ).pack(side="left", padx=(0, 5))
    ttk.Button(
        toolbar, text="⚙ Settings", command=on_settings
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
    pause_var = tk.StringVar(value="0.75s")
    pause_combo = ttk.Combobox(
        options_frame,
        textvariable=pause_var,
        values=["0.15s", "0.35s", "0.5s", "0.75s", "1.0s", "1.5s", "2.0s", "3.0s", "5.0s"],
        state="readonly",
        width=7,
    )
    pause_combo.pack(side="left", padx=(2, 0))

    # Grey out pause when split is off
    def _on_split_change(*args):
        if split_var.get() == "off":
            pause_combo.config(state="disabled")
        else:
            pause_combo.config(state="readonly")

    split_var.trace_add("write", _on_split_change)

    generate_button = ttk.Button(root, text="Generate Audio", command=on_generate)
    generate_button.grid(row=5, column=0, padx=10, pady=(5, 2), sticky="ew")

    cancel_button = ttk.Button(root, text="Cancel", command=on_generate)  # callback patched later
    cancel_button.grid(row=6, column=0, padx=10, pady=(0, 5), sticky="ew")
    cancel_button.grid_remove()  # hidden until generation starts

    # ── Status Label ─────────────────────────────────────────
    status_label = ttk.Label(root, text="")
    status_label.grid(row=7, column=0, padx=10, pady=5, sticky="ew")

    # ── Audio Controls ───────────────────────────────────────
    audio_frame = ttk.LabelFrame(root, text="Generated Audio")
    audio_frame.grid(row=8, column=0, padx=10, pady=(5, 10), sticky="ew")
    audio_frame.columnconfigure(1, weight=1)

    from tts_studio.ui.seek_bar import SeekBar

    seek_bar = SeekBar(audio_frame)
    seek_bar.grid(row=0, column=0, columnspan=3, padx=10, pady=(8, 4), sticky="ew")

    # Transport cluster: Play / Pause / Speed grouped on the left
    controls = ttk.Frame(audio_frame)
    controls.grid(row=1, column=0, columnspan=2, padx=(10, 4), pady=(2, 10), sticky="w")

    play_button = ttk.Button(
        controls,
        text="▶ Play",
        command=on_play,
        state=tk.DISABLED,
        style="Accent.TButton",
    )
    play_button.pack(side="left")

    pause_resume_button = ttk.Button(
        controls, text="⏸ Pause", command=on_pause_resume, state=tk.DISABLED
    )
    pause_resume_button.pack(side="left", padx=(6, 0))

    ttk.Label(controls, text="Speed:").pack(side="left", padx=(14, 4))
    speed_var = tk.StringVar(value="1.0x")
    speed_combo = ttk.Combobox(
        controls,
        textvariable=speed_var,
        values=["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"],
        state="readonly",
        width=5,
    )
    speed_combo.pack(side="left")
    speed_combo.bind("<<ComboboxSelected>>", lambda _e: on_speed_change(speed_var.get()))

    save_button = ttk.Button(audio_frame, text="💾 Save", command=on_save, state=tk.DISABLED)
    save_button.grid(row=1, column=2, padx=(4, 10), pady=(2, 10), sticky="e")

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
        "cancel_button": cancel_button,
        "status_label": status_label,
        "seek_bar": seek_bar,
        "play_button": play_button,
        "pause_resume_button": pause_resume_button,
        "save_button": save_button,
        "speed_var": speed_var,
        "speed_combo": speed_combo,
        "split_combo": split_combo,
        "split_var": split_var,
        "pause_var": pause_var,
        "pause_combo": pause_combo,
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


def set_split_enabled(widgets: dict, enabled: bool) -> None:
    """Enable/disable the split dropdown. Show hover tooltip when disabled."""
    combo = widgets["split_combo"]
    if enabled:
        combo.config(state="readonly")
        _unbind_tooltip(combo)
    else:
        combo.config(state="disabled")
        _bind_tooltip(combo, "Kokoro splits text into paragraphs natively")


def _bind_tooltip(widget: tk.Widget, text: str) -> None:
    tw = None

    def _enter(_e):
        nonlocal tw
        if tw is not None:
            return
        tw = tk.Toplevel(widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{widget.winfo_rootx()}+{widget.winfo_rooty() + 25}")
        label = tk.Label(tw, text=text, background="#ffffe0", relief="solid", borderwidth=1, padx=4, pady=2)
        label.pack()

    def _leave(_e):
        nonlocal tw
        if tw is not None:
            tw.destroy()
            tw = None

    widget.bind("<Enter>", _enter, add="+")
    widget.bind("<Leave>", _leave, add="+")


def _unbind_tooltip(widget: tk.Widget) -> None:
    widget.unbind("<Enter>")
    widget.unbind("<Leave>")
