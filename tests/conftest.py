"""Shared test configuration."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tts_studio.config import configure_espeak

configure_espeak()
