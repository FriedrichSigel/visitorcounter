#!/usr/bin/env python3
"""
lora_transmitter.py — LoRaWAN-Uplink fuer den Personenzaehl-Prototyp.

Zielhardware: Dragino LA66 USB LoRaWAN Adapter V2 (EU868), AT-Protokoll ueber
CP2102-USB-TTL. Zielinfrastruktur: LoRaWAN-Netz der Stadtwerke Potsdam ->
Urbane Datenplattform (UDP).

Designentscheidungen (relevant fuer Kapitel 4.b.viii der Arbeit):

  1. ENTKOPPLUNG. Der Uplink laeuft in einem eigenen Worker-Thread mit Queue.
     Die Zaehlpipeline ruft nur `send_count(...)` auf und kehrt sofort zurueck.
     Ein LoRa-Timeout (bis zu mehreren Sekunden) darf die Frame-Verarbeitung
     nicht ausbremsen — sonst bricht die Erkennungsrate ein.

  2. AUSFALL IST NORMALBETRIEB. Fehlender Join, kein Gateway, abgezogener Stick:
     alles wird geloggt und gepuffert, nichts wirft eine Exception nach oben.
     Der Sensor zaehlt weiter, auch wenn die Funkstrecke tot ist. Die CSV-Dateien
     bleiben die Wahrheit; LoRa ist nur der Transportweg.

  3. DUTY CYCLE. EU868 erlaubt 1 % Sendezeit. Bei SF12 ist ein 25-Byte-Frame
     rund 1,2 s in der Luft -> rechnerisch ein Uplink alle ~2 Minuten. Der
     MIN_SEND_INTERVAL_S-Wert erzwingt das konservativ. Das ist der Grund, warum
     aggregiert und nicht pro Person gesendet wird.

  4. PRIVACY BY DESIGN. Das Nachrichtenformat enthaelt ausschliesslich
     aggregierte Zaehlwerte. Keine Bilder, keine Koordinaten, keine Track-IDs.

Konfiguration ueber Umgebungsvariablen (KEINE Keys im Code oder im Repo!):
    LORA_ENABLED=1              # 0 = DummyTransport (Standard)
    LORA_PORT=/dev/ttyUSB0
    LORA_BAUD=9600
    LORA_FPORT=2
    LORA_CONFIRMED=0            # 1 = bestaetigte Uplinks (kostet Duty Cycle)
    LORA_MIN_INTERVAL_S=120

Abhaengigkeit: pyserial  ->  pip install pyserial --break-system-packages
"""

from __future__ import annotations

import logging
import os
import queue
import struct
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

log = logging.getLogger("lora")


# ============================================================================
# Nachrichtenformat — 25 Byte, big endian
# ============================================================================
#
#  Offset  Laenge  Feld              Typ     Bedeutung
#  ------  ------  ----------------  ------  ----------------------------------
#     0       1    version           uint8   Formatversion (aktuell 1)
#     1       1    sensor_id         uint8   Eingang 1..17 (Volkspark Biosphaere)
#     2       4    timestamp         uint32  Unix-Zeit UTC, Sekunden
#     6       2    count_in          uint16  Eintritte im Intervall
#     8       2    count_out         uint16  Austritte im Intervall
#    10       2    count_total_in    uint16  Eintritte seit Geraetestart
#    12       2    count_total_out   uint16  Austritte seit Geraetestart
#    14       2    interval_s        uint16  Laenge des Aggregationsintervalls (s)
#    16       1    zone_count        uint8   Anzahl konfigurierter Zaehlzonen
#    17       1    mode              uint8   0=Linie 1=ROI 2=Mehrere Flaechen
#    18       1    status            uint8   Bitfeld, siehe unten
#    19       2    frames_processed  uint16  Frames im Intervall (Plausibilitaet)
#    21       4    reserved          uint32  Reserve fuer Formaterweiterung
#  ------  ------  ----------------  ------  ----------------------------------
#                                    25 Byte gesamt
#
#  status-Bitfeld:
#    Bit 0  Kamera liefert Bilder
#    Bit 1  KI-Beschleuniger (Hailo) aktiv
#    Bit 2  Konfiguration geladen
#    Bit 3  Werte seit letztem Uplink gepuffert (Nachsendung)
#
#  25 Byte passen auch bei SF12 in die EU868-Payload-Grenze (51 Byte) — das
#  Format ist damit unabhaengig vom Spreading Factor sendbar. Das war die
#  bestimmende Randbedingung beim Entwurf.

