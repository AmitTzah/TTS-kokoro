"""Entry point — ``python -m kokoro_tts`` or ``kokoro-tts`` console script."""

from __future__ import annotations

from kokoro_tts.config import configure_espeak
from kokoro_tts.splash import create_splash, destroy_splash


def main() -> None:
    """Launch the Kokoro TTS GUI.

    1. Show a splash window immediately (before heavy imports).
    2. Import heavy modules while the splash is visible.
    3. Destroy the splash label and build the full UI into the same root.
    """
    # Step 1 — splash (only tkinter, near-instant)
    root, label = create_splash()

    # Step 2 — heavy work while splash is visible
    configure_espeak()

    # Step 3 — build the full app, reusing the splash root
    # Import here so the heavy imports inside app.py only run now,
    # while the splash is still visible
    from kokoro_tts.app import TTSApp  # noqa: E402

    destroy_splash(root, label)
    TTSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
