"""Thin wrapper — delegates to tts_studio package.

For new usage:  python -m tts_studio
Legacy:         python tts-gui.pyw
"""

import sys
from pathlib import Path

_src = Path(__file__).resolve().parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from tts_studio.__main__ import main

if __name__ == "__main__":
    main()
