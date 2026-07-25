"""WAV file save dialog."""

from __future__ import annotations

import shutil
from pathlib import Path
from tkinter import filedialog


def save_audio_dialog(source_path: Path | str, title: str = "Save Audio As") -> str | None:
    """Show a Save As dialog and copy the audio file to the chosen location.

    Args:
        source_path: Path to the temporary WAV file.
        title: Dialog title.

    Returns:
        The destination path if saved, or ``None`` if the user cancelled.
    """
    dest = filedialog.asksaveasfilename(
        defaultextension=".wav",
        filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
        title=title,
    )
    if not dest:
        return None

    shutil.copy2(str(source_path), dest)
    return dest
