"""
Tracking-State und -Logik: welche Objekte gerade getrackt werden,
Aktualisierung pro Frame, und das Flushen von Objekten, die verschwunden sind.

Ab dieser Version pro Klasse getrennt: tracked_objects ist ein Dict von
Klasse -> {track_id: daten}, statt einem einzigen flachen Dict über alle
Klassen hinweg. Damit hat jede Klasse (person, car, bicycle, ...) ihren
eigenen ID-Raum — ein "car" mit ID 3 und eine "person" mit ID 3 können sich
nicht mehr gegenseitig überschreiben (behebt das insbesondere für den
track_id=0-Fallback klassenübergreifend, siehe HANDOFF.md Abschnitt 4).
"""

import threading

from collections import deque

from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class

from config import (
    FRAMES_UNTIL_GONE, TRACKED_LABELS,
    COUNTING_POINTS, COUNTING_REGIONS, COUNTING_ENABLED, COUNTING_MODE,
    REVERSE_COUNTING_DIRECTION, COUNTING_SNAP_TO_NEAREST,
    AUTO_CONFIG_COLLECTION_ENABLED, MAX_FLUSHED_OBJECTS, DEBUG_FILES_ENABLED,
)
from counting import build_counter, should_count_track
from logging_utils import log_track_event_csv, log_count_event
from visualization import draw_movement_image, save_flush_image, save_finalize_image
from auto_config import log_track_for_collection


