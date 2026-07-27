"""
Aufwärmlauf — einmal pro Systemstart.

Problem, das dieses Skript löst:
    Der allererste Pipeline-Start nach einem Neustart des Geräts dauert lange
    (Hailo-Firmware laden, Modell auf den Beschleuniger schieben, GStreamer-
    Registry aufbauen, Kamera initialisieren). Beobachtet wurden bis zu zwei
    Minuten. Jeder weitere Start danach geht schnell.

    In der App fällt das genau an der unpassendsten Stelle auf: "Frame laden"
    in Tab 2 scheint zu hängen, und wer den ersten Zähllauf startet, weiss
    nicht, ob etwas kaputt ist oder ob es nur dauert.

Lösung:
    Direkt nach dem Start der App einmal die Pipeline mit USB-Eingang
    hochfahren, warten bis Bilder fliessen (das Vorschaufenster steht dann),
    eine Sekunde stehen lassen und wieder sauber beenden. Danach sind alle
    Caches warm und jeder folgende Start ist schnell.

    Das passiert genau EINMAL pro Systemstart. Erkannt wird das an der
    Boot-ID des Kernels (/proc/sys/kernel/random/boot_id), die sich bei jedem
    Neustart ändert. Sie wird in einer Markerdatei abgelegt; stimmt sie
    überein, war der Aufwärmlauf in dieser Sitzung schon.

Beenden:
    Über SIGINT — dasselbe Signal wie Ctrl+C und wie die Schaltfläche
    "Stoppen" in Tab 3. Das ist laut Projektstand der einzige Weg, auf dem
    core.py zuverlässig sauber herunterfährt. Reagiert der Prozess nicht,
    wird stufenweise mit SIGTERM und SIGKILL nachgefasst.

Datenschutz:
    Der Aufwärmlauf zeichnet nichts auf. RECORDING_ENABLED wird für den
    Unterprozess ausdrücklich auf "false" gesetzt, unabhängig davon, was in
    der Umgebung steht — ein Aufwärmlauf soll unter keinen Umständen Bilder
    speichern. Siehe docs/entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md

Verwendung:
    python warmup.py                # nur, wenn seit dem Systemstart noch nicht
    python warmup.py --force        # in jedem Fall
    python warmup.py --input rpi    # anderer Eingang
    python warmup.py --status       # nur prüfen, nichts starten
"""

import argparse
import os
import signal
import subprocess
import sys
import threading
import time

# Markerdatei mit der Boot-ID des letzten Aufwärmlaufs. Liegt neben dem Code,
# damit sie unabhängig vom Aufrufort gefunden wird.
MARKER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           ".warmup_state")

BOOT_ID_PATH = "/proc/sys/kernel/random/boot_id"

# Zeile in der Ausgabe von core.py, an der zu erkennen ist, dass Bilder
# fliessen — dann steht auch das Vorschaufenster.
READY_MARKER = "Frame count:"

# Der erste Start nach einem Neustart darf lange dauern; danach greift der
# Abbruch. Lieber grosszügig, als den Aufwärmlauf abzuwürgen.
DEFAULT_TIMEOUT_SECONDS = 240

# Wie lange das Fenster stehen bleibt, nachdem die ersten Bilder da sind.
SETTLE_SECONDS = 1.0


def current_boot_id():
    """Boot-ID des laufenden Systems. None, wenn nicht ermittelbar."""
    try:
        with open(BOOT_ID_PATH) as f:
            return f.read().strip()
    except OSError:
        return None


def last_warmup_boot_id():
    """Boot-ID, bei der zuletzt aufgewärmt wurde. None, wenn nie."""
    try:
        with open(MARKER_FILE) as f:
            return f.read().strip()
    except OSError:
        return None


def mark_warmed_up():
    """Merkt den aktuellen Systemstart als aufgewärmt vor."""
    boot_id = current_boot_id()
    if not boot_id:
        return
    try:
        with open(MARKER_FILE, "w") as f:
            f.write(boot_id)
    except OSError as exc:
        print(f"Hinweis: Markerdatei nicht schreibbar ({exc}) — der "
              f"Aufwärmlauf läuft beim nächsten Start erneut.")


def needs_warmup():
    """
    True, wenn seit dem letzten Systemstart noch nicht aufgewärmt wurde.

    Lässt sich die Boot-ID nicht lesen (anderes Betriebssystem, gesperrtes
    /proc), wird bewusst False zurückgegeben: dann lieber gar nicht automatisch
    starten, als bei jedem App-Start eine Pipeline hochzufahren.
    """
    boot_id = current_boot_id()
    if not boot_id:
        return False
    return last_warmup_boot_id() != boot_id


