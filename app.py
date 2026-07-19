"""
app.py — zentrale Steuer-App: ein Fenster mit Sidebar-Navigation (statt
Tabs), um die gesamte Pipeline zu bedienen, ohne zwischen mehreren
Terminals/Skripten zu wechseln. UI-Bibliothek: customtkinter (dunkles
Design mit blauen Akzenten).

    1. Input             — Videodatei, USB- oder Pi-Kamera wählen
    2. Konfiguration      — Zählgeometrie setzen (nutzt roi_config_app.RoiConfigApp),
                            inkl. manueller Verfahren (Linie / ROI / Mehrere Flächen)
                            und der Auto-Verfahren (Clustering / Randraster)
    3. Start              — core.py als Subprozess starten/stoppen (normaler Zähllauf,
                            standardmäßig OHNE Zeitlimit)
    4. Live-Auswertung    — Konsolen-Ausgabe live mitlesen + aktuelle Zählerstände
    5. Auto-Konfiguration — Datensammlung für die Auto-Verfahren: Start-/Endpunkte
                            sammeln (mit Zeitlimit), danach in Tab 2 auswerten
                            gleichwertig nebeneinander: Linie, Fläche/ROI,
                            Mehrere Flächen, Auto: Clustering, Auto: Randraster
    3. Start              — core.py als Subprozess starten/stoppen, inkl.
                            Datensammlung für die Auto-Konfiguration aktivieren
    4. Live-Auswertung    — Konsolen-Ausgabe live mitlesen + aktuelle Zählerstände

Ersetzt NICHT die einzelnen Skripte — core.py, roi_config_app.py,
auto_config*.py bleiben eigenständig auf der Kommandozeile nutzbar.

Nutzung:
    python app.py

Voraussetzung: customtkinter (pip install customtkinter --break-system-packages).
"""

import csv
import json
import os
import queue
import signal
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog
import ctk_dialogs as messagebox   # CustomTkinter-Dialoge im App-Design

import customtkinter as ctk

import lora_message
from roi_config_app import RoiConfigApp, load_first_frame
from ui_utils import make_scrollable
from recording import find_usb_mount, free_gb

# Höhe der LoRa-Hinweisbox in Pixeln: klein, solange LoRa aus ist,
# hoch genug für die komplette Byte-Tabelle, sobald es an ist.
LORA_HINT_HEIGHT_OFF = 54
LORA_HINT_HEIGHT_ON = 300

ZAEHLUNG_CSV = "zaehlung.csv"
ROI_CONFIG_PATH = "roi_config.json"

PAGE_NAMES = ["1. Input", "2. Konfiguration", "3. Start", "4. Live-Auswertung", "5. Auto-Konfiguration"]

