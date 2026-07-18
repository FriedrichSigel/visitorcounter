# Umbau ergebniss-Ausgabe + Start-Cleanup — Änderungsprotokoll

**Stand 15.07.2026.** Fünf Dateien geändert/neu, alle Änderungen isoliert getestet.

## Was umgesetzt wurde

### 1. `ergebniss.txt` entfällt komplett
`logging_utils.py`: Funktion `log_track_event()` und Konstante `RESULTS_FILE`
entfernt. `tracking.py`: alle Aufrufe raus (`flush_stale`, `finalize`). Es wird
keine Fließtext-Datei mehr geschrieben — `ergebniss.csv` ist die einzige
Track-Ausgabe. `build_log_entry()` bleibt (liefert weiter die
`first_entry`/`last_entry`-Strings im Track-dict, nur ohne txt-Ziel).

### 2. `ergebniss.csv` als frischer Zwischenspeicher
Durch den Start-Cleanup (siehe 5) wird die alte `ergebniss.csv` bei jedem
echten Lauf weggeräumt — die Datei sammelt damit **nur die Tracks des aktuellen
Laufs**. Nur Klassen aus `TRACKED_LABELS` landen darin; das ist bereits durch
den Filter `if label not in TRACKED_LABELS: continue` in `core.py` garantiert
(Tracks anderer Klassen entstehen gar nicht erst).

### 3. Neue Spalte `avg_confidence`
Neues Schema (11 Spalten):
```
display_id, kind, track_id, label, start_x, start_y, end_x, end_y,
avg_confidence, first_timestamp, last_timestamp
```
- `core.py` reicht die pro Detection ohnehin vorhandene `confidence` an
  `update_track()` durch.
- `tracking.py` hält pro Track `conf_sum`/`conf_count` und bildet beim Abschluss
  den **laufenden Durchschnitt über alle Frames** (`_attach_avg_confidence`).
- Kein einziger Konfidenzwert → leere Zelle (statt 0.0), damit „unbekannt" und
  „Konfidenz 0" unterscheidbar bleiben.
- `csv_utils.ensure_current_schema()` archiviert automatisch eine alte
  `ergebniss.csv` mit dem 10-Spalten-Schema, falls doch mal eine übrig ist.

### 4. Zwei getrennte Bewegungsbilder, ordentlich benannt
`visualization.py`: statt `tracked_objects_<ts>.png` / `..._ENDE.png` jetzt
```
bewegungsbild_<ts>_flush.png      # alle im Lauf per Timeout geflushten Tracks
bewegungsbild_<ts>_finalize.png   # alle beim Programmende noch aktiven Tracks
```
Beide werden am Programmende erzeugt: das Flush-Bild im `finally`-Block von
`core.py` (aus `flushed_objects`), das Finalize-Bild in `finalize()` (aus den
verbliebenen Tracks). Funktionen `save_movement_image`/`save_summary_image` →
`save_flush_image`/`save_finalize_image`.

### 5. Start-Cleanup (neu: `cleanup_utils.py`)
Beim Start eines echten Zähllaufs (nicht im Snapshot-Modus) werden alle
Artefakte des vorherigen Laufs in `vorherige_laeufe/<Zeitstempel>/` verschoben
(nicht gelöscht):
```
ergebniss.csv, ergebniss.txt (Altbestand), zaehlung.csv,
auto_config_points.csv, auto_config_clusters.png, auto_config_border.png,
bewegungsbild_*.png, tracked_objects_*.png (Altbestand)
```
**Bewahrt** (überdauern den Lauf): `roi_config.json` (aktive Konfiguration),
`camera_raw.png` (Referenzbild). Legt den Archivordner nur an, wenn es
tatsächlich etwas zu archivieren gibt — sauberer Erststart erzeugt keinen
leeren Ordner. Im Snapshot-Modus (`CORE_SNAPSHOT_ONLY`) wird NICHT aufgeräumt.

## Getestet (ohne Hailo, isoliert)

- `ergebniss.csv` mit korrektem 11-Spalten-Schema, `avg_confidence=0.8734`
  bei vorhandener, leer bei fehlender Confidence. `ergebniss.txt` wird nicht
  erzeugt.
- Confidence-Mittelung: `[0.9, 0.8, 0.7] → 0.8000`; 0 Werte → `None`.
- Cleanup: archiviert die richtigen Dateien, bewahrt `roi_config.json` +
  `camera_raw.png`, leerer Erststart → kein Ordner (`None`).
- Alle fünf Dateien kompilieren, keine verwaisten Referenzen auf entfernte
  Funktionen/Namen.

## Geänderte Dateien
```
logging_utils.py   txt-Funktionen raus, avg_confidence-Spalte
tracking.py        confidence in update_track, laufender Durchschnitt, zwei Bilder, kein txt
visualization.py   bewegungsbild_*_flush/_finalize, save_flush/finalize_image
core.py            confidence durchreichen, save_flush_image, Start-Cleanup
cleanup_utils.py   NEU — archive_previous_run()
```

## Nicht Teil dieser Aufgabe (aber notiert)
Das bus/truck-Rätsel aus dem echten Lauf: `TRACKED_LABELS` kommt aus
`roi_config.json["classes"]`, dort fehlten bus/truck — sie erschienen aber in
den Ergebnissen. Entweder wurde der Lauf mit anderer `roi_config.json`
gefahren, oder es gibt einen zweiten Detektionspfad. Sollte vor der finalen
Auswertung noch geklärt werden, ist aber unabhängig von diesem Umbau.
