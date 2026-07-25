"""First-launch setup wizard — lets the user pick which models to download."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from tts_studio.models.registry import AVAILABLE_MODELS


class SetupWizard:
    """First-launch model selection dialog."""

    def __init__(self, root: tk.Tk, on_complete: Callable[[list[str]], None]):
        self.root = root
        self.on_complete = on_complete
        self._vars: dict[str, tk.BooleanVar] = {}

        self._build()

    def _build(self) -> None:
        self.root.title("TTS Studio — Setup")

        ttk.Label(
            self.root,
            text="Welcome to TTS Studio",
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(20, 5))

        ttk.Label(
            self.root,
            text="Select the models you want to install.\n"
                 "You can add or remove models later from Model Manager.",
            justify="center",
        ).pack(pady=(0, 15))

        # Model list with checkboxes
        frame = ttk.Frame(self.root)
        frame.pack(padx=20, pady=10, fill="both", expand=True)

        for i, model in enumerate(AVAILABLE_MODELS):
            var = tk.BooleanVar(value=False)
            self._vars[model.id] = var

            row = ttk.Frame(frame)
            row.pack(fill="x", pady=3)

            cb = ttk.Checkbutton(row, variable=var)
            cb.pack(side="left")

            info = ttk.Frame(row)
            info.pack(side="left", padx=(5, 0))

            ttk.Label(info, text=model.name, font=("Segoe UI", 10, "bold")).pack(
                anchor="w"
            )
            detail = f"{model.size_mb} MB  •  {', '.join(model.languages[:3])}"
            if len(model.languages) > 3:
                detail += f" +{len(model.languages) - 3} more"
            ttk.Label(info, text=f"{model.description}\n{detail}", foreground="gray").pack(
                anchor="w"
            )

        # Buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=(10, 20))

        ttk.Button(
            btn_frame,
            text="Continue with selected models",
            command=self._finish,
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="Skip (I'll add models later)",
            command=lambda: self.on_complete([]),
        ).pack(side="left", padx=5)

    def _finish(self) -> None:
        selected = [mid for mid, var in self._vars.items() if var.get()]
        self.on_complete(selected)
