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

# Darstellung der Einzugsgebiete ("Punkte ohne Treffer der naechsten Flaeche
# zuordnen"). Jeder Bildbereich wird in der Farbe der Flaeche eingefaerbt, der
# er zugeschlagen wuerde — aber deutlich heller und durchscheinend, damit die
# eigentliche Flaeche klar davon unterscheidbar bleibt.
CATCHMENT_ALPHA = 0.30      # Deckkraft der Einfaerbung (0 = unsichtbar, 1 = deckend)
CATCHMENT_LIGHTEN = 0.55    # Anteil Weiss, der der Flaechenfarbe beigemischt wird
CATCHMENT_GRID = 8          # Rasterweite in Pixeln — groeber = schneller

AUTO_MODES = ("auto_cluster", "auto_border")


def _point_to_segment_distance(px, py, ax, ay, bx, by):
    """Kuerzester Abstand des Punktes (px,py) zur Strecke (ax,ay)-(bx,by)."""
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def _point_in_polygon(px, py, points):
    """Ray-Casting: liegt der Punkt innerhalb des Polygons?"""
    inside = False
    n = len(points)
    for i in range(n):
        ax, ay = points[i]
        bx, by = points[(i + 1) % n]
        if (ay > py) != (by > py):
            x_cross = ax + (py - ay) * (bx - ax) / (by - ay)
            if px < x_cross:
                inside = not inside
    return inside


def _distance_to_polygon(px, py, points):
    """Abstand zum Polygon; 0, wenn der Punkt darin liegt."""
    if len(points) >= 3 and _point_in_polygon(px, py, points):
        return 0.0
    best = float("inf")
    n = len(points)
    for i in range(n):
        ax, ay = points[i]
        bx, by = points[(i + 1) % n]
        d = _point_to_segment_distance(px, py, ax, ay, bx, by)
        if d < best:
            best = d
    return best


