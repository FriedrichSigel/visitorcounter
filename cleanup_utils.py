"""
cleanup_utils.py — Aufräumen der Ausgabedateien beim Programmstart.

Beim Start von core.py werden alle Ausgabe-Artefakte eines früheren Laufs in
einen neu erstellten Archivordner verschoben (nicht gelöscht), damit das
Arbeitsverzeichnis für den neuen Lauf sauber ist und sich Ergebnisse nicht
zwischen Läufen vermischen. Gut fürs Debugging: Jeder Lauf startet mit einem
leeren Blatt, alte Läufe bleiben nachvollziehbar erhalten.

Betroffen sind: ergebniss.csv, zaehlung.csv, die Bewegungsbilder, die
Auto-Config-Sammeldaten (auto_config_points.csv) und deren Kontrollbilder.
NICHT betroffen: roi_config.json (die aktive Konfiguration) und camera_raw.png
(das Referenzbild) — die sollen einen Lauf überdauern.
"""

import glob
import os
import shutil
from datetime import datetime

# Verzeichnis, in dem die Archivordner angelegt werden.
ARCHIVE_ROOT = "vorherige_laeufe"

# Feste Dateinamen, die (wenn vorhanden) archiviert werden.
_ARCHIVE_FILES = [
    "ergebniss.csv",
    "ergebniss.txt",          # Altbestand aus früheren Versionen mit einräumen
    "zaehlung.csv",
    "auto_config_points.csv",
    "auto_config_clusters.png",
    "auto_config_border.png",
]

# Glob-Muster für die Bewegungsbilder (tragen einen Zeitstempel im Namen).
_ARCHIVE_PATTERNS = [
    "bewegungsbild_*.png",           # neue Namensgebung (siehe visualization.py)
    "tracked_objects_*.png",         # Altbestand aus früheren Versionen
]


def archive_previous_run(workdir="."):
    """
    Verschiebt alle Ausgabe-Artefakte eines früheren Laufs in einen neuen
    Archivordner ARCHIVE_ROOT/<Zeitstempel>/. Legt den Ordner nur an, wenn es
    tatsächlich etwas zu archivieren gibt (kein leerer Ordner bei erstem Start).

    Gibt den Pfad des Archivordners zurück, oder None, wenn nichts zu
    archivieren war.
    """
    # Sammeln, was existiert
    to_move = []
    for name in _ARCHIVE_FILES:
        path = os.path.join(workdir, name)
        if os.path.isfile(path):
            to_move.append(path)
    for pattern in _ARCHIVE_PATTERNS:
        to_move.extend(glob.glob(os.path.join(workdir, pattern)))

    # Nichts da -> nichts tun (sauberer Erststart)
    if not to_move:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = os.path.join(workdir, ARCHIVE_ROOT, timestamp)
    os.makedirs(archive_dir, exist_ok=True)

    moved = 0
    for path in to_move:
        try:
            shutil.move(path, os.path.join(archive_dir, os.path.basename(path)))
            moved += 1
        except OSError as e:
            print(f"WARNUNG: {path} konnte nicht archiviert werden: {e}")

    print(f"{moved} Datei(en) des vorherigen Laufs archiviert nach {archive_dir}")
    return archive_dir
