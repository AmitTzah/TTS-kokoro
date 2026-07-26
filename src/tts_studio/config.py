"""Centralized configuration for TTS Studio."""

from __future__ import annotations

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Model storage — project-local, gitignored
MODELS_DIR = _PROJECT_ROOT / "models"
os.environ["HF_HOME"] = str(MODELS_DIR / "huggingface")

# Window icon
ICON_PATH = _PROJECT_ROOT / "text-to-speech-icon.ico"

# eSpeak (needed by kokoro)
import sys as _sys

if _sys.platform == "win32":
    ESPEAK_LIBRARY_PATH = r"C:\Program Files\eSpeak NG\libespeak-ng.dll"
    ESPEAK_EXECUTABLE_PATH = r"C:\Program Files\eSpeak NG\espeak-ng.exe"
else:
    ESPEAK_LIBRARY_PATH = "libespeak-ng.so"
    ESPEAK_EXECUTABLE_PATH = "espeak-ng"


def configure_espeak() -> None:
    if not os.path.exists(ESPEAK_LIBRARY_PATH):
        raise FileNotFoundError(f"espeak library not found: {ESPEAK_LIBRARY_PATH}")
    if not os.path.exists(ESPEAK_EXECUTABLE_PATH):
        raise FileNotFoundError(f"espeak executable not found: {ESPEAK_EXECUTABLE_PATH}")
    os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = ESPEAK_LIBRARY_PATH
    os.environ["PHONEMIZER_ESPEAK_PATH"] = ESPEAK_EXECUTABLE_PATH


SAMPLE_RATE: int = 24000
