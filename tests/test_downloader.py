"""Tests for tts_studio.models.downloader — HF cache detection."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


class TestGetDownloadedModels:
    def test_multiple_models_exact_match(self) -> None:
        """Each cache dir should only match its exact hf_repo, not prefixes."""
        with tempfile.TemporaryDirectory() as tmp:
            hub = Path(tmp) / "huggingface" / "hub"
            hub.mkdir(parents=True)
            (hub / "models--hexgrad--Kokoro-82M").mkdir()
            (hub / "models--ResembleAI--chatterbox").mkdir()
            (hub / "models--ResembleAI--chatterbox-turbo").mkdir()

            with patch(
                "tts_studio.models.downloader.get_models_dir",
                return_value=Path(tmp),
            ):
                from tts_studio.models.downloader import get_downloaded_models

                dl = get_downloaded_models()

        assert "kokoro-v1.0-en" in dl
        assert "chatterbox-turbo" in dl
        assert "chatterbox-multilingual-v3" in dl

    def test_prefix_not_matched_as_exact(self) -> None:
        """chatterbox-turbo cache dir should NOT match chatterbox (multilingual) model."""
        with tempfile.TemporaryDirectory() as tmp:
            hub = Path(tmp) / "huggingface" / "hub"
            hub.mkdir(parents=True)
            (hub / "models--ResembleAI--chatterbox-turbo").mkdir()

            with patch(
                "tts_studio.models.downloader.get_models_dir",
                return_value=Path(tmp),
            ):
                from tts_studio.models.downloader import get_downloaded_models

                dl = get_downloaded_models()

        assert "chatterbox-turbo" in dl
        assert "chatterbox-multilingual-v3" not in dl

    def test_empty_when_no_models(self) -> None:
        """Empty list when no HF cache exists."""
        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "tts_studio.models.downloader.get_models_dir",
                return_value=Path(tmp),
            ):
                from tts_studio.models.downloader import get_downloaded_models

                dl = get_downloaded_models()

        assert dl == []


class TestIsDownloaded:
    def test_downloaded_when_cache_exists(self) -> None:
        """Returns True when HF cache dir matches exactly."""
        with tempfile.TemporaryDirectory() as tmp:
            hub = Path(tmp) / "huggingface" / "hub"
            hub.mkdir(parents=True)
            (hub / "models--hexgrad--Kokoro-82M").mkdir()

            with patch(
                "tts_studio.models.downloader.get_models_dir",
                return_value=Path(tmp),
            ):
                from tts_studio.models.downloader import is_downloaded

                assert is_downloaded("kokoro-v1.0-en") is True

    def test_not_downloaded_when_prefix_match(self) -> None:
        """chatterbox-turbo should NOT match chatterbox (multilingual)."""
        with tempfile.TemporaryDirectory() as tmp:
            hub = Path(tmp) / "huggingface" / "hub"
            hub.mkdir(parents=True)
            (hub / "models--ResembleAI--chatterbox-turbo").mkdir()

            with patch(
                "tts_studio.models.downloader.get_models_dir",
                return_value=Path(tmp),
            ):
                from tts_studio.models.downloader import is_downloaded

                assert is_downloaded("chatterbox-multilingual-v3") is False
                assert is_downloaded("chatterbox-turbo") is True

    def test_not_downloaded_when_no_cache(self) -> None:
        """Returns False when no matching cache dir."""
        with tempfile.TemporaryDirectory() as tmp:
            hub = Path(tmp) / "huggingface" / "hub"
            hub.mkdir(parents=True)

            with patch(
                "tts_studio.models.downloader.get_models_dir",
                return_value=Path(tmp),
            ):
                from tts_studio.models.downloader import is_downloaded

                assert is_downloaded("kokoro-v1.0-en") is False
