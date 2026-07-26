"""Central registry of all available TTS models across all providers."""

from __future__ import annotations

from tts_studio.engines.base import ModelInfo

AVAILABLE_MODELS: list[ModelInfo] = [
    # -- Kokoro -------------------------------------------------
    ModelInfo(
        id="kokoro-v1.0-en",
        name="Kokoro v1.0 (English)",
        provider="kokoro",
        languages=["en"],
        size_mb=350,
        description="54 English voices, 9 accent variants. Fast, lightweight.",
        hf_repo="hexgrad/Kokoro-82M",
    ),
    # -- Chatterbox ---------------------------------------------
    ModelInfo(
        id="chatterbox-turbo",
        name="Chatterbox Turbo (350M)",
        provider="chatterbox",
        languages=["en"],
        size_mb=700,
        description="Low-latency English. Voice cloning only (needs reference audio). Paralinguistic tags.",
        hf_repo="ResembleAI/chatterbox-turbo",
    ),
    ModelInfo(
        id="chatterbox-multilingual-v3",
        name="Chatterbox Multilingual V3 (500M)",
        provider="chatterbox",
        languages=["en", "fr", "de", "es", "it", "pt", "ja", "zh", "ar", "hi", "ko", "nl", "pl", "ru", "sv", "tr", "he", "da", "fi", "no", "ms", "sw", "el"],
        size_mb=1000,
        description="23+ languages. Voice cloning with improved speaker similarity.",
        hf_repo="ResembleAI/chatterbox",
    ),
]


def get_models_by_provider(provider: str) -> list[ModelInfo]:
    """Filter available models by provider name."""
    return [m for m in AVAILABLE_MODELS if m.provider == provider]


def get_model(model_id: str) -> ModelInfo | None:
    """Look up a model by its ID."""
    for m in AVAILABLE_MODELS:
        if m.id == model_id:
            return m
    return None