MSG_VERSION = 1
MSG_STRUCT = struct.Struct(">BBIHHHHHBBBHI")
MSG_LEN = MSG_STRUCT.size  # == 25

STATUS_CAMERA_OK = 1 << 0
STATUS_ACCEL_OK = 1 << 1
STATUS_CONFIG_OK = 1 << 2
STATUS_BUFFERED = 1 << 3

MODE_LINE = 0
MODE_ROI = 1
MODE_MULTI_ROI = 2

MODE_NAMES = {MODE_LINE: "Linie", MODE_ROI: "ROI", MODE_MULTI_ROI: "Mehrere Flaechen"}


@dataclass
class CountMessage:
    sensor_id: int
    count_in: int
    count_out: int
    count_total_in: int
    count_total_out: int
    interval_s: int
    zone_count: int
    mode: int
    status: int
    frames_processed: int
    timestamp: int | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = int(datetime.now(timezone.utc).timestamp())

    def pack(self) -> bytes:
        """Serialisiert die Nachricht in genau MSG_LEN Byte."""
        def u16(v: int) -> int:
            return max(0, min(65535, int(v)))

        def u8(v: int) -> int:
            return max(0, min(255, int(v)))

        data = MSG_STRUCT.pack(
            MSG_VERSION,
            u8(self.sensor_id),
            int(self.timestamp) & 0xFFFFFFFF,
            u16(self.count_in),
            u16(self.count_out),
            u16(self.count_total_in),
            u16(self.count_total_out),
            u16(self.interval_s),
            u8(self.zone_count),
            u8(self.mode),
            u8(self.status),
            u16(self.frames_processed),
            0,  # reserved
        )
        assert len(data) == MSG_LEN, f"Formatfehler: {len(data)} statt {MSG_LEN} Byte"
        return data

    @classmethod
    def unpack(cls, data: bytes) -> "CountMessage":
        """Gegenstueck zu pack() — dient als Referenz fuer den Payload-Decoder
        auf Seiten des Network Servers (dort in JavaScript nachzubauen)."""
        if len(data) != MSG_LEN:
            raise ValueError(f"Erwartet {MSG_LEN} Byte, bekommen {len(data)}")
        (ver, sid, ts, cin, cout, tin, tout,
         interval, zones, mode, status, frames, _res) = MSG_STRUCT.unpack(data)
        if ver != MSG_VERSION:
            raise ValueError(f"Unbekannte Formatversion: {ver}")
        return cls(sensor_id=sid, timestamp=ts, count_in=cin, count_out=cout,
                   count_total_in=tin, count_total_out=tout, interval_s=interval,
                   zone_count=zones, mode=mode, status=status,
                   frames_processed=frames)

    def hex(self) -> str:
        return self.pack().hex()


# ============================================================================
# Transport-Abstraktion
# ============================================================================

class Transport(Protocol):
    def connect(self) -> bool: ...
    def is_joined(self) -> bool: ...
    def send(self, payload: bytes) -> bool: ...
    def close(self) -> None: ...


class DummyTransport:
    """Kein Funk — protokolliert nur. Standard, solange LORA_ENABLED != 1.

    Damit laeuft die gesamte Pipeline auch ohne angesteckte Hardware, was fuer
    Labortests und fuer die Entwicklung am Laptop noetig ist."""

    def __init__(self) -> None:
        self.sent: list[bytes] = []

    def connect(self) -> bool:
        log.info("DummyTransport aktiv — es wird nicht gefunkt.")
        return True

    def is_joined(self) -> bool:
        return True

    def send(self, payload: bytes) -> bool:
        self.sent.append(payload)
        log.info("DUMMY-Uplink (%d Byte): %s", len(payload), payload.hex())
        return True

    def close(self) -> None:
        log.info("DummyTransport geschlossen. %d Nachrichten simuliert.", len(self.sent))


