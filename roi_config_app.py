"""
roi_config_app.py — Visuelles Konfigurationswerkzeug für die Zählgeometrie.
UI-Bibliothek: customtkinter (dunkles Design, siehe app.py für den
Gesamtkontext mit Sidebar-Navigation).

Zeigt einen Frame aus dem Zielvideo (oder ein Standbild) an. Darauf:
  - Zählmodus wählen — alle fünf gleichwertig nebeneinander:
      * Linie (zwei Klicks, Kreuzungstest, IN/OUT)
      * Fläche/ROI (drei oder mehr Klicks, dann "Fläche schließen", IN/OUT
        beim Betreten/Verlassen einer einzelnen Fläche)
      * Mehrere Flächen (mehrere benannte Flächen anlegen, zählt Übergänge
        zwischen ihnen, z. B. "A -> B")
      * Auto: Clustering — Zonen automatisch aus gesammelten Start-/End-
        punkten ableiten (DBSCAN, siehe auto_config_clustering.py)
      * Auto: Randraster — feste Zonen am Bildrand, Punkte werden der
        nächstgelegenen zugeordnet
  - Klassen per Checkbox auswählen (welche Objekte gezählt werden)
  - Richtung (IN/OUT) per Checkbox umkehren, mit Live-Vorschaupfeil
  - Speichern schreibt roi_config.json — bei den Auto-Modi immer als
    mode="multi_roi" (das Laufzeitformat, das core.py versteht)

Nutzung:
    python roi_config_app.py --input videodatei.mp4
    python roi_config_app.py --input standbild.jpg

Voraussetzung: customtkinter (pip install customtkinter --break-system-packages).
Für die Auto-Modi zusätzlich scikit-learn/scipy (siehe auto_config_clustering.py).
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import tkinter as tk
import ctk_dialogs as messagebox   # CustomTkinter-Dialoge, messagebox-kompatible API
import ctk_dialogs as simpledialog # askstring liegt ebenfalls hier

import cv2
import customtkinter as ctk
from PIL import Image, ImageTk

from counting import point_side
from frame_utils import load_frame_from_file
from auto_config import load_collected_points, split_into_batches, POINTS_FILE
from auto_config_clustering import (
    cluster_points, clusters_to_regions, draw_cluster_debug_image,
    generate_border_regions, assign_tracks_to_border, draw_border_debug_image,
)
import config as app_config

CONFIG_PATH = "roi_config.json"
ALL_CLASSES = ["person", "bicycle", "car", "motorcycle", "bus", "truck"]

CAMERA_RAW_PATH = app_config.CAMERA_RAW_PATH
# Grosszuegig bemessen: die Hailo-Pipeline braucht beim ALLERERSTEN Start
# (Modell laden, HEF kompilieren/cachen usw.) oft deutlich laenger als bei
# folgenden Starts, wo vieles schon im Dateisystem-Cache liegt.
SNAPSHOT_TIMEOUT_SECONDS = 120

# Feste Anzeigefläche für den Frame. Der geladene Frame wird IMMER
# seitenverhältnistreu in diese Box skaliert (auch hochskaliert, wenn er
# kleiner ist) und darin zentriert — dadurch bleibt der Canvas unabhängig von
# der Frame-Auflösung konstant groß, das Layout springt beim Laden nicht mehr,
# und die rechte Bedienspalte behält immer ihren Platz.
DISPLAY_WIDTH = 960

# Feste Breite der rechten Bedienspalte. Die Bedienelemente liegen in einem
# eigenen Frame (self.side) — NICHT im selben Grid wie der Canvas. Grund:
# ein Canvas mit rowspan über die Bedienzeilen zwingt Tk, die Canvas-Höhe auf
# diese Zeilen zu verteilen; dabei entstehen die beobachteten Lücken und
# abgeschnittenen Elemente. Getrennte Container = getrennte Höhenrechnung.
SIDE_PANEL_WIDTH = 265
DISPLAY_HEIGHT = 540  # 16:9 zu 960 — kompakter, trifft ~3/5-Breite im Fenster-Layout

# Canvas-Hintergrund passend zum dunklen Theme (statt Tkinter-Standardgrau)
CANVAS_BG = "#242424"
CANVAS_PLACEHOLDER_FG = "#888888"

# Leerer Arbeitsbereich: Wenn kein Frame geladen ist, kann die Geometrie
# trotzdem gesetzt werden — der Canvas zeigt dann eine neutrale Fläche mit
# Hilfsraster statt eines Kamerabildes. Die Koordinaten werden gegen diese
# Referenzauflösung normalisiert; da die Konfiguration ohnehin relativ
# (0.0-1.0) gespeichert wird, passt sie später zu jeder echten Auflösung,
# solange das Seitenverhältnis stimmt (16:9).
BLANK_REFERENCE_WIDTH = 1280
BLANK_REFERENCE_HEIGHT = 720
BLANK_CANVAS_BG = "#F2F2F2"
BLANK_GRID_COLOR = "#D0D0D0"
BLANK_HINT_COLOR = "#909090"

REGION_COLORS = ["#4CAF50", "#29B6F6", "#FFA726", "#EC407A", "#EEEEEE", "#EF5350"]

AUTO_MODES = ("auto_cluster", "auto_border")


def _capture_snapshot_via_core(input_value, timeout=SNAPSHOT_TIMEOUT_SECONDS):
    """
    Nimmt das Referenzbild über core.py im Snapshot-Modus auf (siehe
    config.SNAPSHOT_ONLY) statt über eine eigene, unabhängige
    cv2.VideoCapture()-Aufnahme — garantiert dieselbe Auflösung und
    denselben Bildausschnitt wie später der Live-Betrieb.
    """
    if os.path.isfile(CAMERA_RAW_PATH):
        os.remove(CAMERA_RAW_PATH)

    env = os.environ.copy()
    env["CORE_SNAPSHOT_ONLY"] = "true"
    cmd = [sys.executable, "core.py", "--input", input_value, "--use-frame"]

    print(f"Nehme Referenzbild über core.py auf ({' '.join(cmd)}) — "
          f"das kann beim allerersten Start deutlich länger dauern "
          f"(Hailo-Pipeline muss Modell laden/cachen) ...")

    # subprocess.run(..., timeout=...) wuerde core.py bei Ueberschreitung
    # per SIGKILL abschiessen — keine Chance auf sauberes Herunterfahren
    # (unser finally-Block/GStreamer-Teardown liefe nie). Steckt core.py
    # gerade mitten in der Hailo-Geraete-/Kamera-Initialisierung, kann das
    # die Hardware in einem gesperrten Zustand zuruecklassen, der erst
    # durch einen sauber beendeten Lauf wieder freigegeben wird — genau
    # das Symptom "geht erst nach manuellem core.py-Start". Deshalb hier
    # bewusst zuerst SIGINT (wie Ctrl+C), SIGKILL nur als letzter Ausweg.
    process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.send_signal(signal.SIGINT)
        try:
            stdout, stderr = process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            # Reagiert selbst auf SIGINT nicht -> jetzt wirklich hart beenden
            process.kill()
            stdout, stderr = process.communicate()

        raise ValueError(
            f"core.py hat innerhalb von {timeout}s keinen Snapshot erzeugt "
            f"(wurde danach sauber per SIGINT beendet, damit keine "
            f"Kamera-/Hailo-Sperre zurückbleibt).\n\n"
            f"Bisherige Ausgabe von core.py bis zum Abbruch:\n"
            f"--- stdout ---\n{stdout or '(leer)'}\n"
            f"--- stderr ---\n{stderr or '(leer)'}\n\n"
            f"Falls core.py hier noch mitten in der Initialisierung steckt, "
            f"core.py einmal manuell mit --input {input_value} --use-frame "
            f"starten und mit Ctrl+C sauber beenden — danach ist oft vieles "
            f"im Cache und spätere Starts (auch über dieses Tool) sind "
            f"deutlich schneller."
        )

    if not os.path.isfile(CAMERA_RAW_PATH):
        raise ValueError(
            f"core.py wurde ausgeführt, hat aber keinen Snapshot erzeugt.\n"
            f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}"
        )

    frame = cv2.imread(CAMERA_RAW_PATH)
    if frame is None:
        raise ValueError(f"{CAMERA_RAW_PATH} wurde geschrieben, konnte aber nicht gelesen werden.")
    print(f"Snapshot übernommen: {frame.shape[1]}x{frame.shape[0]}.")
    return frame


def load_first_frame(path):
    """
    Lädt den ersten Frame aus einem Video, direkt ein Bild bei einer
    Bilddatei, oder holt bei path in ("usb", "rpi") ein frisches
    Referenzbild aus der echten Hailo-Pipeline.

    Der datei-basierte Fall (Bild/Video) wird an frame_utils delegiert, das
    GUI-frei ist; der Kamera-Snapshot bleibt hier, weil er core.py als
    Subprozess über die Hailo-Pipeline aufruft.
    """
    if path in ("usb", "rpi"):
        return _capture_snapshot_via_core(path)

    return load_frame_from_file(path)


class RoiConfigApp:
    """
    Baut das UI-Gerüst OHNE Frame — nutzbar sowohl standalone (main() ruft
    sofort load_frame() nach der Konstruktion auf) als auch eingebettet in
    eine Seite von app.py, wo der Frame erst nach Auswahl eines Inputs auf
    einer anderen Seite geladen werden kann.

    master: ein CTk-Root ODER ein CTkFrame/Frame, in das die Bedienelemente
    per grid() platziert werden.
    """

    def __init__(self, master, frame_width=None):
        self.master = master
        self.root = master

        # Anzeigebreite des Frames. Standard DISPLAY_WIDTH (Standalone-Betrieb);
        # app.py übergibt beim Einbetten die feste 3/5-Breite, damit der Canvas
        # exakt in die mittlere Layout-Spalte passt und das Fenster nicht
        # breiter zieht. Höhe seitenverhältnistreu (16:9).
        self.display_width = frame_width if frame_width else DISPLAY_WIDTH
        self.display_height = round(self.display_width * 9 / 16)

        self.points = []
        self.polygon_closed = False
        self.regions = []
        self.current_points = []
        self.auto_regions = None
        self.canvas_items = []

        self.orig_h = None
        self.orig_w = None
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.photo = None
        self.frame_bgr = None

        # --- Linke Seite: Canvas ---
        # Canvas und Bedienspalte liegen in ZWEI getrennten Grid-Zellen der
        # gleichen Zeile. Der Canvas hat bewusst KEIN rowspan mehr (siehe
        # Kommentar bei SIDE_PANEL_WIDTH).
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=0)
        master.grid_columnconfigure(1, weight=0)

        self.canvas = tk.Canvas(master, width=self.display_width, height=self.display_height,
                                 cursor="cross", bg=CANVAS_BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=10, pady=10, sticky="nw")
        self.canvas.bind("<Button-1>", self.on_click)

        # Ohne geladenen Frame direkt den leeren Arbeitsbereich aufziehen,
        # damit sofort konfiguriert werden kann.
        self._setup_blank_workspace()

        # --- Rechte Seite: Bedienelemente in eigenem Container ---
        side = ctk.CTkFrame(master, fg_color="transparent", width=SIDE_PANEL_WIDTH)
        side.grid(row=0, column=1, sticky="nw", pady=10, padx=(0, 10))
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1, minsize=SIDE_PANEL_WIDTH)
        self.side = side

        row = 0
        ctk.CTkLabel(side, text="Zählmodus", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=row, column=0, sticky="w", padx=10, pady=(0, 5))
        row += 1

        self.mode_var = tk.StringVar(value="line")
        mode_options = [
            ("Linie (2 Punkte)", "line"),
            ("Fläche / ROI (3+ Punkte)", "roi"),
            ("Mehrere Flächen (Übergänge)", "multi_roi"),
            ("Auto: Clustering (DBSCAN)", "auto_cluster"),
            ("Auto: Randraster", "auto_border"),
        ]
        for label, value in mode_options:
            ctk.CTkRadioButton(side, text=label, variable=self.mode_var, value=value,
                                command=self.on_mode_change).grid(row=row, column=0, sticky="w", padx=20, pady=2)
            row += 1

        self.close_button = ctk.CTkButton(side, text="Fläche schließen", command=self.close_polygon)
        self.close_button.grid(row=row, column=0, sticky="we", padx=10, pady=(8, 2))
        self.close_button.grid_remove()
        row += 1

        self.undo_button = ctk.CTkButton(side, text="Letzte Fläche löschen", fg_color="gray30",
                                          command=self.undo_last_region)
        self.undo_button.grid(row=row, column=0, sticky="we", padx=10, pady=(0, 5))
        self.undo_button.grid_remove()
        row += 1

        # --- Auto-Konfigurations-Panel ---
        self.auto_frame = ctk.CTkFrame(side, corner_radius=8)
        self.auto_frame.grid(row=row, column=0, sticky="we", padx=10, pady=(5, 5))
        self.auto_frame.grid_remove()
        row += 1

        ctk.CTkLabel(self.auto_frame, text="Auto-Konfiguration", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8, 4))

        self.collection_status_var = tk.StringVar(value="Noch keine Punkte gesammelt.")
        ctk.CTkLabel(self.auto_frame, textvariable=self.collection_status_var,
                     wraplength=210, justify="left", text_color="gray70").grid(
            row=1, column=0, columnspan=2, sticky="w", padx=10)
        ctk.CTkButton(self.auto_frame, text="Sammel-Status aktualisieren", fg_color="gray30",
                      command=self._refresh_collection_status).grid(
            row=2, column=0, columnspan=2, sticky="we", padx=10, pady=(4, 8))

        self.cluster_params_frame = ctk.CTkFrame(self.auto_frame, fg_color="transparent")
        ctk.CTkLabel(self.cluster_params_frame, text="eps (Pixel):").grid(row=0, column=0, sticky="w")
        self.eps_var = tk.StringVar(value=str(app_config.AUTO_CONFIG_DBSCAN_EPS_PIXELS))
        ctk.CTkEntry(self.cluster_params_frame, textvariable=self.eps_var, width=70).grid(row=0, column=1, padx=5)
        ctk.CTkLabel(self.cluster_params_frame, text="min_samples:").grid(row=1, column=0, sticky="w", pady=(3, 0))
        self.min_samples_var = tk.StringVar(value=str(app_config.AUTO_CONFIG_DBSCAN_MIN_SAMPLES))
        ctk.CTkEntry(self.cluster_params_frame, textvariable=self.min_samples_var, width=70).grid(
            row=1, column=1, padx=5, pady=(3, 0))

        self.border_params_frame = ctk.CTkFrame(self.auto_frame, fg_color="transparent")
        ctk.CTkLabel(self.border_params_frame, text="Segmente je Kante:").grid(row=0, column=0, sticky="w")
        self.segments_var = tk.StringVar(value=str(app_config.AUTO_CONFIG_BORDER_SEGMENTS_PER_EDGE))
        ctk.CTkEntry(self.border_params_frame, textvariable=self.segments_var, width=70).grid(row=0, column=1, padx=5)
        ctk.CTkLabel(self.border_params_frame, text="Randtiefe (0-1):").grid(row=1, column=0, sticky="w", pady=(3, 0))
        self.depth_var = tk.StringVar(value=str(app_config.AUTO_CONFIG_BORDER_DEPTH_RATIO))
        ctk.CTkEntry(self.border_params_frame, textvariable=self.depth_var, width=70).grid(
            row=1, column=1, padx=5, pady=(3, 0))
        ctk.CTkLabel(self.border_params_frame, text="Mindestbewegung (px):").grid(row=2, column=0, sticky="w", pady=(3, 0))
        self.min_dist_var = tk.StringVar(value=str(app_config.AUTO_CONFIG_MIN_TRACK_DISTANCE_PIXELS))
        ctk.CTkEntry(self.border_params_frame, textvariable=self.min_dist_var, width=70).grid(
            row=2, column=1, padx=5, pady=(3, 0))

        ctk.CTkButton(self.auto_frame, text="Auswerten", command=self._run_auto_evaluation).grid(
            row=4, column=0, columnspan=2, sticky="we", padx=10, pady=(8, 4))

        self.auto_result_var = tk.StringVar(value="")
        ctk.CTkLabel(self.auto_frame, textvariable=self.auto_result_var, text_color="gray70",
                     wraplength=210, justify="left").grid(row=5, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 8))

        ctk.CTkLabel(side, text="Klassen zählen", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=row, column=0, sticky="w", padx=10, pady=(15, 5))
        row += 1

        self.class_vars = {}
        for cls in ALL_CLASSES:
            var = tk.BooleanVar(value=True)
            ctk.CTkCheckBox(side, text=cls, variable=var).grid(row=row, column=0, sticky="w", padx=20, pady=2)
            self.class_vars[cls] = var
            row += 1

        self.reverse_var = tk.BooleanVar(value=False)
        self.reverse_check = ctk.CTkCheckBox(
            side, text="Richtung umkehren (IN/OUT tauschen)",
            variable=self.reverse_var, command=self.redraw,
        )
        self.reverse_check.grid(row=row, column=0, sticky="w", padx=10, pady=(15, 0))
        row += 1

        self.snap_var = tk.BooleanVar(value=False)
        self.snap_check = ctk.CTkCheckBox(
            side, text="Punkte ohne Treffer der nächsten\nFläche zuordnen (statt 'außerhalb')",
            variable=self.snap_var,
        )
        self.snap_check.grid(row=row, column=0, sticky="w", padx=10, pady=(5, 0))
        self.snap_check.grid_remove()
        row += 1

        # IN-Feld-Auswahl (nur multi_roi): bestimmt, welche Fläche als
        # "IN-Bereich" gilt. Übergang in dieses Feld = IN, heraus = OUT — damit
        # passt multi_roi in dasselbe IN/OUT-Nachrichtenformat wie Linie/ROI
        # (für den LoRa-Versand). Wird aus den benannten Flächen befüllt.
        self.in_field_placeholder = "(kein Feld gewählt)"
        self.in_field_var = tk.StringVar(value=self.in_field_placeholder)
        self.in_field_label = ctk.CTkLabel(
            side, text="IN-Feld (rein = IN, raus = OUT):")
        self.in_field_label.grid(row=row, column=0, sticky="w", padx=10, pady=(12, 0))
        row += 1
        self.in_field_menu = ctk.CTkOptionMenu(
            side, variable=self.in_field_var, values=[self.in_field_placeholder])
        self.in_field_menu.grid(row=row, column=0, sticky="we", padx=10, pady=(2, 0))
        self.in_field_label.grid_remove()
        self.in_field_menu.grid_remove()
        row += 1

        ctk.CTkButton(side, text="Zurücksetzen", fg_color="gray30", command=self.reset_geometry).grid(
            row=row, column=0, sticky="we", padx=10, pady=(15, 5))
        row += 1
        ctk.CTkButton(
            side, text="Speichern", fg_color="#2E8B57", hover_color="#256e46",
            font=ctk.CTkFont(weight="bold"), command=self.save,
        ).grid(row=row, column=0, sticky="we", padx=10, pady=5)
        row += 1

        self.status_var = tk.StringVar()
        ctk.CTkLabel(side, textvariable=self.status_var, wraplength=SIDE_PANEL_WIDTH - 30,
                     text_color="gray70", justify="left").grid(
            row=row, column=0, sticky="w", padx=10, pady=10)

        # Höhe der Bedienspalte einmal nach dem Aufbau an den tatsächlichen
        # Bedarf anpassen (grid_propagate ist aus, damit die Breite fix bleibt).
        side.after(60, self._fit_side_height)

        self._update_status_for_mode()

    def _fit_side_height(self):
        """
        Passt die Höhe der Bedienspalte an ihren tatsächlichen Bedarf an.

        grid_propagate(False) hält die BREITE fest (sonst zieht ein langer
        Hinweistext die Spalte auseinander); die HÖHE muss dann aber von Hand
        gesetzt werden, sonst werden untere Elemente wie 'Speichern'
        abgeschnitten. Wird nach jedem Moduswechsel erneut aufgerufen, weil
        ein-/ausgeblendete Elemente den Bedarf ändern.
        """
        try:
            self.side.update_idletasks()
            bbox = self.side.grid_bbox()
            needed = bbox[3] if bbox else 0
            self.side.configure(height=max(needed + 12, 200))
        except Exception:
            pass

    def load_frame(self, frame_bgr):
        self.frame_bgr = frame_bgr
        self.orig_h, self.orig_w = frame_bgr.shape[:2]

        # Seitenverhältnistreu in die feste Anzeigebox einpassen (auch
        # hochskalieren, wenn der Frame kleiner ist).
        self.scale = min(self.display_width / self.orig_w, self.display_height / self.orig_h)
        disp_w, disp_h = int(self.orig_w * self.scale), int(self.orig_h * self.scale)

        # Bild in der festen Box zentrieren; der Rand ist der Offset, um den
        # Klickkoordinaten korrigiert werden müssen (siehe _to_normalized).
        self.offset_x = (self.display_width - disp_w) // 2
        self.offset_y = (self.display_height - disp_h) // 2

        # Canvas-Größe bleibt fix — NICHT mehr an den Frame anpassen.
        self.canvas.config(width=self.display_width, height=self.display_height)

        self._display_image_on_canvas(frame_bgr)
        self.reset_geometry()

    def _setup_blank_workspace(self):
        """
        Bereitet das Konfigurieren OHNE Kamerabild vor.

        Setzt Skalierung und Offsets so, dass der gesamte Canvas der
        Referenzauflösung (BLANK_REFERENCE_*) entspricht. Dadurch liefert
        _to_normalized() auch ohne Frame gültige 0.0-1.0-Koordinaten, und
        Klicks/Speichern funktionieren wie gewohnt.
        """
        self.frame_bgr = None
        self.orig_w = BLANK_REFERENCE_WIDTH
        self.orig_h = BLANK_REFERENCE_HEIGHT
        self.scale = min(self.display_width / self.orig_w,
                         self.display_height / self.orig_h)
        disp_w = int(self.orig_w * self.scale)
        disp_h = int(self.orig_h * self.scale)
        self.offset_x = (self.display_width - disp_w) // 2
        self.offset_y = (self.display_height - disp_h) // 2
        self._draw_blank_canvas()

    def _draw_blank_canvas(self):
        """Zeichnet die neutrale Arbeitsfläche mit Hilfsraster und Hinweis."""
        self.canvas.delete("all")
        self.canvas_items = []

        disp_w = int(self.orig_w * self.scale)
        disp_h = int(self.orig_h * self.scale)
        x0, y0 = self.offset_x, self.offset_y
        x1, y1 = x0 + disp_w, y0 + disp_h

        self.canvas.create_rectangle(x0, y0, x1, y1, fill=BLANK_CANVAS_BG,
                                     outline=BLANK_GRID_COLOR, tags=("blank",))

        # Zehntel-Raster als Orientierungshilfe — ohne Bild fehlen sonst
        # jegliche Anhaltspunkte, wo im Bildausschnitt man klickt.
        for i in range(1, 10):
            gx = x0 + disp_w * i / 10
            gy = y0 + disp_h * i / 10
            width = 2 if i == 5 else 1
            self.canvas.create_line(gx, y0, gx, y1, fill=BLANK_GRID_COLOR,
                                    width=width, tags=("blank",))
            self.canvas.create_line(x0, gy, x1, gy, fill=BLANK_GRID_COLOR,
                                    width=width, tags=("blank",))

        self.canvas.create_text(
            (x0 + x1) // 2, y0 + 22,
            text="Ohne Kamerabild — Koordinaten relativ zum Bildausschnitt "
                 f"({self.orig_w}x{self.orig_h} Referenz, 16:9)",
            fill=BLANK_HINT_COLOR, font=("Arial", 10), tags=("blank",))
        self.canvas.create_text(
            (x0 + x1) // 2, y1 - 22,
            text="'Frame laden' oben zeigt stattdessen das echte Kamerabild.",
            fill=BLANK_HINT_COLOR, font=("Arial", 10), tags=("blank",))

    def _redraw_background(self):
        """Hintergrund neu zeichnen — Kamerabild, falls vorhanden, sonst die
        leere Arbeitsfläche."""
        if self.frame_bgr is not None:
            self._display_image_on_canvas(self.frame_bgr)
        else:
            self._draw_blank_canvas()

    def _display_image_on_canvas(self, img_bgr):
        disp_w, disp_h = int(self.orig_w * self.scale), int(self.orig_h * self.scale)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (disp_w, disp_h))
        self.photo = ImageTk.PhotoImage(Image.fromarray(img_resized))

        self.canvas.delete("all")
        self.canvas_items = []
        # Am Zentrier-Offset platzieren, damit das Bild mittig in der festen
        # Box sitzt (statt oben links).
        self.canvas.create_image(self.offset_x, self.offset_y, anchor="nw", image=self.photo)

    # --- Modus- und Klick-Handling ---

    def on_mode_change(self):
        self.reset_geometry()
        mode = self.mode_var.get()
        # Nach dem Umschalten die Spaltenhöhe neu bestimmen (verzögert, damit
        # Tk die ein-/ausgeblendeten Elemente schon eingerechnet hat).
        self.side.after(30, self._fit_side_height)

        # IN-Feld-Auswahl nur im manuellen multi_roi-Modus zeigen.
        if mode == "multi_roi":
            self.in_field_label.grid()
            self.in_field_menu.grid()
            self._refresh_in_field_options()
        else:
            self.in_field_label.grid_remove()
            self.in_field_menu.grid_remove()

        if mode == "roi":
            self.close_button.grid()
            self.undo_button.grid_remove()
            self.reverse_check.grid()
            self.snap_check.grid_remove()
            self.auto_frame.grid_remove()
        elif mode == "multi_roi":
            self.close_button.grid()
            self.undo_button.grid()
            self.reverse_check.grid_remove()
            self.snap_check.grid()
            self.auto_frame.grid_remove()
        elif mode in AUTO_MODES:
            self.close_button.grid_remove()
            self.undo_button.grid_remove()
            self.reverse_check.grid_remove()
            self.snap_check.grid_remove()
            self.auto_frame.grid()
            if mode == "auto_cluster":
                self.border_params_frame.grid_remove()
                self.cluster_params_frame.grid(row=3, column=0, columnspan=2, sticky="w", padx=10)
            else:
                self.cluster_params_frame.grid_remove()
                self.border_params_frame.grid(row=3, column=0, columnspan=2, sticky="w", padx=10)
            self._refresh_collection_status()
        else:  # line
            self.close_button.grid_remove()
            self.undo_button.grid_remove()
            self.reverse_check.grid()
            self.snap_check.grid_remove()
            self.auto_frame.grid_remove()

    def _update_status_for_mode(self):
        mode = self.mode_var.get()
        blank = " (ohne Kamerabild — Raster als Orientierung)" if self.frame_bgr is None else ""
        if mode == "line":
            self.status_var.set(
                "Klicke zwei Punkte, um die Zähllinie zu setzen." + blank)
        elif mode == "roi":
            self.status_var.set(
                "Klicke mindestens drei Punkte, dann 'Fläche schließen'." + blank)
        elif mode == "multi_roi":
            self.status_var.set(
                "Klicke mindestens drei Punkte für die erste Fläche, dann "
                "'Fläche schließen' und einen Namen vergeben. Danach die "
                "nächste Fläche klicken. Mindestens zwei Flächen nötig." + blank
            )
        else:
            self.status_var.set(
                "Kein manuelles Klicken nötig. Erst core.py mit aktivierter "
                "Datensammlung laufen lassen, dann links 'Auswerten' klicken."
            )

    def on_click(self, event):
        if self.orig_w is None:
            return

        mode = self.mode_var.get()
        if mode in AUTO_MODES:
            return

        if mode == "line":
            if len(self.points) >= 2:
                self.reset_geometry()
            self.points.append((event.x, event.y))
            self.redraw()
            if len(self.points) == 1:
                self.status_var.set("Ersten Punkt gesetzt. Klicke den zweiten Punkt.")
            else:
                self.status_var.set("Linie gesetzt. Bei Bedarf Richtung umkehren, dann Speichern.")

        elif mode == "roi":
            if self.polygon_closed:
                return
            self.points.append((event.x, event.y))
            self.redraw()
            self.status_var.set(
                f"{len(self.points)} Punkt(e) gesetzt. Weiter klicken oder "
                f"'Fläche schließen' (mindestens 3 Punkte nötig)."
            )

        else:  # multi_roi
            self.current_points.append((event.x, event.y))
            self.redraw()
            self.status_var.set(
                f"{len(self.current_points)} Punkt(e) für die aktuelle Fläche. "
                f"'Fläche schließen', wenn fertig (mindestens 3 Punkte)."
            )

    def close_polygon(self):
        mode = self.mode_var.get()

        if mode == "roi":
            if len(self.points) < 3:
                messagebox.showwarning("Fehlt noch", "Bitte mindestens 3 Punkte für die Fläche setzen.", parent=self.root)
                return
            self.polygon_closed = True
            self.redraw()
            self.status_var.set("Fläche geschlossen. Bei Bedarf zurücksetzen, sonst Speichern.")

        elif mode == "multi_roi":
            if len(self.current_points) < 3:
                messagebox.showwarning("Fehlt noch", "Bitte mindestens 3 Punkte für die Fläche setzen.", parent=self.root)
                return
            name = simpledialog.askstring(
                "Name der Fläche", "Wie soll diese Fläche heißen?", parent=self.root)
            if not name:
                return
            if any(r["name"] == name for r in self.regions):
                messagebox.showwarning("Name vergeben", f"Der Name '{name}' wird schon verwendet.", parent=self.root)
                return
            self.regions.append({"name": name, "points": list(self.current_points)})
            self.current_points = []
            self.redraw()
            self._refresh_in_field_options()
            self.status_var.set(
                f"Fläche '{name}' gespeichert ({len(self.regions)} insgesamt). "
                f"Weitere Fläche klicken oder Speichern (mind. 2 Flächen nötig)."
            )

    def _refresh_in_field_options(self):
        """Befüllt das IN-Feld-Menü mit den aktuellen Flächennamen. Behält die
        bisherige Auswahl bei, wenn die Fläche noch existiert."""
        if not hasattr(self, "in_field_menu"):
            return
        names = [r["name"] for r in self.regions]
        values = names if names else [self.in_field_placeholder]
        self.in_field_menu.configure(values=values)
        if self.in_field_var.get() not in values:
            self.in_field_var.set(values[0])

    def undo_last_region(self):
        if self.regions:
            removed = self.regions.pop()
            self.redraw()
            self._refresh_in_field_options()
            self.status_var.set(f"Fläche '{removed['name']}' entfernt.")

    def reset_geometry(self):
        self.points = []
        self.polygon_closed = False
        self.regions = []
        self.current_points = []
        self.auto_regions = None
        self._redraw_background()
        self.redraw()
        self._refresh_in_field_options()
        self._update_status_for_mode()

    # --- Zeichnen ---

    def redraw(self):
        for item_id in self.canvas_items:
            self.canvas.delete(item_id)
        self.canvas_items = []

        mode = self.mode_var.get()

        if mode in AUTO_MODES:
            return

        if mode == "multi_roi":
            for i, region in enumerate(self.regions):
                color = REGION_COLORS[i % len(REGION_COLORS)]
                self._draw_named_polygon(region["points"], region["name"], color=color, closed=True)
            for (x, y) in self.current_points:
                oid = self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill="#FFD54F", outline="black")
                self.canvas_items.append(oid)
            if len(self.current_points) >= 2:
                self._draw_named_polygon(self.current_points, None, color="#FFD54F", closed=False)
            return

        for (x, y) in self.points:
            oid = self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill="#FFD54F", outline="black")
            self.canvas_items.append(oid)

        if mode == "line" and len(self.points) == 2:
            self._draw_line_and_arrow()
        elif mode == "roi" and len(self.points) >= 2:
            self._draw_named_polygon(self.points, "Fläche\n(innen = IN)" if self.polygon_closed else None,
                                      color="#FFD54F", closed=self.polygon_closed)

    def _draw_line_and_arrow(self):
        (ax, ay), (bx, by) = self.points
        lid = self.canvas.create_line(ax, ay, bx, by, fill="#FFD54F", width=3)
        self.canvas_items.append(lid)

        mid = ((ax + bx) / 2, (ay + by) / 2)
        dx, dy = bx - ax, by - ay
        length = max((dx ** 2 + dy ** 2) ** 0.5, 1e-6)
        perp = (-dy / length, dx / length)

        test_point = (mid[0] + perp[0], mid[1] + perp[1])
        perp_is_positive_side = point_side((ax, ay), (bx, by), test_point) > 0
        in_is_positive_side = not self.reverse_var.get()

        if perp_is_positive_side == in_is_positive_side:
            direction_perp = perp
        else:
            direction_perp = (-perp[0], -perp[1])

        arrow_len = 50
        tip = (mid[0] + direction_perp[0] * arrow_len, mid[1] + direction_perp[1] * arrow_len)
        aid = self.canvas.create_line(mid[0], mid[1], tip[0], tip[1],
                                       fill="#4CAF50", width=3, arrow=tk.LAST)
        self.canvas_items.append(aid)
        tid = self.canvas.create_text(tip[0], tip[1] - 12, text="IN", fill="#4CAF50",
                                       font=("Arial", 12, "bold"))
        self.canvas_items.append(tid)

    def _draw_named_polygon(self, points, name, color, closed):
        coords = []
        for (x, y) in points:
            coords.extend([x, y])
        if closed and len(points) >= 3:
            coords.extend([points[0][0], points[0][1]])

        pid = self.canvas.create_line(*coords, fill=color, width=3 if closed else 2)
        self.canvas_items.append(pid)

        if name:
            cx = sum(p[0] for p in points) / len(points)
            cy = sum(p[1] for p in points) / len(points)
            tid = self.canvas.create_text(cx, cy, text=name, fill=color,
                                           font=("Arial", 11, "bold"), justify="center")
            self.canvas_items.append(tid)

    # --- Auto-Konfiguration ---

    def _refresh_collection_status(self):
        if not os.path.isfile(POINTS_FILE):
            self.collection_status_var.set(f"Noch keine Punkte gesammelt ({POINTS_FILE} existiert nicht).")
            return
        points = load_collected_points()
        batches = split_into_batches(
            points, strategy=app_config.AUTO_CONFIG_BATCH_STRATEGY,
            batch_seconds=app_config.AUTO_CONFIG_BATCH_SECONDS,
            batch_size=app_config.AUTO_CONFIG_BATCH_SIZE,
        )
        self.collection_status_var.set(f"{len(points)} Punkte gesammelt, {len(batches)} Batch(es).")

    def _run_auto_evaluation(self):
        if self.frame_bgr is None:
            # Die Auto-Modi zeichnen ihr Ergebnis als Overlay auf den Frame —
            # dafür ist ein echtes Bild zwingend. Manuelles Klicken (Linie,
            # Fläche, Mehrere Flächen) geht dagegen auch ohne.
            messagebox.showwarning(
                "Fehlt noch",
                "Die Auto-Konfiguration wertet die gesammelten Punkte auf dem "
                "Kamerabild aus — dafür bitte oben 'Frame laden' benutzen.\n\n"
                "Ohne Bild lassen sich nur die manuellen Modi (Linie, Fläche, "
                "Mehrere Flächen) konfigurieren.",
                parent=self.root)
            return

        points = load_collected_points()
        if not points:
            messagebox.showwarning(
                "Keine Daten", f"{POINTS_FILE} ist leer oder existiert nicht — "
                               "erst core.py mit aktivierter Datensammlung laufen lassen.",
                parent=self.root)
            return

        mode = self.mode_var.get()
        frame_width, frame_height = self.orig_w, self.orig_h
        self.auto_regions = None

        if mode == "auto_cluster":
            try:
                eps = float(self.eps_var.get())
                min_samples = int(self.min_samples_var.get())
            except ValueError:
                messagebox.showerror("Ungültige Eingabe", "eps/min_samples müssen Zahlen sein.", parent=self.root)
                return

            clusters, noise_points = cluster_points(points, point_type=None,
                                                     eps_pixels=eps, min_samples=min_samples)
            if not clusters:
                self.auto_result_var.set(
                    f"Keine Cluster gefunden (+ {len(noise_points)} Ausreißer). "
                    f"eps/min_samples anpassen oder mehr Daten sammeln.")
                return

            regions = clusters_to_regions(clusters, frame_width, frame_height)
            debug_img = draw_cluster_debug_image(self.frame_bgr, clusters, noise_points, regions)
            self.auto_result_var.set(
                f"{len(clusters)} Cluster (+ {len(noise_points)} Ausreißer) -> "
                f"{len(regions)} Flächen: {', '.join(r['name'] for r in regions)}")

        else:  # auto_border
            try:
                segments = int(self.segments_var.get())
                depth = float(self.depth_var.get())
                min_dist = float(self.min_dist_var.get())
            except ValueError:
                messagebox.showerror("Ungültige Eingabe", "Segmente/Randtiefe/Mindestbewegung müssen Zahlen sein.", parent=self.root)
                return

            regions = generate_border_regions(frame_width, frame_height,
                                               segments_per_edge=segments, border_depth_ratio=depth)
            crossings, filtered_out = assign_tracks_to_border(
                points, regions, frame_width, frame_height, min_track_distance_pixels=min_dist)
            debug_img = draw_border_debug_image(self.frame_bgr, regions, crossings, filtered_out)

            pair_summary = {}
            for c in crossings:
                key = f"{c['start_region']} -> {c['end_region']}"
                pair_summary[key] = pair_summary.get(key, 0) + 1
            top_pairs = ", ".join(f"{k}: {v}" for k, v in
                                  sorted(pair_summary.items(), key=lambda kv: -kv[1])[:5])
            self.auto_result_var.set(
                f"{len(regions)} Randflächen. {len(crossings)} echte Überquerungen, "
                f"{len(filtered_out)} aussortiert.\nHäufigste: {top_pairs or '(keine)'}")

        self.auto_regions = regions
        self._display_image_on_canvas(debug_img)

    # --- Speichern ---

    def save(self):
        mode = self.mode_var.get()

        if mode == "line" and len(self.points) != 2:
            messagebox.showwarning("Fehlt noch", "Bitte zuerst zwei Punkte für die Zähllinie klicken.", parent=self.root)
            return
        if mode == "roi" and (len(self.points) < 3 or not self.polygon_closed):
            messagebox.showwarning("Fehlt noch", "Bitte die Fläche mit mindestens 3 Punkten schließen.", parent=self.root)
            return
        if mode == "multi_roi" and len(self.regions) < 2:
            messagebox.showwarning(
                "Fehlt noch", "Bitte mindestens zwei benannte Flächen anlegen, um Übergänge zu zählen.",
                parent=self.root)
            return
        if mode == "multi_roi":
            # Für den LoRa-Versand (IN/OUT-Format) muss feststehen, welche
            # Fläche der IN-Bereich ist.
            in_field = self.in_field_var.get()
            if in_field == self.in_field_placeholder or \
                    not any(r["name"] == in_field for r in self.regions):
                messagebox.showwarning(
                    "IN-Feld fehlt",
                    "Bitte am Ende ein Feld als IN-Bereich auswählen. "
                    "Übergänge in dieses Feld zählen als IN, heraus als OUT.",
                    parent=self.root)
                return
        if mode in AUTO_MODES and not self.auto_regions:
            messagebox.showwarning("Fehlt noch", "Bitte zuerst 'Auswerten' klicken.", parent=self.root)
            return

        selected = [cls for cls, var in self.class_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("Fehlt noch", "Bitte mindestens eine Klasse auswählen.", parent=self.root)
            return

        saved_mode = "multi_roi" if mode in AUTO_MODES else mode

        config = {
            "mode": saved_mode,
            "classes": selected,
            "reverse_direction": self.reverse_var.get(),
            "snap_to_nearest": self.snap_var.get(),
            "points": [],
            "regions": [],
            # Nur für multi_roi relevant: Fläche, deren Betreten als IN und
            # deren Verlassen als OUT gewertet wird (LoRa-Nachrichtenformat).
            "in_field": "",
        }

        if mode in AUTO_MODES:
            config["regions"] = self.auto_regions
        elif mode == "multi_roi":
            for region in self.regions:
                pts_norm = [self._to_normalized(x, y) for (x, y) in region["points"]]
                config["regions"].append({"name": region["name"], "points": pts_norm})
            config["in_field"] = self.in_field_var.get()
        else:
            config["points"] = [self._to_normalized(x, y) for (x, y) in self.points]

        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)

        messagebox.showinfo("Gespeichert", f"Konfiguration gespeichert in {CONFIG_PATH}", parent=self.root)
        self.status_var.set(f"Gespeichert: {CONFIG_PATH}")

    def _to_normalized(self, x, y):
        # Klickkoordinaten sind Canvas-Pixel; erst den Zentrier-Offset des
        # Bildes abziehen, dann über die Skalierung auf Originalpixel und
        # schließlich auf 0.0-1.0 normalisieren.
        orig_x = (x - self.offset_x) / self.scale
        orig_y = (y - self.offset_y) / self.scale
        return [orig_x / self.orig_w, orig_y / self.orig_h]


def main():
    parser = argparse.ArgumentParser(description="Zählgeometrie (Linie, Fläche(n) oder Auto-Konfiguration) visuell konfigurieren")
    parser.add_argument("--input", required=True,
                         help="Pfad zu einer Videodatei oder einem Bild für die Vorschau")
    args = parser.parse_args()

    frame = load_first_frame(args.input)

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Zählgeometrie konfigurieren")
    root.geometry("1100x650")

    from ui_utils import make_scrollable
    container = make_scrollable(root)
    app = RoiConfigApp(container)
    app.load_frame(frame)
    root.mainloop()


if __name__ == "__main__":
    main()
