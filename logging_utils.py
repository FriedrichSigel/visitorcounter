"""
Alles, was mit dem Schreiben von Tracking-Ergebnissen zu tun hat:
ergebniss.csv (Feature-Zeilen aller gesammelten Tracks, dient als
Zwischenspeicher für die spätere Auswertung, z. B. mit einem
Nearest-Neighbor-Algorithmus) und zaehlung.csv (Zähl-Ereignisse aus der
Zähllogik).

ergebniss.txt (Fließtext für Menschen) wird bewusst NICHT mehr geschrieben —
die maschinenlesbare ergebniss.csv ist die einzige Track-Ausgabe.
"""

import csv
import os

from csv_utils import ensure_current_schema

RESULTS_FILE_CSV = "ergebniss.csv"
COUNTS_FILE_CSV = "zaehlung.csv"

_CSV_HEADER = [
    "display_id", "kind", "track_id", "label",
    "start_x", "start_y", "end_x", "end_y",
    "avg_confidence",
    "first_timestamp", "last_timestamp",
]

_COUNTS_CSV_HEADER = ["timestamp", "display_id", "label", "direction", "is_transition"]


def build_log_entry(timestamp, label, track_id, cx, cy, x_min, y_min, x_max, y_max):
    """
    Baut eine einzelne Log-Zeile für eine Detection. Wird beim Anlegen/
    Aktualisieren eines Tracks (first_entry/last_entry) verwendet, um den
    Zustand der ersten und letzten Sichtung menschenlesbar festzuhalten.
    """
    return (
        f"{timestamp} | Label: {label} | ID: {track_id} | "
        f"xcentre: {cx:.4f}, ycentre: {cy:.4f}, "
        f"xmin: {x_min:.4f}, ymin: {y_min:.4f}, "
        f"xmax: {x_max:.4f}, ymax: {y_max:.4f}"
    )


def log_track_event_csv(kind, track_id, data):
    """
    Hängt eine Zeile für einen abgeschlossenen Track an ergebniss.csv an —
    eine Zeile pro FLUSH-/FINALIZE-Ereignis, als feste Feature-Zeile.

    Spalten: display_id, kind, track_id, label, start_x, start_y, end_x, end_y,
    avg_confidence, first_timestamp, last_timestamp

    display_id ist die pro Klasse hochzählende, lesbare ID (z. B. "car_ID_3");
    track_id bleibt zusätzlich erhalten für Rückverfolgung auf die rohe,
    klassenübergreifend geteilte Hailo-ID. avg_confidence ist die über alle
    Frames des Tracks gemittelte Erkennungskonfidenz (0.0-1.0).

    Direkt einlesbar mit pandas.read_csv() bzw. als Feature-Matrix für
    z. B. sklearn.neighbors.NearestNeighbors — keine Konvertierung nötig.
    """
    ensure_current_schema(RESULTS_FILE_CSV, _CSV_HEADER)
    file_exists = os.path.isfile(RESULTS_FILE_CSV)
    with open(RESULTS_FILE_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(_CSV_HEADER)
        avg_conf = data.get("avg_confidence")
        writer.writerow([
            data.get("display_id", ""),
            kind,
            track_id,
            data["object"],
            data["start"][0], data["start"][1],
            data["end"][0], data["end"][1],
            f"{avg_conf:.4f}" if avg_conf is not None else "",
            data.get("first_timestamp", ""),
            data.get("last_timestamp", ""),
        ])


def log_count_event(timestamp, display_id, label, direction, is_transition=True):
    """
    Hängt ein Zähl-Ereignis an zaehlung.csv an — eine Zeile pro Mal, das ein
    Track die Zählgeometrie kreuzt ODER (bei mehreren Flächen) im selben
    Bereich beginnt und endet (siehe counting.py).

    Spalten: timestamp, display_id, label, direction, is_transition

    is_transition=False kennzeichnet Zeilen, die zwar protokolliert, aber
    NICHT in den Zählerständen berücksichtigt wurden (z. B. "A (kein
    Wechsel)" bei MultiRoiCounter) — beim Auswerten der CSV danach filtern,
    um nur echte Übergänge zu betrachten.
    """
    ensure_current_schema(COUNTS_FILE_CSV, _COUNTS_CSV_HEADER)
    file_exists = os.path.isfile(COUNTS_FILE_CSV)
    with open(COUNTS_FILE_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(_COUNTS_CSV_HEADER)
        writer.writerow([timestamp, display_id, label, direction, is_transition])