class LA66Transport:
    """Echter Transport ueber den Dragino LA66 (AT-Protokoll, seriell).

    AT-Kommandos laut Dragino-Handbuch:
        AT              -> OK                          (Lebenszeichen)
        AT+NJS=?        -> 1 = gejoint, 0 = nicht      (Join-Status)
        AT+JOIN         -> loest OTAA-Join aus
        AT+SENDB=<confirm>,<fport>,<len>,<hexdata>     (Binaer-Uplink)
    """

    def __init__(self, port: str, baud: int = 9600, fport: int = 2,
                 confirmed: bool = False, timeout: float = 2.0):
        self.port = port
        self.baud = baud
        self.fport = fport
        self.confirmed = confirmed
        self.timeout = timeout
        self._ser = None

    # -- intern -------------------------------------------------------------

    def _cmd(self, cmd: str, wait: float = 2.0) -> list[str]:
        if self._ser is None:
            return []
        self._ser.reset_input_buffer()
        self._ser.write((cmd + "\r\n").encode("ascii"))
        self._ser.flush()

        deadline = time.time() + wait
        lines: list[str] = []
        while time.time() < deadline:
            raw = self._ser.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").strip()
            if line:
                lines.append(line)
                deadline = time.time() + 0.4
        return lines

    # -- Transport-Protokoll ------------------------------------------------

    def connect(self) -> bool:
        try:
            import serial
        except ImportError:
            log.error("pyserial fehlt — LoRa deaktiviert. "
                      "pip install pyserial --break-system-packages")
            return False

        try:
            self._ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
            time.sleep(0.3)
        except Exception as e:
            log.error("LA66: Port %s nicht zu oeffnen: %s", self.port, e)
            self._ser = None
            return False

        resp = self._cmd("AT", wait=1.5)
        if "OK" not in " ".join(resp).upper():
            log.error("LA66: keine AT-Antwort auf %s (Antwort: %r)", self.port, resp)
            self.close()
            return False

        log.info("LA66: verbunden auf %s @ %d Baud.", self.port, self.baud)

        if not self.is_joined():
            log.warning("LA66: noch nicht gejoint — loese AT+JOIN aus.")
            self._cmd("AT+JOIN", wait=2.0)
            # Nicht blockierend warten: der Worker-Thread puffert derweil.
        return True

    def is_joined(self) -> bool:
        if self._ser is None:
            return False
        resp = self._cmd("AT+NJS=?", wait=1.5)
        return any(l.strip() in ("1", "AT+NJS=1") for l in resp)

    def send(self, payload: bytes) -> bool:
        if self._ser is None:
            return False
        if not self.is_joined():
            log.warning("LA66: Uplink verworfen — kein Join.")
            return False

        confirm = 1 if self.confirmed else 0
        cmd = (f"AT+SENDB={confirm:02d},{self.fport:02d},"
               f"{len(payload)},{payload.hex()}")
        resp = self._cmd(cmd, wait=8.0)
        joined = " ".join(resp).upper()

        if "OK" in joined and "ERROR" not in joined:
            log.info("LA66: Uplink gesendet (%d Byte, Fport %d).",
                     len(payload), self.fport)
            return True

        log.error("LA66: Uplink fehlgeschlagen. Antwort: %r", resp)
        return False

    def close(self) -> None:
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None


# ============================================================================
# Sender — entkoppelter Worker-Thread
# ============================================================================

