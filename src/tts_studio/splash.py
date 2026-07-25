"""Lightweight splash window shown before heavy imports complete.

The splash uses only tkinter (no torch, no models) so it can appear
within milliseconds of launch.  Once the heavy imports finish, the
caller destroys the splash label and repurposes the Tk root for the
full UI.
"""

from __future__ import annotations

import ctypes
import tkinter as tk
from tkinter import ttk


def _set_app_id() -> None:
    """Give the app its own Windows taskbar identity (not Python's icon)."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "kokoro.tts.gui"
        )
    except Exception:
        pass  # Non-Windows or API unavailable — not critical


def create_splash() -> tuple[tk.Tk, ttk.Label]:
    """Create and display a splash window.

    Returns:
        ``(root, label)`` — the Tk root window and the splash label.
        The caller should do heavy imports, then call :func:`destroy_splash`
        and build the main UI into *root*.
    """
    _set_app_id()
    root = tk.Tk()

    # Set icon BEFORE any window manager calls (eval, update) so the
    # taskbar picks up our icon, not the Python default.
    from tts_studio.config import ICON_PATH

    if ICON_PATH.exists():
        # iconbitmap sets the title-bar icon (.ico works here)
        root.iconbitmap(str(ICON_PATH))
        # iconphoto sets the taskbar icon (.ico not supported — use Pillow)
        try:
            from PIL import Image, ImageTk

            img = Image.open(ICON_PATH)
            photo = ImageTk.PhotoImage(img)
            root.iconphoto(True, photo)
            root._icon_photo = photo  # Keep reference
        except Exception:
            pass  # Pillow not available — title bar icon still works

    root.title("TTS Studio — Starting...")
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
