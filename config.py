"""
Zentrale Konfiguration: welche Objektklassen getrackt werden, ihre
Darstellungsfarben, und Stellschrauben für die Tracking-Logik.

Bewusst von der eigentlichen Tracking-/Zeichenlogik getrennt, damit
zukünftige Änderungen (z. B. weitere Klassen, andere Flush-Zeit) an
genau einer Stelle passieren.
"""

import json
import os

# --- ROI-Konfiguration (Zählgeometrie, Klassen, Richtung) ---
# Wird von roi_config_app.py geschrieben (visuelles Konfigurationswerkzeug,
# Linie/Fläche(n) per Mausklick setzen) und hier beim Start automatisch
# geladen. Falls die Datei noch nicht existiert (z. B. beim allerersten
# Start), greifen die Standardwerte in _DEFAULT_ROI_CONFIG unten.
#
# "mode" unterstützt "line", "roi" und "multi_roi" (siehe counting.py).
# "auto" (automatische Wegerkennung per Clustering) ist für später
# vorgesehen (siehe ToDo.md), damit sich das Dateiformat dann nicht nochmal
# ändern muss.
ROI_CONFIG_PATH = "roi_config.json"

# Wird von roi_config_app.py für --input usb/rpi genutzt: core.py speichert
# dort beim allerersten Frame ein Referenzbild und beendet sich sofort
# danach (siehe SNAPSHOT_ONLY unten) — GARANTIERT dieselbe Auflösung und
# denselben Bildausschnitt wie später die Live-Pipeline, weil es exakt
# dieselbe Pipeline ist. Eine unabhängige cv2.VideoCapture()-Aufnahme
# konnte davon abweichen (andere Auflösung/anderer Ausschnitt als das, was
# die Hailo-Pipeline intern verarbeitet) — genau das hat die
# Größen-/Ausrichtungs-Diskrepanz zwischen Konfiguration und Live-Bild
# verursacht, siehe HANDOFF.md.
CAMERA_RAW_PATH = "camera_raw.png"

# Per Umgebungsvariable von roi_config_app.py gesetzt (nicht als CLI-Flag,
# da core.py --input/--use-frame intern vom Hailo-Framework geparst werden
# und wir nicht wissen, ob zusätzliche eigene CLI-Argumente dort vertragen
# werden — Umgebungsvariablen umgehen dieses Risiko, siehe auch
# RUN_DURATION_SECONDS/AUTO_CONFIG_COLLECTION_ENABLED oben für dasselbe Muster).
_env_snapshot_only = os.environ.get("CORE_SNAPSHOT_ONLY")
SNAPSHOT_ONLY = (_env_snapshot_only.lower() == "true") if _env_snapshot_only is not None else False

# Dreht NUR das "User Frame"-Live-Vorschaufenster horizontal, NACHDEM
# unsere eigenen Overlays (Boxen, Zählgeometrie) schon draufgezeichnet
# sind — betrifft ausschließlich die Anzeige, NICHT die Zähllogik (die
# arbeitet auf den rohen Hailo-Erkennungsdaten, lange bevor irgendetwas
# gezeichnet oder angezeigt wird). Hintergrund: Bei --input usb scheint
# Hailos eigener Anzeigemechanismus (set_frame(), für uns nicht einsehbar)
# das Bild zusätzlich zu spiegeln — dieser Flip hier gleicht das aus, falls
# aktiviert. Erst ausprobieren, ob True das Live-Fenster wieder unspiegelt
# zeigt (mit camera_raw.png vergleichen), dann dauerhaft setzen.
LIVE_PREVIEW_HORIZONTAL_FLIP = False

# Auto-Konfiguration (automatische Zonenerkennung per Clustering/Randraster,
# Tab 5 in app.py + die beiden "Auto: ..."-Zählmodi in roi_config_app.py)
# ist noch nicht ausgereift genug für den Produktiveinsatz. Auf False
# gesetzt blendet app.py Tab 5 aus und roi_config_app.py die beiden
# Auto-Zählmodi im Konfigurationsschritt - der Code bleibt dabei komplett
# erhalten, es wird nur die Sichtbarkeit in der UI umgeschaltet. Für einen
# späteren Wiedereinstieg einfach auf True setzen.
SHOW_AUTO_CONFIG = False

