#!/usr/bin/env python3
"""
lora_send_loop.py — Zyklischer LoRa-Sendetest für den LA66 USB Adapter V2.

Sendet einen Zähl-Frame (18-Byte-Zählformat v2) über AT+SENDB. Solange das
Senden nicht bestätigt wird, wird jede RETRY_SECONDS erneut versucht. Nach
einem erfolgreichen Uplink wird PAUSE_MINUTES pausiert, um den EU868-Duty-Cycle
(1 %) zu schonen und die Bandbreite nicht zu spammen.

Zwei Betriebsarten:

  * Statisch (Standard): sendet immer denselben Frame (--payload bzw. der
    eingebaute Test-Frame). Gut für einen reinen Funktest.

  * Live (--live-counts): baut den Frame vor JEDEM Sendeversuch neu aus der
    aktuellen Konfiguration (roi_config.json) und den Zählerständen
    (zaehlung.csv) — über das gemeinsame Modul lora_message. Übertragen wird
    der Zuwachs (Delta) seit dem letzten ERFOLGREICHEN Uplink: ein
    fehlgeschlagener Uplink verliert also keine Zählungen, sie werden beim
    nächsten Erfolg mitgesendet. Diese Betriebsart nutzt app.py (Tab 3).

Nutzung:
    python3 lora_send_loop.py
    python3 lora_send_loop.py --pause 10 --retry 60
    python3 lora_send_loop.py --payload 02032A05073F0803020105060000000000
    python3 lora_send_loop.py --live-counts --sensor-id 3 --pause 5

Beenden mit Strg-C.

Voraussetzung: pyserial (auf dem Pi vorhanden). Das Skript nutzt denselben
Port/dieselbe Baudrate wie la66_probe.py. lora_message.py muss im selben
Verzeichnis liegen (für --live-counts).
"""

import argparse
import json
import sys
import time
from datetime import datetime

import serial

try:
    import lora_message
except ImportError:
    lora_message = None   # nur für --live-counts nötig; sonst egal

# --- Standardwerte (per Kommandozeile überschreibbar) ---
DEFAULT_PORT = (
    "/dev/serial/by-id/"
    "usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0"
)
DEFAULT_BAUD = 9600
DEFAULT_RETRY_SECONDS = 60      # Sendeversuch-Intervall, wenn (noch) nicht erfolgreich
DEFAULT_PAUSE_MINUTES = 5       # Pause nach erfolgreichem Senden

# Test-Frame aus der Formatspezifikation (Sensor 3, Frame 42, 8 person in / 3 out,
# 2 bicycle in / 1 out, 5 car in / 6 out, alle Klassen aktiv, Status ok).
# 18 Byte = Header(6) + 6 Klassen x (in,out). Endet auf ...0000 für truck.
DEFAULT_PAYLOAD_HEX = "02032A05073F080302010506000000000000"
FPORT = 2
CONFIRM = 0                     # 0 = unbestätigt (kein ACK vom Netz nötig)

# --- Live-Betrieb (--live-counts): woher Konfiguration und Zählerstände kommen ---
DEFAULT_CONFIG_PATH = "roi_config.json"
DEFAULT_COUNTS_CSV = "zaehlung.csv"
DEFAULT_SENSOR_ID = 1
# Pause zwischen den einzelnen Frames EINES Intervalls. Aktuell liefert der
# Provider je Zyklus genau einen Frame; die Schleife ist aber allgemein
# gehalten, falls später wieder mehrere Frames pro Intervall nötig werden.
DEFAULT_FRAME_GAP_SECONDS = 6

# Wortmarken in der LA66-Ausgabe, die Erfolg bzw. "Modul beschäftigt" anzeigen.
SUCCESS_MARKERS = ("txDone", "TX_DONE", "JOINED", "Join Success")
BUSY_MARKERS = ("AT_ERROR", "AT_BUSY_ERROR", "AT_PARAM_ERROR")


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def open_serial(port, baud):
    """
    Öffnet die serielle Schnittstelle, OHNE das Modul zurückzusetzen.

    Hintergrund: pyserial legt beim Öffnen standardmäßig DTR und RTS an. Bei
    vielen USB-Seriell-Wandlern (auch dem hier verwendeten CP2102) hängen
    diese Leitungen am Reset-Eingang des Funkmoduls. Jedes Öffnen des Ports
    löst dann einen Neustart des LA66 aus — und ein neu gestartetes
    OTAA-Gerät meldet sich zwangsläufig neu am Netz an (Join).

    Wird das Skript also in kurzen Abständen neu gestartet, erzeugt allein
    das eine Kette von Join-Vorgängen ohne einen einzigen Uplink. Deshalb
    werden beide Leitungen hier vor dem Öffnen abgeschaltet.
    """
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baud
    ser.timeout = 1
    # Vor dem Öffnen abschalten; pyserial übernimmt die Werte beim open().
    ser.dtr = False
    ser.rts = False
    ser.open()
    # Nach dem Öffnen noch einmal sicherstellen — nicht jede Plattform
    # übernimmt die Werte schon vorher.
    try:
        ser.dtr = False
        ser.rts = False
    except (OSError, ValueError):
        pass
    return ser


