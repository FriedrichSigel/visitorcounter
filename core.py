"""
Einstiegspunkt: verbindet die Hailo-GStreamer-Pipeline, den Pro-Frame-Callback
und die Module tracking / visualization / logging_utils / config miteinander.

Enthält bewusst nur noch: die Pipeline-Klasse (MyDetectionApp), den
Pro-Frame-Callback (app_callback) und den __main__-Startblock — die eigentliche
Tracking-/Zeichen-/Logging-Logik lebt in den jeweiligen Modulen.
"""

import datetime
import os
import signal

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import cv2
import hailo

from hailo_apps.hailo_app_python.core.common.buffer_utils import get_caps_from_pad, get_numpy_from_buffer
from hailo_apps.hailo_app_python.apps.detection.detection_pipeline import GStreamerDetectionApp

from config import (
    TRACKED_LABELS, SUMMARY_CANVAS_WIDTH, SUMMARY_CANVAS_HEIGHT, RUN_DURATION_SECONDS,
    SNAPSHOT_ONLY, CAMERA_RAW_PATH, LIVE_PREVIEW_HORIZONTAL_FLIP,
    RECORDING_ENABLED, RECORDING_DIR, RECORDING_BITRATE_KBPS,
    RECORDING_SEGMENT_SECONDS, RECORDING_FPS,
)
from tracking import TrackingState
from visualization import (
    draw_live_overlay, draw_detection_count, draw_movement_image, save_flush_image,
    draw_counting_geometry, draw_counts_overlay,
)
from logging_utils import build_log_entry
from cleanup_utils import archive_previous_run
from recording import build_recording_bin, resolve_target_dir, estimate_hours


# -----------------------------------------------------------------------------------------------
# Pipeline-Klasse — überschreibt on_eos() statt on_bus_message().
#
# Die Basisklasse hat für source_type == "file" einen Sonderfall in on_eos():
# sie spult die Pipeline per Seek zurück auf Position 0 und startet die
# Wiedergabe neu ("Video rewound successfully. Restarting playback...") statt
# zu stoppen. on_bus_message() zu überschreiben fängt das NICHT ab — on_eos()
# wird über einen eigenen Pfad aufgerufen. Erst das Überschreiben von on_eos()
# selbst ersetzt die Schleife durch einen echten, einmaligen Stopp.
# Bestätigt von Hailo-Mitarbeitern: https://community.hailo.ai/t/stop-processing-video-files/11231
# -----------------------------------------------------------------------------------------------
class MyDetectionApp(GStreamerDetectionApp):
    def on_eos(self):
        print("End-of-stream (Video zu Ende) — Programm wird beendet.")
        user_data.finalize()   # Alle verbleibenden Tracks speichern und Ausgabebild schreiben
        self.shutdown()        # GStreamer-Pipeline stoppen und die Main Loop beenden


# -----------------------------------------------------------------------------------------------
# Mitschnitt (nur Benchmark-/Laborläufe)
# -----------------------------------------------------------------------------------------------
def _build_recording_sink():
    """
    Bereitet den Aufnahme-Bin vor: Zielordner prüfen, Reichweite abschätzen,
    Bin bauen. Gibt None zurück, wenn die Aufnahme nicht möglich ist — der
    Zähllauf startet dann trotzdem, nur eben ohne Video. Ein fehlender USB-Stick
    darf keinen Messlauf verhindern.
    """
    target_dir, note = resolve_target_dir(RECORDING_DIR)
    print(note)
    if target_dir is None:
        return None

    hours = estimate_hours(target_dir, RECORDING_BITRATE_KBPS)
    if hours is not None:
        print(f"  Reichweite bei dieser Bitrate: ca. {hours:.1f} Stunden")

    return build_recording_bin(
        target_dir,
        bitrate_kbps=RECORDING_BITRATE_KBPS,
        segment_seconds=RECORDING_SEGMENT_SECONDS,
        fps=RECORDING_FPS,
    )


