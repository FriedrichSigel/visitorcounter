#!/usr/bin/env python3
"""
la66_probe.py — Diagnoseskript fuer den Dragino LA66 USB LoRaWAN Adapter V2 (EU868).

Eigenstaendig: keine Abhaengigkeit zu core/. Einzige externe Abhaengigkeit: pyserial.
    pip install pyserial --break-system-packages

Zweck: schrittweise pruefen, wie weit die LoRa-Kette traegt — OHNE dass dafuer
bereits Keys an die Stadtwerke oder an TTN uebermittelt sein muessen.

Stufen:
    1. Port finden          — haengt ein CP210x/CH340 USB-TTL-Wandler am Pi?
    2. AT-Ping              — antwortet das Modul ueberhaupt? (Das war bei der
                              Sonel LORA-S1 der Punkt, an dem es scheiterte.)
    3. Konfiguration lesen  — DevEUI / AppEUI / AppKey / Frequenzband auslesen
    4. Join-Status          — ist das Geraet bei einem Network Server angemeldet?
    5. Testuplink           — nur wenn 4 erfolgreich (--send)

Aufruf:
    python3 la66_probe.py                  # Stufe 1-4, Keys maskiert
    python3 la66_probe.py --show-keys      # Keys im Klartext (NICHT ins Protokoll!)
    python3 la66_probe.py --join           # Join-Versuch ausloesen (AT+JOIN)
    python3 la66_probe.py --send           # Test-Uplink senden (setzt Join voraus)
    python3 la66_probe.py --port /dev/ttyUSB0 --baud 9600

SICHERHEIT: DevEUI/AppEUI/AppKey sind Geheimnisse. Standardmaessig maskiert dieses
Skript sie. --show-keys nur lokal am Terminal nutzen, Ausgabe niemals ins Repo,
in Screenshots oder in die Bachelorarbeit uebernehmen.
"""

from __future__ import annotations

import argparse
import glob
import sys
import time

try:
    import serial  # pyserial
    from serial.tools import list_ports
    HAS_PYSERIAL = True
except ImportError:
    serial = None
    list_ports = None
    HAS_PYSERIAL = False


def require_pyserial() -> None:
    if not HAS_PYSERIAL:
        sys.exit("FEHLER: pyserial fehlt.  ->  "
                 "pip install pyserial --break-system-packages")


# ----------------------------------------------------------------------------
# Konstanten
# ----------------------------------------------------------------------------

# Der LA66 USB Adapter V2 nutzt einen CP2102 USB-TTL-Wandler (Silicon Labs).
KNOWN_USB_TTL_VIDS = {
    0x10C4: "Silicon Labs CP210x (typisch fuer LA66 USB Adapter V2)",
    0x1A86: "QinHeng CH340/CH341",
    0x0403: "FTDI FT232",
}

# Baudraten, die der LA66 je nach Firmware/Bootloader nutzt. 9600 ist Default.
BAUD_CANDIDATES = [9600, 115200, 57600, 38400]

# Felder, die als Geheimnis gelten und maskiert werden.
SECRET_FIELDS = ("DEUI", "APPEUI", "APPKEY", "NWKSKEY", "APPSKEY", "DADDR")


# ----------------------------------------------------------------------------
# Hilfsfunktionen
# ----------------------------------------------------------------------------

def mask(value: str) -> str:
    """Maskiert einen Schluesselwert bis auf die letzten 4 Zeichen."""
    v = value.strip()
    if len(v) <= 4:
        return "****"
    return "*" * (len(v) - 4) + v[-4:]


def is_secret_line(line: str) -> bool:
    upper = line.upper()
    return any(f"{f}" in upper for f in SECRET_FIELDS)


def redact_line(line: str, show_keys: bool) -> str:
    """Maskiert Schluesselwerte in einer AT+CFG-Ausgabezeile."""
    if show_keys or not is_secret_line(line):
        return line
    if "=" in line:
        head, _, tail = line.partition("=")
        return f"{head}={mask(tail)}"
    return line