_DEFAULT_ROI_CONFIG = {
    "mode": "line",
    "points": [[0.0, 0.5], [1.0, 0.5]],
    "regions": [],
    "classes": ["person", "bicycle", "car", "motorcycle", "bus", "truck"],
    "reverse_direction": False,
    "snap_to_nearest": False,
    # Erst ab dieser Erkennungskonfidenz wird ein Objekt gezählt (0.0-1.0).
    "min_confidence": 0.5,
    # Nur für mode="multi_roi": Namen der Flächen, die als IN-Bereich gelten
    # (Liste; ältere Konfigurationen speichern hier einen einzelnen String).
    # Übergang aus einer OUT- in eine IN-Fläche = IN, umgekehrt = OUT. Wird
    # für den LoRa-/MQTT-Versand gebraucht, damit multi_roi dasselbe
    # IN/OUT-Format nutzen kann.
    "in_field": [],
}


def _load_roi_config():
    if os.path.isfile(ROI_CONFIG_PATH):
        try:
            with open(ROI_CONFIG_PATH) as f:
                loaded = json.load(f)
            merged = dict(_DEFAULT_ROI_CONFIG)
            merged.update(loaded)
            return merged
        except (json.JSONDecodeError, OSError, KeyError) as e:
            print(f"WARNUNG: {ROI_CONFIG_PATH} konnte nicht gelesen werden ({e}) — nutze Standardwerte.")
    return dict(_DEFAULT_ROI_CONFIG)


_roi_config = _load_roi_config()

# Aktueller Zählmodus: "line", "roi" oder "multi_roi" (siehe counting.py).
COUNTING_MODE = _roi_config["mode"]

# COCO-Klassen, die getrackt werden — alle anderen Detections werden ignoriert.
# Kommt aus roi_config.json (per Checkbox in roi_config_app.py auswählbar),
# sonst alle sechs Klassen als Default.
TRACKED_LABELS = set(_roi_config["classes"])

# Zählgeometrie in normalisierten Koordinaten (0.0-1.0, unabhängig von der
# tatsächlichen Videoauflösung). Bei mode="line": genau zwei Punkte (A, B).
# Bei mode="roi": drei oder mehr Punkte (Polygon-Eckpunkte). Bei
# mode="multi_roi" ungenutzt (siehe COUNTING_REGIONS stattdessen).
COUNTING_POINTS = tuple(tuple(point) for point in _roi_config["points"])

# Nur bei mode="multi_roi" genutzt: Liste mehrerer benannter Flächen,
# [{"name": str, "points": [[x,y], ...]}, ...], je normalisiert 0.0-1.0.
COUNTING_REGIONS = _roi_config["regions"]

# Nur bei mode="multi_roi" genutzt: Punkte außerhalb aller Flächen der
# nächstgelegenen Fläche zuordnen, statt sie als "außerhalb" zu zählen.
# Opt-in-Checkbox in roi_config_app.py.
COUNTING_SNAP_TO_NEAREST = _roi_config["snap_to_nearest"]

# Dreht die IN/OUT-Zuordnung um, ohne die Linie selbst zu ändern. Kommt aus
# roi_config.json (Checkbox in roi_config_app.py).
REVERSE_COUNTING_DIRECTION = _roi_config["reverse_direction"]

# Erkennungen unterhalb dieser Konfidenz werden nicht gezählt. Aus der
# Konfiguration mit Rückfall auf 0.5, falls das Feld fehlt (ältere Dateien).
COUNTING_MIN_CONFIDENCE = float(_roi_config.get("min_confidence", 0.5))

# BGR-Farbtupel fürs Live-Overlay auf dem Videoframe (OpenCV nutzt BGR, nicht RGB).
# Bewusst für ALLE möglichen Klassen definiert, unabhängig von TRACKED_LABELS —
# betrifft nur die Darstellung, nicht die Filterung.
LABEL_COLORS_BGR = {
    "person":     (0, 255, 0),
    "bicycle":    (0, 128, 255),
    "car":        (255, 128, 0),
    "motorcycle": (255, 0, 128),
    "bus":        (128, 0, 255),
    "truck":      (255, 255, 0),
}

