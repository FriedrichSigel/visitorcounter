"""
uebergangs_payload.py — baut die ausführliche Übergangs-Nachricht (Format 3).

GEHÖRT AUF DEN SENSOR, neben lora_send_loop.py und mqtt_send_loop.py.

Warum es das gibt:
    Über LoRa passten nur 18 Byte in eine Nachricht. Deshalb wurden alle
    Übergänge auf ein einziges IN/OUT-Paar je Klasse zusammengefaltet: alles,
    was ins IN-Feld lief, war "hinein", alles heraus "hinaus". Wohin jemand
    ging, ging dabei verloren.

    Über MQTT gibt es diese Grenze nicht. Diese Datei baut deshalb die
    vollständige Übergangsmatrix: für jedes Paar (von-Feld, nach-Feld) und
    jede Klasse die Anzahl im abgelaufenen Intervall.

Struktur der Nachricht (JSON):

    {
      "format": 3,
      "sensor_id": 1,
      "sequenz": 7,
      "gesendet_am": "2026-07-24T13:05:00Z",
      "intervall_min": 5,
      "status": { "kamera_ok": true, ... },
      "felder": ["office", "ausgang", "Vorlesung", "Anlage"],
      "in_feld": ["office"],
      "uebergaenge": [
        { "von": "Anlage", "nach": "office", "klasse": "person", "anzahl": 3 },
        ...
      ],
      "summen": { "person": { "in": 5, "out": 2 } }
    }

    "uebergaenge" ist eine Liste statt einer vollen Matrix, weil die Matrix
    fast leer wäre: bei 4 Feldern und 6 Klassen gibt es 72 mögliche
    Kombinationen, belegt sind typisch ein bis zwei Dutzend. Nur Einträge mit
    anzahl > 0 werden übertragen.

    "summen" bleibt aus Verträglichkeitsgründen erhalten — damit lassen sich
    Nachrichten dieses Formats mit den früheren LoRa-Nachrichten vergleichen.

Datenschutz:
    Übertragen werden ausschliesslich ABGEZÄHLTE Übergänge je Intervall, keine
    Einzelereignisse: keine Zeitpunkte einzelner Personen, keine Kennungen,
    keine Koordinaten, keine Bilder. Der Detailgrad steigt gegenüber LoRa von
    "hinein/hinaus" auf "von wo nach wo" — das bleibt eine aggregierte
    Bewegungsstatistik über die Fläche, keine Beobachtung einzelner Personen.

    Zu bedenken bei sehr kurzen Intervallen: Steht in einer Nachricht genau
    ein Übergang, beschreibt sie faktisch die Bewegung einer einzelnen Person.
    Deshalb ist ein Intervall von einigen Minuten nicht nur eine Frage des
    Datenvolumens, sondern auch der Datensparsamkeit.
"""

import csv
import json
import os
from datetime import datetime, timezone

FORMAT_VERSION = 3

# Merkdatei: bis zu welcher Zeile in zaehlung.csv wurde schon gesendet.
# Liegt neben der CSV, damit beides zusammen gesichert/verschoben wird.
STANDARD_MARKER = ".uebergaenge_gesendet"

CANONICAL_CLASSES = ["person", "bicycle", "car", "motorcycle", "bus", "truck"]


