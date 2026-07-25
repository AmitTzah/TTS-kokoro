"""Text splitting utilities — used by the controller to chunk long text."""

from __future__ import annotations

import re


def split_text(text: str, mode: str = "paragraphs") -> list[str]:
    """Split text by paragraphs, sentences, or not at all.

    Args:
        text: Input text to split.
        mode: ``"paragraphs"`` (split on newlines), ``"sentences"``
              (split on ``. ! ?``), or ``"off"`` (no splitting).

    Returns:
        List of text chunks.
    """
    if mode == "off":
        return [text]

    if mode == "sentences":
        return [
            s.strip()
            for s in re.split(r"(?<=[.!?])\s+", text.strip())
            if s.strip()
        ]

    # mode == "paragraphs"
    # Split on any number of newlines (1+).  Each block of text
    # separated by newlines is a paragraph.
    return [
        p.strip()
        for p in re.split(r"\n+", text.strip())
        if p.strip()
    ] or [text]
