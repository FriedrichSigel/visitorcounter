"""
tabs/autoconfig_tab.py — Seite 5: Auto-Konfiguration (Datensammlung für die
automatische Wegerkennung). Nur eingebunden, wenn config.SHOW_AUTO_CONFIG
aktiv ist (siehe app.py). Siehe tabs/__init__.py für die Mixin-Begründung.
"""

import customtkinter as ctk

from ui_utils import make_scrollable


class AutoConfigTabMixin:
    """Seite 5: startet dieselbe Pipeline wie Seite 3
    (pipeline_control.py._start_pipeline), aber mit collection=True."""

    def _build_autoconfig_tab(self):
        frame = make_scrollable(self.page_frames["5. Auto-Konfiguration"])

        ctk.CTkLabel(frame, text="Auto-Konfiguration - Datensammlung",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(5, 8))

        ctk.CTkLabel(
            frame,
            text="Sammelt Start- und Endpunkte aller Tracks (statt nur zu zählen), "
                 "als Datengrundlage für die automatische Zählgeometrie. Ablauf:\n"
                 "  1. Hier die Datensammlung mit gewünschter Dauer starten.\n"
                 "  2. Nach Ablauf entsteht auto_config_points.csv.\n"
                 "  3. In Tab 2 das Verfahren (Clustering / Randraster) wählen, "
                 "auswerten und speichern.",
            justify="left", wraplength=580, text_color=("gray30", "gray70"),
        ).pack(anchor="w", padx=6, pady=(0, 14))

        # Sammeldauer (= Zeitlimit NUR für die Datensammlung)
        dur_frame = ctk.CTkFrame(frame, corner_radius=8)
        dur_frame.pack(anchor="w", fill="x", pady=(0, 15))
        ctk.CTkLabel(dur_frame, text="Sammeldauer",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
        row = ctk.CTkFrame(dur_frame, fg_color="transparent")
        row.pack(anchor="w", padx=12, pady=(0, 4))
        ctk.CTkLabel(row, text="Dauer (Sekunden, leer = unbegrenzt):").pack(side="left")
        ctk.CTkEntry(row, textvariable=self.collection_duration_var, width=80).pack(side="left", padx=5)
        ctk.CTkLabel(dur_frame,
                     text="Dieses Zeitlimit gilt nur für die Datensammlung - "
                          "normale Zählläufe (Tab 3) laufen ohne Limit.",
                     text_color=("gray25", "gray60"), wraplength=560, justify="left").pack(
            anchor="w", padx=12, pady=(0, 10))

        # Start/Stop
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(anchor="w")
        self.autoconfig_start_button = ctk.CTkButton(
            btn_frame, text="▶  Datensammlung starten", fg_color="#2E8B57", hover_color="#256e46",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self._start_pipeline(collection=True), width=220)
        self.autoconfig_start_button.pack(side="left", padx=(0, 10))
        self.autoconfig_stop_button = ctk.CTkButton(
            btn_frame, text="■  Stoppen", fg_color="#B23A3A", hover_color="#8f2e2e",
            font=ctk.CTkFont(weight="bold"), command=self._stop_pipeline, width=160, state="disabled")
        self.autoconfig_stop_button.pack(side="left")

        ctk.CTkLabel(
            frame,
            text="Nach der Sammlung: weiter in Tab 2 → 'Auto: Clustering (DBSCAN)' "
                 "oder 'Auto: Randraster' → auswerten und speichern.",
            text_color="#D9A441", wraplength=560, justify="left",
        ).pack(anchor="w", pady=(16, 0))
