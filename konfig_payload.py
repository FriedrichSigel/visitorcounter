"""
konfig_payload.py — sendet die Zählkonfiguration als MQTT-Nachricht (Format 4).

NUR im Zusatz-Feature der MQTT-Anbindung. GEHÖRT AUF DEN SENSOR.

Wozu:
    Der Server zeigt Zählwerte an, weiß aber nicht, WIE gezählt wurde: welche
    Flächen, welches IN-Feld, welche Klassen, welcher Modus. Wer die Daten
    später auswertet, muss das kennen — sonst ist "5 Übergänge Anlage→office"
    ohne Bezug. Diese Nachricht überträgt die Konfiguration (roi_config.json),
    damit die Empfangsseite den Kontext hat.

    Zwei Umfänge wählbar:
      "voll"  — die komplette roi_config.json, inklusive der Punkt-Koordinaten
                der Flächen. Damit kann der Server die Zonen sogar zeichnen.
      "kompakt" — nur die Eckdaten: Modus, Feldnamen, IN-Feld, Klassen. Ohne
                Koordinaten. Reicht, um Zählwerte einzuordnen, und ist deutlich
                kleiner.

Struktur (Format 4):

    {
      "format": 4,
      "sensor_id": 1,
      "gesendet_am": "2026-07-25T09:00:00Z",
      "umfang": "kompakt",
      "modus": "multi_roi",
      "in_feld": "office",
      "felder": ["office", "ausgang", "Vorlesung", "Anlage"],
      "klassen": ["person", "bicycle", ...],
      "snap_to_nearest": true,
      "konfig": { ... nur bei umfang="voll": die ganze roi_config.json ... }
    }

Datenschutz:
    Die Konfiguration enthält keine personenbezogenen Daten — nur die
    Geometrie der Zählzonen und die gewählten Klassen. Sie zu senden ist
    unbedenklich; die Koordinaten beschreiben Bildbereiche, keine Personen.
"""

import json
import os
from datetime import datetime, timezone

FORMAT_VERSION = 4


class KonfigProvider:
    """
    Baut die Konfigurations-Nachricht aus roi_config.json.

    Anders als die Zähl-Provider hat diese Nachricht kein Delta: sie ist eine
    Momentaufnahme des aktuellen Zustands. Gesendet wird sie seltener — einmal
    beim Start und danach nur, wenn sich die Datei geändert hat (erkannt an der
    Änderungszeit).
    """

    def __init__(self, config_path="roi_config.json", sensor_id=1,
                 umfang="kompakt"):
        if umfang not in ("kompakt", "voll"):
            raise ValueError("umfang muss 'kompakt' oder 'voll' sein")
        self.config_path = config_path
        self.sensor_id = sensor_id
        self.umfang = umfang
        self._letzte_mtime = None

    def hat_sich_geaendert(self):
        """True, wenn die Konfigurationsdatei seit dem letzten Senden neuer ist."""
        try:
            mtime = os.path.getmtime(self.config_path)
        except OSError:
            return False
        return mtime != self._letzte_mtime

    def build(self):
        """
        Baut die Nachricht als dict. None, wenn die Datei nicht lesbar ist.
        """
        try:
            with open(self.config_path) as f:
                cfg = json.load(f)
        except (OSError, ValueError):
            return None

        felder = [r.get("name") for r in cfg.get("regions", []) if r.get("name")]

        nachricht = {
            "format": FORMAT_VERSION,
            "sensor_id": self.sensor_id,
            "gesendet_am": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "umfang": self.umfang,
            "modus": cfg.get("mode"),
            "in_feld": cfg.get("in_field"),
            "felder": felder,
            "klassen": cfg.get("classes", []),
            "snap_to_nearest": cfg.get("snap_to_nearest", False),
        }

        if self.umfang == "voll":
            # Die komplette Datei mitgeben — damit kann der Server die Zonen
            # zeichnen. Bewusst als eigenes Feld, nicht vermischt mit den
            # Eckdaten oben.
            nachricht["konfig"] = cfg

        return nachricht

    def commit(self):
        """Merkt die aktuelle Änderungszeit als gesendet vor."""
        try:
            self._letzte_mtime = os.path.getmtime(self.config_path)
        except OSError:
            pass

    @staticmethod
    def zusammenfassen(nachricht):
        if not nachricht:
            return "keine Konfiguration"
        felder = ", ".join(nachricht.get("felder", [])) or "keine"
        return (f"Konfiguration ({nachricht.get('umfang')}): "
                f"Modus {nachricht.get('modus')}, Felder [{felder}], "
                f"IN-Feld {nachricht.get('in_feld')}")
