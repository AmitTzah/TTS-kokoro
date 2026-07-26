"""Seek bar widget — canvas slider + time labels for audio playback."""

from __future__ import annotations

import time
import tkinter as tk
from tkinter import ttk

from tts_studio.ui.theme import ACCENT, ACCENT_HOVER, BG, BORDER, SURFACE, TEXT, TRACK

_TICK_MS = 33  # ~30fps glide between position polls


class SeekBar(ttk.Frame):
    """Playback position slider with time labels.

    A custom canvas-drawn slider: rounded track, accent-filled progress,
    circular thumb, and a VLC-style time bubble while dragging. Dragging
    is handled entirely inside the widget (no shared variable with the
    polling loop). Between polls the thumb glides smoothly by
    extrapolating from the last known position while playing.

    Usage::

        bar = SeekBar(parent)
        bar.set_duration(30.5)
        bar.set_playing(True)
        bar.set_position(12.3)        # update from polling
        bar.on_seek = lambda sec: ...  # user dragged to new position
    """

    _CANVAS_H = 34
    _TRACK_CY = 23
    _TRACK_H = 6
    _THUMB_R = 7
    _THUMB_R_ACTIVE = 8

    def __init__(self, parent: tk.Widget):
        super().__init__(parent)
        self._duration = 0.0
        self._position = 0.0
        self._dragging = False
        self._hover = False
        self._playing = False
        self._anchor_pos = 0.0
        self._anchor_time = time.monotonic()
        self.on_seek = None  # set by owner: callback(seconds)

        self._build()
        self.after(_TICK_MS, self._tick)

    def _build(self) -> None:
        self._canvas = tk.Canvas(
            self,
            height=self._CANVAS_H,
            bg=BG,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 1))

        self._current_label = ttk.Label(self, text="0:00", style="SeekTime.TLabel")
        self._current_label.grid(row=1, column=0, sticky="w")

        self._total_label = ttk.Label(self, text="0:00", style="SeekTime.TLabel")
        self._total_label.grid(row=1, column=1, sticky="e")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self._canvas.bind("<Button-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._canvas.bind("<Enter>", self._on_enter)
        self._canvas.bind("<Leave>", self._on_leave)
        self._canvas.bind("<Configure>", lambda _e: self._redraw())

    # ── public API ────────────────────────────────────────────

    def set_duration(self, seconds: float) -> None:
        self._duration = max(0.0, seconds)
        self._total_label.config(text=_fmt(self._duration))
        self._redraw()

    def set_position(self, seconds: float) -> None:
        """Update slider from playback polling (ignored during drag)."""
        if self._dragging:
            return
        self._anchor(seconds)

    def set_playing(self, playing: bool) -> None:
        """Tell the widget whether audio is advancing (enables glide)."""
        self._playing = playing
        self._anchor_pos = self._position
        self._anchor_time = time.monotonic()

    def reset(self) -> None:
        self._duration = 0.0
        self._position = 0.0
        self._dragging = False
        self._playing = False
        self._current_label.config(text="0:00")
        self._total_label.config(text="0:00")
        self._redraw()

    # ── interaction ───────────────────────────────────────────

    def _on_press(self, event: tk.Event) -> None:
        if self._duration <= 0:
            return
        self._dragging = True
        self._set_display(self._x_to_seconds(event.x))

    def _on_drag(self, event: tk.Event) -> None:
        if not self._dragging:
            return
        self._set_display(self._x_to_seconds(event.x))

    def _on_release(self, event: tk.Event) -> None:
        if not self._dragging:
            return
        self._dragging = False
        if self._duration <= 0:
            return
        seconds = self._x_to_seconds(event.x)
        self._anchor(seconds)
        if self.on_seek is not None:
            self.on_seek(seconds)

    def _on_enter(self, _event: tk.Event) -> None:
        self._hover = True
        self._redraw()

    def _on_leave(self, _event: tk.Event) -> None:
        self._hover = False
        self._redraw()

    # ── position state ────────────────────────────────────────

    def _clamp(self, seconds: float) -> float:
        if self._duration <= 0:
            return 0.0
        return max(0.0, min(seconds, self._duration))

    def _anchor(self, seconds: float) -> None:
        """Set a known-good position the glide extrapolates from."""
        seconds = self._clamp(seconds)
        self._position = seconds
        self._anchor_pos = seconds
        self._anchor_time = time.monotonic()
        self._current_label.config(text=_fmt(seconds))
        self._redraw()

    def _set_display(self, seconds: float) -> None:
        """Update the displayed position during a drag (no re-anchoring)."""
        self._position = self._clamp(seconds)
        self._current_label.config(text=_fmt(self._position))
        self._redraw()

    def _tick(self) -> None:
        """Glide the thumb between polls while playing."""
        if self._playing and not self._dragging and self._duration > 0:
            shown = min(
                self._anchor_pos + (time.monotonic() - self._anchor_time),
                self._duration,
            )
            if abs(shown - self._position) > 0.004:
                self._position = shown
                self._current_label.config(text=_fmt(shown))
                self._redraw()
        self.after(_TICK_MS, self._tick)

    # ── drawing ───────────────────────────────────────────────

    def _track_bounds(self) -> tuple[float, float]:
        """Left/right x-coords of the draggable track region."""
        pad = self._THUMB_R_ACTIVE + 2
        width = self._canvas.winfo_width()
        return pad, max(pad, width - pad)

    def _x_to_seconds(self, x: float) -> float:
        x0, x1 = self._track_bounds()
        span = x1 - x0
        frac = 0.0 if span <= 0 else (x - x0) / span
        frac = max(0.0, min(1.0, frac))
        return frac * self._duration

    def _redraw(self) -> None:
        c = self._canvas
        c.delete("all")

        x0, x1 = self._track_bounds()
        cy = self._TRACK_CY
        half = self._TRACK_H / 2

        # Background track
        _rounded_bar(c, x0, cy - half, x1, cy + half, half, fill=TRACK)

        if self._duration <= 0:
            return

        frac = self._position / self._duration
        tx = x0 + frac * (x1 - x0)

        # Filled (elapsed) portion
        if tx > x0:
            _rounded_bar(c, x0, cy - half, tx, cy + half, half, fill=ACCENT)

        # Thumb (slightly larger on hover / while dragging)
        r = self._THUMB_R_ACTIVE if (self._dragging or self._hover) else self._THUMB_R
        outline = ACCENT_HOVER if self._dragging else ACCENT
        c.create_oval(
            tx - r, cy - r, tx + r, cy + r,
            fill="#ffffff", outline=outline, width=2,
        )

        # VLC-style time bubble above the thumb while dragging
        if self._dragging:
            self._draw_bubble(tx)

    def _draw_bubble(self, thumb_x: float) -> None:
        c = self._canvas
        text = _fmt(self._position)
        width = len(text) * 6 + 12
        height = 16
        # Keep the bubble fully inside the canvas
        max_x = self._canvas.winfo_width()
        cx = min(max(thumb_x, width / 2 + 1), max_x - width / 2 - 1)
        cy = height / 2 + 1
        c.create_rectangle(
            cx - width / 2, cy - height / 2,
            cx + width / 2, cy + height / 2,
            fill=SURFACE, outline=BORDER,
        )
        c.create_text(cx, cy, text=text, fill=TEXT, font=("Segoe UI", 8))


def _rounded_bar(
    canvas: tk.Canvas,
    x0: float, y0: float, x1: float, y1: float,
    radius: float, *, fill: str,
) -> None:
    """Draw a horizontally rounded bar (rectangle with semicircle caps)."""
    if x1 - x0 < radius * 2:
        radius = max(0.5, (x1 - x0) / 2)
    canvas.create_rectangle(x0 + radius, y0, x1 - radius, y1, fill=fill, outline="")
    canvas.create_oval(x0, y0, x0 + 2 * radius, y1, fill=fill, outline="")
    canvas.create_oval(x1 - 2 * radius, y0, x1, y1, fill=fill, outline="")


def _fmt(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"
