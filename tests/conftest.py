"""Shared test configuration — runs before any test is collected."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Configure espeak (needed by kokoro library's G2P)
from kokoro_tts.config import configure_espeak

configure_espeak()