# Benannte Farben fürs Pillow-basierte Bewegungsbild (finalize() und Endauswertung)
TRACK_COLORS = {
    "person":     "green",
    "bicycle":    "blue",
    "car":        "orange",
    "motorcycle": "pink",
    "bus":        "purple",
    "truck":      "yellow",
}

# Anzahl aufeinanderfolgender Frames ohne Sichtung, bevor ein Objekt geflusht wird
FRAMES_UNTIL_GONE = 30

# Obergrenze für die im Speicher gehaltenen geflushten Tracks (nur für das
# Flush-Bewegungsbild am Laufende). Verhindert unbegrenztes Speicherwachstum bei
# sehr langen Läufen; die vollständige Track-Historie steht weiterhin in
# ergebniss.csv. 0/None wäre unbegrenzt — bewusst gedeckelt.
MAX_FLUSHED_OBJECTS = 500

# Maximale Laufzeit in Sekunden, danach beendet sich das Programm automatisch
# genau wie bei einem echten Video-Ende (inkl. finalize() und Bewegungsbild).
# None = keine Begrenzung, Programm läuft bis manuell per Ctrl+C abgebrochen
# (bisheriges Standardverhalten). Besonders nützlich bei --input usb/rpi,
# wo es kein natürliches Video-Ende (EOS) gibt.
#
# Per Umgebungsvariable überschreibbar (setzt z. B. app.py, wenn im Tab
# "Auto-Konfiguration" eine Sammeldauer gewählt wird). Standard ist KEIN
# Zeitlimit — ein normaler Zähllauf läuft, bis er per Video-Ende oder Stopp
# beendet wird. Das Zeitlimit ist nur für die Auto-Config-Datensammlung
# gedacht und wird dort über die GUI gesetzt.
_env_duration = os.environ.get("RUN_DURATION_SECONDS")
RUN_DURATION_SECONDS = int(_env_duration) if _env_duration else None

# --- Mitschnitt für Benchmark-/Laborläufe (recording.py) -------------------
#
# WICHTIG — Abgrenzung zum Normalbetrieb:
# Der Sensor ist nach Privacy by Design gebaut: im Zählbetrieb werden Frames
# verarbeitet und VERWORFEN, gespeichert werden nur aggregierte Zählwerte.
# Diese Mitschnittfunktion ist die einzige Ausnahme. Sie dient ausschliesslich
# dazu, die Zählgenauigkeit unter Laborbedingungen gegen echtes Bildmaterial
# zu prüfen (Ground Truth für die Evaluation). Sie ist deshalb standardmässig
# AUS, muss bewusst eingeschaltet werden und darf im Feldeinsatz NICHT
# verwendet werden.
# Regeln: docs/entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md
_env_recording = os.environ.get("RECORDING_ENABLED")
RECORDING_ENABLED = (_env_recording.lower() == "true") if _env_recording is not None else False

# Zielordner. "auto" = eingehängten USB-Datenträger suchen und dort schreiben;
# nur wenn keiner gefunden wird, wird auf ./aufnahmen (SD-Karte) ausgewichen.
# Alternativ ein fester Pfad, z. B. "/media/fritz/STICK/aufnahmen".
RECORDING_DIR = os.environ.get("RECORDING_DIR", "auto")

# Bitrate in kbit/s. 2000 reicht für 720p, um Übertritte sicher nachzuvollziehen
# (~0,9 GB pro Stunde).
RECORDING_BITRATE_KBPS = int(os.environ.get("RECORDING_BITRATE_KBPS", "2000"))

# Länge eines Segments in Sekunden. Kürzere Segmente = weniger Verlust bei
# einem Absturz und früher hochladbar.
RECORDING_SEGMENT_SECONDS = int(os.environ.get("RECORDING_SEGMENT_SECONDS", "600"))

# Bilder pro Sekunde im Mitschnitt. Der Pi 5 encodiert in Software (kein
# Hardware-H.264 mehr), deshalb bewusst niedrig — 15 fps genügen, um
# Übertritte zu beurteilen.
RECORDING_FPS = int(os.environ.get("RECORDING_FPS", "15"))

