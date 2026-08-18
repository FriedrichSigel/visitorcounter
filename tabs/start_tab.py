"""
tabs/start_tab.py — Seite 3: Pipeline starten/stoppen. Fügt nur noch die
Abschnitte aus recording_controls.py, lora_controls.py, mqtt_controls.py und
pipeline_control.py zusammen (MainApp mischt alle vier zusätzlich ein) -
kennt deren Aufbau-Details nicht (Information Hiding). Siehe
tabs/__init__.py für die Mixin-Begründung.
"""

import tkinter as tk

import customtkinter as ctk

from ui_utils import make_scrollable


class StartTabMixin:
    """Seite 3: Layout drumherum (Debug-Hauptschalter, Start-/Stopp-Knöpfe,
    Statuszeile) plus Einbindung der Mitschnitt-/LoRa-/MQTT-Abschnitte.

    Debug-Funktionen (Mitschnitt, Live-Vorschau, Zeitlimit, Debug-Dateien,
    detaillierte Konsole) sind hinter einem Hauptschalter versteckt - im
    Feldeinsatz sollen sie erst gar nicht sichtbar/aktivierbar sein, nur im
    Labor. LoRa/MQTT sind davon ausgenommen und bleiben immer sichtbar, das
    sind reguläre Betriebsfunktionen, keine Debug-Hilfsmittel."""

    def _build_start_tab(self):
        frame = make_scrollable(self.page_frames["3. Start"])
        ctk.CTkLabel(frame, text="Pipeline starten / stoppen", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", pady=(5, 15))

        # Statuszeile des Aufwärmlaufs - nur sichtbar, solange er laeuft bzw.
        # kurz danach.
        ctk.CTkLabel(frame, textvariable=self.warmup_status_var,
                     text_color="#4FC3F7", wraplength=560, justify="left").pack(
            anchor="w", padx=10, pady=(0, 6))

        self._build_debug_section(frame)

        # --- LoRa-Versand -------------------------------------------------
        self._build_lora_section(frame)

        # --- MQTT-Versand -------------------------------------------------
        self._build_mqtt_section(frame)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(anchor="w")
        self.start_button = ctk.CTkButton(
            btn_frame, text="▶  Pipeline starten", fg_color="#2E8B57", hover_color="#256e46",
            font=ctk.CTkFont(weight="bold"), command=self._start_pipeline, width=180)
        self.start_button.pack(side="left", padx=(0, 10))
        self.stop_button = ctk.CTkButton(
            btn_frame, text="■  Stoppen", fg_color="#B23A3A", hover_color="#8f2e2e",
            font=ctk.CTkFont(weight="bold"), command=self._stop_pipeline, width=180, state="disabled")
        self.stop_button.pack(side="left")

        self.pipeline_status_var = tk.StringVar(value="Status: gestoppt")
        ctk.CTkLabel(frame, textvariable=self.pipeline_status_var, font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", pady=20)

        self.collection_hint_var = tk.StringVar(value="")
        ctk.CTkLabel(frame, textvariable=self.collection_hint_var, text_color="#D9A441",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w")

        ctk.CTkLabel(
            frame,
            text="Hinweis: 'Stoppen' schickt der Pipeline dasselbe Signal wie Ctrl+C "
                 "im Terminal (SIGINT) - das ist der einzige Shutdown-Weg, der in "
                 "core.py zuverlässig sauber funktioniert.",
            text_color=("gray25", "gray60"), wraplength=500, justify="left",
        ).pack(anchor="w", pady=10)

    def _build_debug_section(self, frame):
        """
        Hauptschalter "Debug-Funktionen" + die dahinter versteckten Optionen:
        Mitschnitt, Live-Vorschau, optionales Zeitlimit, Debug-Dateien
        (ergebniss.csv, Bewegungsbilder, Benchmark-Bericht) und detaillierte
        Konsolenausgabe (Frame-/Detection-Zeilen). Ausgeschaltet (Standard)
        sind alle diese Optionen unerreichbar - _start_pipeline() erzwingt
        das zusätzlich beim tatsächlichen Start (siehe pipeline_control.py),
        damit eine im Labor aktivierte Option nicht versehentlich in den
        Feldeinsatz mitgenommen wird, nur weil der Haken noch gesetzt ist.
        """
        self.debug_enabled_var = tk.BooleanVar(value=self.settings["debug_enabled"])
        ctk.CTkCheckBox(
            frame, text="Debug-Funktionen aktivieren",
            variable=self.debug_enabled_var, command=self._on_debug_toggle,
            font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(0, 4))
        # Direkte Widget-Referenz statt Index/Reihenfolge-Raten: debug_frame
        # wird beim Ein-/Ausblenden immer direkt NACH diesem Label wieder
        # eingefügt (siehe _on_debug_toggle) - sonst würde ein einfaches
        # erneutes pack() den Frame ans Ende rutschen lassen, hinter die
        # inzwischen schon gepackten LoRa-/MQTT-Abschnitte.
        self._debug_frame_anchor = ctk.CTkLabel(
            frame,
            text="Nur für Labor-/Testläufe. Schaltet Mitschnitt, Live-Vorschau, "
                 "Zeitlimit, Debug-Dateien und detaillierte Konsolenausgabe frei - "
                 "im Feldeinsatz ausgeschaltet lassen.",
            text_color="#E0A030", wraplength=560, justify="left",
        )
        self._debug_frame_anchor.pack(anchor="w", padx=10, pady=(0, 10))

        self.debug_frame = ctk.CTkFrame(frame, fg_color="transparent")
        # Wird von _on_debug_toggle() gepackt/entpackt - hier noch nicht
        # anzeigen, das passt zusammen mit dem Checkbox-Zustand unten.

        # --- Mitschnitt (Benchmark) - bewusst ganz oben innerhalb der
        # Debug-Optionen, weil die Entscheidung "wird dieser Lauf
        # aufgezeichnet?" vor allen anderen Debug-Optionen steht.
        self._build_recording_section(self.debug_frame)

        self.use_frame_var = tk.BooleanVar(value=self.settings["use_frame"])
        ctk.CTkCheckBox(self.debug_frame, text="Live-Vorschau anzeigen (--use-frame)",
                        variable=self.use_frame_var).pack(anchor="w", padx=10, pady=(0, 4))
        ctk.CTkLabel(
            self.debug_frame,
            text="Hinweis: Die Live-Vorschau kann bei sehr langen Läufen instabil "
                 "werden. Für Dauerläufe die Vorschau deaktiviert lassen.",
            text_color=("gray25", "gray60"), wraplength=560, justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 12))

        # Debug-Dateien: ergebniss.csv (Track-Zwischenspeicher) und die
        # Bewegungsbilder. zaehlung.csv ist davon ausdrücklich NICHT
        # betroffen (siehe config.DEBUG_FILES_ENABLED) - die wird immer
        # geschrieben, LoRa/MQTT und die Zählerstands-Anzeige (Tab 4)
        # brauchen sie unabhängig vom Debug-Schalter.
        self.debug_files_var = tk.BooleanVar(value=self.settings["debug_files_enabled"])
        ctk.CTkCheckBox(
            self.debug_frame,
            text="Debug-Dateien erzeugen (ergebniss.csv, Bewegungsbilder,\n"
                 "Benchmark-Bericht bei aktivem Mitschnitt)",
            variable=self.debug_files_var,
        ).pack(anchor="w", padx=10, pady=(0, 12))

        # Detaillierte Konsolenausgabe: ohne diese Option filtert Tab 4 die
        # "Frame count:"/"Detection:"-Zeilen aus core.py heraus (Status-,
        # Zähl- und [LoRa]/[MQTT]-Zeilen bleiben immer sichtbar) - siehe
        # tabs/output_tab.py, _should_show_console_line().
        self.verbose_console_var = tk.BooleanVar(value=self.settings["verbose_console_enabled"])
        ctk.CTkCheckBox(
            self.debug_frame,
            text="Live-Konsolenausgabe: Frame-/Detection-Zeilen anzeigen",
            variable=self.verbose_console_var,
        ).pack(anchor="w", padx=10, pady=(0, 12))

        # Optionales Zeitlimit für den normalen Zähllauf. Leer = kein Limit.
        # (Das automatische Stoppen nach fester Zeit war früher an die
        # Auto-Config-Datensammlung gekoppelt und lief versehentlich auch bei
        # normalen Läufen - das ist jetzt entkoppelt: normale Läufe laufen ohne
        # Limit, sofern hier nichts eingetragen wird.)
        dur_frame = ctk.CTkFrame(self.debug_frame, corner_radius=8)
        dur_frame.pack(anchor="w", fill="x", pady=(0, 15))
        ctk.CTkLabel(dur_frame, text="Optionales Zeitlimit",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
        row = ctk.CTkFrame(dur_frame, fg_color="transparent")
        row.pack(anchor="w", padx=12, pady=(0, 10))
        ctk.CTkLabel(row, text="Laufdauer (Sekunden, leer = kein Limit):").pack(side="left")
        ctk.CTkEntry(row, textvariable=self.run_duration_var, width=80).pack(side="left", padx=5)

        self._on_debug_toggle()   # setzt die anfängliche Sichtbarkeit von debug_frame

    def _on_debug_toggle(self):
        """Zeigt/versteckt debug_frame passend zum Hauptschalter."""
        if self.debug_enabled_var.get():
            self.debug_frame.pack(anchor="w", fill="x", after=self._debug_frame_anchor)
        else:
            self.debug_frame.pack_forget()
        # Ein-/Ausblenden verändert das Layout der Seite - Redraw anstossen
        # (dasselbe Muster wie beim Mitschnitt-/LoRa-Umschalten).
        if hasattr(self, "page_frames"):
            self.root.after(20, lambda: self._redraw_tree(self.page_frames["3. Start"]))
