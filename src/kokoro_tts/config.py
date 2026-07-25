"""Centralized configuration: paths, constants, and environment setup.

This is the single source of truth for all project-wide settings.
Both the GUI and the setup script import from here — no duplication.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ── Project root ──────────────────────────────────────────────────
# config.py lives at: src/kokoro_tts/config.py
# Project root is 3 levels up
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

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


# ── Kokoro-82M model paths ────────────────────────────────────────
KOKORO_DIR = _PROJECT_ROOT / "Kokoro-82M"
MODEL_PATH = KOKORO_DIR / "kokoro-v0_19.pth"
VOICES_DIR = KOKORO_DIR / "voices"

# Add Kokoro-82M to Python path so we can import models / kokoro
sys.path.insert(0, str(KOKORO_DIR))

# ── Voices ────────────────────────────────────────────────────────
VOICE_CATEGORIES: dict[str, list[str]] = {
    "American Female": ["af", "af_bella", "af_nicole", "af_sarah", "af_sky"],
    "American Male": ["am_adam", "am_michael"],
    "British Female": ["bf_emma", "bf_isabella"],
    "British Male": ["bm_george", "bm_lewis"],
}

ALL_VOICES: list[str] = [
    voice for voices in VOICE_CATEGORIES.values() for voice in voices
]

# First character of voice name → phonemizer language code
VOICE_LANG: dict[str, str] = {"a": "a", "b": "b"}  # American English, British English

# ── Audio ─────────────────────────────────────────────────────────
SAMPLE_RATE: int = 24000
