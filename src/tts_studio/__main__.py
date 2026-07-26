"""Entry point — ``python -m tts_studio``."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

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

    _purge_stale_temp_files()

    root, label = create_splash()
    configure_espeak()

    root.update()

    # Defer the heavy import so the splash has time to render fully.
    # Without this, Windows marks the window "Not Responding" during
    # the 3-5 second import of torch/kokoro/chatterbox.
    def _build_ui():
        from tts_studio.app import TTSApp  # noqa: E402

        destroy_splash(root, label)
        TTSApp(root)

    root.after(100, _build_ui)
    root.mainloop()


_STALE_TEMP_AGE_SECONDS = 86400  # 1 day


def _purge_stale_temp_files() -> None:
    """Remove app-specific temp WAV files left behind by previous crashes."""
    import tempfile
    import time

    temp_dir = tempfile.gettempdir()
    now = time.time()

    for prefix in ("tts_gen_", "tts_speed_"):
        for entry in Path(temp_dir).glob(f"{prefix}*.wav"):
            try:
                if now - entry.stat().st_mtime > _STALE_TEMP_AGE_SECONDS:
                    entry.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    main()