# --- Feste Layout-Maße (alles aus der Fensterbreite abgeleitet) ---
# Das Fenster wird in der Breite nie größer. Aufteilung: 1/5 Sidebar,
# 4/5 Content. In Tab 2 (Konfiguration) teilt sich der Content in 3/4 Frame-
# Bereich (= 3/5 des Fensters) und 1/4 Konfig-Spalte (= 1/5 des Fensters).
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 760
SIDEBAR_WIDTH = WINDOW_WIDTH // 5           # 1/5 = 256
CONTENT_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH  # 4/5 = 1024
# Innerhalb von Tab 2: Frame-Bereich (~3/5 des Fensters) und Konfig-Spalte
# (~1/5, breit genug für die längsten Labels wie "Mehrere Flächen (Übergänge)"
# und "Richtung umkehren (IN/OUT tauschen)"). Werte so gewählt, dass Canvas +
# Bedienspalte + Scrollbalken sicher in die feste CONTENT_WIDTH passen.
CONFIG_FRAME_WIDTH = 660    # Canvas-Breite (16:9 -> 371 hoch), ~0.52 der Fensterbreite
CONFIG_PANEL_WIDTH = 300    # Bedienspalte rechts

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Personenzähl-Steuerung")

        # Feste Layout-Maße. Die gesamte App leitet ihre Breiten aus WINDOW_WIDTH
        # ab (1/5 Sidebar, 4/5 Content; in Tab 2 davon wiederum 3/5 Frame + 1/5
        # Konfig). Das Fenster wird in der Breite NICHT vergrößerbar gemacht,
        # damit keine Komponente die App unbeabsichtigt breiter zieht.
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        # Höhe darf wachsen (Scrollbereiche), Breite bleibt fest.
        self.root.minsize(WINDOW_WIDTH, 500)
        self.root.maxsize(WINDOW_WIDTH, self.root.winfo_screenheight())

        self.input_value = None      # Pfad zur Videodatei, oder "usb"/"rpi"
        self.process = None          # subprocess.Popen von core.py, solange die Pipeline läuft
        self.lora_process = None     # subprocess.Popen von lora_send_loop.py (nur wenn LoRa aktiv)
        self.output_queue = queue.Queue()

        # Auto-Config-Datensammlung (Tab 5): Sammeldauer als Zeitlimit.
        self.collection_duration_var = tk.StringVar(value="300")
        # Optionales Zeitlimit für normale Zählläufe (Tab 3). Leer = kein Limit
        # (Standard). Nur setzen, wer einen Lauf bewusst zeitlich begrenzen will.
        self.run_duration_var = tk.StringVar(value="")

        # --- LoRa-Versand (Tab 3) ---
        # An/aus, Sende-Intervall (Minuten, Pause nach erfolgreichem Uplink)
        # und Sensor-ID (Byte 1 der Nachricht). Wird beim Start als eigener
        # Subprozess (lora_send_loop.py --live-counts) mitgestartet.
        # --- Mitschnitt (Tab 3) ---
        # Zeichnet parallel zum Zähllauf ein Video mit eingebrannter Uhrzeit
        # auf, um die Zählergebnisse hinterher am Bildmaterial zu prüfen.
        # Wird core.py über Umgebungsvariablen mitgegeben (siehe config.py).
        self.recording_enabled_var = tk.BooleanVar(value=False)
        self.recording_dir_var = tk.StringVar(value="auto")
        self.recording_bitrate_var = tk.StringVar(value="2000")
        self.recording_fps_var = tk.StringVar(value="15")
        self.recording_segment_var = tk.StringVar(value="600")

        self.lora_enabled_var = tk.BooleanVar(value=False)
        self.lora_interval_var = tk.StringVar(value="5")
        self.lora_sensor_id_var = tk.StringVar(value="1")

        # --- Sidebar links (1/5 der Fensterbreite) ---
        self.sidebar = ctk.CTkFrame(root, width=SIDEBAR_WIDTH, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(self.sidebar, text="Personenzählung",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(padx=20, pady=(25, 30), anchor="w")

        self.nav_buttons = {}
        for name in PAGE_NAMES:
            btn = ctk.CTkButton(
                self.sidebar, text=name, anchor="w", corner_radius=6,
                fg_color="transparent", text_color=("gray10", "gray90"),
                hover_color=("gray80", "gray28"),
                command=lambda n=name: self._show_page(n),
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[name] = btn

        # --- Inhaltsbereich rechts (4/5 der Fensterbreite, feste Breite) ---
        self.content = ctk.CTkFrame(root, width=CONTENT_WIDTH, corner_radius=0, fg_color="transparent")
        self.content.pack(side="right", fill="both", expand=True)
        self.content.pack_propagate(False)

        self.page_frames = {name: ctk.CTkFrame(self.content, fg_color="transparent") for name in PAGE_NAMES}

        self._build_input_tab()
        self._build_config_tab()
        self._build_start_tab()
        self._build_output_tab()
        self._build_autoconfig_tab()

        self._show_page(PAGE_NAMES[0])

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._poll_output()

    def _show_page(self, name):
        for frame in self.page_frames.values():
            frame.pack_forget()
        self.page_frames[name].pack(fill="both", expand=True, padx=15, pady=15)
        for n, btn in self.nav_buttons.items():
            is_active = (n == name)
            btn.configure(fg_color=("gray75", "gray25") if is_active else "transparent")

        # Seite nach dem Einblenden einmal komplett neu zeichnen lassen.
        #
        # Hintergrund: alle fünf Seiten werden im __init__ gebaut, aber nur die
        # erste wird sofort gepackt. customtkinter zeichnet seine Widgets auf
        # interne Canvas-Elemente, und diese Zeichenoperation läuft bei einem
        # noch nicht eingeblendeten (unmapped) Widget gegen eine Größe von 1x1.
        # Ergebnis: Flächen bleiben schwarz oder werden nur teilweise gefüllt
        # (abgeschnittene Kopfleiste bei "Optionales Zeitlimit"), bis ein
        # <Enter>- oder <Configure>-Ereignis — also z. B. Mauszeiger drüber —
        # ein Neuzeichnen auslöst. Deshalb hier explizit anstoßen, sobald die
        # Seite tatsächlich sichtbar ist.
        self.root.after(20, lambda: self._redraw_tree(self.page_frames[name]))

    def _redraw_tree(self, widget):
        """Ruft rekursiv das interne Neuzeichnen jedes customtkinter-Widgets auf.

        Vor dem ersten Zeichnen müssen die Geometrie-Berechnungen abgeschlossen
        sein, sonst kennt das Widget seine endgültige Größe noch nicht und der
        Fehler wiederholt sich nur mit anderen Maßen.
        """
        try:
            self.root.update_idletasks()
        except Exception:
            return
        self._redraw_recursive(widget)

    def _redraw_recursive(self, widget):
        draw = getattr(widget, "_draw", None)
        if callable(draw):
            try:
                draw(no_color_updates=False)
            except Exception:
                # Einzelne Widgets dürfen scheitern, ohne den Rest der Seite
                # ungezeichnet zu lassen.
                pass
        try:
            children = widget.winfo_children()
        except Exception:
            return
        for child in children:
            self._redraw_recursive(child)

    # -----------------------------------------------------------------
    # Seite 1: Input
    # -----------------------------------------------------------------
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
        ctk.CTkLabel(frame, textvariable=self.file_path_var, text_color="gray70").pack(anchor="w", padx=10)

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

    # -----------------------------------------------------------------
    # Seite 2: Konfiguration (bettet RoiConfigApp ein)
    # -----------------------------------------------------------------
    def _build_config_tab(self):
        frame = make_scrollable(self.page_frames["2. Konfiguration"])

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", pady=(0, 4))
        ctk.CTkButton(top, text="Frame laden (nutzt Input von Seite 1)",
                      command=self._load_config_frame).pack(side="left")
        self.config_status_var = tk.StringVar(value="Noch kein Frame geladen.")
        ctk.CTkLabel(top, textvariable=self.config_status_var, text_color="gray70").pack(side="left", padx=15)

        # Zweite Zeile: bestehende Konfiguration einlesen und anzeigen. Ohne
        # das laesst sich nur schwer pruefen, was auf dem Geraet tatsaechlich
        # eingestellt ist — man musste die JSON-Datei von Hand oeffnen.
        second = ctk.CTkFrame(frame, fg_color="transparent")
        second.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(second, text="Aktuelle Konfiguration laden",
                      fg_color="gray30", command=self._load_existing_config).pack(side="left")
        self.config_loaded_var = tk.StringVar(value="")
        ctk.CTkLabel(second, textvariable=self.config_loaded_var,
                     text_color="gray70").pack(side="left", padx=15)

        container = ctk.CTkFrame(frame, fg_color="transparent")
        container.pack(fill="both", expand=True)
        # Frame-Anzeigebreite fest an die 3/5-Layoutspalte binden, damit der
        # Canvas das Fenster nicht breiter zieht.
        self.roi_config_widget = RoiConfigApp(container, frame_width=CONFIG_FRAME_WIDTH)

    def _load_existing_config(self):
        """
        Liest roi_config.json und stellt sie in Tab 2 dar — Modus, Geometrie,
        Klassen, Richtung, IN-Feld. Damit ist auf einen Blick sichtbar, womit
        das Geraet gerade tatsaechlich zaehlt.
        """
        ok = self.roi_config_widget.load_config()
        if ok:
            self.config_loaded_var.set(f"Geladen aus {ROI_CONFIG_PATH}")
        else:
            self.config_loaded_var.set("Nicht geladen — siehe Meldung.")

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

    # -----------------------------------------------------------------
    # Seite 3: Start/Stop der Pipeline
    # -----------------------------------------------------------------
    def _build_start_tab(self):
        frame = make_scrollable(self.page_frames["3. Start"])
        ctk.CTkLabel(frame, text="Pipeline starten / stoppen", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", pady=(5, 15))

        # --- Mitschnitt (Benchmark) — bewusst ganz oben, weil die Entscheidung
        # "wird dieser Lauf aufgezeichnet?" vor allen anderen Optionen steht.
        rec_frame = ctk.CTkFrame(frame, corner_radius=8)
        rec_frame.pack(anchor="w", fill="x", pady=(0, 12))
        ctk.CTkCheckBox(
            rec_frame, text="Video mitschneiden (Benchmark / Laborlauf)",
            variable=self.recording_enabled_var, command=self._on_recording_toggle,
            font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            rec_frame,
            text="Nur für Benchmark-/Laborläufe. Im Normalbetrieb werden keine "
                 "Bilddaten gespeichert (Privacy by Design) — diese Option "
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

        # Zeigt freien Speicher und geschätzte Reichweite — die eigentliche
        # Frage bei einem Laborlauf ist "wie lange reicht der Platz?".
        self.recording_info_var = tk.StringVar(value="")
        ctk.CTkLabel(rec_frame, textvariable=self.recording_info_var,
                     text_color="gray70", wraplength=560, justify="left").pack(
            anchor="w", padx=12, pady=(6, 10))

        for var in (self.recording_dir_var, self.recording_bitrate_var):
            var.trace_add("write", lambda *_: self._refresh_recording_info())

        self.use_frame_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(frame, text="Live-Vorschau anzeigen (--use-frame)",
                        variable=self.use_frame_var).pack(anchor="w", padx=10, pady=(0, 4))
        ctk.CTkLabel(
            frame,
            text="Hinweis: Die Live-Vorschau kann bei sehr langen Läufen instabil "
                 "werden. Für Dauerläufe die Vorschau deaktiviert lassen.",
            text_color="gray60", wraplength=560, justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 12))

        # --- LoRa-Versand -------------------------------------------------
        # Zwischen Live-Vorschau und Zeitlimit: optionaler Versand der
        # Zählerstände über den LA66-LoRa-Adapter. Läuft als eigener
        # Subprozess (lora_send_loop.py --live-counts), der die von core.py
        # geschriebene zaehlung.csv liest — die Zähl-Pipeline selbst bleibt
        # davon unberührt (bewusst entkoppelt, siehe HANDOFF.md/ToDo.md).
        lora_frame = ctk.CTkFrame(frame, corner_radius=8)
        lora_frame.pack(anchor="w", fill="x", pady=(0, 15))
        ctk.CTkCheckBox(
            lora_frame, text="Daten per LoRa senden (LA66)",
            variable=self.lora_enabled_var, command=self._on_lora_toggle,
            font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        lora_row = ctk.CTkFrame(lora_frame, fg_color="transparent")
        lora_row.pack(anchor="w", padx=12, pady=(0, 6))
        ctk.CTkLabel(lora_row, text="Sende-Intervall (Minuten):").pack(side="left")
        self.lora_interval_entry = ctk.CTkEntry(
            lora_row, textvariable=self.lora_interval_var, width=60)
        self.lora_interval_entry.pack(side="left", padx=(5, 20))
        ctk.CTkLabel(lora_row, text="Sensor-ID:").pack(side="left")
        self.lora_sensor_entry = ctk.CTkEntry(
            lora_row, textvariable=self.lora_sensor_id_var, width=60)
        self.lora_sensor_entry.pack(side="left", padx=5)

        # Hinweis mit der Struktur der Nachricht — richtet sich nach der
        # Konfiguration (roi_config.json). Monospace, damit die Byte-Tabelle
        # ausgerichtet bleibt.
        #
        # Bewusst eine CTkTextbox statt eines CTkLabel: das Label war breiter
        # als die scrollbare Seite, wurde deshalb rechts abgeschnitten
        # ("Inaktive Klassen belegen il...") und hat das Layout der
        # nachfolgenden Abschnitte zerschossen. Eine Textbox hat eine feste
        # Größe, scrollt ihren Inhalt selbst (waagerecht dank wrap="none") und
        # lässt den Rest der Seite dadurch in Ruhe. read-only über state.
        self.lora_hint_box = ctk.CTkTextbox(
            lora_frame, height=LORA_HINT_HEIGHT_OFF, wrap="none", activate_scrollbars=True,
            text_color="gray70", font=ctk.CTkFont(family="Courier", size=11))
        self.lora_hint_box.pack(anchor="w", fill="x", padx=12, pady=(4, 4))
        self.lora_hint_box.configure(state="disabled")
        ctk.CTkButton(
            lora_frame, text="Struktur aus Konfiguration aktualisieren",
            command=self._refresh_lora_hint, width=280, height=26,
            fg_color="transparent", border_width=1).pack(anchor="w", padx=12, pady=(0, 10))

        # Hint aktualisiert sich mit, wenn Intervall/Sensor-ID geändert werden.
        self.lora_interval_var.trace_add("write", lambda *_: self._refresh_lora_hint())
        self.lora_sensor_id_var.trace_add("write", lambda *_: self._refresh_lora_hint())
        self._on_lora_toggle()   # setzt Feld-Zustände + baut den Hint einmal auf
        self._on_recording_toggle()   # setzt Feld-Zustände des Mitschnitts

        # Optionales Zeitlimit für den normalen Zähllauf. Leer = kein Limit.
        # (Das automatische Stoppen nach fester Zeit war früher an die
        # Auto-Config-Datensammlung gekoppelt und lief versehentlich auch bei
        # normalen Läufen — das ist jetzt entkoppelt: normale Läufe laufen ohne
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
                 "im Terminal (SIGINT) — das ist der einzige Shutdown-Weg, der in "
                 "core.py zuverlässig sauber funktioniert.",
            text_color="gray60", wraplength=500, justify="left",
        ).pack(anchor="w", pady=10)

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
                "kurz warten, bis er im Dateimanager auftaucht — oder den Ordner "
                "von Hand wählen.",
                parent=self.root)

    def _refresh_recording_info(self):
        """Zeigt freien Speicher am Zielort und die geschätzte Aufnahmedauer."""
        if not hasattr(self, "recording_info_var"):
            return
        if not self.recording_enabled_var.get():
            self.recording_info_var.set(
                "Aus. Der Mitschnitt ist nur für Labor-/Benchmarkläufe gedacht — "
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
        # Elternverzeichnis — der Zielordner wird erst von core.py angelegt.
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
                f"{prefix}\n{free:.1f} GB frei — reicht für ca. {hours:.1f} Stunden "
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

    def _on_lora_toggle(self):
        """Aktiviert/deaktiviert die LoRa-Eingabefelder und baut den Hint neu."""
        state = "normal" if self.lora_enabled_var.get() else "disabled"
        # Felder existieren erst nach _build_start_tab — defensiv prüfen.
        if hasattr(self, "lora_interval_entry"):
            self.lora_interval_entry.configure(state=state)
            self.lora_sensor_entry.configure(state=state)
        self._refresh_lora_hint()
        # Die Hinweisbox ändert beim Umschalten ihre Höhe; alles darunter rutscht
        # und muss neu gezeichnet werden (sonst bleiben Restflächen schwarz).
        if hasattr(self, "page_frames"):
            self.root.after(20, lambda: self._redraw_tree(self.page_frames["3. Start"]))

    def _load_roi_config(self):
        """Liest roi_config.json (für den Struktur-Hint). Fällt bei Fehler auf
        eine leere Standardstruktur zurück, ohne die GUI zu stören."""
        try:
            with open(ROI_CONFIG_PATH) as f:
                return json.load(f)
        except (OSError, ValueError):
            return {"mode": "line", "classes": list(lora_message.CANONICAL_CLASSES)}

    def _refresh_lora_hint(self):
        """Baut den Hinweistext mit der Nachrichtenstruktur neu — abhängig von
        der aktuellen Konfiguration, dem gewählten Intervall und der Sensor-ID."""
        if not hasattr(self, "lora_hint_box"):
            return
        if not self.lora_enabled_var.get():
            self._set_lora_hint(
                "LoRa-Versand aus. Aktivieren, um die Nachrichtenstruktur "
                "und das Sende-Intervall zu sehen.", LORA_HINT_HEIGHT_OFF)
            return

        cfg = self._load_roi_config()
        interval = self.lora_interval_var.get().strip()
        interval_display = interval if interval else "?"
        try:
            sensor_id = int(self.lora_sensor_id_var.get().strip() or "0")
        except ValueError:
            sensor_id = 0

        # Aktuelle Zählerstände (falls schon vorhanden) mit anzeigen.
        if cfg.get("mode") == "multi_roi":
            hint = lora_message.describe_multi_roi_structure(
                cfg, interval_minutes=interval_display, sensor_id=sensor_id,
                counts_csv=ZAEHLUNG_CSV)
        else:
            counts_in, counts_out = lora_message.read_counts_from_zaehlung(
                ZAEHLUNG_CSV, cfg.get("classes", []))
            hint = lora_message.describe_structure(
                cfg, interval_minutes=interval_display, sensor_id=sensor_id,
                counts_in=counts_in, counts_out=counts_out)
        self._set_lora_hint(hint, LORA_HINT_HEIGHT_ON)

    def _set_lora_hint(self, text, height):
        """Schreibt Text in die (sonst schreibgeschützte) Hinweis-Textbox und
        passt ihre Höhe an — kurz bei ausgeschaltetem LoRa, hoch genug für die
        vollständige Byte-Tabelle bei eingeschaltetem."""
        box = self.lora_hint_box
        box.configure(state="normal", height=height)
        box.delete("1.0", "end")
        box.insert("1.0", text)
        box.configure(state="disabled")

    def _validate_lora_settings(self):
        """Prüft Intervall und Sensor-ID vor dem Start. Rückgabe: (interval_min,
        sensor_id) oder None bei ungültiger Eingabe (Dialog wurde gezeigt)."""
        interval_raw = self.lora_interval_var.get().strip()
        try:
            interval = int(interval_raw)
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Ungültiges Intervall",
                "Bitte ein Sende-Intervall in ganzen Minuten (> 0) angeben.",
                parent=self.root)
            return None
        if interval < 2:
            # EU868-Duty-Cycle 1 % — unter ~2 min riskiert man Verstöße.
            if not messagebox.askyesno(
                    "Sehr kurzes Intervall",
                    f"Ein Intervall von {interval} min kann den EU868-Duty-Cycle "
                    f"(1 %) verletzen. Trotzdem verwenden?", parent=self.root):
                return None
        try:
            sensor_id = int(self.lora_sensor_id_var.get().strip())
            if not (0 <= sensor_id <= 255):
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Ungültige Sensor-ID",
                "Die Sensor-ID muss eine ganze Zahl zwischen 0 und 255 sein.",
                parent=self.root)
            return None
        return interval, sensor_id

    def _start_lora_sender(self, interval_min, sensor_id):
        """Startet lora_send_loop.py --live-counts als eigenen Subprozess.
        Dessen Ausgabe wird (mit Präfix) in dasselbe Live-Log geleitet."""
        cmd = [
            sys.executable, "lora_send_loop.py", "--live-counts",
            "--pause", str(interval_min),
            "--sensor-id", str(sensor_id),
            "--config", ROI_CONFIG_PATH,
            "--counts-csv", ZAEHLUNG_CSV,
            # Wird nur aufgerufen, nachdem core.py erfolgreich gestartet ist —
            # setzt die Status-Bits für Kamera/Hailo im Frame (Byte 4).
            "--pipeline-ok",
        ]
        try:
            self.lora_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
        except Exception as e:
            # LoRa-Fehler darf den Zähllauf nicht abbrechen — nur melden.
            self.output_queue.put(f"[LoRa] Start fehlgeschlagen: {e}\n")
            self.lora_process = None
            return
        threading.Thread(target=self._read_lora_output, daemon=True).start()
        self.output_queue.put(
            f"[LoRa] Sender gestartet (Intervall {interval_min} min, "
            f"Sensor-ID {sensor_id}).\n")

    def _read_lora_output(self):
        for line in self.lora_process.stdout:
            self.output_queue.put(f"[LoRa] {line}")
        self.output_queue.put("__LORA_ENDED__")

    def _stop_lora_sender(self):
        """Beendet den LoRa-Subprozess (SIGINT, wie Strg-C), falls er läuft."""
        if self.lora_process is None:
            return
        try:
            self.lora_process.send_signal(signal.SIGINT)
        except Exception:
            pass

    def _start_pipeline(self, collection=False):
        """
        Startet core.py als Subprozess.

        collection=False (Tab 3, normaler Zähllauf): kein Zeitlimit, außer der
          Nutzer trägt in Tab 3 eines ein (run_duration_var). Keine Datensammlung.
        collection=True (Tab 5, Auto-Konfiguration): Datensammlung aktiv, mit der
          in Tab 5 gewählten Sammeldauer als Zeitlimit.
        """
        if not self.input_value:
            messagebox.showwarning("Fehlt noch", "Bitte zuerst auf Seite 1 einen Input auswählen.", parent=self.root)
            return
        if self.process is not None:
            messagebox.showinfo("Läuft bereits", "Die Pipeline läuft schon.", parent=self.root)
            return

        # LoRa nur bei normalen Zählläufen (Tab 3), nicht bei der
        # Auto-Config-Datensammlung. Vor dem Start prüfen, damit nicht erst
        # core.py läuft und dann die LoRa-Eingabe scheitert.
        lora_settings = None
        if not collection and self.lora_enabled_var.get():
            lora_settings = self._validate_lora_settings()
            if lora_settings is None:
                return

        # Mitschnitt ebenfalls nur bei normalen Zählläufen (Tab 3). Bei der
        # Auto-Config-Datensammlung wäre er nutzlos und würde nur CPU kosten.
        recording_settings = None
        if not collection and self.recording_enabled_var.get():
            recording_settings = self._validate_recording_settings()
            if recording_settings is None:
                return

        cmd = [sys.executable, "core.py", "--input", self.input_value]
        env = os.environ.copy()

        if collection:
            # Auto-Config-Datensammlung: aktiviert das Punkte-Sammeln und nutzt
            # die Sammeldauer als Zeitlimit. Live-Vorschau bewusst AUS (stabiler
            # bei längeren Sammelläufen).
            env["AUTO_CONFIG_COLLECTION_ENABLED"] = "true"
            duration = self.collection_duration_var.get().strip()
            if duration:
                env["RUN_DURATION_SECONDS"] = duration
            self.collection_hint_var.set(
                f"⚠ Datensammlung AKTIV (Sammeldauer: {duration or 'unbegrenzt'}s). "
                f"Danach in Tab 2 auswerten (Clustering / Randraster).")
        else:
            # Normaler Zähllauf: KEIN Zeitlimit, außer der Nutzer trägt in Tab 3
            # ausdrücklich eines ein. Keine Datensammlung.
            if self.use_frame_var.get():
                cmd.append("--use-frame")
            run_duration = self.run_duration_var.get().strip()
            if run_duration:
                env["RUN_DURATION_SECONDS"] = run_duration
            self.collection_hint_var.set("")

            if recording_settings is not None:
                env["RECORDING_ENABLED"] = "true"
                env["RECORDING_DIR"] = recording_settings["dir"]
                env["RECORDING_BITRATE_KBPS"] = str(recording_settings["bitrate"])
                env["RECORDING_FPS"] = str(recording_settings["fps"])
                env["RECORDING_SEGMENT_SECONDS"] = str(recording_settings["segment"])
                self.collection_hint_var.set(
                    "● Mitschnitt AKTIV — der genaue Zielordner und die Reichweite "
                    "stehen in der Ausgabe auf Seite 4.")

        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, env=env,
            )
        except Exception as e:
            messagebox.showerror("Fehler beim Starten", str(e), parent=self.root)
            self.process = None
            return

        threading.Thread(target=self._read_process_output, daemon=True).start()

        # LoRa-Sender als zweiten Subprozess mitstarten (liest die von core.py
        # geschriebene zaehlung.csv). Erst NACH erfolgreichem core-Start, damit
        # nicht gesendet wird, wenn die Zählung gar nicht läuft.
        if lora_settings is not None:
            interval_min, sensor_id = lora_settings
            self._start_lora_sender(interval_min, sensor_id)

        self.pipeline_status_var.set(f"Status: läuft (PID {self.process.pid})")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        if collection:
            self.autoconfig_start_button.configure(state="disabled")
            self.autoconfig_stop_button.configure(state="normal")
        self._show_page("4. Live-Auswertung")

    def _read_process_output(self):
        for line in self.process.stdout:
            self.output_queue.put(line)
        self.output_queue.put("__PROCESS_ENDED__")

    def _stop_pipeline(self):
        if self.process is None:
            return
        # LoRa-Sender zuerst beenden — ohne laufende Zählung soll nicht weiter
        # gesendet werden.
        self._stop_lora_sender()
        self.process.send_signal(signal.SIGINT)
        self.pipeline_status_var.set("Status: wird beendet...")
        self.stop_button.configure(state="disabled")
        # Eskalation: Wenn der Prozess nach dem SIGINT nicht innerhalb weniger
        # Sekunden endet (z. B. weil er in nativem Hailo-/GStreamer-Code hängt),
        # hart nachfassen — erst SIGTERM, dann SIGKILL —, damit kein Zombie
        # zurückbleibt, der die PID/den Status blockiert.
        self.root.after(4000, self._escalate_stop)

    def _escalate_stop(self):
        if self.process is None:
            return
        if self.process.poll() is not None:
            return  # sauber beendet, nichts zu tun
        print("SIGINT wirkungslos — sende SIGTERM.")
        try:
            self.process.terminate()
        except Exception:
            pass
        self.root.after(3000, self._force_kill)

    def _force_kill(self):
        if self.process is None:
            return
        if self.process.poll() is not None:
            return
        print("SIGTERM wirkungslos — sende SIGKILL.")
        try:
            self.process.kill()
        except Exception:
            pass

    def _on_process_ended(self, exit_code=None):
        # Idempotent: kann sowohl über das stdout-Signal als auch über den
        # Liveness-Check (poll()) ausgelöst werden — der zweite Aufruf darf
        # nichts kaputtmachen.
        if self.process is None:
            return
        self.process = None

        # Falls der LoRa-Sender noch läuft (z. B. weil core.py abgestürzt ist
        # statt regulär gestoppt zu werden), ebenfalls beenden.
        self._stop_lora_sender()

        if exit_code is None or exit_code == 0:
            self.pipeline_status_var.set("Status: gestoppt")
        elif exit_code < 0:
            # Negativer Code = durch Signal beendet (z. B. -2 = SIGINT beim
            # regulären Stopp, -6 = SIGABRT bei nativem terminate()/Crash).
            sig = -exit_code
            if sig == signal.SIGINT:
                self.pipeline_status_var.set("Status: gestoppt")
            else:
                self.pipeline_status_var.set(
                    f"Status: ABGESTÜRZT (Signal {sig}) — siehe Log. "
                    f"Neustart über 'Start' möglich.")
        else:
            self.pipeline_status_var.set(
                f"Status: ABGESTÜRZT (Exit {exit_code}) — siehe Log. "
                f"Neustart über 'Start' möglich.")

        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        # Auch die Auto-Config-Buttons (Tab 5) zurücksetzen, falls der Lauf von
        # dort gestartet wurde.
        if hasattr(self, "autoconfig_start_button"):
            self.autoconfig_start_button.configure(state="normal")
            self.autoconfig_stop_button.configure(state="disabled")

    # -----------------------------------------------------------------
    # Seite 4: Live-Auswertung
    # -----------------------------------------------------------------
    def _build_output_tab(self):
        frame = self.page_frames["4. Live-Auswertung"]

        ctk.CTkLabel(frame, text="Live-Konsolenausgabe", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", pady=(0, 5))
        self.log_text = ctk.CTkTextbox(frame, height=320, fg_color="#151515", text_color="#4CAF50",
                                        font=ctk.CTkFont(family="Courier", size=12))
        self.log_text.pack(fill="both", expand=True, pady=(0, 10))

        ctk.CTkLabel(frame, text=f"Aktuelle Zählerstände (aus {ZAEHLUNG_CSV}, nur echte Übergänge)",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.counts_text = ctk.CTkTextbox(frame, height=140)
        self.counts_text.pack(fill="x")

    # -----------------------------------------------------------------
    # Seite 5: Auto-Konfiguration (Datensammlung)
    # -----------------------------------------------------------------
    def _build_autoconfig_tab(self):
        frame = make_scrollable(self.page_frames["5. Auto-Konfiguration"])

        ctk.CTkLabel(frame, text="Auto-Konfiguration — Datensammlung",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(5, 8))

        ctk.CTkLabel(
            frame,
            text="Sammelt Start- und Endpunkte aller Tracks (statt nur zu zählen), "
                 "als Datengrundlage für die automatische Zählgeometrie. Ablauf:\n"
                 "  1. Hier die Datensammlung mit gewünschter Dauer starten.\n"
                 "  2. Nach Ablauf entsteht auto_config_points.csv.\n"
                 "  3. In Tab 2 das Verfahren (Clustering / Randraster) wählen, "
                 "auswerten und speichern.",
            justify="left", wraplength=580, text_color="gray70",
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
                     text="Dieses Zeitlimit gilt nur für die Datensammlung — "
                          "normale Zählläufe (Tab 3) laufen ohne Limit.",
                     text_color="gray60", wraplength=560, justify="left").pack(
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

    def _poll_output(self):
        try:
            while True:
                line = self.output_queue.get_nowait()
                if line == "__PROCESS_ENDED__":
                    self._on_process_ended()
                elif line == "__LORA_ENDED__":
                    # LoRa-Sender ist beendet (regulär oder Fehler) — Referenz
                    # freigeben, Rest läuft normal weiter.
                    self.lora_process = None
                    self.log_text.insert("end", "[LoRa] Sender beendet.\n")
                    self.log_text.see("end")
                else:
                    self.log_text.insert("end", line)
                    self.log_text.see("end")
        except queue.Empty:
            pass

        # Liveness-Check: Auch wenn KEIN "__PROCESS_ENDED__" über stdout kam
        # (z. B. weil core.py durch einen nativen C++-Fehler hart abgestürzt
        # ist — terminate()/std::system_error —, ohne stdout sauber zu
        # schließen), erkennen wir hier direkt am Prozessstatus, dass er weg
        # ist. Ohne diesen Check bliebe die App auf "läuft (PID …)" hängen und
        # ein Neustart wäre blockiert.
        if self.process is not None:
            exit_code = self.process.poll()
            if exit_code is not None:
                self._on_process_ended(exit_code)

        self._refresh_counts()
        self.root.after(500, self._poll_output)

    def _refresh_counts(self):
        if not os.path.isfile(ZAEHLUNG_CSV):
            return
        try:
            with open(ZAEHLUNG_CSV, newline="") as f:
                rows = list(csv.DictReader(f))
        except (OSError, csv.Error):
            return

        tally = {}
        for row in rows:
            if row.get("is_transition") == "True":
                key = (row.get("label", "?"), row.get("direction", "?"))
                tally[key] = tally.get(key, 0) + 1

        self.counts_text.delete("1.0", "end")
        if not tally:
            self.counts_text.insert("end", "(noch keine Zählungen)")
        for (label, direction), count in sorted(tally.items()):
            self.counts_text.insert("end", f"{label}: {direction}: {count}\n")

    # -----------------------------------------------------------------
    def _on_close(self):
        if self.process is not None:
            if messagebox.askyesno("Beenden", "Die Pipeline läuft noch. Trotzdem beenden?", parent=self.root):
                self._stop_pipeline()
                self.root.after(1000, self.root.destroy)
            return
        self.root.destroy()


def main():
    root = ctk.CTk()
    MainApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
