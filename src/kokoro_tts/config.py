"""Centralized configuration: paths, constants, and environment setup.

This is the single source of truth for all project-wide settings.
Both the GUI and the setup script import from here — no duplication.
"""

from __future__ import annotations

import os
from pathlib import Path

# ── Project root ──────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ── Model storage ─────────────────────────────────────────────────
# Store model weights in the project folder (gitignored models/)
# instead of the global ~/.cache/huggingface so the project is
# self-contained.  Only affects this process.
os.environ["HF_HOME"] = str(_PROJECT_ROOT / "models" / "huggingface")

# ── Window icon ───────────────────────────────────────────────────
ICON_PATH = _PROJECT_ROOT / "text-to-speech-icon.ico"

# ── eSpeak-NG ─────────────────────────────────────────────────────
ESPEAK_LIBRARY_PATH = r"C:\Program Files\eSpeak NG\libespeak-ng.dll"
ESPEAK_EXECUTABLE_PATH = r"C:\Program Files\eSpeak NG\espeak-ng.exe"


def configure_espeak() -> None:
    """Validate eSpeak-NG installation and set environment variables."""
    if not os.path.exists(ESPEAK_LIBRARY_PATH):
        raise FileNotFoundError(
            f"Could not find espeak library at {ESPEAK_LIBRARY_PATH}"
        )
    if not os.path.exists(ESPEAK_EXECUTABLE_PATH):
        raise FileNotFoundError(
            f"Could not find espeak executable at {ESPEAK_EXECUTABLE_PATH}"
        )
    os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = ESPEAK_LIBRARY_PATH
    os.environ["PHONEMIZER_ESPEAK_PATH"] = ESPEAK_EXECUTABLE_PATH


# ── Languages (v1.0) ──────────────────────────────────────────────
LANG_CODES: dict[str, str] = {
    "a": "American English",
    "b": "British English",
    "e": "Spanish",
    "f": "French",
    "h": "Hindi",
    "i": "Italian",
    "p": "Portuguese",
    "j": "Japanese",
    "z": "Mandarin Chinese",
}

# ── Audio ─────────────────────────────────────────────────────────
SAMPLE_RATE: int = 24000
