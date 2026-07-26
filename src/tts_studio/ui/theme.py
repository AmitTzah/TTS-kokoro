"""Modern light theme for TTS Studio.

Shared color palette plus :func:`apply_theme`, which switches ttk to the
``clam`` base theme (fully styleable, unlike the native ``vista`` theme)
and configures a clean, modern light look.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# ── palette ──────────────────────────────────────────────────
BG = "#f4f5f7"           # window / frame background
SURFACE = "#ffffff"      # cards, entry fields
BORDER = "#d7dae0"       # subtle borders
TEXT = "#1f2430"         # primary text
TEXT_MUTED = "#6b7280"   # secondary text (time labels, hints)
ACCENT = "#3b82f6"       # primary action / progress fill
ACCENT_HOVER = "#2563eb" # hover / pressed accent
TRACK = "#dfe2e8"        # seek-bar empty track

_FONT = "Segoe UI"


def apply_theme(root: tk.Tk) -> None:
    """Apply the modern light theme to the whole application."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass  # fall back to whatever theme is available

    root.configure(bg=BG)

    # ── base ─────────────────────────────────────────────────
    style.configure(
        ".",
        background=BG,
        foreground=TEXT,
        fieldbackground=SURFACE,
        bordercolor=BORDER,
        lightcolor=SURFACE,
        darkcolor=BORDER,
        troughcolor=TRACK,
        font=(_FONT, 9),
    )
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure(
        "TLabelframe",
        background=BG,
        foreground=TEXT_MUTED,
        bordercolor=BORDER,
    )
    style.configure(
        "TLabelframe.Label",
        background=BG,
        foreground=TEXT_MUTED,
        font=(_FONT, 9, "bold"),
    )

    # ── buttons ──────────────────────────────────────────────
    style.configure(
        "TButton",
        background=SURFACE,
        foreground=TEXT,
        bordercolor=BORDER,
        padding=(10, 5),
    )
    style.map(
        "TButton",
        background=[("pressed", "#e8ebf0"), ("active", "#eef1f5")],
        bordercolor=[("focus", ACCENT)],
        foreground=[("disabled", TEXT_MUTED)],
    )
    style.configure(
        "Accent.TButton",
        background=ACCENT,
        foreground="#ffffff",
        bordercolor=ACCENT_HOVER,
        padding=(12, 5),
    )
    style.map(
        "Accent.TButton",
        background=[
            ("pressed", ACCENT_HOVER),
            ("active", ACCENT_HOVER),
            ("disabled", TRACK),
        ],
        bordercolor=[("disabled", BORDER)],
        foreground=[("disabled", TEXT_MUTED)],
    )

    # ── inputs ───────────────────────────────────────────────
    style.configure(
        "TCombobox",
        fieldbackground=SURFACE,
        background=SURFACE,
        foreground=TEXT,
        bordercolor=BORDER,
        arrowcolor=TEXT_MUTED,
        padding=(6, 3),
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", SURFACE)],
        bordercolor=[("focus", ACCENT)],
        foreground=[("disabled", TEXT_MUTED)],
    )
    style.configure(
        "TEntry",
        fieldbackground=SURFACE,
        bordercolor=BORDER,
        padding=(6, 3),
    )

    # ── progress bar ─────────────────────────────────────────
    style.configure(
        "TProgressbar",
        background=ACCENT,
        troughcolor=TRACK,
        bordercolor=BORDER,
    )

    # ── seek-bar time labels ─────────────────────────────────
    style.configure(
        "SeekTime.TLabel",
        background=BG,
        foreground=TEXT_MUTED,
        font=(_FONT, 8),
    )