def query_join_status(ser, timeout_s=4):
    """
    Fragt den Anmeldestatus ab (AT+NJS=?). Rückgabe: True (angemeldet),
    False (nicht angemeldet) oder None (keine verwertbare Antwort).

    Wichtig für die Fehlersuche: Dieses Skript löst NIE selbst einen Join
    aus — es sendet ausschließlich AT+SENDB. Erscheinen in der TTN-Konsole
    fortlaufend Join-Vorgänge, kommen die vom Modul selbst. Das passiert,
    wenn das Modul die Join-Antwort des Netzes nicht empfängt und es deshalb
    immer wieder versucht. Die Ursache liegt dann außerhalb dieses Skripts
    (Empfang, Antenne, Gateway-Downlink, Modulkonfiguration).
    """
    try:
        ser.reset_input_buffer()
        ser.write(b"AT+NJS=?\r\n")
        ser.flush()
    except (OSError, serial.SerialException):
        return None

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            line = ser.readline().decode(errors="replace").strip()
        except (OSError, serial.SerialException):
            return None
        if not line:
            continue
        log(f"  LA66> {line}")
        kompakt = line.replace(" ", "")
        if kompakt in ("1", "NJS=1") or "NJS=1" in kompakt:
            return True
        if kompakt in ("0", "NJS=0") or "NJS=0" in kompakt:
            return False
    return None


def build_command(payload_hex):
    """Baut das AT+SENDB-Kommando: AT+SENDB=<confirm>,<Fport>,<len>,<hexdata>."""
    length = len(payload_hex) // 2          # Byte-Anzahl
    return f"AT+SENDB={CONFIRM:02d},{FPORT:02d},{length},{payload_hex}\r\n"


def read_response(ser, timeout_s=8):
    """
    Liest die serielle Ausgabe bis timeout_s Sekunden und wertet aus, ob das
    Senden bestätigt wurde. Gibt zurück: "ok" | "busy" | "timeout".
    Die gelesenen Zeilen werden mitgeloggt, damit man den Funkverlauf sieht.
    """
    deadline = time.time() + timeout_s
    saw_busy = False
    while time.time() < deadline:
        line = ser.readline().decode(errors="replace").strip()
        if not line:
            continue
        log(f"  LA66> {line}")
        if any(m in line for m in SUCCESS_MARKERS):
            return "ok"
        if any(m in line for m in BUSY_MARKERS):
            saw_busy = True
            # nicht sofort abbrechen — evtl. folgt noch txDone eines laufenden Zyklus
    return "busy" if saw_busy else "timeout"


def send_once(ser, payload_hex):
    """Sendet den Frame einmal und meldet, ob er bestätigt wurde (True/False)."""
    cmd = build_command(payload_hex)
    log(f"Sende: {cmd.strip()}")
    ser.reset_input_buffer()               # alte Zeilen (rxTimeout etc.) verwerfen
    ser.write(cmd.encode())
    ser.flush()
    result = read_response(ser)
    if result == "ok":
        log("  -> txDone: Uplink erfolgreich abgesetzt.")
        return True
    if result == "busy":
        log("  -> Modul beschäftigt (AT_ERROR) — vermutlich mitten im Funkzyklus. "
            "Neuer Versuch später.")
        return False
    log("  -> keine Bestätigung (Timeout). Neuer Versuch später.")
    return False


