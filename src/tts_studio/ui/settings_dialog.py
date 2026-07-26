"""Engine settings dialog with tabs per engine."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from tts_studio.settings import DEFAULTS, get_engine_settings, set_engine_setting


class SettingsDialog:
    """Dialog for adjusting engine-specific generation parameters."""

    def __init__(self, root: tk.Tk, parent: tk.Tk | None = None):
        self.root = root
        self.root.title("Settings")
        self.root.geometry("400x300")
        self.root.resizable(False, False)

        if parent is not None:
            px = parent.winfo_rootx() + 50
            py = parent.winfo_rooty() + 50
            self.root.geometry(f"+{px}+{py}")

        self._all_vars: dict[str, dict[str, tk.DoubleVar]] = {}
        self._build()

    def _build(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        for engine_name in sorted(DEFAULTS.keys()):
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=engine_name.title())
            self._build_tab(frame, engine_name)

        # Shared feedback label below notebook
        self._feedback = ttk.Label(self.root, text="", foreground="green")
        self._feedback.pack(pady=(5, 10))

    def _build_tab(self, frame: ttk.Frame, engine_name: str) -> None:
        settings = get_engine_settings(engine_name)
        self._all_vars[engine_name] = {}

        # Only show numeric settings (skip last_voice etc.)
        numeric = {k: v for k, v in settings.items() if isinstance(v, (int, float))}
        for key, value in sorted(numeric.items()):
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=3, padx=15)

            label = key.replace("_", " ").title()
            ttk.Label(row, text=label, width=18).pack(side="left")

            var = tk.DoubleVar(value=value)
            self._all_vars[engine_name][key] = var

            scale = ttk.Scale(
                row,
                from_=self._range(key)[0],
                to=self._range(key)[1],
                variable=var,
                orient="horizontal",
            )
            scale.pack(side="left", fill="x", expand=True, padx=(5, 5))

            val_label = ttk.Label(row, text=f"{value:.2f}", width=5)
            val_label.pack(side="right")

            engine = engine_name
            k = key

            var.trace_add(
                "write",
                lambda *a, e=engine, k2=k, l=val_label: l.config(
                    text=f"{self._all_vars[e][k2].get():.2f}"
                ),
            )

        btn_row = ttk.Frame(frame)
        btn_row.pack(pady=(15, 5))

        ttk.Button(
            btn_row,
            text="Save",
            command=lambda e=engine_name: self._save(e),
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_row,
            text="Reset to Defaults",
            command=lambda e=engine_name: self._reset(e),
        ).pack(side="left", padx=5)

    @staticmethod
    def _range(key: str) -> tuple[float, float]:
        ranges = {
            "speed": (0.5, 2.0),
            "exaggeration": (0.0, 1.0),
            "cfg_weight": (0.0, 1.0),
            "temperature": (0.0, 2.0),
            "repetition_penalty": (1.0, 2.0),
        }
        return ranges.get(key, (0.0, 1.0))

    def _save(self, engine_name: str) -> None:
        for key, var in self._all_vars.get(engine_name, {}).items():
            set_engine_setting(engine_name, key, var.get())
        self._feedback.config(text="Saved!")
        self.root.after(2000, lambda: self._feedback.config(text=""))

    def _reset(self, engine_name: str) -> None:
        defaults = DEFAULTS.get(engine_name, {})
        for key, var in self._all_vars.get(engine_name, {}).items():
            var.set(defaults.get(key, var.get()))
        self._feedback.config(text="Reset to defaults")
        self.root.after(2000, lambda: self._feedback.config(text=""))
