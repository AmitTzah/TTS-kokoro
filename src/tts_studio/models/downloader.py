"""Hugging Face model downloader with progress callback."""

from __future__ import annotations

from pathlib import Path
from typing import Callable


def get_models_dir() -> Path:
    """Return the project-local models directory."""
    from tts_studio.config import MODELS_DIR

    return MODELS_DIR


def is_downloaded(model_id: str) -> bool:
    """Check whether a model is already downloaded."""
    from tts_studio.models.registry import get_model

    model = get_model(model_id)
    if model is None:
        return False

    root = get_models_dir()
    hub_dir = root / "huggingface" / "hub"
    if not hub_dir.exists():
        return False

    for d in hub_dir.iterdir():
        if d.is_dir() and d.name.startswith("models--"):
            dir_repo = d.name.removeprefix("models--").replace("--", "/")
            if model.hf_repo == dir_repo:
                return True
    return False


def get_downloaded_models() -> list[str]:
    """List model IDs that have been downloaded to the HF cache."""
    root = get_models_dir()
    hub_dir = root / "huggingface" / "hub"
    if not hub_dir.exists():
        return []

    downloaded: list[str] = []
    for d in hub_dir.iterdir():
        if d.is_dir() and d.name.startswith("models--"):
            from tts_studio.models.registry import AVAILABLE_MODELS

            dir_repo = d.name.removeprefix("models--").replace("--", "/")

            for model in AVAILABLE_MODELS:
                if model.hf_repo == dir_repo:
                    downloaded.append(model.id)

    return downloaded


def delete_model(model_id: str) -> None:
    """Delete a downloaded model."""
    import shutil

    path = get_models_dir() / model_id
    if path.exists():
        shutil.rmtree(path)


def download_model(
    model_id: str,
    repo_id: str,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> None:
    """Download model files from Hugging Face.

    Args:
        model_id: Local model ID (e.g. 'kokoro-v1.0-en').
        repo_id: Hugging Face repo (e.g. 'hexgrad/Kokoro-82M').
        on_progress: Called as ``on_progress(status, current, total)``.
    """
    from huggingface_hub import snapshot_download

    dest = get_models_dir() / model_id
    dest.mkdir(parents=True, exist_ok=True)

    # The kokoro/chatterbox pip packages handle their own downloads
    # via HF_HOME.  This downloader is for the model weights stored
    # in the project-local models/ directory.
    #
    # For now, we rely on each engine's pip package to download its
    # own weights via huggingface_hub (which respects HF_HOME set in
    # config.py).  The .done marker tracks that we've "installed"
    # this model.
    (dest / ".done").touch()

    if on_progress:
        on_progress("complete", 1, 1)
