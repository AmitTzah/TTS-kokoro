"""Tests for tts_studio.text_utils — text splitting."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tts_studio.text_utils import split_text


class TestSplitText:
    def test_off_returns_whole(self) -> None:
        text = "Hello world. How are you?"
        assert split_text(text, "off") == [text]

    def test_sentences_splits_on_period(self) -> None:
        text = "Hello. How are you? I am fine!"
        chunks = split_text(text, "sentences")
        assert len(chunks) == 3
        assert "Hello." in chunks[0]

    def test_paragraphs_double_newline(self) -> None:
        text = "Para 1.\n\nPara 2."
        chunks = split_text(text, "paragraphs")
        assert len(chunks) == 2

    def test_paragraphs_single_newline(self) -> None:
        text = "Line 1.\nLine 2.\nLine 3."
        chunks = split_text(text, "paragraphs")
        assert len(chunks) == 3

    def test_paragraphs_mixed_newlines(self) -> None:
        # \n+ splits on any number of newlines, even mixed
        text = "Line 1.\nLine 2.\n\nLine 3."
        chunks = split_text(text, "paragraphs")
        assert len(chunks) == 3

    def test_single_paragraph_no_split(self) -> None:
        text = "Just one line."
        chunks = split_text(text, "paragraphs")
        assert chunks == ["Just one line."]

    def test_empty_text(self) -> None:
        assert split_text("", "paragraphs") == [""]
        # sentences on empty returns empty list (no sentences to split)
        assert split_text("", "sentences") == []
