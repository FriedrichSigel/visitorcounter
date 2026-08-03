"""
tabs/recording_controls.py — Mitschnitt-Abschnitt von Seite 3 (Benchmark-/
Laborlauf-Aufzeichnung). Eigene Datei statt Teil von tabs/start_tab.py, weil
Aufbau + Validierung + Hilfsfunktionen des Mitschnitts ein in sich
abgeschlossenes Thema sind (Separation of Concerns) - start_tab.py bindet nur
noch _build_recording_section() ein, ohne dessen Details zu kennen
(Information Hiding). Siehe tabs/__init__.py für die Mixin-Begründung.
"""

import os
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk
import ctk_dialogs as messagebox

from recording import find_usb_mount, free_gb


class RecordingControlsMixin:
    """Mitschnitt-Checkbox + Einstellungen (Ziel, Bitrate, Bilder/s,
    Segmentlänge) - nur für Benchmark-/Laborläufe, siehe Docstring in
    recording.py."""

    def _build_recording_section(self, frame):
        """Baut den Mitschnitt-Abschnitt in `frame` (Tab 3) auf. Bewusst ganz
        oben in der Seite, weil die Entscheidung "wird dieser Lauf
        aufgezeichnet?" vor allen anderen Optionen steht."""
        rec_frame = ctk.CTkFrame(frame, corner_radius=8)
        rec_frame.pack(anchor="w", fill="x", pady=(0, 12))
        ctk.CTkCheckBox(
            rec_frame, text="Video mitschneiden (Benchmark / Laborlauf)",
            variable=self.recording_enabled_var, command=self._on_recording_toggle,
            font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            rec_frame,
            text="Nur für Benchmark-/Laborläufe. Im Normalbetrieb werden keine "
                 "Bilddaten gespeichert (Privacy by Design) - diese Option "
                 "deshalb im Feldeinsatz ausgeschaltet lassen. Aufnahmen nach "
                 "der Auswertung löschen.",
            text_color="#E0A030", wraplength=560, justify="left").pack(
            anchor="w", padx=12, pady=(0, 8))

        rec_row = ctk.CTkFrame(rec_frame, fg_color="transparent")
        rec_row.pack(anchor="w", fill="x", padx=12)
        ctk.CTkLabel(rec_row, text="Ziel:").pack(side="left")
        self.recording_dir_entry = ctk.CTkEntry(
            rec_row, textvariable=self.recording_dir_var, width=260)
        self.recording_dir_entry.pack(side="left", padx=(5, 5))
        self.recording_browse_button = ctk.CTkButton(
            rec_row, text="Ordner wählen", width=110, fg_color="gray30",
            command=self._choose_recording_dir)
        self.recording_browse_button.pack(side="left", padx=(0, 5))
        self.recording_usb_button = ctk.CTkButton(
            rec_row, text="USB suchen", width=100, fg_color="gray30",
            command=self._detect_recording_usb)
        self.recording_usb_button.pack(side="left")

        rec_row2 = ctk.CTkFrame(rec_frame, fg_color="transparent")
        rec_row2.pack(anchor="w", fill="x", padx=12, pady=(6, 0))
        ctk.CTkLabel(rec_row2, text="Bitrate (kbit/s):").pack(side="left")
        self.recording_bitrate_entry = ctk.CTkEntry(
            rec_row2, textvariable=self.recording_bitrate_var, width=70)
        self.recording_bitrate_entry.pack(side="left", padx=(5, 15))
        ctk.CTkLabel(rec_row2, text="Bilder/s:").pack(side="left")
        self.recording_fps_entry = ctk.CTkEntry(
            rec_row2, textvariable=self.recording_fps_var, width=60)
        self.recording_fps_entry.pack(side="left", padx=(5, 15))
        ctk.CTkLabel(rec_row2, text="Segment (s):").pack(side="left")
        self.recording_segment_entry = ctk.CTkEntry(
            rec_row2, textvariable=self.recording_segment_var, width=70)
        self.recording_segment_entry.pack(side="left", padx=5)

        # Zeigt freien Speicher und geschätzte Reichweite - die eigentliche
        # Frage bei einem Laborlauf ist "wie lange reicht der Platz?".
        self.recording_info_var = tk.StringVar(value="")
        ctk.CTkLabel(rec_frame, textvariable=self.recording_info_var,
                     text_color=("gray30", "gray70"), wraplength=560, justify="left").pack(
            anchor="w", padx=12, pady=(6, 10))

        for var in (self.recording_dir_var, self.recording_bitrate_var):
            var.trace_add("write", lambda *_: self._refresh_recording_info())

        self._on_recording_toggle()   # setzt Feld-Zustände des Mitschnitts

    def _on_recording_toggle(self):
        """Schaltet die Eingabefelder des Mitschnitts frei und aktualisiert die
        Platzanzeige."""
        state = "normal" if self.recording_enabled_var.get() else "disabled"
        for widget_name in ("recording_dir_entry", "recording_browse_button",
                            "recording_usb_button", "recording_bitrate_entry",
                            "recording_fps_entry", "recording_segment_entry"):
            widget = getattr(self, widget_name, None)
            if widget is not None:
                widget.configure(state=state)
        self._refresh_recording_info()
        if hasattr(self, "page_frames"):
            self.root.after(20, lambda: self._redraw_tree(self.page_frames["3. Start"]))

    def _choose_recording_dir(self):
        path = filedialog.askdirectory(title="Zielordner für den Mitschnitt wählen")
        if path:
            self.recording_dir_var.set(path)

    def _detect_recording_usb(self):
        """Sucht einen eingehängten USB-Datenträger und trägt ihn als Ziel ein.

        Nutzt dieselbe Suche wie core.py, damit die GUI nicht etwas anderes
        anzeigt, als der Zähllauf später tatsächlich verwendet.
        """
        usb = find_usb_mount()
        if usb:
            self.recording_dir_var.set(os.path.join(usb, "visitorcounter_aufnahmen"))
        else:
            messagebox.showinfo(
                "Nichts gefunden",
                "Kein eingehängter USB-Datenträger gefunden. Stick anstecken und "
                "kurz warten, bis er im Dateimanager auftaucht - oder den Ordner "
                "von Hand wählen.",
                parent=self.root)

    def _refresh_recording_info(self):
        """Zeigt freien Speicher am Zielort und die geschätzte Aufnahmedauer."""
        if not hasattr(self, "recording_info_var"):
            return
        if not self.recording_enabled_var.get():
            self.recording_info_var.set(
                "Aus. Der Mitschnitt ist nur für Labor-/Benchmarkläufe gedacht - "
                "im Dauerbetrieb ausgeschaltet lassen.")
            return

        target = self.recording_dir_var.get().strip()
        if not target or target.lower() == "auto":
            usb = find_usb_mount()
            target = os.path.join(usb, "visitorcounter_aufnahmen") if usb else os.path.abspath("aufnahmen")
            prefix = f"Automatisch gewählt: {target}"
        else:
            prefix = f"Ziel: {target}"

        # Für die Platzberechnung reicht das nächstgelegene existierende
        # Elternverzeichnis - der Zielordner wird erst von core.py angelegt.
        probe = target
        while probe and not os.path.isdir(probe):
            parent = os.path.dirname(probe)
            if parent == probe:
                break
            probe = parent

        try:
            bitrate = int(self.recording_bitrate_var.get().strip() or "0")
        except ValueError:
            bitrate = 0

        free = free_gb(probe) if probe else 0.0
        if bitrate > 0:
            gb_per_hour = bitrate * 3600 / 8 / 1_000_000
            hours = max(free - 2.0, 0) / gb_per_hour
            self.recording_info_var.set(
                f"{prefix}\n{free:.1f} GB frei - reicht für ca. {hours:.1f} Stunden "
                f"({gb_per_hour:.2f} GB/h). 2 GB bleiben als Reserve frei.")
        else:
            self.recording_info_var.set(f"{prefix}\n{free:.1f} GB frei.")

    def _validate_recording_settings(self):
        """Prüft die Zahlenfelder des Mitschnitts. Rückgabe: dict oder None."""
        fields = {
            "Bitrate": (self.recording_bitrate_var, 100, 20000),
            "Bilder/s": (self.recording_fps_var, 1, 60),
            "Segmentlänge": (self.recording_segment_var, 10, 3600),
        }
        values = {}
        for label, (var, low, high) in fields.items():
            raw = var.get().strip()
            try:
                value = int(raw)
            except ValueError:
                messagebox.showwarning(
                    "Ungültige Eingabe",
                    f"{label} muss eine ganze Zahl sein (eingegeben: '{raw}').",
                    parent=self.root)
                return None
            if not (low <= value <= high):
                messagebox.showwarning(
                    "Ungültige Eingabe",
                    f"{label} muss zwischen {low} und {high} liegen.",
                    parent=self.root)
                return None
            values[label] = value

        return {
            "dir": self.recording_dir_var.get().strip() or "auto",
            "bitrate": values["Bitrate"],
            "fps": values["Bilder/s"],
            "segment": values["Segmentlänge"],
        }