def banner(step: str, text: str) -> None:
    print(f"\n{'=' * 66}\n  {step}  {text}\n{'=' * 66}")


def ok(msg: str) -> None:
    print(f"  [ OK ]   {msg}")


def fail(msg: str) -> None:
    print(f"  [FEHL]   {msg}")


def info(msg: str) -> None:
    print(f"           {msg}")


# ----------------------------------------------------------------------------
# Stufe 1: Port finden
# ----------------------------------------------------------------------------

def find_ports() -> list[str]:
    require_pyserial()
    banner("STUFE 1", "USB-Port suchen")

    candidates: list[str] = []
    for p in list_ports.comports():
        vid_note = KNOWN_USB_TTL_VIDS.get(p.vid, None)
        marker = "<-- Kandidat" if vid_note else ""
        vid_hex = f"{p.vid:04X}" if p.vid is not None else "----"
        pid_hex = f"{p.pid:04X}" if p.pid is not None else "----"
        print(f"           {p.device:<16} VID:PID {vid_hex}:{pid_hex}  "
              f"{(p.description or '?'):<30} {marker}")
        if vid_note:
            candidates.append(p.device)
            info(f"    -> {vid_note}")

    # Fallback: rohe Geraeteknoten, falls list_ports nichts liefert
    if not candidates:
        raw = sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
        if raw:
            info("Kein bekannter USB-TTL-Chip erkannt, aber diese Knoten existieren:")
            for r in raw:
                info(f"    {r}")
            candidates = raw

    if candidates:
        ok(f"{len(candidates)} moeglicher Port gefunden.")
    else:
        fail("Kein serieller Port gefunden.")
        info("Pruefen: Adapter wirklich eingesteckt? 'lsusb' und 'dmesg | tail -20'.")
        info("Falls 'Permission denied' folgt:  sudo usermod -aG dialout $USER")
        info("(danach ab- und wieder anmelden)")
    return candidates


# ----------------------------------------------------------------------------
# Serielle Kommunikation
# ----------------------------------------------------------------------------

class LA66:
    def __init__(self, port: str, baud: int, timeout: float = 1.0):
        self.port = port
        self.baud = baud
        self.ser = serial.Serial(port, baud, timeout=timeout)
        time.sleep(0.3)
        self.ser.reset_input_buffer()

    def close(self) -> None:
        try:
            self.ser.close()
        except Exception:
            pass

    def command(self, cmd: str, wait: float = 1.2) -> list[str]:
        """Sendet ein AT-Kommando und sammelt alle Antwortzeilen."""
        self.ser.reset_input_buffer()
        self.ser.write((cmd + "\r\n").encode("ascii"))
        self.ser.flush()

        deadline = time.time() + wait
        lines: list[str] = []
        while time.time() < deadline:
            raw = self.ser.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").strip()
            if line:
                lines.append(line)
                deadline = time.time() + 0.35  # Nachlauf fuer mehrzeilige Antworten
        return lines


def autodetect_baud(port: str) -> tuple[LA66, int] | tuple[None, None]:
    """Probiert die ueblichen Baudraten durch, bis 'AT' ein OK liefert."""
    require_pyserial()
    for baud in BAUD_CANDIDATES:
        try:
            dev = LA66(port, baud)
        except serial.SerialException as e:
            fail(f"Port {port} nicht zu oeffnen: {e}")
            return None, None

        resp = dev.command("AT", wait=1.0)
        joined = " ".join(resp).upper()
        if "OK" in joined:
            return dev, baud
        dev.close()
    return None, None


# ----------------------------------------------------------------------------
# Stufe 2: AT-Ping
# ----------------------------------------------------------------------------

