"""Setup script — downloads model + voice files and generates a test audio.

Usage::

    python scripts/setup.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

# Add src/ to path so we can import kokoro_tts
_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_SRC))

from kokoro_tts.config import (
    ALL_VOICES,
    KOKORO_DIR,
    MODEL_PATH,
    VOICES_DIR,
    configure_espeak,
)
from kokoro_tts.model.loader import load_model
from kokoro_tts.tts.generator import generate_audio


def _download(url: str, dest: Path) -> None:
    """Download a file with progress reporting."""
    if dest.exists():
        print(f"  SKIP  {dest.name} (already exists)")
        return

    print(f"  DOWNLOAD  {dest.name}  ...", end=" ", flush=True)
    resp = requests.get(url, stream=True)
    resp.raise_for_status()

    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(1024):
            f.write(chunk)
    print("done.")


def main() -> None:
    """Run the setup: download files, load model, generate test audio."""
    print("Kokoro TTS Setup\n" + "=" * 50)

    # 1. Configure eSpeak
    print("\n[1/4] Configuring eSpeak-NG ...")
    configure_espeak()
    print("  OK.")

    # 2. Download model
    print("\n[2/4] Downloading model ...")
    _download(
        "https://huggingface.co/hexgrad/Kokoro-82M/resolve/2f0893c/kokoro-v0_19.pth",
        MODEL_PATH,
    )

    # 3. Download voices
    print("\n[3/4] Downloading voices ...")
    for name in ALL_VOICES:
        _download(
            f"https://huggingface.co/hexgrad/Kokoro-82M/resolve/2f0893c/voices/{name}.pt",
            VOICES_DIR / f"{name}.pt",
        )

    # 4. Test generation
    print("\n[4/4] Testing audio generation ...")
    import torch

    if not torch.cuda.is_available():
        print("  ⚠ WARNING: CUDA not available — using CPU (slow).")
        print("    To use your NVIDIA GPU, install the CUDA version of PyTorch:")
        print("    pip uninstall torch torchvision torchaudio -y")
        print("    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Device: {device}")

    model = load_model(device)
    voicepack = torch.load(
        str(VOICES_DIR / "af.pt"), map_location=device, weights_only=True
    )

    text = (
        "How could I know? It's an unanswerable question. "
        "Like asking an unborn child if they'll lead a good life. "
        "They haven't even been born."
    )
    wav_path, phonemes = generate_audio(model, text, voicepack, lang="a")
    print(f"  Output : {wav_path}")
    print(f"  Phonemes: {phonemes}")

    print("\n" + "=" * 50)
    print("Setup complete!  Run the GUI with:  python -m kokoro_tts")


if __name__ == "__main__":
    main()
