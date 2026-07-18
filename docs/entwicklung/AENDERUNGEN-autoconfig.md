# Auto-Konfiguration von der GUI entkoppelt — Änderungsprotokoll

**Stand 15.07.2026.** Ziel: Die automatische Wegerkennung
(`auto_config.py` + `auto_config_clustering.py`) läuft jetzt unabhängig von der
GUI (`roi_config_app.py`, tkinter/customtkinter). `config.py` bleibt bewusst
die gemeinsame Parameterquelle — das wird später auch so bleiben.

## Das Problem vorher

`auto_config_clustering.py` importierte im `__main__`-Block:

```python
from roi_config_app import load_first_frame   # nur für die Bildauflösung
```

`roi_config_app.py` zieht beim Import `tkinter`, `customtkinter` und
`PIL.ImageTk` nach. Folge: Die Auto-Konfiguration ließ sich nicht auf einem Pi
ohne Display, nicht in einer schlanken venv und nicht isoliert testen —
obwohl sie sachlich nur `cv2`, `numpy`, `scikit-learn`, `scipy` braucht.

## Die Änderung (kleinstmöglicher Schnitt)

**Neu: `frame_utils.py`** — GUI-freie Frame-Beschaffung aus Bild-/Videodateien,
nur `cv2` + `os`. Enthält:
- `load_frame_from_file(path)` — der datei-basierte Teil des früheren
  `load_first_frame` (Bild direkt, Video über drei OpenCV-Backends mit
  Fallback-Meldung).
- `get_frame_size(path)` — liefert nur `(width, height)`; genau das, was die
  Auto-Konfiguration zur Normalisierung braucht.

**`roi_config_app.py`** — `load_first_frame` behält seinen Kamera-Zweig
(`usb`/`rpi` → Snapshot über `core.py`), delegiert den Datei-Fall aber an
`frame_utils.load_frame_from_file`. Kein Funktionsverlust, kein Duplikat.

**`auto_config_clustering.py`** — importiert die Auflösung jetzt aus
`frame_utils` statt aus `roi_config_app`:

```python
from frame_utils import load_frame_from_file
frame = load_frame_from_file(args.input)
```

## Warum der Kamera-Snapshot NICHT mitgewandert ist

`_capture_snapshot_via_core()` startet `core.py` als Subprozess über die
Hailo-Pipeline (für `--input usb`/`rpi`). Das ist inhärent Pipeline-/GUI-Seite
und hat in einem schlanken Auto-Config-Modul nichts verloren. Wer die
Auto-Konfiguration mit Kameraeingabe fahren will, nimmt vorher einmal ein
`camera_raw.png` auf (über `roi_config_app.py` oder `core.py`) und übergibt
dieses als `--input`.

## Verifiziert

- Alle drei Dateien kompilieren.
- Kein `import roi_config_app` mehr in der Auto-Config-Kette (nur noch in
  Kommentaren/Docstrings).
- **End-to-End-Test mit den echten 56 Punkten aus dem Lauf vom 15.07.** —
  Import der kompletten Kette *ohne* tkinter (nur `config` als
  Parameter-Stub), DBSCAN (6 Cluster) und Randraster (12 Überquerungen)
  liefen sauber durch, `save_auto_regions` schrieb gültiges
  `roi_config.json`. `frame_utils.get_frame_size('camera_raw.png')` = 1280×720.

## Nutzung jetzt (unverändert im Aufruf)

```bash
# DBSCAN-Clustering
python auto_config_clustering.py --input camera_raw.png
# Randraster
python auto_config_clustering.py --input camera_raw.png --border
# Ergebnis übernehmen
python auto_config_clustering.py --input camera_raw.png --border --save
```

Der einzige praktische Unterschied: Es wird jetzt **kein** tkinter/customtkinter
mehr benötigt, um diese Befehle auszuführen.

## Abhängigkeitsgraph nachher

```
auto_config.py              → csv_utils, config            (stdlib + config)
auto_config_clustering.py   → counting, frame_utils, config, sklearn, scipy, cv2, numpy
frame_utils.py              → cv2, os                       (GUI-frei)
roi_config_app.py           → frame_utils, counting, auto_config, ... , tkinter/customtkinter
```

Die Auto-Config-Kette (obere drei Zeilen) berührt tkinter/customtkinter
nirgends mehr.

## Offen / später

- `config.py` bleibt gemeinsame Parameterquelle (bewusste Entscheidung). Falls
  die Auto-Config später ganz eigenständig werden soll, wären die
  `AUTO_CONFIG_*`-Werte als CLI-Argumente mit Defaults der nächste Schritt —
  nicht jetzt nötig.
- `should_count_track()` in `counting.py` ist weiterhin ein Platzhalter
  (akzeptiert jeden Track). Der aus den echten Daten motivierte Kurz-Track-Filter
  (z. B. `truck_ID_2` mit 66 ms) könnte hier ansetzen.