class LoRaTransmitter:
    """Nimmt Zaehlnachrichten entgegen und sendet sie im Hintergrund.

    `send_count()` ist nicht blockierend und darf aus dem Frame-Callback der
    Pipeline heraus aufgerufen werden."""

    def __init__(self, transport: Transport, min_interval_s: int = 120,
                 max_buffer: int = 50):
        self.transport = transport
        self.min_interval_s = min_interval_s
        self._q: queue.Queue[CountMessage] = queue.Queue(maxsize=max_buffer)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_send = 0.0
        self._dropped = 0
        self._sent = 0

    def start(self) -> bool:
        if not self.transport.connect():
            log.error("LoRa-Transport nicht verfuegbar — Sensor zaehlt ohne Uplink weiter.")
            return False
        self._thread = threading.Thread(target=self._worker, name="lora-tx", daemon=True)
        self._thread.start()
        log.info("LoRa-Sender gestartet (Mindestabstand %d s).", self.min_interval_s)
        return True

    def send_count(self, msg: CountMessage) -> None:
        """Nicht blockierend. Bei vollem Puffer wird die AELTESTE Nachricht
        verworfen — aktuelle Zaehlwerte sind wichtiger als alte."""
        try:
            self._q.put_nowait(msg)
        except queue.Full:
            try:
                self._q.get_nowait()
                self._q.put_nowait(msg)
                self._dropped += 1
                log.warning("LoRa-Puffer voll — aelteste Nachricht verworfen "
                            "(insgesamt %d).", self._dropped)
            except queue.Empty:
                pass

    def _worker(self) -> None:
        while not self._stop.is_set():
            try:
                msg = self._q.get(timeout=1.0)
            except queue.Empty:
                continue

            # Duty-Cycle-Bremse
            wait = self.min_interval_s - (time.time() - self._last_send)
            if wait > 0:
                if self._stop.wait(wait):
                    break

            if self.transport.send(msg.pack()):
                self._last_send = time.time()
                self._sent += 1
            else:
                # Nicht wegwerfen: zurueck in den Puffer, Flag setzen.
                msg.status |= STATUS_BUFFERED
                try:
                    self._q.put_nowait(msg)
                except queue.Full:
                    self._dropped += 1
                self._stop.wait(30)  # Ruhe vor dem naechsten Versuch

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self.transport.close()
        log.info("LoRa-Sender gestoppt. Gesendet: %d, verworfen: %d, im Puffer: %d.",
                 self._sent, self._dropped, self._q.qsize())


# ============================================================================
# Factory — liest die Umgebungsvariablen
# ============================================================================

def build_transmitter() -> LoRaTransmitter:
    """Baut den Sender gemaess Umgebung. Ohne LORA_ENABLED=1 immer Dummy."""
    enabled = os.getenv("LORA_ENABLED", "0") == "1"

    if not enabled:
        return LoRaTransmitter(DummyTransport(), min_interval_s=0)

    transport = LA66Transport(
        port=os.getenv("LORA_PORT", "/dev/ttyUSB0"),
        baud=int(os.getenv("LORA_BAUD", "9600")),
        fport=int(os.getenv("LORA_FPORT", "2")),
        confirmed=os.getenv("LORA_CONFIRMED", "0") == "1",
    )
    return LoRaTransmitter(
        transport,
        min_interval_s=int(os.getenv("LORA_MIN_INTERVAL_S", "120")),
    )


# ============================================================================
# Selbsttest — laeuft OHNE Hardware
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(message)s")

    print(f"\nNachrichtenformat: {MSG_LEN} Byte "
          f"(EU868-Payload-Grenze bei SF12: 51 Byte)\n")

    demo = CountMessage(
        sensor_id=3,
        count_in=12, count_out=9,
        count_total_in=430, count_total_out=411,
        interval_s=300,
        zone_count=2,
        mode=MODE_MULTI_ROI,
        status=STATUS_CAMERA_OK | STATUS_ACCEL_OK | STATUS_CONFIG_OK,
        frames_processed=8931,
    )

    raw = demo.pack()
    print(f"  Payload (hex) : {demo.hex()}")
    print(f"  Laenge        : {len(raw)} Byte")
    print(f"  AT-Kommando   : AT+SENDB=00,02,{len(raw)},{demo.hex()}")

    # Round-Trip beweist, dass der Decoder auf Serverseite umkehrbar ist
    back = CountMessage.unpack(raw)
    assert back.pack() == raw, "Round-Trip fehlgeschlagen!"
    print(f"  Round-Trip    : OK (Modus '{MODE_NAMES[back.mode]}', "
          f"Sensor {back.sensor_id}, {back.count_in} rein / {back.count_out} raus)")

    print("\n  -> Selbsttest der Serialisierung bestanden. "
          "Fuer echten Funk: LORA_ENABLED=1 setzen.\n")

    tx = build_transmitter()
    tx.start()
    tx.send_count(demo)
    time.sleep(1)
    tx.stop()