class TrackingState(app_callback_class):
    """
    Hält den gesamten Tracking-State über alle Frames hinweg.
    Entspricht der bisherigen user_app_callback_class — hierher verschoben,
    weil sie inhaltlich Tracking-State ist, keine Pipeline-Verdrahtung.
    """

    def __init__(self):
        super().__init__()  # Setzt Frame-Zähler und use_frame-Flag aus der Basisklasse

        # Aktive Tracks, pro Klasse getrennt gehalten:
        # {"person": {track_id: {...}}, "car": {track_id: {...}}, ...}
        # Jeder innere Eintrag: {"object", "start", "end", "first_entry",
        # "last_entry", "first_timestamp", "last_timestamp", "last_seen_frame"}
        # Für jede Klasse aus TRACKED_LABELS wird direkt ein leeres Dict
        # angelegt, damit spätere Auswertungen ("wie viele Autos gerade
        # aktiv?") nicht erst prüfen müssen, ob die Klasse schon existiert.
        self.tracked_objects = {label: {} for label in TRACKED_LABELS}

        # Läuft pro Klasse separat hoch, sobald ein neuer Track dieser Klasse
        # entsteht — ergibt lesbare IDs wie "car_ID_3" statt der rohen,
        # klassenübergreifend geteilten Hailo-track_id. Wird NIE zurückgesetzt
        # oder wiederverwendet, auch nicht nach einem Flush — der Endstand
        # ist damit gleichzeitig die Gesamtzahl unterschiedlicher Objekte
        # dieser Klasse im gesamten Lauf.
        self.class_counters = {label: 0 for label in TRACKED_LABELS}

        # Objekte, die nach dem Verschwinden aus tracked_objects entfernt wurden.
        # Bleibt bewusst eine flache Liste (nicht pro Klasse verschachtelt) —
        # jedes Element trägt "object" (Klasse) und "id" schon mit, das reicht
        # für die Endauswertung (Bild, CSV) völlig aus.
        # Deque statt Liste mit fester Obergrenze: Bei sehr langen Läufen (viele
        # tausend Frames) würde eine unbegrenzte Liste stetig Speicher belegen,
        # und das Flush-Bewegungsbild würde mit tausenden überlagerten
        # Trajektorien ohnehin unlesbar. Die Deque behält automatisch nur die
        # letzten MAX_FLUSHED_OBJECTS Tracks (FIFO). Die CSV-Ausgabe
        # (ergebniss.csv) enthält weiterhin ALLE Tracks — hier geht es nur um
        # die Bild-Zwischenspeicherung.
        self.flushed_objects = deque(maxlen=MAX_FLUSHED_OBJECTS)

        # Lock — der Callback läuft im GStreamer-Thread,
        # finalize() kann im Hauptthread laufen — Lock verhindert Race Conditions
        self.lock = threading.Lock()

        # Frame-Dimensionen des Videos — beim ersten gültigen Frame gesetzt,
        # werden später fürs Ausgabebild gebraucht
        self.frame_width = None
        self.frame_height = None

        # finalize() kann theoretisch zweimal aufgerufen werden (einmal über
        # on_eos(), einmal unbedingt im finally-Block von __main__). Dieses
        # Flag macht den zweiten Aufruf zu einem No-Op, statt das echte Bild
        # mit einer leeren Fläche zu überschreiben.
        self.finalized = False

        # Zähllogik: prüft bei ABSCHLUSS eines Tracks (Flush oder Finalize —
        # also an derselben Stelle, an der auch ergebniss.csv geschrieben
        # wird), ob die Strecke Start->Ende die konfigurierte Zählgeometrie
        # kreuzt. None, wenn COUNTING_ENABLED = False in config.py.
        _geometry = COUNTING_REGIONS if COUNTING_MODE == "multi_roi" else COUNTING_POINTS
        self.counter = (
            build_counter(COUNTING_MODE, _geometry, TRACKED_LABELS,
                          reverse=REVERSE_COUNTING_DIRECTION, snap_to_nearest=COUNTING_SNAP_TO_NEAREST)
            if COUNTING_ENABLED else None
        )

    def update_track(self, track_id, label, center, entry, current_frame, timestamp, confidence=None):
        """
        Legt einen neuen Track an oder aktualisiert einen bestehenden für den
        aktuellen Frame. Gibt die lesbare display_id zurück (z. B. "car_ID_3"),
        damit der Aufrufer sie sofort fürs Live-Overlay/den Frame-Log nutzen kann.

        confidence: Erkennungskonfidenz dieser Detection (0.0-1.0). Wird pro
        Track als laufender Durchschnitt über alle Frames gehalten
        (conf_sum / conf_count), damit ein einzelner Ausreißer-Frame den Wert
        nicht dominiert.
        """
        with self.lock:
            # setdefault statt direktem Zugriff: falls label doch mal nicht in
            # TRACKED_LABELS vorinitialisiert war, wird die Klasse hier sicher angelegt.
            class_tracks = self.tracked_objects.setdefault(label, {})

            if track_id not in class_tracks:
                # Erste Sichtung dieser track_id innerhalb dieser Klasse — neue
                # display_id vergeben und Eintrag anlegen:
                # - "object":          Klassenname (z. B. "car")
                # - "display_id":      lesbare, pro Klasse hochzählende ID (z. B. "car_ID_3"), bleibt fix
                # - "start":           Mittelpunkt bei der ersten Detection (wird nie wieder verändert)
                # - "end":             Mittelpunkt (wird jeden Frame aktualisiert)
                # - "first_entry":     vollständiger Log-String der ersten Detection (bleibt fix)
                # - "last_entry":      vollständiger Log-String der letzten Detection (wird aktualisiert)
                # - "first_timestamp": roher Zeitstempel der ersten Detection (bleibt fix) — für CSV-Export
                # - "last_timestamp":  roher Zeitstempel der letzten Detection (wird aktualisiert) — für CSV-Export
                # - "last_seen_frame": Frame-Nummer (wird aktualisiert, Basis für die Flush-Logik)
                # - "conf_sum"/"conf_count": laufende Summe/Anzahl der Konfidenzwerte für den Durchschnitt
                self.class_counters[label] = self.class_counters.get(label, 0) + 1
                display_id = f"{label}_ID_{self.class_counters[label]}"
                class_tracks[track_id] = {
                    "object":          label,
                    "display_id":      display_id,
                    "start":           center,
                    "end":             center,
                    "first_entry":     entry,
                    "last_entry":      entry,
                    "first_timestamp": timestamp,
                    "last_timestamp":  timestamp,
                    "last_seen_frame": current_frame,
                    "conf_sum":        confidence if confidence is not None else 0.0,
                    "conf_count":      1 if confidence is not None else 0,
                }
            else:
                # Objekt schon bekannt — nur die Felder aktualisieren, die sich ändern
                class_tracks[track_id]["end"]             = center
                class_tracks[track_id]["last_entry"]      = entry
                class_tracks[track_id]["last_timestamp"]  = timestamp
                class_tracks[track_id]["last_seen_frame"] = current_frame
                if confidence is not None:
                    class_tracks[track_id]["conf_sum"]   += confidence
                    class_tracks[track_id]["conf_count"] += 1
                display_id = class_tracks[track_id]["display_id"]

            return display_id

    @staticmethod
    def _attach_avg_confidence(data):
        """Ergänzt data um "avg_confidence" (Mittel über alle Frames) — None,
        wenn kein einziger Konfidenzwert vorlag."""
        count = data.get("conf_count", 0)
        data["avg_confidence"] = (data["conf_sum"] / count) if count else None
        return data

    def _check_counting(self, data):
        """
        Wird für einen gerade ABGESCHLOSSENEN Track aufgerufen (aus
        flush_stale() oder finalize() — genau dort, wo auch ergebniss.csv
        geschrieben wird). Prüft, ob die Strecke Start->Ende die Zähl-
        geometrie kreuzt, und protokolliert das Ergebnis in zaehlung.csv.

        Nutzt bewusst nur Start-/Endposition des gesamten Tracks, nicht den
        Weg pro Frame — einfacher und ausreichend, solange Objekte die
        Geometrie nicht mehrfach hin und her überqueren.

        check_crossing() gibt (text, ist_übergang) zurück. Bei
        ist_übergang=False (aktuell nur bei MultiRoiCounter: Start und Ende
        im selben Bereich) wird trotzdem protokolliert, aber NICHT gezählt —
        so bleibt sichtbar, dass der Track existierte, ohne die
        Zählerstände zu verfälschen.
        """
        if self.counter is None:
            return
        if not should_count_track(data):
            return

        direction, is_transition = self.counter.check_crossing(
            data["object"], data["start"], data["end"],
            self.frame_width, self.frame_height,
        )
        if direction is None:
            return

        log_count_event(data["last_timestamp"], data["display_id"], data["object"],
                         direction, is_transition)
        if is_transition:
            print(f"ZÄHLUNG: {data['display_id']} hat die Linie überquert ({direction})")
        else:
            print(f"INFO: {data['display_id']} — kein echter Übergang, nur protokolliert ({direction})")

    def flush_stale(self, current_frame):
        """Entfernt und protokolliert Objekte, die seit FRAMES_UNTIL_GONE Frames nicht mehr gesehen wurden — pro Klasse."""
        with self.lock:
            for label, class_tracks in self.tracked_objects.items():
                gone_ids = [
                    tid for tid, data in class_tracks.items()
                    if current_frame - data["last_seen_frame"] >= FRAMES_UNTIL_GONE
                ]
                for tid in gone_ids:
                    data = class_tracks.pop(tid)
                    self._attach_avg_confidence(data)
                    self.flushed_objects.append({"id": tid, **data})
                    # ergebniss.csv ist eine Debug-Datei (siehe config.py) —
                    # zaehlung.csv (_check_counting() unten) ist es NICHT und
                    # wird deshalb unabhängig davon immer geschrieben.
                    if DEBUG_FILES_ENABLED:
                        log_track_event_csv("FLUSH", tid, data)
                    if AUTO_CONFIG_COLLECTION_ENABLED:
                        log_track_for_collection(data)
                    self._check_counting(data)

    def finalize(self):
        """
        Wird bei EOS oder Ctrl+C aufgerufen.
        Schreibt alle noch aktiven Tracks nach ergebniss.csv, gibt eine
        Konsolen-Zusammenfassung aus und speichert das Bewegungsbild.

        Durch self.finalized nur einmal ausführbar. Der Check-and-Set liegt
        bewusst INNERHALB des Locks (nicht davor) — sonst können zwei
        gleichzeitige Aufrufe (z. B. echtes EOS und ein manuell ausgelöster
        Shutdown, die sich zeitlich überschneiden) beide den Check bestehen,
        bevor einer von beiden das Flag setzt, und der zweite Aufruf lief
        dann auf einem bereits geleerten tracked_objects — überschrieb damit
        das echte Bild mit einer leeren Fläche.
        """
        with self.lock:
            if self.finalized:
                return
            self.finalized = True

            # Atomarer Snapshot + Leerung von tracked_objects (pro Klasse)
            remaining_by_class = {label: dict(tracks) for label, tracks in self.tracked_objects.items()}
            for tracks in self.tracked_objects.values():
                tracks.clear()

        # Für Logging/Zeichnen zu einer flachen LISTE zusammenführen (nicht zu
        # einem Dict!) — sonst könnten sich numerisch gleiche track_ids
        # verschiedener Klassen wieder gegenseitig überschreiben, genau das
        # Problem, das die Klassentrennung oben eigentlich lösen soll.
        remaining_list = [
            {"id": tid, **data}
            for label, tracks in remaining_by_class.items()
            for tid, data in tracks.items()
        ]

        # Alle verbleibenden (nie geflushten) Tracks nach ergebniss.csv schreiben
        # (Debug-Datei — zaehlung.csv über _check_counting() ist davon nicht
        # betroffen, siehe Kommentar in flush_stale()).
        for item in remaining_list:
            self._attach_avg_confidence(item)
            if DEBUG_FILES_ENABLED:
                log_track_event_csv("FINALIZE", item["id"], item)
            if AUTO_CONFIG_COLLECTION_ENABLED:
                log_track_for_collection(item)
            self._check_counting(item)

        # Kompakte Zusammenfassung auf der Konsole
        print("\n(Track; Startpunkt; Endpunkt)")
        for item in remaining_list:
            print(f"({item['display_id']}; {item['start']}; {item['end']})")

        # Bewegungsbild der FINALIZE-Tracks (beim Programmende noch aktiv gewesen)
        if not DEBUG_FILES_ENABLED:
            print("Debug-Dateien deaktiviert — kein Finalize-Bewegungsbild geschrieben.")
        elif self.frame_width and self.frame_height:
            img = draw_movement_image(self.frame_width, self.frame_height, remaining_list)
            path = save_finalize_image(img)
            print(f"Bewegungsbild (Finalize) gespeichert als {path}")
        else:
            print("Keine Frame-Dimensionen verfügbar — Finalize-Bild konnte nicht erstellt werden.")

        # Zusammenfassung der Zählung
        if self.counter is not None:
            summary = self.counter.summary_lines()
            print("\n--- Zählung (Linienkreuzungen) ---")
            if summary:
                for line in summary:
                    print(line)
            else:
                print("Keine Linienkreuzung erkannt.")
