"""Thin wrapper — delegates to the refactored kokoro_tts package.

For new usage, prefer::

    python -m kokoro_tts

This file exists for backward compatibility with the old launch command::

    python tts-gui.pyw
"""

import sys
from pathlib import Path

# Add src/ to path so we can import kokoro_tts without pip install -e .
_src = Path(__file__).resolve().parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from kokoro_tts.__main__ import main

if __name__ == "__main__":
    main()
