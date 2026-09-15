"""
Alles, was Pixel auf ein Bild oder einen Videoframe malt: das Live-Overlay
(OpenCV, während der Wiedergabe) und die Bewegungsbilder (Pillow, am Ende
eines Tracks bzw. am Ende des Programmlaufs).
"""

import datetime

import cv2
import numpy as np
from PIL import Image, ImageDraw

from config import LABEL_COLORS_BGR, TRACK_COLORS

# --- Ausgabe-Dateinamen ---
# Einmal beim Import generiert, damit alle Teile des Programms denselben
# zeitgestempelten Dateinamen verwenden.
_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
# Zwei getrennte Bewegungsbilder pro Lauf, beide am Programmende erzeugt:
#  - Flush:    alle Tracks, die während des Laufs per Timeout geflusht wurden
#  - Finalize: alle Tracks, die beim Programmende noch aktiv waren
FLUSH_OUTPUT_PATH = f"bewegungsbild_{_timestamp}_flush.png"
FINALIZE_OUTPUT_PATH = f"bewegungsbild_{_timestamp}_finalize.png"


def draw_live_overlay(frame, x_min, y_min, x_max, y_max, width, height,
                       display_id, label, confidence, center):
    """Zeichnet Bounding Box, Label-Text und Mittelpunkt-Punkt auf einen
    einzelnen Videoframe (nur wenn --use-frame aktiv ist).

    display_id ist die lesbare, pro Klasse hochzählende ID (z. B. "car_ID_3");
    label wird weiterhin separat gebraucht, um die richtige Farbe nachzuschlagen."""
    color = LABEL_COLORS_BGR.get(label, (255, 255, 255))  # Weiß als Fallback für unbekannte Klassen

    # Bounding Box (Koordinaten von normalisiert [0,1] in Pixel umgerechnet)
    cv2.rectangle(frame,
                  (int(x_min * width), int(y_min * height)),
                  (int(x_max * width), int(y_max * height)),
                  color, 2)

    # Label-Text oberhalb der Bounding Box
    cv2.putText(frame,
                f"{display_id} {confidence:.2f}",
                (int(x_min * width), int(y_min * height) - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Kleiner roter Punkt im Zentrum der Bounding Box
    cv2.circle(frame, center, 4, (0, 0, 255), -1)


def draw_detection_count(frame, count):
    """Schreibt die Anzahl aktuell getrackter Objekte oben links ins Bild."""
    cv2.putText(frame, f"Tracked: {count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)


def draw_counting_geometry(frame, mode, geometry):
    """
    Zeichnet die Zählgeometrie (gelb) auf den Live-Frame — hilfreich zum
    Kalibrieren. mode="line": Linie zwischen zwei Punkten. mode="roi":
    geschlossenes Polygon über alle Punkte. mode="multi_roi": mehrere
    benannte Polygone, je mit Namen beschriftet (geometry = Liste von
    (name, [Punkte])).
    """
    if mode == "multi_roi":
        for name, points_pixel in geometry:
            if len(points_pixel) < 3:
                continue
            pts = np.array([[int(x), int(y)] for x, y in points_pixel], dtype=np.int32)
            cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 255), thickness=2)
            cx = int(sum(p[0] for p in points_pixel) / len(points_pixel))
            cy = int(sum(p[1] for p in points_pixel) / len(points_pixel))
            cv2.putText(frame, name, (cx - 20, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    elif mode == "roi" and len(geometry) >= 3:
        pts = np.array([[int(x), int(y)] for x, y in geometry], dtype=np.int32)
        cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 255), thickness=2)
    elif len(geometry) == 2:
        (x1, y1), (x2, y2) = geometry
        cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 255), 2)


def draw_counts_overlay(frame, summary_lines):
    """Schreibt die aktuellen IN/OUT-Zählerstände pro Klasse unten links ins Bild."""
    height = frame.shape[0]
    start_y = height - 15 - (len(summary_lines) - 1) * 25
    for i, line in enumerate(summary_lines):
        cv2.putText(frame, line, (10, start_y + i * 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)


def draw_movement_image(canvas_width, canvas_height, tracks):
    """
    Zeichnet für jeden Track eine Bewegungslinie (Start- zu Endpunkt) auf
    eine neue weiße Fläche.

    `tracks` darf sein:
      - ein dict {track_id: data}, wie von TrackingState.finalize() genutzt, oder
      - eine Liste von dicts, die je einen "id"-Key enthalten, wie für die
        Endauswertung aus flushed_objects genutzt (siehe __main__ in core.py).

    Jedes `data`-dict muss mindestens "object", "start", "end" enthalten.

    Vereinheitlicht die zwei früher fast identischen Zeichenblöcke aus
    finalize() und dem finally-Block von __main__.
    """
    img = Image.new("RGB", (canvas_width, canvas_height), color="white")
    draw = ImageDraw.Draw(img)

    items = tracks.items() if isinstance(tracks, dict) else ((t["id"], t) for t in tracks)

    for tid, data in items:
        color = TRACK_COLORS.get(data["object"], "red")  # Rot als Fallback für unbekannte Klassen
        start = data["start"]   # Pixelposition bei der ersten Detection
        end   = data["end"]     # Pixelposition bei der letzten Detection

        # Linie, die den Bewegungspfad des Objekts zeigt
        draw.line([start, end], fill=color, width=4)

        r = 6
        # Blauer gefüllter Kreis am Startpunkt
        draw.ellipse([start[0] - r, start[1] - r, start[0] + r, start[1] + r], fill="blue")
        # Roter gefüllter Kreis am Endpunkt
        draw.ellipse([end[0] - r, end[1] - r, end[0] + r, end[1] + r], fill="red")
        # Textlabel mit lesbarer display_id (z. B. "car_ID_3") nahe dem Endpunkt
        label_text = data.get("display_id", f"{data['object']}_ID_{tid}")
        draw.text((end[0] + 8, end[1] - 8), label_text, fill="black")

    return img


def save_flush_image(img):
    """Speichert das Bewegungsbild aller während des Laufs geflushten Tracks."""
    img.save(FLUSH_OUTPUT_PATH)
    return FLUSH_OUTPUT_PATH


def save_finalize_image(img):
    """Speichert das Bewegungsbild aller beim Programmende noch aktiven Tracks."""
    img.save(FINALIZE_OUTPUT_PATH)
    return FINALIZE_OUTPUT_PATH
