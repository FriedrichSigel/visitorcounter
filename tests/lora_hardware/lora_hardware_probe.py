"""
lora_hardware_probe.py — Diagnosewerkzeug: findet heraus, ob und wie sich
ein angeschlossenes USB-Gerät (hier: das Sonel LORA-S1) über eine serielle
Schnittstelle ansprechen lässt.

Hintergrund: Laut Herstellerdokumentation ist das LORA-S1 ein proprietäres
Zubehör für Sonels eigene PV-Messgeräte (IRM-1 <-> MPI-540-PV/PVM-1530),
kein offen dokumentierter LoRaWAN-USB-Adapter (siehe HANDOFF.md). Dieses
Skript probiert es trotzdem systematisch aus, statt das nur zu vermuten:

  1. lsusb (falls verfügbar) — zeigt VID:PID, unabhängig davon, ob ein
     serieller Port erkannt wird
  2. Suche nach seriellen Geräten (/dev/ttyUSB*, /dev/ttyACM* o. ä.)
  3. Für jeden gefundenen Port: mehrere gängige Baudraten durchprobieren,
     kurz passiv horchen (falls das Gerät von selbst sendet), dann ein
     paar verbreitete Abfragebefehle schicken — JEDE Antwort wird roh
     protokolliert (Hex + Text), auch Rauschen/Müll.

Wie die Ergebnisse zu deuten sind:
  - Kein serielles Gerät gefunden -> nutzt vermutlich keinen Standard-
    USB-Seriell-Chip, pyserial kann es dann gar nicht ansprechen.
  - Port gefunden, aber nie eine Antwort -> wartet vermutlich auf ein
    eigenes (unbekanntes) Pairing-Protokoll, nicht auf einfache AT-Befehle.
  - Port gefunden UND irgendeine Antwort kommt -> Protokoll ist evtl.
    doch (teilweise) nutzbar, weitere Analyse der geloggten Rohdaten nötig.

Nutzung auf dem Pi (Gerät VORHER per USB anstecken):
    pip install pyserial --break-system-packages
    python lora_hardware_probe.py
"""

import subprocess
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print("pyserial ist nicht installiert. Installieren mit:")
    print("  pip install pyserial --break-system-packages")
    sys.exit(1)

BAUD_RATES_TO_TRY = [9600, 19200, 38400, 57600, 115200]

# Ein paar verbreitete Abfragebefehle bei seriellen LoRa-/Funkmodulen.
# Keiner davon ist speziell fürs Sonel-Gerät bekannt — das ist Teil des
# Ausprobierens, nicht eine bestätigte Kompatibilität.
PROBE_COMMANDS = [
    b"AT\r\n",
    b"AT+VERSION\r\n",
    b"AT+INFO\r\n",
    b"\r\n",
]


def list_serial_ports():
    """
    Listet alle erkannten seriellen Geräte mit Hersteller-/Produkt-Info,
    falls vom Betriebssystem bereitgestellt — hilft, das Sonel-Gerät zu
    identifizieren, falls mehrere serielle Geräte angeschlossen sind.
    """
    ports = list(list_ports.comports())
    if not ports:
        print("Keine seriellen Geräte gefunden (kein /dev/ttyUSB*, /dev/ttyACM* o. ä.).")
        print("Das deutet darauf hin, dass das Gerät keinen Standard-USB-Seriell-Chip")
        print("nutzt und sich damit vermutlich nicht per pyserial ansprechen lässt.")
        return []

    print(f"{len(ports)} serielle(s) Gerät(e) gefunden:")
    for p in ports:
        vid_pid = f" (VID:PID={p.vid:04x}:{p.pid:04x})" if p.vid else ""
        print(f"  {p.device}  —  {p.description}{vid_pid}")
    return ports


def probe_port(port_name, baudrate, timeout=2):
    """
    Öffnet den Port bei einer bestimmten Baudrate, hört kurz passiv (falls
    das Gerät von selbst etwas sendet), schickt dann nacheinander die
    PROBE_COMMANDS und protokolliert jede Antwort roh (Text + Hex).

    Gibt True zurück, wenn IRGENDEINE Antwort kam (auch Rauschen/Müll),
    sonst False.
    """
    got_any_response = False
    try:
        with serial.Serial(port_name, baudrate, timeout=timeout) as ser:
            print(f"\n--- {port_name} @ {baudrate} Baud ---")

            time.sleep(0.5)
            passive = ser.read(256)
            if passive:
                got_any_response = True
                print(f"  Passiv empfangen (ohne Anfrage): {passive!r} (hex: {passive.hex()})")

            for cmd in PROBE_COMMANDS:
                ser.reset_input_buffer()
                ser.write(cmd)
                time.sleep(0.3)
                response = ser.read(256)
                if response:
                    got_any_response = True
                    print(f"  Gesendet: {cmd!r} -> Antwort: {response!r} (hex: {response.hex()})")
                else:
                    print(f"  Gesendet: {cmd!r} -> keine Antwort")

    except serial.SerialException as e:
        print(f"  Port {port_name} @ {baudrate} konnte nicht geöffnet werden: {e}")

    return got_any_response


def main():
    print("=== LoRa-Hardware-Diagnose ===\n")

    try:
        result = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("USB-Geräte (lsusb):")
            print(result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("(lsusb nicht verfügbar oder fehlgeschlagen, überspringe)\n")

    ports = list_serial_ports()
    if not ports:
        print("\nOhne erkannten seriellen Port kann dieses Skript nicht weitermachen.")
        return

    any_success = False
    for p in ports:
        for baud in BAUD_RATES_TO_TRY:
            if probe_port(p.device, baud):
                any_success = True

    print("\n=== Zusammenfassung ===")
    if any_success:
        print("Mindestens eine Antwort wurde empfangen — siehe Rohdaten oben.")
        print("Nächster Schritt: anhand der Hex-Werte versuchen zu verstehen, welches")
        print("Protokoll das Gerät spricht (z. B. Rücksprache mit Sonel-Support, oder")
        print("Vergleich mit bekannten LoRa-Modul-Protokollen).")
    else:
        print("Keine Antwort auf irgendeinen der Testbefehle. Das bestätigt den Verdacht")
        print("aus HANDOFF.md: das Sonel LORA-S1 spricht vermutlich ein proprietäres")
        print("Pairing-Protokoll mit Sonels eigenen Geräten, nicht generische AT-Befehle.")
        print("Empfehlung: ein dediziertes LoRaWAN-USB-Modul besorgen.")


if __name__ == "__main__":
    main()
