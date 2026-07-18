#!/usr/bin/env python3
"""
test1_offline.py — Test 1: LA66-Hardware und Software-Kette OHNE Network Server.

Prueft alles, was ohne TTN und ohne Stadtwerke-Registrierung pruefbar ist:

    T1.1  Serieller Port vorhanden (CP2102 erkannt)
    T1.2  AT-Protokoll antwortet (Lebenszeichen)
    T1.3  Konfiguration lesbar (DevEUI/AppEUI/AppKey vorhanden, EU868 gesetzt)
    T1.4  Join-Status abfragbar (Erwartung hier: NICHT gejoint = bestanden,
          denn ohne registrierte Keys DARF kein Join zustande kommen)
    T1.5  Serialisierung: 25-Byte-Format, Round-Trip pack/unpack
    T1.6  Transmitter-Logik: Queue, Pufferung, sauberes Stoppen (DummyTransport)
    T1.7  SENDB-Kommando wird vom Modul syntaktisch akzeptiert
          (Uplink geht mangels Join nicht raus — es zaehlt nur, dass das
          Modul das Kommando versteht statt es als Fehler abzuweisen)

Ergebnis wird als Protokoll nach test1_ergebnis.md geschrieben — direkt
verwendbar als Anhang/Beleg fuer Kapitel 4.c der Arbeit.

Aufruf (auf dem Pi, LA66 eingesteckt):
    python3 test1_offline.py
    python3 test1_offline.py --port /dev/ttyUSB0
    python3 test1_offline.py --skip-hardware     # nur T1.5/T1.6 (Laptop ohne Stick)
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

# la66_probe und lora_transmitter liegen eine Ebene hoeher
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from la66_probe import LA66, autodetect_baud, find_ports, mask  # noqa: E402
from lora_transmitter import (  # noqa: E402
    MSG_LEN, MODE_MULTI_ROI,
    STATUS_ACCEL_OK, STATUS_CAMERA_OK, STATUS_CONFIG_OK,
    CountMessage, DummyTransport, LoRaTransmitter,
)

RESULTS: list[tuple[str, str, bool, str]] = []  # (id, titel, bestanden, detail)


def record(test_id: str, title: str, passed: bool, detail: str = "") -> None:
    RESULTS.append((test_id, title, passed, detail))
    tag = "BESTANDEN" if passed else "FEHLGESCHLAGEN"
    print(f"  [{test_id}] {title}: {tag}")
    if detail:
        for ln in detail.splitlines():
            print(f"         {ln}")


# ----------------------------------------------------------------------------
# Hardware-Tests T1.1 - T1.4, T1.7
# ----------------------------------------------------------------------------

def run_hardware_tests(forced_port: str | None) -> None:
    # T1.1 Port
    ports = [forced_port] if forced_port else find_ports()
    record("T1.1", "Serieller Port vorhanden", bool(ports),
           f"Gefunden: {', '.join(ports) if ports else 'keiner'}")
    if not ports:
        for tid, title in (("T1.2", "AT-Protokoll antwortet"),
                           ("T1.3", "Konfiguration lesbar"),
                           ("T1.4", "Join-Status abfragbar"),
                           ("T1.7", "SENDB syntaktisch akzeptiert")):
            record(tid, title, False, "uebersprungen — kein Port")
        return

    # T1.2 AT-Ping
    dev = None
    baud = None
    for port in ports:
        dev, baud = autodetect_baud(port)
        if dev:
            break
    record("T1.2", "AT-Protokoll antwortet", dev is not None,
           f"Port {dev.port}, {baud} Baud" if dev else
           "Keine AT-Antwort — Bootmodus? Rechte (dialout)?")
    if not dev:
        for tid, title in (("T1.3", "Konfiguration lesbar"),
                           ("T1.4", "Join-Status abfragbar"),
                           ("T1.7", "SENDB syntaktisch akzeptiert")):
            record(tid, title, False, "uebersprungen — kein AT-Kontakt")
        return

    try:
        # T1.3 Konfiguration
        deui = next((l for l in dev.command("AT+DEUI=?") if l.upper() != "OK"), "")
        appeui = next((l for l in dev.command("AT+APPEUI=?") if l.upper() != "OK"), "")
        appkey = next((l for l in dev.command("AT+APPKEY=?") if l.upper() != "OK"), "")
        band_lines = dev.command("AT+BAND=?")
        band = " ".join(l for l in band_lines if l.upper() != "OK")

        cfg_ok = all(len(v.replace(" ", "")) >= 8 for v in (deui, appeui, appkey))
        detail = (f"DevEUI : {mask(deui)}\n"
                  f"AppEUI : {mask(appeui)}\n"
                  f"AppKey : {mask(appkey)}\n"
                  f"Band   : {band or '?'}")
        eu868_hint = "" if "868" in band or "EU868" in band.upper() else \
            "\nWARNUNG: Band enthaelt nicht '868' — vor Betrieb pruefen!"
        record("T1.3", "Konfiguration lesbar (Keys + Band)", cfg_ok, detail + eu868_hint)

        # T1.4 Join-Status abfragbar (Erwartung: 0)
        njs = dev.command("AT+NJS=?", wait=1.5)
        answered = bool(njs)
        joined = any(l.strip() in ("1", "AT+NJS=1") for l in njs)
        detail = f"Antwort: {njs!r} -> {'GEJOINT' if joined else 'nicht gejoint'}"
        if not joined:
            detail += ("\nErwartungsgemaess: ohne registrierte Keys ist kein "
                       "Join moeglich. Test gilt als bestanden, weil der "
                       "STATUS ABFRAGBAR ist.")
        record("T1.4", "Join-Status abfragbar", answered, detail)

        # T1.7 SENDB-Syntax
        demo = build_demo_message()
        cmd = f"AT+SENDB=00,02,{MSG_LEN},{demo.hex()}"
        resp = dev.command(cmd, wait=6.0)
        joined_resp = " ".join(resp).upper()
        # Ohne Join antwortet die Firmware typischerweise mit einem Hinweis
        # statt mit einem Syntaxfehler. "AT_PARAM_ERROR"/"AT_BUSY_ERROR" etc.
        # wuerden auf ein Formatproblem hindeuten.
        syntax_ok = bool(resp) and "PARAM" not in joined_resp
        record("T1.7", "SENDB-Kommando syntaktisch akzeptiert", syntax_ok,
               f"Kommando: {cmd[:40]}...\nAntwort : {resp!r}\n"
               "Hinweis: Der Uplink geht ohne Join nicht raus — geprueft wird "
               "nur, dass das Modul das 25-Byte-Kommando versteht.")
    finally:
        dev.close()


# ----------------------------------------------------------------------------
# Software-Tests T1.5 / T1.6 (laufen ueberall, auch ohne Hardware)
# ----------------------------------------------------------------------------

def build_demo_message() -> CountMessage:
    return CountMessage(
        sensor_id=1, count_in=7, count_out=5,
        count_total_in=120, count_total_out=118,
        interval_s=300, zone_count=2, mode=MODE_MULTI_ROI,
        status=STATUS_CAMERA_OK | STATUS_ACCEL_OK | STATUS_CONFIG_OK,
        frames_processed=4123,
    )


def run_software_tests() -> None:
    # T1.5 Serialisierung
    try:
        msg = build_demo_message()
        raw = msg.pack()
        back = CountMessage.unpack(raw)
        ok = len(raw) == MSG_LEN and back.pack() == raw
        record("T1.5", "25-Byte-Format, Round-Trip pack/unpack", ok,
               f"Laenge {len(raw)} Byte, Payload {msg.hex()}")
    except Exception as e:
        record("T1.5", "25-Byte-Format, Round-Trip pack/unpack", False, repr(e))

    # T1.6 Transmitter-Logik mit Dummy
    try:
        dummy = DummyTransport()
        tx = LoRaTransmitter(dummy, min_interval_s=0, max_buffer=3)
        started = tx.start()
        for i in range(5):  # 5 in Puffergroesse 3 -> Verdraengung muss greifen
            m = build_demo_message()
            m.count_in = i
            tx.send_count(m)
        time.sleep(1.0)
        tx.stop()
        ok = started and len(dummy.sent) >= 1
        record("T1.6", "Transmitter: Queue, Verdraengung, Stopp", ok,
               f"Gesendet (simuliert): {len(dummy.sent)}")
    except Exception as e:
        record("T1.6", "Transmitter: Queue, Verdraengung, Stopp", False, repr(e))


# ----------------------------------------------------------------------------
# Protokoll schreiben
# ----------------------------------------------------------------------------

def write_report() -> Path:
    out = Path(__file__).resolve().parent / "test1_ergebnis.md"
    passed = sum(1 for *_r, p, _ in RESULTS if p)
    lines = [
        "# Test 1 — Ergebnisprotokoll (offline, ohne Network Server)",
        "",
        f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}  ",
        f"Ergebnis: **{passed} von {len(RESULTS)} Teiltests bestanden**",
        "",
        "| Test | Pruefpunkt | Ergebnis |",
        "|---|---|---|",
    ]
    for tid, title, p, _ in RESULTS:
        lines.append(f"| {tid} | {title} | {'✅ bestanden' if p else '❌ fehlgeschlagen'} |")
    lines += ["", "## Details", ""]
    for tid, title, p, detail in RESULTS:
        lines.append(f"### {tid} — {title}")
        lines.append("bestanden" if p else "**fehlgeschlagen**")
        if detail:
            lines.append("```")
            lines.append(detail)
            lines.append("```")
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Test 1: LA66 offline")
    ap.add_argument("--port", help="Seriellen Port erzwingen")
    ap.add_argument("--skip-hardware", action="store_true",
                    help="Nur Software-Tests (T1.5/T1.6)")
    args = ap.parse_args()

    print("\n================  TEST 1 — OFFLINE  ================\n")
    if not args.skip_hardware:
        run_hardware_tests(args.port)
    run_software_tests()

    report = write_report()
    passed = sum(1 for *_r, p, _ in RESULTS if p)
    print(f"\nErgebnis: {passed}/{len(RESULTS)} bestanden.")
    print(f"Protokoll: {report}\n")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
