"""
csv_utils.py — kleine, gemeinsam genutzte Hilfsfunktion für alle CSV-
Schreiber im Projekt (logging_utils.py, auto_config.py): verhindert
Schema-Drift.

Ohne diese Prüfung schreibt eine Datei, die schon vor einer Code-Änderung
existierte (z. B. bevor eine neue Spalte ergänzt wurde), stillschweigend
mit MEHR/ANDEREN Spalten weiter, als ihre eigene Kopfzeile zeigt — jede
neue Zeile passt dann nicht mehr zur ersten Zeile der Datei. Das Ergebnis:
eine CSV-Datei mit unterschiedlicher Spaltenanzahl je nachdem, wann die
Zeile geschrieben wurde. Jede spätere Auswertung (z. B. pandas.read_csv())
würde Werte in die falschen Spalten einsortieren, ohne einen Fehler zu
werfen. Genau das ist im Projekt bereits mit ergebniss.csv und
zaehlung.csv passiert (siehe HANDOFF.md), nachdem display_id bzw.
is_transition nachträglich als Spalte ergänzt wurden.
"""

import os
from datetime import datetime

# Merkt sich pro Prozesslauf, welche Pfade schon geprüft wurden, damit nicht
# bei jeder einzelnen geschriebenen Zeile erneut die Datei geöffnet und die
# erste Zeile gelesen wird — einmal pro Datei und Programmlauf reicht.
_checked_paths = set()


def ensure_current_schema(path, expected_header):
    """
    Prüft, ob eine bereits vorhandene CSV-Datei zur aktuell erwarteten
    Kopfzeile passt. Falls nicht (z. B. weil eine ältere Codeversion
    weniger oder andere Spalten geschrieben hat), wird die alte Datei
    umbenannt (archiviert) statt inkonsistent weiterbeschrieben zu werden.

    Tut nichts, wenn:
    - der Pfad in diesem Prozesslauf schon geprüft wurde,
    - die Datei noch nicht existiert (wird beim ersten Schreiben ohnehin
      mit korrekter Kopfzeile neu angelegt),
    - die Datei leer ist, oder
    - das Schema bereits passt.
    """
    if path in _checked_paths:
        return
    _checked_paths.add(path)

    if not os.path.isfile(path):
        return

    with open(path, newline="") as f:
        first_line = f.readline().rstrip("\r\n")

    if not first_line:
        return  # leere Datei, kein Problem

    actual_header = first_line.split(",")
    if actual_header == list(expected_header):
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base, ext = os.path.splitext(path)
    archive_path = f"{base}_altes_format_{timestamp}{ext}"
    os.rename(path, archive_path)
    print(
        f"WARNUNG: '{path}' hatte ein anderes Spaltenformat als aktuell "
        f"erwartet (vermutlich von einer älteren Codeversion geschrieben, "
        f"z. B. vor einer später ergänzten Spalte). Alte Datei archiviert "
        f"als '{archive_path}' (Daten bleiben erhalten, nur umbenannt), "
        f"'{path}' wird mit dem aktuellen Format neu angelegt."
    )