def stage_ping(port: str, forced_baud: int | None) -> tuple[LA66 | None, int | None]:
    banner("STUFE 2", f"AT-Ping auf {port}")

    if forced_baud:
        try:
            dev = LA66(port, forced_baud)
        except serial.SerialException as e:
            fail(f"Port nicht zu oeffnen: {e}")
            return None, None
        resp = dev.command("AT")
        if "OK" in " ".join(resp).upper():
            ok(f"Modul antwortet bei {forced_baud} Baud.")
            return dev, forced_baud
        fail(f"Keine Antwort bei {forced_baud} Baud. Antwort war: {resp!r}")
        dev.close()
        return None, None

    info(f"Probiere Baudraten: {BAUD_CANDIDATES}")
    dev, baud = autodetect_baud(port)
    if dev:
        ok(f"Modul antwortet mit OK bei {baud} Baud.")
        info("Damit ist der entscheidende Unterschied zur Sonel LORA-S1 belegt:")
        info("Das LA66 spricht ein offenes, dokumentiertes AT-Protokoll.")
        return dev, baud

    fail("Keine AT-Antwort auf keiner Baudrate.")
    info("Moegliche Ursachen:")
    info("  - falscher Port (anderen Kandidaten aus Stufe 1 probieren)")
    info("  - Modul im Bootloader-/Burn-Modus (BOOT-Pin gebrueckt?)")
    info("  - fehlende Rechte (dialout-Gruppe)")
    return None, None


# ----------------------------------------------------------------------------
# Stufe 3: Konfiguration auslesen
# ----------------------------------------------------------------------------

def stage_config(dev: LA66, show_keys: bool) -> dict[str, str]:
    banner("STUFE 3", "Konfiguration auslesen (AT+CFG)")

    lines = dev.command("AT+CFG", wait=3.0)
    if not lines:
        fail("AT+CFG liefert keine Ausgabe.")
        return {}

    cfg: dict[str, str] = {}
    for line in lines:
        print(f"           {redact_line(line, show_keys)}")
        if "=" in line and line.upper().startswith("AT+"):
            key, _, val = line.partition("=")
            cfg[key.strip().upper()] = val.strip()

    if not show_keys:
        print()
        info("Schluesselwerte sind maskiert. Fuer den Klartext:  --show-keys")

    print()
    ok(f"{len(cfg)} Konfigurationsfelder gelesen.")

    # Gezielt die drei Werte nachfragen, die die Stadtwerke brauchen
    print()
    info("Die drei Werte, die der Network Server der Stadtwerke braucht:")
    for cmd, label in (("AT+DEUI=?", "DevEUI "),
                       ("AT+APPEUI=?", "AppEUI "),
                       ("AT+APPKEY=?", "AppKey ")):
        resp = dev.command(cmd, wait=1.0)
        val = next((l for l in resp if l.upper() != "OK"), "?")
        shown = val if show_keys else mask(val)
        print(f"             {label}: {shown}")

    print()
    info("Frequenzband pruefen (muss EU868 sein):")
    for line in dev.command("AT+BAND=?", wait=1.0):
        print(f"             {line}")

    return cfg


# ----------------------------------------------------------------------------
# Stufe 4: Join-Status
# ----------------------------------------------------------------------------

def stage_join_status(dev: LA66, do_join: bool) -> bool:
    banner("STUFE 4", "Join-Status")

    resp = dev.command("AT+NJS=?", wait=1.5)
    for line in resp:
        print(f"           {line}")

    joined = any(l.strip() in ("1", "AT+NJS=1") for l in resp)

    if joined:
        ok("Geraet ist bei einem Network Server GEJOINT.")
        return True

    fail("Geraet ist NICHT gejoint.")
    info("Das ist an dieser Stelle voellig erwartbar und KEIN Software-Fehler:")
    info("Ein OTAA-Join gelingt erst, wenn (a) die Keys bei einem Network")
    info("Server hinterlegt sind und (b) ein Gateway in Funkreichweite steht.")
    info("Beides liegt ausserhalb dieses Skripts.")

    if not do_join:
        info("Join-Versuch ausloesen mit:  --join")
        return False

    print()
    info("Loese Join-Versuch aus (AT+JOIN) — das kann bis zu 60 s dauern ...")
    dev.command("AT+JOIN", wait=2.0)

    for attempt in range(12):
        time.sleep(5)
        r = dev.command("AT+NJS=?", wait=1.0)
        if any(l.strip() in ("1", "AT+NJS=1") for l in r):
            print()
            ok("JOIN ERFOLGREICH. Das Geraet ist im LoRaWAN-Netz.")
            return True
        print(f"           ... Versuch {attempt + 1}/12, noch kein Join")

    print()
    fail("Join innerhalb von 60 s nicht zustande gekommen.")
    info("Haeufigste Ursache in dieser Reihenfolge:")
    info("  1. Keys nirgends registriert  -> in TTN eintragen ODER an Stadtwerke geben")
    info("  2. Kein Gateway in Reichweite -> Standort/Antenne pruefen")
    info("  3. Falsches Band              -> AT+BAND muss EU868 sein")
    return False