# Container: "mkv" (Standard) oder "mp4". MKV ist absturzfest — MP4 schreibt
# sein Inhaltsverzeichnis erst beim Schliessen und ist bei einem Abbruch
# komplett unlesbar, obwohl die Bilddaten auf der Platte liegen.
RECORDING_CONTAINER = os.environ.get("RECORDING_CONTAINER", "mkv")


# Ob die Zähllogik aktiv ist. False = nur Tracking wie bisher, keine Zählung.
COUNTING_ENABLED = True

# Fallback-Canvas-Größe für das Endauswertungsbild, NUR falls nie ein
# gültiger Frame verarbeitet wurde (frame_width/height dann None). Im
# Normalfall wird stattdessen die tatsächliche Videoauflösung verwendet.
SUMMARY_CANVAS_WIDTH = 1500
SUMMARY_CANVAS_HEIGHT = 1500

# --- Auto-Konfiguration: Datensammlung & Batch-Einteilung ---
# Vorstufe für den geplanten "auto"-Zählmodus (automatische Wegerkennung
# per Clustering, siehe ToDo.md). Siehe auto_config.py für die Logik.

# Schaltet die Datensammlung ein. Wenn True, schreibt tracking.py bei jedem
# abgeschlossenen Track zusätzlich zu ergebniss.csv einen Punkt in die
# eigene Datei auto_config_points.csv. Die Sammeldauer wird nicht hier,
# sondern über RUN_DURATION_SECONDS gesteuert — für die gewünschte
# Sammeldauer setzen und core.py normal laufen lassen.
#
# Per Umgebungsvariable überschreibbar (setzt app.py, wenn die Sammlung
# über die GUI aktiviert wird), sonst gilt der Wert unten.
_env_collection = os.environ.get("AUTO_CONFIG_COLLECTION_ENABLED")
AUTO_CONFIG_COLLECTION_ENABLED = (_env_collection.lower() == "true") if _env_collection is not None else False

# "time_window": ein neuer Batch nach jeweils AUTO_CONFIG_BATCH_SECONDS
# Sekunden. "fixed_size": ein Batch pro AUTO_CONFIG_BATCH_SIZE Punkte.
AUTO_CONFIG_BATCH_STRATEGY = "time_window"
AUTO_CONFIG_BATCH_SECONDS = 300
AUTO_CONFIG_BATCH_SIZE = 50

# DBSCAN-Parameter fürs Clustering der gesammelten Start-/Endpunkte (Paket 3).
# eps in PIXELN (nicht normalisiert) — abhängig von Videoauflösung und
# Kameraabstand ggf. anpassen: zu klein -> viele kleine Cluster/Ausreißer,
# zu groß -> unterschiedliche Wege verschmelzen zu einem Cluster.
# min_samples: Mindestanzahl Punkte, um überhaupt einen Cluster zu bilden;
# kleinere Ansammlungen gelten als Ausreißer (Rauschen), nicht als Cluster.
AUTO_CONFIG_DBSCAN_EPS_PIXELS = 50
AUTO_CONFIG_DBSCAN_MIN_SAMPLES = 3

# --- Auto-Konfiguration: Randraster-Modus (Alternative zum Clustering) ---
# Nur relevant mit --border in auto_config_clustering.py. Fester Raster aus
# ROI-Flächen entlang der vier Bildränder, statt Zonen aus den gesammelten
# Punkten zu clustern — sinnvoll, wenn die Objekterkennung Tracks
# zwischendurch verliert und dadurch Start-/Endpunkte in der Bildmitte
# entstehen, die keine echten Ein-/Ausgänge sind und das Clustering verfälschen.
AUTO_CONFIG_BORDER_SEGMENTS_PER_EDGE = 4
AUTO_CONFIG_BORDER_DEPTH_RATIO = 0.08

# Mindest-Pixelabstand zwischen Start- und Endposition eines Tracks, damit
# er als echte Randüberquerung gilt (nicht nur als kurz verlorene und an
# fast derselben Stelle wieder aufgenommene Erkennung).
AUTO_CONFIG_MIN_TRACK_DISTANCE_PIXELS = 40
