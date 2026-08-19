"""
tabs/config_tab.py — Seite 2: Zählgeometrie konfigurieren (bettet
RoiConfigApp komplett ein). Siehe tabs/__init__.py für die Mixin-Begründung.
"""

import json
import tkinter as tk

import customtkinter as ctk
import ctk_dialogs as messagebox

from roi_config_app import RoiConfigApp, load_first_frame
from ui_utils import make_scrollable

from .constants import ROI_CONFIG_PATH, CONFIG_FRAME_WIDTH


class ConfigTabMixin:
    """Seite 2: Zählgeometrie setzen. Nutzt Input-Wert aus Seite 1
    (InputTabMixin.self.input_value) und legt self.roi_config_widget an, das
    die eigentliche Konfigurationsarbeit übernimmt (RoiConfigApp)."""

    def _build_config_tab(self):
        frame = make_scrollable(self.page_frames["2. Konfiguration"])

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", pady=(0, 4))
        ctk.CTkButton(top, text="Frame laden (nutzt Input von Seite 1)",
                      command=self._load_config_frame).pack(side="left")
        self.config_status_var = tk.StringVar(value="Noch kein Frame geladen.")
        ctk.CTkLabel(top, textvariable=self.config_status_var, text_color=("gray30", "gray70")).pack(side="left", padx=15)

        # Zweite Zeile: bestehende Konfiguration einlesen und anzeigen. Ohne
        # das laesst sich nur schwer pruefen, was auf dem Geraet tatsaechlich
        # eingestellt ist - man musste die JSON-Datei von Hand oeffnen.
        second = ctk.CTkFrame(frame, fg_color="transparent")
        second.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(second, text="Aktuelle Konfiguration laden",
                      fg_color="gray30", command=self._load_existing_config).pack(side="left")
        self.config_loaded_var = tk.StringVar(value="")
        ctk.CTkLabel(second, textvariable=self.config_loaded_var,
                     text_color=("gray30", "gray70")).pack(side="left", padx=15)

        container = ctk.CTkFrame(frame, fg_color="transparent")
        container.pack(fill="both", expand=True)
        # Frame-Anzeigebreite fest an die 3/5-Layoutspalte binden, damit der
        # Canvas das Fenster nicht breiter zieht.
        self.roi_config_widget = RoiConfigApp(
            container, frame_width=CONFIG_FRAME_WIDTH,
            classes=self._load_model_classes())

        # Beim Start automatisch die zuletzt gespeicherte Zählgeometrie in
        # den Editor laden (still, ohne Warnung, falls es noch keine gibt -
        # z. B. beim allerersten Start eines frisch aufgesetzten Geräts).
        # roi_config.json selbst bleibt dabei unverändert; core.py liest sie
        # ohnehin unabhängig von dieser Anzeige.
        if self.roi_config_widget.load_config(silent=True):
            self.config_loaded_var.set(f"Automatisch geladen aus {ROI_CONFIG_PATH}")

    def _load_model_classes(self):
        """
        Liest die auf Seite 1 optional angegebene Klassen-JSON-Datei zum
        gewählten .hef-Modell (Liste von Namen). Fehlt die Angabe oder ist
        die Datei ungültig, gilt None - RoiConfigApp fällt dann auf die feste
        Standardliste zurück (roi_config_app.ALL_CLASSES).
        """
        path = self.settings.get("model_labels_path", "")
        if not path:
            return None
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            classes = [str(c) for c in data if str(c).strip()]
            return classes or None
        except (OSError, ValueError, TypeError):
            return None

    def _load_existing_config(self):
        """
        Liest roi_config.json und stellt sie in Tab 2 dar - Modus, Geometrie,
        Klassen, Richtung, IN-Feld. Damit ist auf einen Blick sichtbar, womit
        das Geraet gerade tatsaechlich zaehlt.
        """
        ok = self.roi_config_widget.load_config()
        if ok:
            self.config_loaded_var.set(f"Geladen aus {ROI_CONFIG_PATH}")
        else:
            self.config_loaded_var.set("Nicht geladen - siehe Meldung.")

    def _load_config_frame(self):
        if not self.input_value:
            messagebox.showwarning("Fehlt noch", "Bitte zuerst auf Seite 1 einen Input auswählen.", parent=self.root)
            return

        # Hinweis auf die geladene Konfiguration loeschen: das Laden eines
        # neuen Frames setzt die Geometrie zurueck, die Meldung "Geladen aus
        # roi_config.json" waere danach schlicht falsch.
        self.config_loaded_var.set("")

        if self.input_value in ("usb", "rpi"):
            self.config_status_var.set(
                "Nehme Referenzbild über die Pipeline auf, bitte warten "
                "(kann beim allerersten Start bis zu 2 Minuten dauern)...")
            self.root.update_idletasks()

        try:
            frame = load_first_frame(self.input_value)
        except Exception as e:
            messagebox.showerror("Fehler beim Laden", str(e), parent=self.root)
            self.config_status_var.set("Laden fehlgeschlagen.")
            return
        self.roi_config_widget.load_frame(frame)
        self.config_status_var.set(f"Frame geladen ({frame.shape[1]}x{frame.shape[0]}).")
