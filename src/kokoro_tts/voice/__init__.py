"""Voice management (v1.0).

Voices are lazy-loaded by :class:`kokoro.KPipeline` — no manual
``torch.load()`` needed.  See :func:`kokoro_tts.ui.main_window.set_voices`
for populating the dropdown.
"""

from kokoro_tts.config import LANG_CODES

__all__ = ["LANG_CODES"]
