#!/usr/bin/env python3
"""
lora_send_loop.py — Zyklischer LoRa-Sendetest für den LA66 USB Adapter V2.

Sendet einen festen Test-Frame (18-Byte-Zählformat v2) über AT+SENDB. Solange
das Senden nicht bestätigt wird, wird jede RETRY_SECONDS erneut versucht. Nach
einem erfolgreichen Uplink wird PAUSE_MINUTES pausiert, um den EU868-Duty-Cycle
(1 %) zu schonen und die Bandbreite nicht zu spammen.

Nutzung:
    python3 lora_send_loop.py
    python3 lora_send_loop.py --pause 10 --retry 60
    python3 lora_send_loop.py --payload 02032A05073F0803020105060000000000

Beenden mit Strg-C.

Voraussetzung: pyserial (auf dem Pi vorhanden). Das Skript nutzt denselben
Port/dieselbe Baudrate wie la66_probe.py.
"""

import argparse
import sys
import time
from datetime import datetime

import serial

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

# Wortmarken in der LA66-Ausgabe, die Erfolg bzw. "Modul beschäftigt" anzeigen.
SUCCESS_MARKERS = ("txDone", "TX_DONE", "JOINED", "Join Success")
BUSY_MARKERS = ("AT_ERROR", "AT_BUSY_ERROR", "AT_PARAM_ERROR")


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


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
    args = ap.parse_args()

    # Payload validieren
    payload = args.payload.strip().replace(" ", "")
    try:
        bytes.fromhex(payload)
    except ValueError:
        log(f"FEHLER: Payload ist kein gültiges Hex: {payload!r}")
        sys.exit(1)

    log(f"Öffne {args.port} @ {args.baud} Baud")
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except serial.SerialException as e:
        log(f"FEHLER: Port konnte nicht geöffnet werden: {e}")
        log("Prüfen: Steckt der LA66? Rechte (dialout-Gruppe)? Richtiger Port?")
        sys.exit(1)

    time.sleep(0.5)  # dem Adapter kurz Zeit geben

    log(f"Test-Frame: {payload}  ({len(payload)//2} Byte, Port {FPORT})")
    log(f"Strategie: alle {args.retry}s versuchen; nach Erfolg {args.pause} min Pause. "
        f"(Strg-C zum Beenden)")

    sent_count = 0
    try:
        while True:
            success = send_once(ser, payload)
            if success:
                sent_count += 1
                log(f"Gesamt erfolgreich gesendet: {sent_count}")
                if args.once:
                    break
                log(f"Pause {args.pause} min bis zum nächsten Uplink ...")
                time.sleep(args.pause * 60)
            else:
                if args.once:
                    break
                time.sleep(args.retry)
    except KeyboardInterrupt:
        log("Abgebrochen. Bis dann.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