def run_warmup(input_value="usb", timeout=DEFAULT_TIMEOUT_SECONDS,
               on_message=None, script_dir=None):
    """
    Führt den Aufwärmlauf durch.

    on_message: optionale Rückrufe für Fortschrittsmeldungen (str). Damit kann
                die App den Stand anzeigen, ohne dass dieses Modul etwas über
                die Oberfläche wissen muss.

    Rückgabe: True, wenn Bilder gesehen wurden.
    """
    def say(text):
        print(text, flush=True)
        if on_message:
            try:
                on_message(text)
            except Exception:
                pass

    script_dir = script_dir or os.path.dirname(os.path.abspath(__file__))
    core_path = os.path.join(script_dir, "core.py")
    if not os.path.exists(core_path):
        say(f"Aufwärmlauf nicht möglich: {core_path} nicht gefunden.")
        return False

    env = os.environ.copy()
    # Aufwärmen heisst aufwärmen — nichts aufzeichnen, nichts senden,
    # nichts sammeln.
    env["RECORDING_ENABLED"] = "false"
    env.pop("AUTO_CONFIG_COLLECTION_ENABLED", None)
    env.pop("RUN_DURATION_SECONDS", None)

    cmd = [sys.executable, "-u", core_path, "--input", input_value, "--use-frame"]

    say("Aufwärmlauf gestartet — der erste Pipeline-Start nach einem Neustart "
        "kann bis zu zwei Minuten dauern.")

    try:
        process = subprocess.Popen(
            cmd, cwd=script_dir, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
    except Exception as exc:
        say(f"Aufwärmlauf konnte nicht gestartet werden: {exc}")
        return False

    saw_frames = threading.Event()

    def read_output():
        """Liest die Ausgabe mit und meldet, sobald Bilder fliessen."""
        try:
            for line in process.stdout:
                if READY_MARKER in line and not saw_frames.is_set():
                    saw_frames.set()
        except Exception:
            pass

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()

    # Warten, bis Bilder ankommen — oder bis die Geduld am Ende ist.
    deadline = time.time() + timeout
    while time.time() < deadline:
        if saw_frames.is_set():
            break
        if process.poll() is not None:
            say("Aufwärmlauf: die Pipeline hat sich vorzeitig beendet.")
            break
        time.sleep(0.2)

    if saw_frames.is_set():
        say("Aufwärmlauf: Vorschau steht, Pipeline wird wieder beendet.")
        # Kurz stehen lassen, damit das Fenster wirklich gezeichnet ist.
        time.sleep(SETTLE_SECONDS)
    elif process.poll() is None:
        say(f"Aufwärmlauf: nach {timeout} s kamen keine Bilder — wird beendet.")

    _stop_process(process, say)

    if saw_frames.is_set():
        mark_warmed_up()
        say("Aufwärmlauf abgeschlossen. Die folgenden Starts gehen schnell.")
        return True

    say("Aufwärmlauf ohne Erfolg — beim nächsten App-Start wird es erneut "
        "versucht.")
    return False


def _stop_process(process, say):
    """
    Beendet core.py stufenweise: SIGINT, dann SIGTERM, dann SIGKILL.

    SIGINT ist der einzige Weg, auf dem core.py zuverlässig sauber
    herunterfährt (dieselbe Stelle wie 'Stoppen' in Tab 3). Die Eskalation
    fängt den Fall ab, dass der Prozess in nativem Hailo-/GStreamer-Code
    festhängt und das Signal nicht verarbeitet.
    """
    if process.poll() is not None:
        return

    try:
        process.send_signal(signal.SIGINT)
    except Exception:
        pass

    for signal_name, action, wait in (
            ("SIGINT", None, 8),
            ("SIGTERM", process.terminate, 4),
            ("SIGKILL", process.kill, 3)):
        if action is not None:
            say(f"Aufwärmlauf: Prozess reagiert nicht — sende {signal_name}.")
            try:
                action()
            except Exception:
                pass
        try:
            process.wait(timeout=wait)
            return
        except subprocess.TimeoutExpired:
            continue


def main():
    parser = argparse.ArgumentParser(
        description="Wärmt die Pipeline einmal pro Systemstart auf.")
    parser.add_argument("--input", default="usb",
                        help="Eingang für den Aufwärmlauf (Standard: usb)")
    parser.add_argument("--force", action="store_true",
                        help="auch dann laufen, wenn schon aufgewärmt wurde")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS,
                        help=f"Abbruch nach n Sekunden (Standard: {DEFAULT_TIMEOUT_SECONDS})")
    parser.add_argument("--status", action="store_true",
                        help="nur anzeigen, ob ein Aufwärmlauf nötig wäre")
    args = parser.parse_args()

    if args.status:
        boot_id = current_boot_id()
        print(f"Boot-ID aktuell : {boot_id or 'nicht ermittelbar'}")
        print(f"Boot-ID Marker  : {last_warmup_boot_id() or 'keine'}")
        print(f"Aufwärmen nötig : {'ja' if needs_warmup() else 'nein'}")
        return 0

    if not args.force and not needs_warmup():
        print("Seit dem letzten Systemstart bereits aufgewärmt — nichts zu tun. "
              "(Mit --force trotzdem ausführen.)")
        return 0

    ok = run_warmup(input_value=args.input, timeout=args.timeout)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
