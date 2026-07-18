#!/usr/bin/env python3
"""
test2_ttn.py — Test 2: Ende-zu-Ende ueber The Things Network (TTN).

Voraussetzung: Das Geraet ist bereits in der TTN-Konsole als End Device
registriert (siehe ANLEITUNG_TEST2.md) und ein TTN-Gateway ist in Reichweite.

Teiltests:
    T2.1  AT-Kontakt (wie Test 1 — Vorbedingung)
    T2.2  OTAA-Join gelingt (AT+JOIN -> AT+NJS=1, Timeout 120 s)
    T2.3  Einzel-Uplink: 25-Byte-Zaehlnachricht wird gesendet
    T2.4  Serien-Uplink: 3 Nachrichten ueber den LoRaTransmitter
          (Duty-Cycle-Bremse aktiv, Intervall via --interval, Standard 60 s)
    T2.5  Manuelle Bestaetigung: Payloads in der TTN-Konsole sichtbar
          und dekodieren korrekt (Abfrage am Ende des Skripts)

Das Skript gibt fuer T2.5 die erwarteten Werte aus, die du in der TTN-Live-
Ansicht wiederfinden musst (Payload-Hex + dekodierte Zaehlwerte).

Ergebnisprotokoll: test2_ergebnis.md

Aufruf:
    python3 test2_ttn.py
    python3 test2_ttn.py --port /dev/ttyUSB0 --interval 60
    python3 test2_ttn.py --skip-series          # nur Join + Einzel-Uplink
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from la66_probe import autodetect_baud, find_ports  # noqa: E402
from lora_transmitter import (  # noqa: E402
    MSG_LEN, MODE_MULTI_ROI,
    STATUS_ACCEL_OK, STATUS_CAMERA_OK, STATUS_CONFIG_OK,
    CountMessage, LA66Transport, LoRaTransmitter,
)

RESULTS: list[tuple[str, str, bool, str]] = []
SENT_PAYLOADS: list[tuple[str, CountMessage]] = []  # (hex, msg) fuer T2.5


def record(test_id: str, title: str, passed: bool, detail: str = "") -> None:
    RESULTS.append((test_id, title, passed, detail))
    tag = "BESTANDEN" if passed else "FEHLGESCHLAGEN"
    print(f"  [{test_id}] {title}: {tag}")
    if detail:
        for ln in detail.splitlines():
            print(f"         {ln}")


def make_msg(seq: int) -> CountMessage:
    """Erzeugt eine eindeutig wiedererkennbare Testnachricht.
    count_in traegt die Sequenznummer, damit die Uplinks in der TTN-Konsole
    zweifelsfrei zuzuordnen sind."""
    return CountMessage(
        sensor_id=99,           # 99 = Testsensor, nicht 1..17
        count_in=seq, count_out=seq * 2,
        count_total_in=100 + seq, count_total_out=90 + seq,
        interval_s=60, zone_count=2, mode=MODE_MULTI_ROI,
        status=STATUS_CAMERA_OK | STATUS_ACCEL_OK | STATUS_CONFIG_OK,
        frames_processed=1000 + seq,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Test 2: LA66 Ende-zu-Ende via TTN")
    ap.add_argument("--port", help="Seriellen Port erzwingen")
    ap.add_argument("--interval", type=int, default=60,
                    help="Mindestabstand zwischen Serien-Uplinks in s (Standard 60)")
    ap.add_argument("--join-timeout", type=int, default=120,
                    help="Maximale Wartezeit auf den Join in s (Standard 120)")
    ap.add_argument("--skip-series", action="store_true",
                    help="T2.4 ueberspringen (nur Join + Einzel-Uplink)")
    args = ap.parse_args()

    print("\n================  TEST 2 — ENDE-ZU-ENDE VIA TTN  ================\n")
    print("Vorbedingung: Geraet ist in der TTN-Konsole registriert und die")
    print("Live-Data-Ansicht der Application ist geoeffnet (zweiter Bildschirm/Handy).\n")

    # ---- T2.1 AT-Kontakt ----------------------------------------------------
    ports = [args.port] if args.port else find_ports()
    dev = None
    baud = None
    for port in ports:
        dev, baud = autodetect_baud(port)
        if dev:
            break
    record("T2.1", "AT-Kontakt", dev is not None,
           f"Port {dev.port}, {baud} Baud" if dev else "kein Modul gefunden")
    if not dev:
        write_report()
        return 1
    port_found, baud_found = dev.port, baud
    dev.close()  # LA66Transport oeffnet den Port selbst

    # ---- T2.2 Join ------------------------------------------------------------
    transport = LA66Transport(port=port_found, baud=baud_found, fport=2,
                              confirmed=False)
    if not transport.connect():
        record("T2.2", "OTAA-Join", False, "Transport-Verbindung fehlgeschlagen")
        write_report()
        return 1

    joined = transport.is_joined()
    if not joined:
        print(f"         Warte auf Join (max. {args.join_timeout} s) ...")
        deadline = time.time() + args.join_timeout
        while time.time() < deadline:
            time.sleep(5)
            if transport.is_joined():
                joined = True
                break
            remaining = int(deadline - time.time())
            print(f"         ... noch kein Join ({remaining} s verbleiben)")

    record("T2.2", "OTAA-Join gelingt", joined,
           "AT+NJS=1 — Geraet ist im TTN" if joined else
           "Kein Join. Checkliste:\n"
           "  1. Keys in TTN exakt uebernommen? (DevEUI/JoinEUI/AppKey)\n"
           "  2. LoRaWAN-Version in TTN: 1.0.3, Regional Parameters EU868\n"
           "  3. Gateway in Reichweite? (TTN Mapper / Konsole > Gateways)\n"
           "  4. Antenne montiert? Standort am Fenster probieren")

    if not joined:
        transport.close()
        write_report()
        return 1

    # ---- T2.3 Einzel-Uplink ---------------------------------------------------
    msg = make_msg(seq=1)
    ok = transport.send(msg.pack())
    if ok:
        SENT_PAYLOADS.append((msg.hex(), msg))
    record("T2.3", "Einzel-Uplink gesendet", ok,
           f"Payload: {msg.hex()}\n"
           f"Erwartung in TTN: Fport 2, 25 Byte, count_in=1, count_out=2")

    # ---- T2.4 Serien-Uplink -----------------------------------------------------
    if args.skip_series:
        record("T2.4", "Serien-Uplink (3x ueber Transmitter)", True,
               "uebersprungen (--skip-series)")
    else:
        tx = LoRaTransmitter(transport, min_interval_s=args.interval)
        # Transport ist schon verbunden; start() wuerde erneut verbinden —
        # deshalb Worker direkt starten:
        import threading
        tx._thread = threading.Thread(target=tx._worker, name="lora-tx", daemon=True)
        tx._thread.start()

        total = 3
        print(f"         Sende {total} Nachrichten, Mindestabstand {args.interval} s")
        print(f"         (Dauer ca. {total * args.interval // 60 + 1} min — Duty Cycle!)")
        for seq in range(2, 2 + total):
            m = make_msg(seq)
            SENT_PAYLOADS.append((m.hex(), m))
            tx.send_count(m)

        # Warten bis Queue leer oder Timeout
        wait_deadline = time.time() + (total + 1) * args.interval + 30
        while time.time() < wait_deadline and not tx._q.empty():
            time.sleep(5)
        sent_count = tx._sent
        tx._stop.set()
        tx._thread.join(timeout=5)

        record("T2.4", "Serien-Uplink (3x ueber Transmitter)", sent_count >= total,
               f"{sent_count} von {total} gesendet, "
               f"{tx._q.qsize()} verblieben im Puffer, {tx._dropped} verworfen")

    transport.close()

    # ---- T2.5 Manuelle Bestaetigung ---------------------------------------------
    print("\n  [T2.5] Manuelle Bestaetigung in der TTN-Konsole")
    print("  Pruefe in TTN > Application > Live data, ob diese Payloads angekommen")
    print("  sind und der Decoder die Werte korrekt anzeigt:\n")
    for i, (hexstr, m) in enumerate(SENT_PAYLOADS, 1):
        print(f"    {i}. {hexstr}")
        print(f"       -> sensor_id={m.sensor_id}, count_in={m.count_in}, "
              f"count_out={m.count_out}, frames={m.frames_processed}")
    answer = input("\n  Alle Payloads in TTN sichtbar und korrekt dekodiert? [j/N] ")
    manual_ok = answer.strip().lower() in ("j", "ja", "y", "yes")
    record("T2.5", "Payloads in TTN sichtbar + korrekt dekodiert", manual_ok,
           f"{len(SENT_PAYLOADS)} Payloads zur Pruefung vorgelegt")

    write_report()
    passed = sum(1 for *_r, p, _ in RESULTS if p)
    print(f"\nErgebnis: {passed}/{len(RESULTS)} bestanden.")
    return 0 if passed == len(RESULTS) else 1


def write_report() -> None:
    out = Path(__file__).resolve().parent / "test2_ergebnis.md"
    passed = sum(1 for *_r, p, _ in RESULTS if p)
    lines = [
        "# Test 2 — Ergebnisprotokoll (Ende-zu-Ende via TTN)",
        "",
        f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}  ",
        f"Ergebnis: **{passed} von {len(RESULTS)} Teiltests bestanden**",
        "",
        "| Test | Pruefpunkt | Ergebnis |",
        "|---|---|---|",
    ]
    for tid, title, p, _ in RESULTS:
        lines.append(f"| {tid} | {title} | {'✅ bestanden' if p else '❌ fehlgeschlagen'} |")
    lines += ["", "## Gesendete Test-Payloads", ""]
    if SENT_PAYLOADS:
        lines.append("| # | Payload (hex) | count_in | count_out |")
        lines.append("|---|---|---|---|")
        for i, (hexstr, m) in enumerate(SENT_PAYLOADS, 1):
            lines.append(f"| {i} | `{hexstr}` | {m.count_in} | {m.count_out} |")
    else:
        lines.append("keine")
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
    print(f"\nProtokoll: {out}")


if __name__ == "__main__":
    sys.exit(main())