class LivePayloadProvider:
    """
    Baut den 18-Byte-Frame im Live-Betrieb (--live-counts) vor jedem Versuch
    neu aus roi_config.json + zaehlung.csv.

    Zwei Zählquellen, je nach Modus:
    - line / roi:  IN/OUT je Klasse direkt aus zaehlung.csv.
    - multi_roi:   IN/OUT werden über das gewählte IN-Feld aus den Übergängen
                   abgeleitet (Übergang -> IN-Feld = IN, IN-Feld -> X = OUT).
    In beiden Fällen dasselbe Format.

    Übertragen wird das Delta seit dem letzten ERFOLGREICHEN Uplink:
    - build() liest die aktuellen (kumulierten) Stände und zieht den zuletzt
      bestätigten Stand ab -> Zuwachs dieses Intervalls.
    - commit() (nur nach Erfolg) schiebt den Referenzstand nach. Schlägt ein
      Uplink fehl, bleibt der Referenzstand stehen, d. h. die Zählungen gehen
      nicht verloren, sondern kommen beim nächsten Erfolg mit.
    """

    def __init__(self, config_path, counts_csv, sensor_id,
                 interval_min=0, pipeline_ok=False):
        if lora_message is None:
            raise RuntimeError(
                "lora_message.py nicht gefunden — für --live-counts nötig. "
                "Muss im selben Verzeichnis wie lora_send_loop.py liegen.")
        self.config_path = config_path
        self.counts_csv = counts_csv
        self.sensor_id = sensor_id
        self.interval_min = interval_min
        # Kamera-/Hailo-Status kann dieser Subprozess nicht selbst messen.
        # app.py startet ihn nur, wenn die Zähl-Pipeline erfolgreich lief, und
        # setzt dann --pipeline-ok. Ohne das Flag bleiben die Bits 0/1 aus,
        # statt einen unbelegten "alles ok"-Zustand zu behaupten.
        self.pipeline_ok = pipeline_ok
        self._last_cycle_failed = False   # -> STATUS_BUFFERED
        self._first_uplink = True         # -> STATUS_PARTIAL
        self._config_ok = False           # -> STATUS_CONFIG_OK
        self.sequence = 0
        # Zuletzt bestätigter (kumulierter) Stand je Klasse.
        self._acked_in = {}
        self._acked_out = {}
        # Zwischenspeicher des zuletzt gebauten Deltas, bis commit() kommt.
        self._pending_cur_in = {}
        self._pending_cur_out = {}

    def _load_config(self):
        try:
            with open(self.config_path) as f:
                cfg = json.load(f)
            self._config_ok = True
            return cfg
        except (OSError, ValueError):
            self._config_ok = False
            log(f"  WARN: {self.config_path} nicht lesbar — nehme alle Klassen.")
            return {"mode": "line",
                    "classes": list(lora_message.CANONICAL_CLASSES)}

    def _build_status(self):
        """Status-Bitfeld (Byte 4) aus dem, was der Sender wirklich weiß."""
        status = 0
        if self.pipeline_ok:
            status |= lora_message.STATUS_CAMERA_OK | lora_message.STATUS_ACCEL_OK
        if self._config_ok:
            status |= lora_message.STATUS_CONFIG_OK
        if self._last_cycle_failed:
            status |= lora_message.STATUS_BUFFERED
        if self._first_uplink:
            status |= lora_message.STATUS_PARTIAL
        return status

    def _read_counts(self, cfg, active):
        """Wählt die Zählquelle nach Modus. Rückgabe: (counts_in, counts_out)."""
        if cfg.get("mode") == "multi_roi":
            in_field = (cfg.get("in_field") or "").strip()
            if not in_field:
                log("  WARN: multi_roi ohne IN-Feld — keine IN/OUT-Werte. "
                    "In Tab 2 ein IN-Feld wählen.")
            return lora_message.read_inout_from_transitions(
                self.counts_csv, in_field, active)
        return lora_message.read_counts_from_zaehlung(self.counts_csv, active)

    @staticmethod
    def _delta(cur, ref):
        """cur - ref je Klasse, nie negativ. Fällt cur unter ref (z. B. weil
        zaehlung.csv zwischendurch archiviert/neu angelegt wurde), gilt cur
        selbst als Delta (Neustart der Zählung erkannt)."""
        out = {}
        for k, v in cur.items():
            base = ref.get(k, 0)
            out[k] = v - base if v >= base else v
        return out

    def build(self):
        """Gibt eine Frame-Liste [(payload_hex, kurz_text)] zurück (immer genau
        ein 18-Byte-Frame)."""
        cfg = self._load_config()
        active = cfg.get("classes", lora_message.CANONICAL_CLASSES)
        cur_in, cur_out = self._read_counts(cfg, active)
        d_in = self._delta(cur_in, self._acked_in)
        d_out = self._delta(cur_out, self._acked_out)

        frame = lora_message.build_frame(
            active, d_in, d_out,
            sensor_id=self.sensor_id, sequence=self.sequence & 0xFF,
            interval_min=self.interval_min, status=self._build_status())
        self.sequence += 1
        self._pending_cur_in, self._pending_cur_out = cur_in, cur_out

        summary = ", ".join(
            f"{c}:{d_in.get(c, 0)}/{d_out.get(c, 0)}"
            for c in lora_message.CANONICAL_CLASSES if c in set(active)
        ) or "(keine aktiven Klassen)"
        return [(lora_message.frame_to_hex(frame), f"Δ [{summary}]")]

    def commit(self):
        """Nach erfolgreichem Uplink: Referenzstand nachziehen."""
        self._acked_in = dict(self._pending_cur_in)
        self._acked_out = dict(self._pending_cur_out)
        self._last_cycle_failed = False
        self._first_uplink = False

    def mark_failed(self):
        """Nach fehlgeschlagenem Zyklus: nächster Frame trägt STATUS_BUFFERED."""
        self._last_cycle_failed = True