# -----------------------------------------------------------------------------------------------
# Pro-Frame-Callback — wird von GStreamer für jeden Frame aufgerufen, der durch die Pipeline läuft
# -----------------------------------------------------------------------------------------------
def app_callback(pad, info, user_data):
    buffer = info.get_buffer()
    if buffer is None:
        return Gst.PadProbeReturn.OK   # Ungültigen Buffer überspringen

    user_data.increment()
    current_frame = user_data.get_count()
    string_to_print = f"Frame count: {current_frame}\n"

    # Videoformat (z. B. "RGB"), Breite und Höhe aus den Pad-Capabilities lesen
    video_format, width, height = get_caps_from_pad(pad)

    # Frame-Dimensionen beim ersten gültigen Frame merken — später fürs Ausgabebild gebraucht
    if width and height:
        user_data.frame_width = width
        user_data.frame_height = height

    # Rohen Videoframe optional als NumPy-RGB-Array holen (braucht --use-frame)
    frame = None
    if user_data.use_frame and video_format is not None and width is not None and height is not None:
        frame = get_numpy_from_buffer(buffer, video_format, width, height)

        # Snapshot-Modus (SNAPSHOT_ONLY, siehe config.py): sobald der erste
        # echte Frame da ist, unverändert (keine Bounding Boxes/Overlays)
        # als Referenzbild speichern und sofort beenden. Genutzt von
        # roi_config_app.py für --input usb/rpi, damit die Referenzaufnahme
        # exakt aus derselben Pipeline kommt wie später der Live-Betrieb.
        if SNAPSHOT_ONLY and not user_data.snapshot_taken:
            user_data.snapshot_taken = True
            snapshot_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(CAMERA_RAW_PATH, snapshot_bgr)
            print(f"Snapshot gespeichert als {CAMERA_RAW_PATH} "
                  f"({frame.shape[1]}x{frame.shape[0]}) — beende Programm.")
            os.kill(os.getpid(), signal.SIGINT)
            return Gst.PadProbeReturn.OK

    # Hailo-ROI (Root-Metadatenobjekt) und alle Detections aus dem Buffer holen
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    detection_count = 0

    for detection in detections:
        label = detection.get_label()

        # Nur Klassen aus TRACKED_LABELS verarbeiten, alle anderen überspringen
        if label not in TRACKED_LABELS:
            continue

        bbox       = detection.get_bbox()        # Normalisierte Bounding Box [0.0 – 1.0]
        confidence = detection.get_confidence()  # Konfidenzwert [0.0 – 1.0]

        # Eindeutige Tracker-ID aus der TRACKER_PIPELINE holen
        # HINWEIS: fällt auf 0 zurück, wenn keine Tracker-ID vorhanden ist. Mehrere
        # gleichzeitig ungetrackte Detections würden dann auf demselben Key kollidieren.
        # In der Praxis selten (der Tracker vergibt normalerweise eine ID), aber als
        # bekannte Einschränkung dokumentiert.
        track_id = 0
        track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
        if len(track) == 1:
            track_id = track[0].get_id()

        # Normalisierte Bbox in absolute Koordinaten umrechnen
        x_min = bbox.xmin()
        y_min = bbox.ymin()
        x_max = x_min + bbox.width()
        y_max = y_min + bbox.height()

        # Mittelpunkt der Bounding Box in Pixelkoordinaten berechnen
        cx = int(((x_min + x_max) / 2) * width) if width else 0
        cy = int(((y_min + y_max) / 2) * height) if height else 0
        center = (cx, cy)

        # Vollständigen zeitgestempelten Log-String für dieses Detection-Ereignis bauen
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry = build_log_entry(timestamp, label, track_id, cx, cy, x_min, y_min, x_max, y_max)

        # update_track() vergibt bei neuen Tracks eine lesbare, pro Klasse
        # hochzählende display_id (z. B. "car_ID_3") und gibt sie zurück
        display_id = user_data.update_track(track_id, label, center, entry, current_frame, timestamp, confidence)

        string_to_print += f"Detection: {display_id} Confidence: {confidence:.2f}\n"
        detection_count += 1

        # --- Auf dem Live-Videoframe zeichnen (nur wenn --use-frame aktiv ist) ---
        if user_data.use_frame and frame is not None:
            draw_live_overlay(frame, x_min, y_min, x_max, y_max, width, height,
                               display_id, label, confidence, center)

    # --- Flush-Logik: Objekte entfernen, die seit frames_until_gone nicht mehr gesehen wurden ---
    user_data.flush_stale(current_frame)

    # --- Frame fertigstellen und an die Anzeige schicken ---
    if user_data.use_frame and frame is not None:
        draw_detection_count(frame, detection_count)

        # Zähllinie + aktuelle IN/OUT-Zählerstände einblenden (nur zur
        # Kontrolle/Kalibrierung — die eigentliche Zählung passiert erst bei
        # Track-Abschluss in tracking.py, nicht hier)
        if user_data.counter is not None and width and height:
            geometry_pixel = user_data.counter.get_geometry_pixels(width, height)
            draw_counting_geometry(frame, user_data.counter.mode, geometry_pixel)
            draw_counts_overlay(frame, user_data.counter.summary_lines())

        # WICHTIG: GStreamer liefert Frames in RGB, OpenCV erwartet BGR — Konvertierung nötig
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Nur die Live-Vorschau spiegeln, falls aktiviert (siehe config.py) —
        # unsere Overlays sind zu diesem Zeitpunkt schon eingezeichnet,
        # werden also mitgespiegelt (bleiben also korrekt zum Bildinhalt
        # ausgerichtet). Die Zähllogik selbst ist davon nicht betroffen.
        if LIVE_PREVIEW_HORIZONTAL_FLIP:
            frame = cv2.flip(frame, 1)

        # Annotierten Frame in die Anzeige-Queue geben
        user_data.set_frame(frame)

    # Alle gesammelten Detection-Infos dieses Frames auf der Konsole ausgeben
    print(string_to_print)

    return Gst.PadProbeReturn.OK


