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
    """Seite 3: Layout drumherum (Live-Vorschau-Schalter, optionales
    Zeitlimit, Start-/Stopp-Knöpfe, Statuszeile) plus Einbindung der
    Mitschnitt-/LoRa-/MQTT-Abschnitte."""

    def _build_start_tab(self):
        frame = make_scrollable(self.page_frames["3. Start"])
        ctk.CTkLabel(frame, text="Pipeline starten / stoppen", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", pady=(5, 15))

        # Statuszeile des Aufwärmlaufs - nur sichtbar, solange er laeuft bzw.
        # kurz danach.
        ctk.CTkLabel(frame, textvariable=self.warmup_status_var,
                     text_color="#4FC3F7", wraplength=560, justify="left").pack(
            anchor="w", padx=10, pady=(0, 6))

        # --- Mitschnitt (Benchmark) - bewusst ganz oben, weil die Entscheidung
        # "wird dieser Lauf aufgezeichnet?" vor allen anderen Optionen steht.
        self._build_recording_section(frame)

        self.use_frame_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(frame, text="Live-Vorschau anzeigen (--use-frame)",
                        variable=self.use_frame_var).pack(anchor="w", padx=10, pady=(0, 4))
        ctk.CTkLabel(
            frame,
            text="Hinweis: Die Live-Vorschau kann bei sehr langen Läufen instabil "
                 "werden. Für Dauerläufe die Vorschau deaktiviert lassen.",
            text_color=("gray25", "gray60"), wraplength=560, justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 12))

        # --- LoRa-Versand -------------------------------------------------
        self._build_lora_section(frame)

        # --- MQTT-Versand -------------------------------------------------
        self._build_mqtt_section(frame)

        # Optionales Zeitlimit für den normalen Zähllauf. Leer = kein Limit.
        # (Das automatische Stoppen nach fester Zeit war früher an die
        # Auto-Config-Datensammlung gekoppelt und lief versehentlich auch bei
        # normalen Läufen - das ist jetzt entkoppelt: normale Läufe laufen ohne
        # Limit, sofern hier nichts eingetragen wird.)
        dur_frame = ctk.CTkFrame(frame, corner_radius=8)
        dur_frame.pack(anchor="w", fill="x", pady=(0, 15))
        ctk.CTkLabel(dur_frame, text="Optionales Zeitlimit",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
        row = ctk.CTkFrame(dur_frame, fg_color="transparent")
        row.pack(anchor="w", padx=12, pady=(0, 10))
        ctk.CTkLabel(row, text="Laufdauer (Sekunden, leer = kein Limit):").pack(side="left")
        ctk.CTkEntry(row, textvariable=self.run_duration_var, width=80).pack(side="left", padx=5)

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