class StaticProvider:
    """Sendet immer denselben (statischen) Frame — der bisherige Testbetrieb."""

    def __init__(self, payload_hex):
        self.payload_hex = payload_hex

    def build(self):
        return [(self.payload_hex, "statisch")]

    def commit(self):
        pass

    def mark_failed(self):
        pass


def main():
    ap = argparse.ArgumentParser(description="Zyklischer LoRa-Sendetest (LA66).")
    ap.add_argument("--port", default=DEFAULT_PORT, help="serielle Schnittstelle")
    ap.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    ap.add_argument("--retry", type=int, default=DEFAULT_RETRY_SECONDS,
                    help="Sekunden zwischen Sendeversuchen, solange nicht erfolgreich")
    ap.add_argument("--pause", type=int, default=DEFAULT_PAUSE_MINUTES,
                    help="Minuten Pause NACH erfolgreichem Senden (Duty-Cycle-Schonung)")
    ap.add_argument("--payload", default=DEFAULT_PAYLOAD_HEX,
                    help="Hex-Payload ohne Leerzeichen (Standard: Test-Frame v2)")
    ap.add_argument("--once", action="store_true",
                    help="nur einmal senden und beenden (für schnellen Test)")
    ap.add_argument("--live-counts", action="store_true",
                    help="Frame vor jedem Senden neu aus Konfig + Zählerständen "
                         "bauen (statt statischem --payload)")
    ap.add_argument("--config", default=DEFAULT_CONFIG_PATH,
                    help="Pfad zu roi_config.json (nur mit --live-counts)")
    ap.add_argument("--counts-csv", default=DEFAULT_COUNTS_CSV,
                    help="Pfad zu zaehlung.csv (nur mit --live-counts)")
    ap.add_argument("--sensor-id", type=int, default=DEFAULT_SENSOR_ID,
                    help="Sensor-ID für Byte 1 des Frames (nur mit --live-counts)")
    ap.add_argument("--pipeline-ok", action="store_true",
                    help="setzt die Status-Bits für Kamera/Hailo (wird von app.py "
                         "gesetzt, wenn die Zähl-Pipeline erfolgreich gestartet ist)")
    ap.add_argument("--frame-gap", type=int, default=DEFAULT_FRAME_GAP_SECONDS,
                    help="Sekunden Pause zwischen mehreren Frames desselben "
                         "Intervalls (multi_roi); Duty-Cycle-Schonung")
    args = ap.parse_args()

    # Provider wählen: statisch oder live. Der Live-Provider entscheidet intern
    # anhand des Modus (line/roi direkt, multi_roi über das IN-Feld).
    provider = None
    mode = None
    if args.live_counts:
        if lora_message is None:
            log("FEHLER: lora_message.py nicht gefunden — für --live-counts nötig.")
            sys.exit(1)
        try:
            with open(args.config) as f:
                mode = json.load(f).get("mode", "line")
        except (OSError, ValueError):
            mode = "line"
            log(f"WARN: {args.config} nicht lesbar — nehme Linien-/ROI-Format an.")
        try:
            provider = LivePayloadProvider(
                args.config, args.counts_csv, args.sensor_id,
                interval_min=args.pause, pipeline_ok=args.pipeline_ok)
        except RuntimeError as e:
            log(f"FEHLER: {e}")
            sys.exit(1)
    else:
        # Payload validieren (nur statischer Betrieb)
        payload = args.payload.strip().replace(" ", "")
        try:
            bytes.fromhex(payload)
        except ValueError:
            log(f"FEHLER: Payload ist kein gültiges Hex: {payload!r}")
            sys.exit(1)
        provider = StaticProvider(payload)

    log(f"Öffne {args.port} @ {args.baud} Baud")
    try:
        ser = open_serial(args.port, args.baud)
    except serial.SerialException as e:
        log(f"FEHLER: Port konnte nicht geöffnet werden: {e}")
        log("Prüfen: Steckt der LA66? Rechte (dialout-Gruppe)? Richtiger Port?")
        sys.exit(1)

    time.sleep(0.5)  # dem Adapter kurz Zeit geben

    # Einmal zu Beginn festhalten, ob das Modul am Netz angemeldet ist. Ohne
    # Anmeldung ist jeder Sendeversuch zwecklos, und die Ursache liegt dann
    # nicht in diesem Skript (siehe Kommentar bei query_join_status).
    status = query_join_status(ser)
    if status is True:
        log("LA66 ist am Netz angemeldet (NJS=1).")
    elif status is False:
        log("ACHTUNG: LA66 ist NICHT angemeldet (NJS=0). Solange das so bleibt, "
            "kann kein Uplink zustande kommen — das Modul versucht dann von "
            "sich aus immer wieder einen Join.")
    else:
        log("Anmeldestatus nicht ermittelbar (Modul antwortet nicht auf AT+NJS=?).")

    if args.live_counts:
        log(f"Live-Modus ({mode}): Frames je Uplink aus {args.config} + "
            f"{args.counts_csv} (Sensor-ID {args.sensor_id}, Port {FPORT}).")
    else:
        log(f"Test-Frame: {payload}  ({len(payload)//2} Byte, Port {FPORT})")
    log(f"Strategie: alle {args.retry}s versuchen; nach Erfolg {args.pause} min Pause. "
        f"(Strg-C zum Beenden)")

    sent_count = 0
    fehlversuche = 0
    try:
        while True:
            # Ein Zyklus = eine Frame-Liste (statisch/Linie: 1 Frame; multi_roi:
            # ggf. Feld-Definition + mehrere Datenteile). Commit erst, wenn der
            # ganze Zyklus durch ist -> nichts geht bei Teilfehlern verloren.
            batch = provider.build()

            if not batch:
                # Nichts zu senden (z. B. multi_roi ohne neue Übergänge).
                log("Keine neuen Daten — warte auf den nächsten Zyklus.")
                if args.once:
                    break
                time.sleep(args.retry)
                continue

            all_ok = True
            for j, (payload_hex, summary) in enumerate(batch):
                log(f"Frame {j+1}/{len(batch)}: {payload_hex}  {summary}")
                if not send_once(ser, payload_hex):
                    all_ok = False
                    break
                if j < len(batch) - 1:      # Duty-Cycle-Pause zwischen Frames
                    time.sleep(args.frame_gap)

            if all_ok:
                provider.commit()
                sent_count += 1
                fehlversuche = 0
                log(f"Gesamt erfolgreich gesendete Zyklen: {sent_count}")
                if args.once:
                    break
                log(f"Pause {args.pause} min bis zum nächsten Uplink ...")
                time.sleep(args.pause * 60)
            else:
                provider.mark_failed()   # nächster Frame trägt STATUS_BUFFERED
                fehlversuche += 1
                # Nach dem dritten Fehlschlag den Anmeldestatus nachfragen.
                # So steht im Protokoll, OB das Modul ueberhaupt am Netz ist —
                # ohne Anmeldung ist weiteres Senden zwecklos und die Ursache
                # liegt nicht in diesem Skript.
                if fehlversuche % 3 == 0:
                    status = query_join_status(ser)
                    if status is False:
                        log("Das Modul ist nicht am Netz angemeldet. Es versucht "
                            "selbstständig einen Join; bis der durchgeht, kann "
                            "kein Uplink gesendet werden.")
                    elif status is True:
                        log("Modul ist angemeldet — der Fehler liegt beim Senden, "
                            "nicht an der Anmeldung.")
                if args.once:
                    break
                time.sleep(args.retry)
    except KeyboardInterrupt:
        log("Abgebrochen. Bis dann.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
