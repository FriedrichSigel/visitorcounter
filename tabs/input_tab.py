"""
tabs/input_tab.py — Seite 1: Input-Quelle wählen (USB-/Pi-Kamera oder
Videodatei). Siehe tabs/__init__.py für die Mixin-Begründung.
"""

import os
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from ui_utils import make_scrollable


class InputTabMixin:
    """
    Seite 1: Videodatei, USB- oder Pi-Kamera als Input wählen.

    Setzt self.input_value - die schmale Schnittstelle, über die die anderen
    Seiten (Konfiguration, Pipeline-Start) erfahren, welcher Input aktiv ist.
    """

    def _build_input_tab(self):
        frame = make_scrollable(self.page_frames["1. Input"])
        ctk.CTkLabel(frame, text="Input-Quelle wählen", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", pady=(5, 15))

        self.input_mode_var = tk.StringVar(value="usb")
        for text, value in [("USB-Kamera (--input usb)", "usb"),
                             ("Raspberry-Pi-Kamera (--input rpi)", "rpi"),
                             ("Videodatei", "file")]:
            ctk.CTkRadioButton(frame, text=text, variable=self.input_mode_var, value=value,
                                command=self._on_input_mode_change).pack(anchor="w", padx=10, pady=3)

        self.file_path_var = tk.StringVar(value="(keine Datei gewählt)")
        self.file_button = ctk.CTkButton(frame, text="Videodatei wählen...", command=self._choose_file)
        self.file_button.pack(anchor="w", padx=10, pady=(15, 5))
        ctk.CTkLabel(frame, textvariable=self.file_path_var, text_color=("gray30", "gray70")).pack(anchor="w", padx=10)

        self.input_status_var = tk.StringVar(value="Noch kein Input ausgewählt.")
        ctk.CTkLabel(frame, textvariable=self.input_status_var, text_color="#4CAF50",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=20)

        self._on_input_mode_change()

    def _on_input_mode_change(self):
        mode = self.input_mode_var.get()
        if mode == "file":
            self.file_button.configure(state="normal")
            if os.path.isfile(self.file_path_var.get()):
                self.input_value = self.file_path_var.get()
                self.input_status_var.set(f"Input gesetzt: {self.input_value}")
            else:
                self.input_value = None
                self.input_status_var.set("Bitte eine Videodatei wählen.")
        else:
            self.file_button.configure(state="disabled")
            self.input_value = mode
            self.input_status_var.set(f"Input gesetzt: {mode}")

    def _choose_file(self):
        path = filedialog.askopenfilename(title="Videodatei wählen")
        if path:
            self.input_value = path
            self.file_path_var.set(path)
            self.input_status_var.set(f"Input gesetzt: {path}")
