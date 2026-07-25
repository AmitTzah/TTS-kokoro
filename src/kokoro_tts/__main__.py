"""Entry point — ``python -m kokoro_tts`` or ``kokoro-tts`` console script."""

from __future__ import annotations

import sys
import traceback


def main() -> None:
    """Launch the Kokoro TTS GUI."""
    try:
        _run()
    except Exception:
        # When launched via pythonw.exe (double-click), there's no console.
        # Show the error in a dialog so the user knows what happened.
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()  # Hide the empty root window
        messagebox.showerror(
            "Kokoro TTS — Startup Error",
            f"The application failed to start:\n\n{traceback.format_exc()}",
        )
        root.destroy()
        sys.exit(1)


def _run() -> None:
    # pythonw.exe (double-click) has no console — sys.stdout/stderr are None,
    # which crashes kokoro's loguru logger.  Redirect to a null device.
    if sys.stdout is None:
        sys.stdout = open("nul", "w")
    if sys.stderr is None:
        sys.stderr = open("nul", "w")

    from kokoro_tts.config import configure_espeak
    from kokoro_tts.splash import create_splash, destroy_splash

    # Step 1 — splash (only tkinter, near-instant)
    root, label = create_splash()

    # Step 2 — heavy imports while splash is visible
    configure_espeak()

    # Step 3 — build the full app, reusing the splash root
    from kokoro_tts.app import TTSApp  # noqa: E402

    destroy_splash(root, label)
    TTSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
