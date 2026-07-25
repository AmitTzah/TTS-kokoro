"""Setup script — CLI convenience for first-time setup.

Installs dependencies and pre-downloads models.
The GUI handles this via the Model Manager, but this script
is useful for headless/CI or first-time CLI users.

Usage::

    python scripts/setup.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Add src/ to path
_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_SRC))

from tts_studio.config import configure_espeak


def _check_package(name: str, pip_name: str | None = None) -> bool:
    """Check if a Python package is installed; offer to install if not."""
    try:
        __import__(name)
        return True
    except ImportError:
        pip = pip_name or name
        print(f"  {name} not found.")
        answer = input(f"  Install {pip}? [Y/n]: ").strip().lower()
        if answer in ("", "y", "yes"):
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip])
            return True
        return False


def main() -> None:
    print("TTS Studio Setup\n" + "=" * 50)

    # 1. eSpeak
    print("\n[1/3] Configuring eSpeak-NG ...")
    configure_espeak()
    print("  OK.")

    # 2. Check packages
    print("\n[2/3] Checking dependencies ...")
    kokoro_ok = _check_package("kokoro")
    chatterbox_ok = _check_package("chatterbox", "chatterbox-tts")

    if not kokoro_ok and not chatterbox_ok:
        print("  No engines installed. Install at least one.")
        print("    pip install kokoro>=0.9.2")
        print("    pip install chatterbox-tts")
        return

    # 3. Pre-download models
    print("\n[3/3] Pre-downloading models ...")
    if kokoro_ok:
        print("  Downloading Kokoro v1.0 (this may take a few minutes)...")
        from kokoro import KPipeline
        KPipeline(lang_code="a")
        print("  Kokoro ready.")

    if chatterbox_ok:
        print("  Downloading Chatterbox Turbo...")
        from tts_studio.engines.chatterbox_engine import ChatterboxEngine
        engine = ChatterboxEngine()
        engine.load_model("chatterbox-turbo")
        print("  Chatterbox ready.")

    print("\n" + "=" * 50)
    print("Setup complete.  Launch with:  python -m tts_studio")


if __name__ == "__main__":
    main()