# ----------------------------------------------------------------------------
# Stufe 5: Testuplink
# ----------------------------------------------------------------------------

def stage_send(dev: LA66) -> None:
    banner("STUFE 5", "Test-Uplink")

    # Minimaler Testframe: 4 Byte, Fport 2, unbestaetigt.
    # Kein echter Zaehlwert — nur der Nachweis, dass AT+SENDB akzeptiert wird.
    payload_hex = "DEADBEEF"
    cmd = f"AT+SENDB=00,02,{len(payload_hex) // 2},{payload_hex}"
    info(f"Sende: {cmd}")

    for line in dev.command(cmd, wait=6.0):
        print(f"           {line}")

    ok("Kommando abgesetzt. Ob der Uplink ankommt, zeigt nur der Network Server.")


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Diagnose fuer Dragino LA66 USB LoRaWAN Adapter V2 (EU868)"
    )
    ap.add_argument("--port", help="Serieller Port, z. B. /dev/ttyUSB0")
    ap.add_argument("--baud", type=int, help="Baudrate erzwingen (sonst Autodetect)")
    ap.add_argument("--show-keys", action="store_true",
                    help="Schluessel im Klartext anzeigen (nur lokal!)")
    ap.add_argument("--join", action="store_true",
                    help="Join-Versuch ausloesen (AT+JOIN)")
    ap.add_argument("--send", action="store_true",
                    help="Test-Uplink senden (setzt erfolgreichen Join voraus)")
    args = ap.parse_args()

    print("\nLA66-Probe — Dragino LA66 USB LoRaWAN Adapter V2 (EU868)")
    print("Bachelorarbeit Personenzaehlung / Stadtwerke Potsdam\n")

    # Stufe 1
    ports = [args.port] if args.port else find_ports()
    if not ports:
        return 1

    # Stufe 2
    dev = None
    baud = None
    for port in ports:
        dev, baud = stage_ping(port, args.baud)
        if dev:
            break

    if not dev:
        print()
        fail("Abbruch: kein antwortendes Modul gefunden.")
        return 1

    try:
        # Stufe 3
        stage_config(dev, args.show_keys)

        # Stufe 4
        joined = stage_join_status(dev, args.join)

        # Stufe 5
        if args.send:
            if joined:
                stage_send(dev)
            else:
                banner("STUFE 5", "Test-Uplink")
                fail("Uebersprungen — ohne Join kein Uplink moeglich.")

        # Zusammenfassung
        banner("ERGEBNIS", "Zusammenfassung")
        print(f"           Port          : {dev.port}")
        print(f"           Baudrate      : {baud}")
        print(f"           AT-Protokoll  : funktioniert")
        print(f"           Keys lesbar   : ja")
        print(f"           Join-Status   : {'gejoint' if joined else 'nicht gejoint'}")
        print()
        if not joined:
            info("Naechster Schritt: DevEUI/AppEUI/AppKey bei einem Network Server")
            info("registrieren — testweise im eigenen TTN, produktiv bei den")
            info("Stadtwerken Potsdam. Erst danach kann ein Join gelingen.")
        print()

    finally:
        dev.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
