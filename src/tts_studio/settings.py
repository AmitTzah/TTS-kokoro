"""Voice/engine settings persistence.

Stores per-engine settings for each voice in a JSON file.
"""

from __future__ import annotations

import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parent.parent.parent / "settings.json"

DEFAULTS: dict[str, dict[str, float]] = {
    "kokoro": {"speed": 1.0},
    "chatterbox": {
        "exaggeration": 0.5,
        "cfg_weight": 0.5,
        "temperature": 0.8,
        "repetition_penalty": 1.2,
    },
}


def _load() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except Exception:
            pass
    return {}


def _save(data: dict) -> None:
    SETTINGS_FILE.write_text(json.dumps(data, indent=2))


def get_engine_settings(engine_name: str) -> dict[str, float]:
    """Return settings dict for an engine, merged with defaults."""
    data = _load()
    defaults = DEFAULTS.get(engine_name, {})
    saved = data.get(engine_name, {})
    return {**defaults, **saved}


def set_engine_setting(engine_name: str, key: str, value: float) -> None:
    """Save a single setting for an engine."""
    data = _load()
    data.setdefault(engine_name, {})[key] = value
    _save(data)
