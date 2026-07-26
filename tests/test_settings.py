"""Tests for tts_studio.settings — persistence."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


class TestSettings:
    def test_get_defaults(self) -> None:
        from tts_studio.settings import DEFAULTS, get_engine_settings

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            pass
        try:
            with patch("tts_studio.settings.SETTINGS_FILE", Path(tmp.name)):
                s = get_engine_settings("kokoro")
                assert s == DEFAULTS["kokoro"]
                assert "speed" in s
        finally:
            Path(tmp.name).unlink(missing_ok=True)

    def test_set_and_get(self) -> None:
        from tts_studio.settings import get_engine_settings, set_engine_setting

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            pass
        try:
            with patch("tts_studio.settings.SETTINGS_FILE", Path(tmp.name)):
                set_engine_setting("kokoro", "speed", 1.5)
                s = get_engine_settings("kokoro")
                assert s["speed"] == 1.5
        finally:
            Path(tmp.name).unlink(missing_ok=True)

    def test_persists_across_loads(self) -> None:
        from tts_studio.settings import get_engine_settings, set_engine_setting

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            pass
        try:
            path = Path(tmp.name)
            with patch("tts_studio.settings.SETTINGS_FILE", path):
                set_engine_setting("chatterbox", "exaggeration", 0.8)
                # Re-read
                s = get_engine_settings("chatterbox")
                assert s["exaggeration"] == 0.8
        finally:
            Path(tmp.name).unlink(missing_ok=True)

    def test_corrupt_file_returns_defaults(self) -> None:
        from tts_studio.settings import DEFAULTS, get_engine_settings

        with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp:
            tmp.write("{not valid json")
        try:
            with patch("tts_studio.settings.SETTINGS_FILE", Path(tmp.name)):
                s = get_engine_settings("kokoro")
                assert s == DEFAULTS["kokoro"]
        finally:
            Path(tmp.name).unlink(missing_ok=True)
