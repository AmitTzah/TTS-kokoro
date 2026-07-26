"""Entry point — ``python -m tts_studio``."""

from __future__ import annotations

import os
import sys
import traceback

# Set Windows app ID at module level — earliest possible.
if sys.platform == "win32":
    import ctypes

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "tts.studio.gui"
        )
    except Exception:
        pass


def main() -> None:
    try:
        _run()
    except Exception:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "TTS Studio — Startup Error",
            f"Failed to start:\n\n{traceback.format_exc()}",
        )
        root.destroy()
        sys.exit(1)


def _run() -> None:
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

    from tts_studio.config import configure_espeak
    from tts_studio.splash import create_splash, destroy_splash

    root, label = create_splash()
    configure_espeak()

    # Pump events one more time before the heavy import so Windows
    # doesn't mark the splash as "Not Responding"
    root.update()

    from tts_studio.app import TTSApp

    destroy_splash(root, label)
    TTSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