class UebergangsProvider:
    """
    Baut die Übergangs-Nachricht aus roi_config.json und zaehlung.csv.

    Dieselbe Arbeitsweise wie der LoRa-Sender: build() liefert die seit dem
    letzten ERFOLGREICHEN Versand hinzugekommenen Übergänge, commit() schiebt
    den Merker erst nach, wenn der Versand bestätigt ist. Schlägt das Senden
    fehl, bleiben die Übergänge stehen und gehen beim nächsten Erfolg mit —
    es geht nichts verloren.
    """

    def __init__(self, config_path="roi_config.json", counts_csv="zaehlung.csv",
                 sensor_id=1, interval_min=5, pipeline_ok=False,
                 marker_path=None):
        self.config_path = config_path
        self.counts_csv = counts_csv
        self.sensor_id = sensor_id
        self.interval_min = interval_min
        self.pipeline_ok = pipeline_ok
        self.marker_path = marker_path or os.path.join(
            os.path.dirname(os.path.abspath(counts_csv)) or ".", STANDARD_MARKER)

        self.sequenz = 0
        self.letzter_versand_fehlgeschlagen = False
        self._offene_zeile = None      # Zeilenstand des gerade gebauten Frames
        self._verarbeitet = self._marker_lesen()

    # -- Merker ------------------------------------------------------------
    def _marker_lesen(self):
        """Zuletzt verarbeitete Zeilenzahl. 0, wenn noch nie gesendet."""
        try:
            with open(self.marker_path) as f:
                daten = json.load(f)
            return int(daten.get("verarbeitete_zeilen", 0))
        except (OSError, ValueError, TypeError):
            return 0

    def _marker_schreiben(self, zeilen):
        try:
            with open(self.marker_path, "w") as f:
                json.dump({"verarbeitete_zeilen": zeilen,
                           "stand": datetime.now().isoformat(timespec="seconds")}, f)
        except OSError:
            # Nicht schreibbar: dann werden Übergänge beim nächsten Start
            # erneut gesendet. Unschön, aber besser als ein Absturz.
            pass

    # -- Konfiguration -----------------------------------------------------
    @staticmethod
    def _in_felder_normalisieren(raw):
        """
        "in_field" aus roi_config.json einheitlich als Liste von Namen lesen.

        Neue Konfigurationen speichern hier eine Liste (mehrere IN-Flächen
        möglich), ältere einen einzelnen Flächennamen als String.
        """
        if isinstance(raw, list):
            return [n for n in raw if n]
        return [raw] if raw else []

    def _konfiguration_lesen(self):
        try:
            with open(self.config_path) as f:
                cfg = json.load(f)
        except (OSError, ValueError):
            return {"felder": [], "in_felder": [], "klassen": [], "modus": None,
                    "gelesen": False}
        return {
            "felder": [r.get("name") for r in cfg.get("regions", [])
                       if r.get("name")],
            "in_felder": self._in_felder_normalisieren(cfg.get("in_field")),
            "klassen": cfg.get("classes", []),
            "modus": cfg.get("mode"),
            "gelesen": True,
        }

    # -- Zählungen ---------------------------------------------------------
    def _zeilen_lesen(self):
        """Alle Datenzeilen aus zaehlung.csv. Leere Liste, wenn nicht lesbar."""
        try:
            with open(self.counts_csv, newline="", encoding="utf-8-sig") as f:
                return list(csv.DictReader(f))
        except (OSError, csv.Error):
            return []

    @staticmethod
    def _richtung_zerlegen(richtung):
        """
        'Anlage->office' -> ('Anlage', 'office').
        'office (kein Wechsel)' -> None (kein Übergang).
        """
        if not richtung or "->" not in richtung:
            return None
        von, _, nach = richtung.partition("->")
        von, nach = von.strip(), nach.strip()
        if not von or not nach:
            return None
        return von, nach

    # -- Aufbau ------------------------------------------------------------
    def build(self):
        """
        Baut die Nachricht als dict. Gibt None zurück, wenn es nichts Neues
        gibt — dann muss auch nichts gesendet werden.
        """
        cfg = self._konfiguration_lesen()
        zeilen = self._zeilen_lesen()
        gesamt = len(zeilen)

        # Wurde die CSV zurückgesetzt oder archiviert (cleanup_utils verschiebt
        # sie beim Start eines neuen Laufs), ist sie kürzer als der Merker.
        # Dann von vorn beginnen, statt alles zu überspringen.
        if gesamt < self._verarbeitet:
            self._verarbeitet = 0

        neue = zeilen[self._verarbeitet:]
        self._offene_zeile = gesamt

        # Übergänge zählen: Schlüssel (von, nach, klasse)
        zaehler = {}
        for zeile in neue:
            if str(zeile.get("is_transition", "")).lower() != "true":
                continue
            paar = self._richtung_zerlegen(zeile.get("direction", ""))
            if paar is None:
                continue
            klasse = (zeile.get("label") or "unbekannt").strip()
            schluessel = (paar[0], paar[1], klasse)
            zaehler[schluessel] = zaehler.get(schluessel, 0) + 1

        if not zaehler:
            return None

        uebergaenge = [
            {"von": von, "nach": nach, "klasse": klasse, "anzahl": anzahl}
            for (von, nach, klasse), anzahl in sorted(zaehler.items())
        ]

        return {
            "format": FORMAT_VERSION,
            "sensor_id": self.sensor_id,
            "sequenz": self.sequenz,
            "gesendet_am": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "intervall_min": self.interval_min,
            "status": {
                "kamera_ok": bool(self.pipeline_ok),
                "beschleuniger_ok": bool(self.pipeline_ok),
                "konfig_ok": bool(cfg["gelesen"] and cfg["felder"]),
                "gepuffert": self.letzter_versand_fehlgeschlagen,
                "teilintervall": False,
            },
            "felder": cfg["felder"],
            "in_feld": cfg["in_felder"],
            "uebergaenge": uebergaenge,
            "summen": self._summen_bilden(uebergaenge, cfg["in_felder"]),
        }

    @staticmethod
    def _summen_bilden(uebergaenge, in_felder):
        """
        Faltet die Übergänge auf das alte IN/OUT-Schema zusammen.

        Damit bleiben Nachrichten dieses Formats mit den früheren
        LoRa-Nachrichten vergleichbar: hinein = Übergang in eine der
        IN-Flächen (aus einer Nicht-IN-Fläche), hinaus = Übergang aus einer
        IN-Fläche heraus (in eine Nicht-IN-Fläche). Übergänge zwischen zwei
        IN- oder zwei Nicht-IN-Flächen zählen nicht.
        """
        summen = {}
        if not in_felder:
            return summen
        in_set = set(in_felder)
        for u in uebergaenge:
            klasse = u["klasse"]
            eintrag = summen.setdefault(klasse, {"in": 0, "out": 0})
            von_in = u["von"] in in_set
            nach_in = u["nach"] in in_set
            if nach_in and not von_in:
                eintrag["in"] += u["anzahl"]
            elif von_in and not nach_in:
                eintrag["out"] += u["anzahl"]
        return summen

    # -- Nach dem Versand --------------------------------------------------
    def commit(self):
        """Nur nach BESTÄTIGTEM Versand aufrufen."""
        if self._offene_zeile is not None:
            self._verarbeitet = self._offene_zeile
            self._marker_schreiben(self._verarbeitet)
        self.sequenz = (self.sequenz + 1) % 65536
        self.letzter_versand_fehlgeschlagen = False

    def mark_failed(self):
        """Versand fehlgeschlagen: Merker bleibt stehen, nächste Nachricht
        trägt das Kennzeichen 'gepuffert'."""
        self.letzter_versand_fehlgeschlagen = True

    # -- Zusammenfassung für die Protokollausgabe --------------------------
    @staticmethod
    def zusammenfassen(nachricht):
        if not nachricht or not nachricht.get("uebergaenge"):
            return "keine Übergänge"
        teile = [f"{u['von']}->{u['nach']} {u['klasse']}x{u['anzahl']}"
                 for u in nachricht["uebergaenge"]]
        gesamt = sum(u["anzahl"] for u in nachricht["uebergaenge"])
        return f"{gesamt} Übergänge: " + ", ".join(teile)
