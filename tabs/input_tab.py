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

        # Startwerte kommen aus app_settings.json (siehe tabs/settings_store.py) -
        # damit steht beim Öffnen wieder derselbe Input wie vor dem letzten
        # Beenden bzw. einem Stromausfall.
        self.input_mode_var = tk.StringVar(value=self.settings.get("input_mode", "usb"))
        for text, value in [("USB-Kamera (--input usb)", "usb"),
                             ("Raspberry-Pi-Kamera (--input rpi)", "rpi"),
                             ("Videodatei", "file")]:
            ctk.CTkRadioButton(frame, text=text, variable=self.input_mode_var, value=value,
                                command=self._on_input_mode_change).pack(anchor="w", padx=10, pady=3)

        saved_file_path = self.settings.get("input_file_path", "")
        self.file_path_var = tk.StringVar(
            value=saved_file_path if saved_file_path else "(keine Datei gewählt)")
        self.file_button = ctk.CTkButton(frame, text="Videodatei wählen...", command=self._choose_file)
        self.file_button.pack(anchor="w", padx=10, pady=(15, 5))
        ctk.CTkLabel(frame, textvariable=self.file_path_var, text_color=("gray30", "gray70")).pack(anchor="w", padx=10)

        self.input_status_var = tk.StringVar(value="Noch kein Input ausgewählt.")
        ctk.CTkLabel(frame, textvariable=self.input_status_var, text_color="#4CAF50",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=20)

        self._build_model_section(frame)

        self._on_input_mode_change()

    def _build_model_section(self, frame):
        """
        Erkennungsmodell (.hef-Datei) wählen. Leer/"(Standardmodell)" heißt:
        --hef-path wird beim Start gar nicht erst übergeben, dann wählt
        hailo_apps selbst das zur erkannten Hailo-Architektur passende
        Standardmodell (siehe tabs/pipeline_control.py). --hef-path ist ein
        von hailo_apps selbst definiertes, offizielles CLI-Argument
        (hailo_app_python/core/common/core.py) - core.py muss dafür nicht
        angepasst werden, core.py übergibt nur die zusätzliche Option beim
        Start des Subprozesses weiter.
        """
        model_frame = ctk.CTkFrame(frame, corner_radius=8)
        model_frame.pack(anchor="w", fill="x", pady=(0, 15))
        ctk.CTkLabel(model_frame, text="Erkennungsmodell",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
        ctk.CTkLabel(
            model_frame,
            text="Optional: eigene .hef-Modelldatei statt des von Hailo automatisch "
                 "gewählten Standardmodells (muss zur erkannten Hailo-Architektur "
                 "passen, z. B. hailo8).",
            text_color=("gray30", "gray70"), wraplength=560, justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 8))

        saved_model_path = self.settings.get("model_hef_path", "")
        self.model_hef_path_var = tk.StringVar(
            value=saved_model_path if saved_model_path else "(Standardmodell)")

        row = ctk.CTkFrame(model_frame, fg_color="transparent")
        row.pack(anchor="w", fill="x", padx=12, pady=(0, 10))
        ctk.CTkButton(row, text="HEF-Datei wählen...", width=150,
                      command=self._choose_model).pack(side="left")
        ctk.CTkButton(row, text="Zurücksetzen", width=110, fg_color="gray30",
                      command=self._reset_model).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(model_frame, textvariable=self.model_hef_path_var,
                     text_color=("gray30", "gray70"), wraplength=560, justify="left").pack(
            anchor="w", padx=12, pady=(0, 10))

        # Klassenliste des Modells: .hef-Dateien enthalten selbst keine
        # standardisiert auslesbare Klassenliste (siehe Begründung in der
        # ToDo-Datei), daher optional separat als JSON-Datei angebbar (Liste
        # von Klassennamen, z. B. ["person", "dog"]). Ohne Angabe gilt
        # weiterhin die feste Standardliste (roi_config_app.ALL_CLASSES).
        ctk.CTkLabel(
            model_frame,
            text="Optional dazu: JSON-Datei mit der Klassenliste des Modells "
                 "(Liste von Namen, z. B. [\"person\", \"dog\"]). Ohne Angabe "
                 "gilt die Standardliste: person, bicycle, car, motorcycle, "
                 "bus, truck.",
            text_color=("gray30", "gray70"), wraplength=560, justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 8))

        saved_labels_path = self.settings.get("model_labels_path", "")
        self.model_labels_path_var = tk.StringVar(
            value=saved_labels_path if saved_labels_path else "(Standardklassen)")

        labels_row = ctk.CTkFrame(model_frame, fg_color="transparent")
        labels_row.pack(anchor="w", fill="x", padx=12, pady=(0, 10))
        ctk.CTkButton(labels_row, text="Klassen-JSON wählen...", width=150,
                      command=self._choose_labels).pack(side="left")
        ctk.CTkButton(labels_row, text="Zurücksetzen", width=110, fg_color="gray30",
                      command=self._reset_labels).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(model_frame, textvariable=self.model_labels_path_var,
                     text_color=("gray30", "gray70"), wraplength=560, justify="left").pack(
            anchor="w", padx=12, pady=(0, 10))

    def _choose_model(self):
        path = filedialog.askopenfilename(
            title="HEF-Modelldatei wählen",
            filetypes=[("HEF-Modell", "*.hef"), ("Alle Dateien", "*.*")])
        if path:
            self.model_hef_path_var.set(path)

    def _reset_model(self):
        self.model_hef_path_var.set("(Standardmodell)")

    def _choose_labels(self):
        path = filedialog.askopenfilename(
            title="Klassen-JSON-Datei wählen",
            filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")])
        if path:
            self.model_labels_path_var.set(path)

    def _reset_labels(self):
        self.model_labels_path_var.set("(Standardklassen)")

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
