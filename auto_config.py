"""
auto_config.py — Datensammlung und Batch-Einteilung für die künftige
automatische Wegerkennung ("auto"-Zählmodus, siehe ToDo.md).

Paket 1 (Datensammelmodus): Wenn AUTO_CONFIG_COLLECTION_ENABLED in config.py
aktiv ist, schreibt tracking.py bei jedem abgeschlossenen Track (Flush oder
Finalize) zusätzlich zu ergebniss.csv einen Punkt in eine EIGENE Datei
(auto_config_points.csv). Bewusst getrennt von ergebniss.csv, damit eine
gezielte Sammelsession nicht mit älteren, nicht zusammengehörigen Läufen
vermischt wird. Start- und Endpunkt eines Tracks werden als zwei separate
Zeilen gespeichert, damit sie später unabhängig voneinander geclustert
werden können (siehe Anforderung: "wo Tracks anfangen bzw aufhören").

Die Sammeldauer wird nicht hier, sondern über die bestehende
RUN_DURATION_SECONDS-Option in config.py gesteuert — einfach für die
gewünschte Dauer der Sammlung setzen und core.py normal laufen lassen.

Paket 2 (Batch-Einteilung): split_into_batches() teilt die gesammelten
Punkte in Batches auf, entweder nach Zeitfenstern oder nach fester
Punktanzahl (siehe AUTO_CONFIG_BATCH_STRATEGY in config.py).

Paket 3 (Clustering) baut auf den Batches auf, ist hier noch NICHT
enthalten — bewusst als nächster, separater Schritt.
"""

import csv
import os
from datetime import datetime

from csv_utils import ensure_current_schema

POINTS_FILE = "auto_config_points.csv"
_POINTS_HEADER = ["timestamp", "display_id", "label", "point_type", "x", "y"]


def log_collection_point(timestamp, display_id, label, point_type, x, y):
    """
    Hängt einen einzelnen Datenpunkt an auto_config_points.csv an.

    point_type: "start" oder "end".
    """
    ensure_current_schema(POINTS_FILE, _POINTS_HEADER)
    file_exists = os.path.isfile(POINTS_FILE)
    with open(POINTS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(_POINTS_HEADER)
        writer.writerow([timestamp, display_id, label, point_type, x, y])


def log_track_for_collection(data):
    """
    Komfortfunktion: schreibt Start- UND Endpunkt eines abgeschlossenen
    Tracks in einem Aufruf. data ist dasselbe dict wie in tracking.py
    (enthält "start", "end", "object", "display_id", "first_timestamp",
    "last_timestamp").
    """
    log_collection_point(data["first_timestamp"], data["display_id"], data["object"],
                          "start", data["start"][0], data["start"][1])
    log_collection_point(data["last_timestamp"], data["display_id"], data["object"],
                          "end", data["end"][0], data["end"][1])


def _parse_timestamp(ts_string):
    """Parst die im Projekt einheitlich genutzten Zeitstempel ('%Y-%m-%d %H:%M:%S.%f')."""
    return datetime.strptime(ts_string, "%Y-%m-%d %H:%M:%S.%f")


def load_collected_points(path=POINTS_FILE):
    """Liest auto_config_points.csv ein und gibt eine Liste von dicts zurück."""
    if not os.path.isfile(path):
        return []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return [
            {
                "timestamp": row["timestamp"],
                "display_id": row["display_id"],
                "label": row["label"],
                "point_type": row["point_type"],
                "x": float(row["x"]),
                "y": float(row["y"]),
            }
            for row in reader
        ]


def split_into_batches(points, strategy="time_window", batch_seconds=300, batch_size=50):
    """
    Teilt eine Liste von Punkten (siehe load_collected_points()) in
    zeitlich sortierte Batches auf.

    strategy="time_window": ein neuer Batch, sobald batch_seconds Sekunden
    seit Batch-Beginn vergangen sind (Standard: 5 Minuten).
    strategy="fixed_size": ein Batch pro batch_size Punkte, in zeitlicher
    Reihenfolge.

    Punkte mit nicht parsbarem Zeitstempel werden übersprungen (mit
    Warnung), statt den gesamten Vorgang abzubrechen.

    Gibt eine Liste von Batches zurück, jeder Batch selbst eine Liste von
    Punkt-dicts.
    """
    parsed = []
    for p in points:
        try:
            ts = _parse_timestamp(p["timestamp"])
        except (ValueError, TypeError):
            print(f"WARNUNG: Zeitstempel '{p.get('timestamp')}' von "
                  f"{p.get('display_id')} konnte nicht geparst werden — "
                  f"Punkt wird übersprungen.")
            continue
        parsed.append((ts, p))

    parsed.sort(key=lambda item: item[0])

    if not parsed:
        return []

    if strategy == "fixed_size":
        return [
            [p for _, p in parsed[i:i + batch_size]]
            for i in range(0, len(parsed), batch_size)
        ]

    if strategy == "time_window":
        batches = []
        batch_start_time = parsed[0][0]
        current_batch = []
        for ts, p in parsed:
            if (ts - batch_start_time).total_seconds() >= batch_seconds:
                if current_batch:
                    batches.append(current_batch)
                current_batch = []
                batch_start_time = ts
            current_batch.append(p)
        if current_batch:
            batches.append(current_batch)
        return batches

    raise ValueError(f"Unbekannte Batch-Strategie: '{strategy}' (erwartet: 'time_window' oder 'fixed_size')")


if __name__ == "__main__":
    # Kleines Kontrollwerkzeug: zeigt, wie viele Punkte gesammelt wurden und
    # wie sie sich auf Batches verteilen — nützlich, um Paket 1+2 zu prüfen,
    # bevor Paket 3 (Clustering) darauf aufbaut.
    from config import AUTO_CONFIG_BATCH_STRATEGY, AUTO_CONFIG_BATCH_SECONDS, AUTO_CONFIG_BATCH_SIZE

    all_points = load_collected_points()
    print(f"{len(all_points)} gesammelte Punkte geladen aus {POINTS_FILE}")

    resulting_batches = split_into_batches(
        all_points,
        strategy=AUTO_CONFIG_BATCH_STRATEGY,
        batch_seconds=AUTO_CONFIG_BATCH_SECONDS,
        batch_size=AUTO_CONFIG_BATCH_SIZE,
    )
    print(f"{len(resulting_batches)} Batch(es) (Strategie: {AUTO_CONFIG_BATCH_STRATEGY})")
    for i, batch in enumerate(resulting_batches, start=1):
        labels = sorted(set(p["label"] for p in batch))
        print(f"  Batch {i}: {len(batch)} Punkte, Klassen: {labels}")
