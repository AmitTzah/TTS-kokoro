"""Abstract base class for TTS engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ModelInfo:
    """Metadata for an available TTS model."""

    id: str
    name: str
    provider: str  # "kokoro" | "chatterbox"
    languages: list[str] = field(default_factory=list)
    size_mb: int = 0
    description: str = ""
    hf_repo: str = ""
    hf_files: list[str] = field(default_factory=list)


@dataclass
class VoiceInfo:
    """Metadata for an available voice."""

    id: str
    name: str
    language: str = ""
    is_custom: bool = False  # True for user-cloned voices (deletable)
    reference_path: str = ""  # Path to reference audio for custom voices


class TTSEngine(ABC):
    """Abstract TTS engine.

    Each provider (Kokoro, Chatterbox, ...) implements this interface.
    """

    @abstractmethod
    def list_models(self) -> list[ModelInfo]:
        """Return all models available from this provider."""
        ...

    @abstractmethod
    def load_model(self, model_id: str) -> None:
        """Load a model into memory."""
        ...

    @abstractmethod
    def list_voices(self) -> list[VoiceInfo]:
        """List voices available for the currently loaded model."""
        ...

    @abstractmethod
    def generate(
        self, text: str, voice_id: str, **kwargs: Any
    ) -> tuple[Path, str | None]:
        """Generate audio. Returns (wav_path, phonemes)."""
        ...

    @abstractmethod
    def unload(self) -> None:
        """Release model resources."""
        ...

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """Whether a model is currently loaded."""
        ...

    @property
    @abstractmethod
    def device(self) -> str:
        """Device string (e.g. 'cuda', 'cpu')."""
        ...

    @property
    def supports_cloning(self) -> bool:
        """Whether this engine supports voice cloning from reference audio."""
        return False

    def add_voice(self, name: str, reference_path: str) -> VoiceInfo:
        """Add a custom voice from a reference audio clip.

        Raises NotImplementedError if the engine doesn't support cloning.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support voice cloning")

    def delete_voice(self, voice_id: str) -> None:
        """Delete a previously added custom voice.

        Raises NotImplementedError if the engine doesn't support cloning.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support voice cloning")