# -----------------------------------------------------------------------------------------------
# Einstiegspunkt
# -----------------------------------------------------------------------------------------------
if __name__ == "__main__":
    # Hält den gesamten Tracking-State über alle Frames hinweg
    user_data = TrackingState()
    user_data.snapshot_taken = False

    if SNAPSHOT_ONLY:
        # Frame-Daten werden für den Snapshot gebraucht, auch wenn
        # --use-frame nicht explizit übergeben wurde.
        user_data.use_frame = True
        print(f"Snapshot-Modus aktiv — speichere den ersten Frame als "
              f"{CAMERA_RAW_PATH} und beende dann automatisch.")
    else:
        # Nur bei einem echten Zähllauf aufräumen: Artefakte des vorherigen
        # Laufs in einen Archivordner verschieben, damit dieser Lauf mit einem
        # sauberen Arbeitsverzeichnis startet (ergebniss.csv als frischer
        # Zwischenspeicher, keine alten Bewegungsbilder/Sammeldaten dazwischen).
        # Im Snapshot-Modus NICHT aufräumen — der erzeugt nur camera_raw.png
        # und soll bestehende Ergebnisse nicht anfassen.
        archive_previous_run()

    # Pipeline erzeugen, Callback und Tracking-State übergeben
    app = MyDetectionApp(app_callback, user_data)

    # Der hailotracker-Baustein trackt in der Basis-Pipeline standardmäßig NUR
    # eine einzige Klasse (class-id=1 -> "person" nach COCO-Nummerierung).
    # Alle anderen Klassen bekommen dadurch nie eine echte HAILO_UNIQUE_ID und
    # fallen in app_callback() auf track_id=0 zurück — das sah aus wie ein
    # Tracking-Bug, war aber diese Pipeline-Einstellung.
    # -1 = klassenübergreifend tracken. Muss vor app.run() gesetzt werden
    # (das Element ist nur im NULL/READY-Zustand änderbar).
    # Quelle: https://community.hailo.ai/t/how-to-change-the-class-hailo-tracker-is-tracking/12693
    hailotracker = app.pipeline.get_by_name("hailo_tracker")
    if hailotracker is not None:
        hailotracker.set_property("class-id", -1)
    else:
        print("WARNUNG: hailotracker-Element 'hailo_tracker' nicht gefunden — "
              "class-id konnte nicht gesetzt werden, es wird vermutlich weiter "
              "nur eine Klasse getrackt.")

    # Die Basis-Pipeline zeigt standardmäßig ZWEI Fenster: das eigene
    # fpsdisplaysink-Element "hailo_display" (Titel "Hailo Detection App",
    # zeigt Hailos Standard-Overlay) UND, wenn --use-frame aktiv ist, das
    # separate "User Frame"-Fenster aus unserem eigenen draw_live_overlay().
    # Wir wollen nur Letzteres behalten, also wird die video-sink-Eigenschaft
    # von "hailo_display" auf ein fakesink umgebogen (verwirft die Frames,
    # ohne sie anzuzeigen) statt xvimagesink. Muss vor app.run() passieren.
    # Quelle: https://community.hailo.ai/t/how-can-i-stop-displaying-the-main-frame-in-detection-py-in-hailo-rpi5-examples/3020
    #
    # Genau dieser Sink ist zugleich der Einhängepunkt für den Mitschnitt
    # (RECORDING_ENABLED, siehe recording.py): der Videostrom, der hier sonst
    # verworfen wird, geht dann stattdessen in den Aufnahme-Bin. Die
    # Zählpipeline selbst bleibt dadurch unverändert — sie bekommt weder ein
    # zusätzliches Element in ihren Verarbeitungspfad noch eine zweite
    # Kameraöffnung, die ohnehin nicht möglich wäre.
    hailo_display = app.pipeline.get_by_name("hailo_display")
    if hailo_display is not None:
        recording_sink = None
        if RECORDING_ENABLED:
            recording_sink = _build_recording_sink()
        if recording_sink is not None:
            hailo_display.set_property("video-sink", recording_sink)
        else:
            fakesink = Gst.ElementFactory.make("fakesink", "hailo_display_fakesink")
            fakesink.set_property("sync", False)
            hailo_display.set_property("video-sink", fakesink)
    else:
        print("WARNUNG: Display-Element 'hailo_display' nicht gefunden — "
              "es öffnen sich vermutlich weiterhin zwei Fenster.")
        if RECORDING_ENABLED:
            print("WARNUNG: Ohne dieses Element kann auch der Mitschnitt nicht "
                  "eingehängt werden — es wird KEIN Video aufgezeichnet.")

    # Optionales Zeitlimit (z. B. für --input usb/rpi ohne natürliches
    # Video-Ende). In config.py über RUN_DURATION_SECONDS einstellbar;
    # None (Standard) = keine Begrenzung, wie bisher manuell per Ctrl+C
    # stoppen.
    #
    # WICHTIG: app.on_eos() hier direkt aufzurufen funktioniert NICHT
    # zuverlässig — die Pipeline lief in Tests danach im Hintergrund weiter
    # (weitere Frames wurden verarbeitet), bis irgendwann ein zweites,
    # echtes EOS/Fehler-Ereignis eintraf und alles doppelt/durcheinander lief,
    # bis hin zu einem harten Absturz. Stattdessen schickt sich das Programm
    # per Timer dasselbe Signal, das auch Ctrl+C auslöst (SIGINT) — das ist
    # der einzige Shutdown-Pfad, der sich in allen bisherigen Tests zuverlässig
    # sauber verhalten hat (except KeyboardInterrupt -> finally in __main__).
    if RUN_DURATION_SECONDS is not None:
        def _stop_after_timeout():
            print(f"Zeitlimit von {RUN_DURATION_SECONDS} Sekunden erreicht — Programm wird beendet.")
            os.kill(os.getpid(), signal.SIGINT)
            return False  # GLib-Konvention: False = Timer nicht wiederholen
        GLib.timeout_add_seconds(RUN_DURATION_SECONDS, _stop_after_timeout)

    try:
        # Startet die GStreamer-Pipeline — blockiert bis EOS oder Fehler
        app.run()
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        # Läuft immer — egal ob durch EOS, Ctrl+C oder etwas anderes beendet.
        # Unbedingt aufrufbar: finalize() ist ein No-Op, falls es schon über
        # on_eos() lief (siehe self.finalized in TrackingState).
        user_data.finalize()

        print("Stopp")

        # Abschließende Zusammenfassung aller im Lauf geflushten Objekte
        # (über die 30-Frame-Timeout-Logik geflusht, NICHT die finalize()-Objekte)
        for obj in user_data.flushed_objects:
            print(f"{obj['display_id']} | Start: {obj['start']} | End: {obj['end']}")

        # Canvas-Größe = tatsächliche Videoauflösung, damit Positionen im Bild
        # exakt den Pixelkoordinaten aus dem Video entsprechen. Fallback auf
        # die feste Größe aus config.py nur, falls nie ein gültiger Frame
        # verarbeitet wurde (frame_width/height dann noch None).
        summary_width = user_data.frame_width or SUMMARY_CANVAS_WIDTH
        summary_height = user_data.frame_height or SUMMARY_CANVAS_HEIGHT

        img = draw_movement_image(summary_width, summary_height, user_data.flushed_objects)
        path = save_flush_image(img)
        print(f"Bewegungsbild (Flush) gespeichert als {path}")
