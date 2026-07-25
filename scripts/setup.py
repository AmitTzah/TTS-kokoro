"""Setup script — installs kokoro package and generates test audio.

The ``kokoro`` pip package auto-downloads model weights on first use.
This script also checks Hugging Face for newer releases.

Usage::

    python scripts/setup.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import requests

# Add src/ to path so we can import kokoro_tts
_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_SRC))

from kokoro_tts.config import configure_espeak

HF_MODEL_ID = "hexgrad/Kokoro-82M"
CURRENT_VERSION = "v1.0"


def _check_for_updates() -> None:
    """Query the Hugging Face API for the latest model SHA."""
    url = f"https://huggingface.co/api/models/{HF_MODEL_ID}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        print("  (could not check for model updates — offline?)")
        return

    latest_sha = data.get("sha", "")[:8]
    if latest_sha:
        print(f"  Model SHA: {latest_sha}")
        print(f"  Visit: https://huggingface.co/{HF_MODEL_ID}")


def _cleanup_vendor() -> None:
    """Offer to delete the old vendored Kokoro-82M/ directory."""
    vendor = Path(__file__).resolve().parent.parent / "Kokoro-82M"
    if not vendor.exists():
        return

    print(f"\n  Old vendored model found: {vendor}")
    print("  v1.0 uses the kokoro pip package — these files are obsolete.")
    answer = input("  Delete Kokoro-82M/ ? [y/N]: ").strip().lower()
    if answer == "y":
        import shutil

        shutil.rmtree(vendor)
        print("  Deleted.")


def main() -> None:
    """Run the setup."""
    print("Kokoro TTS v1.0 Setup\n" + "=" * 50)

    # 0. Check for updates + cleanup
    print("\n[0/4] Checking for updates ...")
    _check_for_updates()
    _cleanup_vendor()

    # 1. Configure eSpeak
    print("\n[1/4] Configuring eSpeak-NG ...")
    configure_espeak()
    print("  OK.")

    # 2. Ensure kokoro package is installed
    print("\n[2/4] Checking kokoro package ...")
    try:
        import kokoro  # noqa: F401
    except ImportError:
        print("  Installing kokoro...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "kokoro>=0.9.2"]
        )
    print(f"  OK (kokoro available)")

    # 3. First-run model download
    print("\n[3/4] Initialising model (first run downloads ~300MB) ...")
    from kokoro import KPipeline

    print("  This may take a few minutes on first run...")
    pipeline = KPipeline(lang_code="a")
    print(f"  Model loaded on: {pipeline.model.device if pipeline.model else 'cpu'}")

    # 4. Test generation
    print("\n[4/4] Testing audio generation ...")
    text = (
        "How could I know? It's an unanswerable question. "
        "Like asking an unborn child if they'll lead a good life. "
        "They haven't even been born."
    )

    from kokoro_tts.tts.generator import generate_audio

    wav_path, phonemes = generate_audio(pipeline, text, "af_heart")
    print(f"  Output : {wav_path}")
    if phonemes:
        safe = phonemes.encode("ascii", "replace").decode()
        print(f"  Phonemes: {safe}")

    print("\n" + "=" * 50)
    print("Setup complete!  Run the GUI with:  python -m kokoro_tts")


if __name__ == "__main__":
    main()