def _lighten(hex_color, amount):
    """Mischt Weiss bei: amount=0 laesst die Farbe, amount=1 ergibt Weiss."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r = int(r + (255 - r) * amount)
    g = int(g + (255 - g) * amount)
    b = int(b + (255 - b) * amount)
    return (r, g, b)


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
        side = ctk.CTkFrame(master, fg_color="transparent")
        side.grid(row=0, column=1, sticky="nw", pady=10, padx=(0, 10))
        # Breite ueber minsize der einzigen Spalte festlegen — NICHT ueber
        # grid_propagate(False) mit fester Hoehe. Der frueher hier verwendete
        # Weg zwang mich, die Hoehe von Hand zu berechnen; diese Rechnung lief
        # beim Aufbau gegen ein noch nicht eingeblendetes Widget und lieferte
        # deshalb je nach Zeitpunkt andere (falsche) Werte. Jetzt bestimmt Tk
        # die Hoehe selbst, die Breite ist trotzdem gedeckelt.
        side.grid_columnconfigure(0, weight=0, minsize=SIDE_PANEL_WIDTH)
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

        # Mindest-Konfidenz: erst ab diesem Wert wird ein erkanntes Objekt
        # gezählt. Objekte, bei denen das Modell unsicherer ist, werden
        # ignoriert. Wert zwischen 0 und 1; Standard 0.5. Wird in der
        # roi_config.json als "min_confidence" gespeichert.
        conf_frame = ctk.CTkFrame(side, fg_color="transparent")
        conf_frame.grid(row=row, column=0, sticky="w", padx=10, pady=(12, 0))
        ctk.CTkLabel(conf_frame, text="Mindest-Konfidenz zum Zählen:").pack(
            side="left")
        self.confidence_var = tk.StringVar(value="0.5")
        self.confidence_entry = ctk.CTkEntry(
            conf_frame, textvariable=self.confidence_var, width=60)
        self.confidence_entry.pack(side="left", padx=(6, 0))
        row += 1

        self.snap_var = tk.BooleanVar(value=False)
        self.snap_check = ctk.CTkCheckBox(
            side, text="Punkte ohne Treffer der nächsten\nFläche zuordnen (statt 'außerhalb')",
            variable=self.snap_var, command=self._on_snap_toggle,
        )
        self.snap_check.grid(row=row, column=0, sticky="w", padx=10, pady=(5, 0))
        self.snap_check.grid_remove()
        row += 1

        # Pro-Fläche-Auswahl: wenn die Zuordnung zur nächsten Fläche an ist,
        # kann hier je Fläche festgelegt werden, ob sie überhaupt Punkte ohne
        # Treffer aufnimmt. So lässt sich das Einzugsgebiet auf einzelne Flächen
        # beschränken (z. B. nur die Eingänge, nicht die Randzonen).
        # Der Rahmen wird bei jedem Bedarf neu mit einer Checkbox je Fläche
        # gefüllt (_refresh_snap_fields); die Zustände hängen an
        # self.snap_field_vars, gespeichert wird pro Fläche in region["snap"].
        self.snap_fields_label = ctk.CTkLabel(
            side, text="Zuordnung gilt für diese Flächen:", text_color="gray70")
        self.snap_fields_label.grid(row=row, column=0, sticky="w", padx=10, pady=(6, 0))
        self.snap_fields_label.grid_remove()
        row += 1
        self.snap_fields_frame = ctk.CTkFrame(side, fg_color="transparent")
        self.snap_fields_frame.grid(row=row, column=0, sticky="we", padx=10, pady=(0, 0))
        self.snap_fields_frame.grid_remove()
        self.snap_field_vars = {}   # Flächenname -> BooleanVar
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

        # Sicherstellen, dass alles gezeichnet wird, sobald das Widget
        # tatsaechlich sichtbar wird (siehe _on_map).
        master.bind("<Map>", self._on_map, add="+")

        self._update_status_for_mode()

    def _on_snap_toggle(self):
        """Ein-/Ausschalten der Zuordnung zur naechsten Flaeche — die
        Einzugsgebiete werden entsprechend ein- oder ausgeblendet."""
        self._refresh_snap_fields()
        # Die Pro-Flaeche-Checkboxen werden hier neu erzeugt; damit sie nicht
        # gegen eine 1x1-Groesse gezeichnet werden (customtkinter-Eigenheit),
        # denselben rekursiven Neuaufbau anstossen wie beim Moduswechsel.
        self.side.after(30, self._force_redraw)
        self._update_status_for_mode()

    def _refresh_snap_fields(self):
        """
        Baut die Pro-Flaeche-Auswahl neu auf: eine Checkbox je benannter
        Flaeche, mit der sich einstellen laesst, ob diese Flaeche Punkte ohne
        Treffer aufnimmt.

        Sichtbar nur, wenn die globale Zuordnung an ist UND der Modus
        multi_roi mit mindestens einer Flaeche vorliegt. Vorhandene Haekchen
        bleiben erhalten (region["snap"]); neue Flaechen starten auf True,
        damit sich das Verhalten ohne Zutun wie bisher verhaelt (alle Flaechen
        nehmen auf).
        """
        # Alte Checkboxen entfernen.
        for child in self.snap_fields_frame.winfo_children():
            child.destroy()
        self.snap_field_vars = {}

        sichtbar = (self.snap_var.get()
                    and self.mode_var.get() == "multi_roi"
                    and any(r.get("name") for r in self.regions))
        if not sichtbar:
            self.snap_fields_label.grid_remove()
            self.snap_fields_frame.grid_remove()
            return

        for region in self.regions:
            name = region.get("name")
            if not name:
                continue
            # Standard True: ohne ausdrueckliche Wahl verhaelt es sich wie der
            # alte globale Schalter (alle Flaechen nehmen auf).
            aktiv = bool(region.get("snap", True))
            var = tk.BooleanVar(value=aktiv)
            self.snap_field_vars[name] = var
            ctk.CTkCheckBox(
                self.snap_fields_frame, text=name, variable=var,
                command=self._on_snap_field_toggle,
                checkbox_width=18, checkbox_height=18,
            ).pack(anchor="w", pady=1)

        self.snap_fields_label.grid()
        self.snap_fields_frame.grid()

    def _on_snap_field_toggle(self):
        """Uebernimmt die Pro-Flaeche-Haekchen in die Flaechendaten und
        zeichnet das Einzugsgebiet-Overlay neu."""
        for region in self.regions:
            name = region.get("name")
            if name in self.snap_field_vars:
                region["snap"] = self.snap_field_vars[name].get()
        self._redraw_background()
        self.redraw()

    def _on_map(self, _event=None):
        """
        Wird aufgerufen, sobald Tab 2 tatsaechlich sichtbar wird.

        Hintergrund: customtkinter zeichnet seine Widgets auf interne
        Canvas-Elemente. Passiert das, waehrend das Widget noch nicht
        eingeblendet ist, rechnet es mit einer Groesse von 1x1 — daher die
        fehlenden Beschriftungen, halb gezeichneten Buttons und verrutschten
        Texte. Ein <Map>-Ereignis ist der frueheste Zeitpunkt, zu dem die
        echten Masse feststehen; deshalb hier ein vollstaendiger Neuaufbau der
        Darstellung.
        """
        self.side.after(30, self._force_redraw)

    def _force_redraw(self):
        """Zeichnet Bedienspalte und Canvas komplett neu."""
        try:
            self.side.update_idletasks()
        except Exception:
            return
        self._redraw_ctk_tree(self.side)
        self._redraw_background()
        self.redraw()

    def _redraw_ctk_tree(self, widget):
        """Ruft rekursiv das interne Neuzeichnen jedes customtkinter-Widgets auf."""
        draw = getattr(widget, "_draw", None)
        if callable(draw):
            try:
                draw(no_color_updates=False)
            except Exception:
                pass
        try:
            children = widget.winfo_children()
        except Exception:
            return
        for child in children:
            self._redraw_ctk_tree(child)

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
        leere Arbeitsfläche. Anschliessend ggf. die Einzugsgebiete darueber."""
        if self.frame_bgr is not None:
            self._display_image_on_canvas(self.frame_bgr)
        else:
            self._draw_blank_canvas()
        self._draw_catchment_overlay()

    def _draw_catchment_overlay(self):
        """
        Faerbt das Bild danach ein, welcher Flaeche ein Punkt zugeschlagen
        wuerde — nur aktiv, wenn "Punkte ohne Treffer der naechsten Flaeche
        zuordnen" eingeschaltet ist.

        Genau das ist ja die Frage, die man beim Setzen dieser Option hat:
        wohin faellt eigentlich alles, was in KEINER Flaeche liegt? Ohne
        Darstellung ist das reine Vorstellungskraft.

        Die Einfaerbung nutzt die Farbe der jeweiligen Flaeche, aber stark
        aufgehellt und durchscheinend (CATCHMENT_LIGHTEN / CATCHMENT_ALPHA),
        damit die eigentliche Flaeche mit ihrem kraeftigen Rand klar
        unterscheidbar bleibt.

        Gerechnet wird auf einem groben Raster (CATCHMENT_GRID) und in PIL,
        nicht mit einzelnen Canvas-Objekten — tausende Rechtecke waeren in Tk
        zu langsam, um beim Klicken fluessig zu bleiben.
        """
        self._catchment_photo = None
        if not self.snap_var.get():
            return
        if self.mode_var.get() != "multi_roi":
            return
        closed_regions = [r for r in self.regions if len(r.get("points", [])) >= 3]
        if not closed_regions:
            return

        disp_w = int(self.orig_w * self.scale)
        disp_h = int(self.orig_h * self.scale)
        if disp_w <= 0 or disp_h <= 0:
            return

        step = max(2, CATCHMENT_GRID)
        cols = max(1, disp_w // step)
        rows = max(1, disp_h // step)

        colors = [_lighten(REGION_COLORS[i % len(REGION_COLORS)], CATCHMENT_LIGHTEN)
                  for i in range(len(self.regions))]
        # Punkte der Flaechen liegen in Canvas-Koordinaten, also inkl. Offset.
        # Nur Flaechen mit gesetztem Haekchen nehmen Punkte ohne Treffer auf —
        # ist bei einer Flaeche "snap" ausgeschaltet, wird sie hier uebergangen
        # und ihr Bereich faellt an die naechste teilnehmende Flaeche (oder
        # bleibt "ausserhalb", wenn gar keine teilnimmt).
        polys = []
        for region in self.regions:
            pts = region.get("points", [])
            if len(pts) >= 3 and region.get("snap", True):
                polys.append([(x - self.offset_x, y - self.offset_y) for (x, y) in pts])
            else:
                polys.append(None)

        # Kleines Bild in Rasteraufloesung fuellen, danach hochskalieren.
        small = Image.new("RGBA", (cols, rows), (0, 0, 0, 0))
        pixels = small.load()
        alpha = int(round(CATCHMENT_ALPHA * 255))

        for gy in range(rows):
            py = gy * step + step / 2
            for gx in range(cols):
                px = gx * step + step / 2
                best_index, best_dist = None, float("inf")
                for i, poly in enumerate(polys):
                    if poly is None:
                        continue
                    d = _distance_to_polygon(px, py, poly)
                    if d < best_dist:
                        best_index, best_dist = i, d
                    if best_dist == 0.0:
                        break
                if best_index is not None:
                    r, g, b = colors[best_index]
                    pixels[gx, gy] = (r, g, b, alpha)

        overlay = small.resize((disp_w, disp_h), Image.NEAREST)
        self._catchment_photo = ImageTk.PhotoImage(overlay)
        self.canvas.create_image(self.offset_x, self.offset_y, anchor="nw",
                                 image=self._catchment_photo)

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
        # Nach dem Umschalten neu zeichnen — ein-/ausgeblendete Elemente
        # veraendern das Layout der Spalte.
        self.side.after(30, self._force_redraw)
        self._apply_mode_widgets(mode)

    def _apply_mode_widgets(self, mode):
        """
        Blendet die Bedienelemente passend zum Modus ein und aus.

        Bewusst getrennt von on_mode_change: beim Laden einer gespeicherten
        Konfiguration muss die Anzeige zum Modus passen, die Geometrie darf
        dabei aber NICHT zurueckgesetzt werden — genau das taete
        on_mode_change ueber reset_geometry.
        """
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

        # Pro-Flaeche-Snap-Auswahl passend zum Modus/Schalter neu aufbauen
        # (blendet sich selbst aus, wenn nicht multi_roi oder snap aus).
        self._refresh_snap_fields()

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
            if self.snap_var.get() and self.regions:
                self.status_var.set(
                    self.status_var.get() +
                    "\n\nDie hellen Farbflächen zeigen, welcher Fläche ein Punkt "
                    "zugeschlagen würde, der in keiner Fläche liegt."
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
            # Hintergrund mit neu zeichnen: die Einzugsgebiete haengen von den
            # Flaechen ab und aendern sich mit jeder neuen Flaeche.
            self._redraw_background()
            self.redraw()
            self._refresh_in_field_options()
            self._refresh_snap_fields()
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
            # Einzugsgebiete haengen an den Flaechen — mit neu zeichnen.
            self._redraw_background()
            self.redraw()
            self._refresh_in_field_options()
            self._refresh_snap_fields()
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

        # Mindest-Konfidenz prüfen: Zahl zwischen 0 und 1.
        try:
            min_conf = float(self.confidence_var.get().strip().replace(",", "."))
            if not (0.0 <= min_conf <= 1.0):
                raise ValueError
        except (ValueError, AttributeError):
            messagebox.showwarning(
                "Ungültige Konfidenz",
                "Die Mindest-Konfidenz muss eine Zahl zwischen 0 und 1 sein "
                "(z. B. 0.5).", parent=self.root)
            return

        saved_mode = "multi_roi" if mode in AUTO_MODES else mode

        config = {
            "mode": saved_mode,
            "classes": selected,
            "reverse_direction": self.reverse_var.get(),
            # Erst ab dieser Konfidenz wird ein erkanntes Objekt gezählt.
            "min_confidence": min_conf,
            # Globaler Schalter bleibt erhalten, damit aeltere Auswertungscode-
            # Stellen, die nur dieses Feld lesen, weiter funktionieren. Die
            # Feinsteuerung steckt zusaetzlich je Flaeche in regions[i]["snap"].
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
            # Aktuelle Pro-Flaeche-Haekchen uebernehmen, falls die Auswahl
            # sichtbar war (bei ausgeschaltetem Snap bleibt region["snap"] auf
            # dem geladenen Wert).
            for region in self.regions:
                name = region.get("name")
                if name in self.snap_field_vars:
                    region["snap"] = self.snap_field_vars[name].get()
            for region in self.regions:
                pts_norm = [self._to_normalized(x, y) for (x, y) in region["points"]]
                eintrag = {"name": region["name"], "points": pts_norm}
                # Pro-Flaeche-Zuordnung mitspeichern. Standard True, damit sich
                # eine Flaeche ohne ausdrueckliche Wahl wie bisher verhaelt.
                eintrag["snap"] = bool(region.get("snap", True))
                config["regions"].append(eintrag)
            config["in_field"] = self.in_field_var.get()
        else:
            config["points"] = [self._to_normalized(x, y) for (x, y) in self.points]

        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)

        messagebox.showinfo("Gespeichert", f"Konfiguration gespeichert in {CONFIG_PATH}", parent=self.root)
        self.status_var.set(f"Gespeichert: {CONFIG_PATH}")

    def _from_normalized(self, nx, ny):
        """
        Gegenstueck zu _to_normalized: rechnet gespeicherte 0.0-1.0-Koordinaten
        zurueck in Canvas-Pixel. Wird beim Laden einer bestehenden
        Konfiguration gebraucht.
        """
        orig_x = nx * self.orig_w
        orig_y = ny * self.orig_h
        return (orig_x * self.scale + self.offset_x,
                orig_y * self.scale + self.offset_y)

    def load_config(self, path=None, silent=False):
        """
        Laedt eine gespeicherte Konfiguration und stellt den kompletten
        Bedienzustand wieder her: Modus, Punkte bzw. Flaechen, Klassenauswahl,
        Richtungsumkehr, Zuordnung zur naechsten Flaeche und IN-Feld.

        Die Datei enthaelt relative Koordinaten (0.0-1.0). Sie werden ueber
        _from_normalized in Canvas-Pixel zurueckgerechnet — dadurch passt eine
        Konfiguration auch dann, wenn sie bei anderer Anzeigegroesse oder ganz
        ohne Kamerabild erstellt wurde.

        Rueckgabe: True bei Erfolg.
        """
        path = path or CONFIG_PATH
        if not os.path.exists(path):
            if not silent:
                messagebox.showwarning(
                    "Keine Konfiguration",
                    f"Es wurde keine Datei {path} gefunden. Erst konfigurieren "
                    f"und speichern, dann laesst sie sich laden.",
                    parent=self.root)
            return False

        try:
            with open(path) as f:
                config = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            if not silent:
                messagebox.showerror(
                    "Datei nicht lesbar",
                    f"{path} konnte nicht gelesen werden:\n{exc}",
                    parent=self.root)
            return False

        mode = config.get("mode", "line")
        if mode not in ("line", "roi", "multi_roi"):
            if not silent:
                messagebox.showwarning(
                    "Unbekannter Modus",
                    f"Der Modus '{mode}' aus der Datei ist unbekannt.",
                    parent=self.root)
            return False

        # Geometrie leeren, aber OHNE reset_geometry — das wuerde ueber
        # on_mode_change wieder alles zuruecksetzen, was wir gerade laden.
        self.points = []
        self.polygon_closed = False
        self.regions = []
        self.current_points = []
        self.auto_regions = None

        self.mode_var.set(mode)
        self._apply_mode_widgets(mode)

        if mode == "multi_roi":
            # Alter globaler Schalter als Rueckfallwert: fehlt in einer Datei
            # die Pro-Flaeche-Angabe (aeltere Konfiguration), erben alle
            # Flaechen den globalen Wert — Verhalten bleibt damit unveraendert.
            global_snap = bool(config.get("snap_to_nearest", False))
            for region in config.get("regions", []):
                pts = [self._from_normalized(nx, ny)
                       for (nx, ny) in region.get("points", [])]
                if len(pts) >= 3:
                    snap = bool(region.get("snap", global_snap))
                    self.regions.append({"name": region.get("name", "?"),
                                         "points": pts, "snap": snap})
        else:
            self.points = [self._from_normalized(nx, ny)
                           for (nx, ny) in config.get("points", [])]
            self.polygon_closed = (mode == "roi" and len(self.points) >= 3)

        # Klassen: nur die in der Datei genannten anhaken.
        saved_classes = config.get("classes")
        if saved_classes is not None:
            for cls, var in self.class_vars.items():
                var.set(cls in saved_classes)

        self.reverse_var.set(bool(config.get("reverse_direction", False)))
        # Mindest-Konfidenz laden; Standard 0.5, wenn nicht vorhanden.
        self.confidence_var.set(str(config.get("min_confidence", 0.5)))
        self.snap_var.set(bool(config.get("snap_to_nearest", False)))

        self._refresh_in_field_options()
        # Pro-Flaeche-Liste passend zum geladenen Snap-Zustand aufbauen —
        # sonst erscheint sie erst, wenn man den Schalter einmal umlegt.
        self._refresh_snap_fields()
        in_field = config.get("in_field") or ""
        if in_field and any(r["name"] == in_field for r in self.regions):
            self.in_field_var.set(in_field)

        self._force_redraw()
        self._describe_loaded_config(config, path)
        return True

    def _describe_loaded_config(self, config, path):
        """Schreibt eine Zusammenfassung des Geladenen in die Statuszeile."""
        mode = config.get("mode", "?")
        mode_names = {"line": "Linie", "roi": "Fläche / ROI",
                      "multi_roi": "Mehrere Flächen"}
        parts = [f"Geladen aus {os.path.basename(path)}",
                 f"Modus: {mode_names.get(mode, mode)}"]
        if mode == "multi_roi":
            names = ", ".join(r["name"] for r in self.regions) or "keine"
            parts.append(f"Flächen: {names}")
            parts.append(f"IN-Feld: {config.get('in_field') or 'NICHT gesetzt'}")
        else:
            parts.append(f"Punkte: {len(self.points)}")
        parts.append("Klassen: " + (", ".join(config.get("classes", [])) or "keine"))
        if config.get("reverse_direction"):
            parts.append("Richtung umgekehrt")
        if config.get("snap_to_nearest"):
            parts.append("Zuordnung zur nächsten Fläche aktiv")
        self.status_var.set("\n".join(parts))

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
