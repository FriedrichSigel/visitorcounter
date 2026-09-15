"""
lora_spiegel.py — spiegelt die LoRa-Nachrichten zur Kontrolle über MQTT.

NUR im Zusatz-Feature. GEHÖRT AUF DEN SENSOR, neben lora_send_loop.py.

Wozu:
    Über LoRa ist nicht sicher, ob eine Nachricht wirklich ankommt — genau das
    war ja das Problem am aktuellen Standort (Uplinks gingen im schwachen Signal
    unter). Dieses Modul baut GENAU DENSELBEN 18-Byte-Frame, den der LoRa-Sender
    erzeugt, und schickt ihn zusätzlich über MQTT. Der Server empfängt damit
    beide Wege und kann abgleichen:

      - Kam die LoRa-Nachricht an, die MQTT-Kopie aber nicht (oder umgekehrt)?
      - Stimmen die Zählwerte beider Wege überein?
      - Wie groß ist die Verlustrate je Weg?

    Das ist eine belastbare Aussage für die Arbeit: nicht "LoRa fühlt sich
    unzuverlässig an", sondern "von N gesendeten Frames kamen über LoRa X, über
    MQTT Y an".

Wie die Gleichheit sichergestellt wird:
    Der Frame wird NICHT neu berechnet, sondern über denselben
    LivePayloadProvider aus lora_send_loop.py gebaut, den auch der LoRa-Sender
    benutzt. Beide Wege sehen damit exakt dieselben Bytes.

    WICHTIG zur Abgrenzung: Dieses Modul baut den Frame nur, es verändert den
    Merker des Providers NICHT (kein commit). Sonst würden sich LoRa-Sender und
    Spiegel gegenseitig die Zählstände wegnehmen. Der Spiegel ist ein reiner
    Mitleser.

Betrieb:
    Am ehrlichsten ist der Abgleich, wenn beide Wege denselben Frame melden.
    Dafür gibt es zwei Wege:

      a) Der LoRa-Sender schreibt jeden gesendeten Frame in eine kleine
         Protokolldatei; der Spiegel liest den letzten Eintrag und schickt ihn
         per MQTT. So ist es GARANTIERT derselbe Frame. (Modus "mitlesen")

      b) Der Spiegel baut selbst einen Frame aus dem aktuellen Zählstand. Das
         ist einfacher, aber nicht bit-genau derselbe wie der zuletzt per LoRa
         gesendete, wenn dazwischen gezählt wurde. (Modus "eigen")

    Modus (a) ist der genauere und wird empfohlen, sobald der LoRa-Sender die
    Protokolldatei schreibt (siehe README).
"""

import json
import os
from datetime import datetime, timezone

# Protokolldatei, in die der LoRa-Sender jeden gesendeten Frame schreibt.
# Der Spiegel liest daraus. Liegt neben zaehlung.csv.
LORA_PROTOKOLL = ".lora_gesendet.log"


class LoRaSpiegel:
    """
    Liefert die zu spiegelnde LoRa-Nachricht als MQTT-taugliches dict.

    Zwei Betriebsarten (siehe Modul-Kopf):
      - "mitlesen": den zuletzt per LoRa gesendeten Frame aus der
                    Protokolldatei nehmen (bit-genau derselbe).
      - "eigen":    einen Frame aus dem aktuellen Zählstand bauen (nutzt den
                    LivePayloadProvider, aber OHNE dessen Merker zu verändern).
    """

    def __init__(self, sensor_id=1, modus="mitlesen", lora_provider=None,
                 protokoll_pfad=None, counts_dir="."):
        self.sensor_id = sensor_id
        self.modus = modus
        self.lora_provider = lora_provider
        self.protokoll_pfad = protokoll_pfad or os.path.join(
            counts_dir, LORA_PROTOKOLL)
        self._letzte_position = 0

    def build(self):
        """
        Baut die Spiegel-Nachricht (Format 5). None, wenn es nichts Neues gibt.
        """
        if self.modus == "mitlesen":
            frame_hex, lora_zeit, lora_seq = self._letzten_frame_lesen()
            if frame_hex is None:
                return None
        else:
            if self.lora_provider is None:
                return None
            # Frame aus dem aktuellen Stand bauen — aber NICHT committen.
            frame_hex = self.lora_provider.build()
            lora_zeit = None
            lora_seq = None
            if not frame_hex:
                return None

        return {
            "format": 5,
            "sensor_id": self.sensor_id,
            "gesendet_am": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "zweck": "lora_kontrolle",
            "modus": self.modus,
            # Der rohe LoRa-Frame als Hex — der Server dekodiert ihn mit
            # demselben Decoder wie eine echte LoRa-Nachricht und vergleicht.
            "lora_frame_hex": frame_hex,
            # Falls aus dem Protokoll: wann und mit welcher Folgenummer der
            # Frame per LoRa rausging. Erlaubt dem Server den zeitlichen
            # Abgleich mit der tatsächlich über TTN empfangenen Nachricht.
            "lora_gesendet_am": lora_zeit,
            "lora_sequenz": lora_seq,
        }

    def _letzten_frame_lesen(self):
        """
        Liest den JÜNGSTEN noch nicht gespiegelten Eintrag aus der
        Protokolldatei. Rückgabe: (frame_hex, zeit, sequenz) oder (None,...).

        Format der Protokolldatei (eine JSON-Zeile je gesendetem Frame):
            {"zeit": "...", "sequenz": 7, "frame": "0201..."}
        """
        try:
            with open(self.protokoll_pfad) as f:
                f.seek(self._letzte_position)
                zeilen = f.readlines()
                self._letzte_position = f.tell()
        except OSError:
            return None, None, None

        # Nur die letzte Zeile interessiert — der jüngste gesendete Frame.
        for zeile in reversed(zeilen):
            zeile = zeile.strip()
            if not zeile:
                continue
            try:
                eintrag = json.loads(zeile)
                return (eintrag.get("frame"), eintrag.get("zeit"),
                        eintrag.get("sequenz"))
            except json.JSONDecodeError:
                continue
        return None, None, None

    def commit(self):
        """
        Der Spiegel verändert bewusst KEINEN Zählstand — er ist nur ein
        Mitleser. Diese Methode existiert nur, damit er dieselbe Schnittstelle
        wie die anderen Provider hat, und tut absichtlich nichts.
        """
        pass

    @staticmethod
    def zusammenfassen(nachricht):
        if not nachricht:
            return "keine LoRa-Kontrollnachricht"
        return (f"LoRa-Kontrolle ({nachricht.get('modus')}): "
                f"Frame {nachricht.get('lora_frame_hex', '')[:16]}…")


def frame_protokollieren(protokoll_pfad, frame_hex, sequenz):
    """
    Hängt einen gesendeten LoRa-Frame an die Protokolldatei an.

    Wird auf der LoRa-Seite aufgerufen (in lora_send_loop.py, nach einem
    erfolgreichen Uplink), damit der Spiegel im Modus "mitlesen" genau diesen
    Frame findet. Bewusst hier, damit beide Seiten dasselbe Format verwenden.

    Datei bleibt klein: es wird nur angehängt; bei Bedarf kann sie extern
    rotiert werden. Ein fehlgeschlagenes Schreiben ist unkritisch — dann fehlt
    dem Spiegel eben ein Eintrag.
    """
    try:
        with open(protokoll_pfad, "a") as f:
            f.write(json.dumps({
                "zeit": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "sequenz": sequenz,
                "frame": frame_hex,
            }) + "\n")
    except OSError:
        pass
