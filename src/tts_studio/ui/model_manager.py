"""Model manager dialog — download/delete models."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from tts_studio.models.manager import (
    AVAILABLE_MODELS,
    delete_model,
    get_downloaded_models,
)


class ModelManager:
    """Dialog for managing installed TTS models."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Model Manager")
        self.root.geometry("550x420")
        self.root.resizable(True, True)

        self._build()
        self._refresh()

    def _build(self) -> None:
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=15, pady=(15, 5))

        ttk.Label(
            header,
            text="Model Manager",
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left")

        ttk.Button(header, text="Refresh", command=self._refresh).pack(side="right")

        ttk.Label(
            self.root,
            text="Installed models are stored in models/. Select a model and click Delete to remove it.",
            foreground="gray",
        ).pack(padx=15, anchor="w")

        # Treeview
        columns = ("status", "name", "provider", "size")
        self._tree = ttk.Treeview(
            self.root, columns=columns, show="headings", selectmode="browse"
        )
        self._tree.heading("status", text="Status")
        self._tree.heading("name", text="Model")
        self._tree.heading("provider", text="Provider")
        self._tree.heading("size", text="Size")

        self._tree.column("status", width=80)
        self._tree.column("name", width=220)
        self._tree.column("provider", width=100)
        self._tree.column("size", width=80)

        scrollbar = ttk.Scrollbar(self.root, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(padx=15, pady=(10, 0), fill="both", expand=True)
        scrollbar.pack(side="right", fill="y", padx=(0, 15), pady=(10, 0))

        # Progress bar (hidden by default)
        self._progress = ttk.Progressbar(
            self.root, orient="horizontal", mode="indeterminate"
        )

        # Status label
        self._status = ttk.Label(self.root, text="", foreground="gray")
        self._status.pack(padx=15, anchor="w")

        # Buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=(5, 15))

        ttk.Button(btn_frame, text="Download", command=self._download).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Delete", command=self._delete).pack(
            side="left", padx=5
        )

    def _refresh(self) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)

        downloaded = get_downloaded_models()

        for model in AVAILABLE_MODELS:
            installed = model.id in downloaded
            status = "INSTALLED" if installed else "Available"
            tag = "installed" if installed else "available"

            self._tree.insert(
                "",
                tk.END,
                values=(status, model.name, model.provider, f"{model.size_mb} MB"),
                tags=(tag,),
            )

        self._tree.tag_configure("installed", foreground="green")
        self._tree.tag_configure("available", foreground="gray")

    def _download(self) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        values = self._tree.item(sel[0], "values")
        model_name = values[1]
        model = next((m for m in AVAILABLE_MODELS if m.name == model_name), None)
        if model is None:
            return

        if model.id in get_downloaded_models():
            messagebox.showinfo("Already Installed", f"{model.name} is already installed.")
            return

        if not messagebox.askyesno(
            "Download Model",
            f"Download {model.name}?\n\n"
            f"This will fetch ~{model.size_mb} MB from Hugging Face.\n"
            f"The model will be stored in models/.",
        ):
            return

        self._tree.item(sel[0], values=("Downloading...", model.name, model.provider, f"{model.size_mb} MB"))
        self._status.config(text=f"Downloading {model.name}...")
        self._progress.pack(padx=15, pady=(5, 0), fill="x")
        self._progress.start()

        # Run download in background thread so UI stays responsive
        threading.Thread(
            target=self._do_download, args=(model,), daemon=True
        ).start()

    def _do_download(self, model) -> None:
        import traceback

        try:
            from tts_studio.config import MODELS_DIR
            import os
            os.environ.setdefault("HF_HOME", str(MODELS_DIR / "huggingface"))

            if model.provider == "kokoro":
                from kokoro import KPipeline
                KPipeline(lang_code="a")
            elif model.provider == "chatterbox":
                from tts_studio.engines.chatterbox_engine import ChatterboxEngine
                engine = ChatterboxEngine()
                engine.load_model(model.id)

            self.root.after(0, self._on_download_done, model.name, True, "")
        except Exception:
            self.root.after(0, self._on_download_done, model.name, False, traceback.format_exc())

    def _on_download_done(self, model_name: str, success: bool, error: str) -> None:
        self._progress.stop()
        self._progress.pack_forget()
        self._status.config(text="")

        if success:
            messagebox.showinfo("Done", f"{model_name} downloaded successfully.")
        else:
            messagebox.showerror("Download Failed", error)

        self._refresh()

    def _delete(self) -> None:
        sel = self._tree.selection()
        if not sel:
            return

        values = self._tree.item(sel[0], "values")
        model_name = values[1]
        model = next((m for m in AVAILABLE_MODELS if m.name == model_name), None)
        if model is None:
            return

        if model.id not in get_downloaded_models():
            messagebox.showinfo("Not Installed", f"{model.name} is not installed.")
            return

        if messagebox.askyesno(
            "Delete Model",
            f"Delete {model.name}?\nThis frees approximately {model.size_mb} MB.",
        ):
            delete_model(model.id)
            self._refresh()
