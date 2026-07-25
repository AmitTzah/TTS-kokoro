"""Lightweight splash window shown before heavy imports complete.

The splash uses only tkinter (no torch, no models) so it can appear
within milliseconds of launch.  Once the heavy imports finish, the
caller destroys the splash label and repurposes the Tk root for the
full UI.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def create_splash() -> tuple[tk.Tk, ttk.Label]:
    """Create and display a splash window.

    Returns:
        ``(root, label)`` — the Tk root window and the splash label.
        The caller should do heavy imports, then call :func:`destroy_splash`
        and build the main UI into *root*.
    """
    root = tk.Tk()
    root.title("Kokoro TTS — Starting...")
    root.geometry("380x80")
    root.resizable(False, False)
    root.eval("tk::PlaceWindow . center")

    label = ttk.Label(
        root,
        text="Loading Kokoro TTS...\nPlease wait.",
        font=("Segoe UI", 10),
    )
    label.pack(expand=True, padx=20, pady=15)
    root.update()  # Force paint — user sees this instantly
    return root, label


def destroy_splash(root: tk.Tk, label: ttk.Label) -> None:
    """Remove the splash content and prepare the root for the main UI."""
    label.destroy()
    root.geometry("")  # Clear fixed geometry — let main UI size naturally
    root.resizable(True, True)
