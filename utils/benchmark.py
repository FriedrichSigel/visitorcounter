"""
benchmark.py — Leistungskennzahlen für Benchmark-/Laborläufe.

NUR AKTIV, WENN RECORDING_ENABLED = True (siehe config.py) — dieselbe
Voraussetzung wie der Video-Mitschnitt (recording.py), aus demselben Grund:
beides ist ausschliesslich für Laborbedingungen gedacht (Genauigkeits-/
Leistungsmessung), nicht für den Normalbetrieb. Wird core.py deshalb auch
nur dann angelegt, wenn der Mitschnitt tatsächlich erfolgreich in die
Pipeline eingehängt wurde (siehe core.py, __main__-Block).

Erfasst:
  - Pro-Frame-Verarbeitungszeit im Callback (core.app_callback): min/max/
    Durchschnitt, daraus die effektive Bildrate über den ganzen Lauf.
  - Leere Puffer im Callback (buffer is None) und ungewöhnlich lange
    Frame-Abstände ("mögliche Aussetzer") als grober Hinweis auf Stau —
    KEIN vollständiger GStreamer-Drop-Zähler, siehe Docstring von
    FrameTimingTracker für die genaue Einschränkung.
  - CPU-Auslastung des Raspberry Pi (aus /proc/stat, ohne Zusatzpaket).
  - SoC-Temperatur und (falls verfügbar) Leistungsaufnahme über das
    Raspberry-Pi-eigene Diagnosewerkzeug `vcgencmd`.
  - Hailo-Beschleuniger-Auslastung: EXPERIMENTELL, best-effort über
    HailoRT's HAILO_MONITOR-Umgebungsvariable. Dieser Teil wurde NICHT an
    echter Hardware verifiziert (siehe read_hailo_utilization()) — liefert
    im Zweifel "nicht verfügbar" statt eines geratenen Werts.

Alle Sammelstellen sind bewusst so gebaut, dass ein fehlendes Werkzeug
(kein Linux, kein vcgencmd, kein HailoRT-Monitor) nie einen Absturz auslöst,
sondern nur zu "nicht verfügbar" im Bericht führt — ein Benchmark-Lauf darf
durch fehlende Diagnosewerkzeuge nicht selbst gefährdet werden.
"""

import glob
import json
import os
import subprocess
import threading
import time
from datetime import datetime

# Wie oft die Ressourcennutzung (CPU/Temperatur/Leistung) abgetastet wird.
SAMPLE_INTERVAL_SECONDS = 1.0

# Ab diesem Vielfachen der bisherigen durchschnittlichen Verarbeitungszeit
# gilt ein Frame als "möglicher Aussetzer" — eine Heuristik dieses Programms,
# KEIN von GStreamer gemeldeter echter Frame-Drop (siehe Modul-Docstring).
STOTTER_FACTOR = 3.0
STOTTER_MIN_SAMPLES = 10   # erst danach greift die Erkennung (Anlaufphase ausblenden)


class FrameTimingTracker:
    """
    Misst die Zeit zwischen zwei Aufrufen von app_callback() — das ist die
    effektive Pro-Frame-Zeit der GESAMTEN Pipeline (Hailo-Inferenz +
    GStreamer-Overhead + eigener Callback), nicht nur des eigenen Codes.

    Einschränkung "Aussetzer"/"leere Puffer": Diese Klasse sieht nur Frames,
    die tatsächlich bis zum eigenen Callback durchkommen. Ein von GStreamer
    VOR dem Callback verworfener Frame (z. B. durch eine leaky-Queue weiter
    vorn in der Pipeline) taucht hier gar nicht erst auf und wird deshalb
    NICHT gezählt. "leere_puffer" und "moegliche_aussetzer" sind also
    Näherungswerte aus Sicht des Callbacks, kein vollständiger
    GStreamer-Drop-Zähler.
    """

    def __init__(self):
        self._last_mark = None
        self._start_time = None
        self.total_frames = 0
        self.delta_count = 0
        self.min_ms = None
        self.max_ms = None
        self._sum_ms = 0.0
        self.empty_buffer_count = 0
        self.stotter_count = 0

    def mark_empty_buffer(self):
        """Aufrufen, wenn im Callback `buffer is None` war."""
        self.empty_buffer_count += 1

    def mark_frame(self):
        """Einmal pro echtem (nicht-leerem) Frame aufrufen, möglichst am
        Anfang von app_callback(), bevor die eigentliche Verarbeitung
        beginnt."""
        now = time.monotonic()
        self.total_frames += 1
        if self._start_time is None:
            self._start_time = now
        if self._last_mark is not None:
            delta_ms = (now - self._last_mark) * 1000.0
            self.delta_count += 1
            self._sum_ms += delta_ms
            if self.min_ms is None or delta_ms < self.min_ms:
                self.min_ms = delta_ms
            if self.max_ms is None or delta_ms > self.max_ms:
                self.max_ms = delta_ms
            if self.delta_count > STOTTER_MIN_SAMPLES:
                avg_so_far = self._sum_ms / self.delta_count
                if delta_ms > avg_so_far * STOTTER_FACTOR:
                    self.stotter_count += 1
        self._last_mark = now

    @property
    def avg_ms(self):
        return self._sum_ms / self.delta_count if self.delta_count else None

    @property
    def fps(self):
        """Durchschnittliche Bildrate über den GESAMTEN Lauf (Framezahl /
        verstrichene Zeit) — robuster gegen einzelne Ausreißer als 1/avg_ms."""
        if self._start_time is None or self._last_mark is None or self.total_frames < 2:
            return None
        elapsed = self._last_mark - self._start_time
        return (self.total_frames - 1) / elapsed if elapsed > 0 else None

    def as_dict(self):
        return {
            "frames_gemessen": self.total_frames,
            "verarbeitungszeit_ms": {
                "min": round(self.min_ms, 2) if self.min_ms is not None else None,
                "max": round(self.max_ms, 2) if self.max_ms is not None else None,
                "durchschnitt": round(self.avg_ms, 2) if self.avg_ms is not None else None,
            },
            "effektive_bildrate_fps": round(self.fps, 2) if self.fps is not None else None,
            "leere_puffer": self.empty_buffer_count,
            "moegliche_aussetzer": self.stotter_count,
            "hinweis": (
                f"'moegliche_aussetzer' zaehlt Frames, deren Verarbeitung mehr als das "
                f"{STOTTER_FACTOR:.0f}-fache des bisherigen Durchschnitts brauchte — eine "
                f"Heuristik dieses Programms, KEIN von GStreamer gemeldeter echter "
                f"Frame-Drop. Vor dem Callback verworfene Frames sieht diese Messung "
                f"grundsaetzlich nicht (siehe Klassen-Docstring in benchmark.py)."
            ),
        }


def _read_proc_stat_cpu_times():
    """Liest die aggregierten CPU-Jiffies aus /proc/stat (erste Zeile "cpu ").
    Rückgabe: (idle_jiffies, total_jiffies) oder None, wenn nicht lesbar
    (z. B. kein Linux — dann ist CPU-Messung nicht verfügbar, kein Fehler)."""
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        parts = line.split()
        if not parts or parts[0] != "cpu":
            return None
        values = [int(x) for x in parts[1:]]
        idle = values[3] + (values[4] if len(values) > 4 else 0)  # idle + iowait
        total = sum(values)
        return idle, total
    except (OSError, ValueError, IndexError):
        return None


def _run_vcgencmd(*args):
    """
    Führt das Raspberry-Pi-eigene Diagnosewerkzeug `vcgencmd` aus.

    Gibt die Ausgabe als String zurück, oder None, wenn das Kommando fehlt,
    fehlschlägt oder zu lange braucht — insbesondere auf einer
    Entwicklungsmaschine ohne Raspberry Pi ist das der Normalfall, kein
    Fehler, der den Lauf stören darf.
    """
    try:
        result = subprocess.run(
            ["vcgencmd", *args], capture_output=True, text=True, timeout=2)
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _read_soc_temp():
    """SoC-Temperatur in °C über `vcgencmd measure_temp`
    (Ausgabeformat: "temp=48.8'C"). None, wenn vcgencmd fehlt/anders antwortet."""
    output = _run_vcgencmd("measure_temp")
    if not output or "temp=" not in output:
        return None
    try:
        return float(output.split("temp=")[1].split("'")[0])
    except (IndexError, ValueError):
        return None


def _parse_pmic_value(line):
    """Extrahiert den Zahlenwert aus einer vcgencmd-pmic_read_adc-Zeile wie
    'EXT5V_V volt(23)=5.10V' oder 'EXT5V_A curr(23)=0.80A'."""
    try:
        return float(line.split("=")[1].rstrip("VA\n"))
    except (IndexError, ValueError):
        return None


def _read_power_watts():
    """
    Schätzt die Leistungsaufnahme des Gesamtsystems (Pi + ggf. daran
    hängender Hailo-AI-HAT) über die 5V-Eingangsschiene, ausgelesen per
    `vcgencmd pmic_read_adc` (Kanäle EXT5V_V/EXT5V_A auf dem Raspberry Pi 5).

    NICHT AN ECHTER HARDWARE VERIFIZIERT: Kanalnamen/-verfügbarkeit können
    je nach Firmware-Version abweichen. Liefert bei unbekanntem Format
    bewusst None statt eines geschätzten Werts.
    """
    output = _run_vcgencmd("pmic_read_adc")
    if not output:
        return None
    volt = amp = None
    for line in output.splitlines():
        if line.startswith("EXT5V_V"):
            volt = _parse_pmic_value(line)
        elif line.startswith("EXT5V_A"):
            amp = _parse_pmic_value(line)
    if volt is None or amp is None:
        return None
    return volt * amp


class ResourceSampler(threading.Thread):
    """
    Tastet im Hintergrund CPU-Auslastung, SoC-Temperatur und (falls
    verfügbar) Leistungsaufnahme ab, während die Pipeline läuft.

    Eigener Daemon-Thread statt Aufruf im Callback: `vcgencmd` ist ein
    externer Prozessaufruf (Millisekunden) — im Callback selbst würde das
    gegen die "nicht-blockierend"-Vorgabe der Hailo-Pipeline verstoßen
    (siehe docs/entwicklung/cleancode.md-Analogon für den Hailo-Guide-Abgleich
    in IMPLEMENTIERUNG_IST.md, Abschnitt 3).
    """

    def __init__(self, interval=SAMPLE_INTERVAL_SECONDS):
        super().__init__(daemon=True)
        self.interval = interval
        self._stop_event = threading.Event()
        self.cpu_samples = []
        self.temp_samples = []
        self.power_samples = []
        self._prev_cpu_times = _read_proc_stat_cpu_times()

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():
            self._sample_once()
            self._stop_event.wait(self.interval)

    def _sample_once(self):
        cpu = self._cpu_percent_since_last()
        if cpu is not None:
            self.cpu_samples.append(cpu)
        temp = _read_soc_temp()
        if temp is not None:
            self.temp_samples.append(temp)
        power = _read_power_watts()
        if power is not None:
            self.power_samples.append(power)

    def _cpu_percent_since_last(self):
        """CPU-Auslastung in Prozent seit dem letzten Sample, aus der
        Differenz der /proc/stat-Jiffies — Standard-Linux-Methode, keine
        zusätzliche Abhängigkeit (kein psutil nötig)."""
        current = _read_proc_stat_cpu_times()
        previous = self._prev_cpu_times
        self._prev_cpu_times = current
        if current is None or previous is None:
            return None
        idle_prev, total_prev = previous
        idle_cur, total_cur = current
        total_delta = total_cur - total_prev
        idle_delta = idle_cur - idle_prev
        if total_delta <= 0:
            return None
        return max(0.0, min(100.0, 100.0 * (total_delta - idle_delta) / total_delta))

    @staticmethod
    def _stats(samples):
        if not samples:
            return None
        return {
            "min": round(min(samples), 2),
            "max": round(max(samples), 2),
            "durchschnitt": round(sum(samples) / len(samples), 2),
            "anzahl_messwerte": len(samples),
        }

    def as_dict(self):
        return {
            "cpu_auslastung_prozent": (
                self._stats(self.cpu_samples)
                or "nicht verfuegbar (nur unter Linux ueber /proc/stat messbar)"),
            "soc_temperatur_celsius": (
                self._stats(self.temp_samples)
                or "nicht verfuegbar (vcgencmd fehlt oder kein Raspberry Pi)"),
            "leistungsaufnahme_watt": (
                self._stats(self.power_samples)
                or "nicht verfuegbar (vcgencmd pmic_read_adc fehlt oder liefert "
                   "keine EXT5V_V/EXT5V_A-Werte)"),
        }


# --- Hailo-Beschleuniger-Auslastung: experimentell -------------------------
#
# HailoRT kann bei gesetzter Umgebungsvariable HAILO_MONITOR periodisch
# Laufzeit-Kennzahlen in eine JSON-Datei unter /tmp schreiben. Dieser
# Mechanismus wurde in diesem Projekt NICHT an echter Hardware verifiziert
# (siehe docs/entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md) — deshalb
# wird hier nur best-effort versucht, ein Ergebnis einzusammeln. Jeder
# Fehlschlag/jede Abweichung führt zu "verfuegbar": False statt zu einer
# geschätzten oder falsch interpretierten Zahl.
HAILO_MONITOR_ENV_VAR = "HAILO_MONITOR"
_HAILO_MONITOR_GLOB = "/tmp/hailo_monitor_of_*.json"


def enable_hailo_monitor_env():
    """Muss VOR dem Start der Hailo-Pipeline aufgerufen werden — die
    Umgebungsvariable wirkt nur beim Prozessstart von HailoRT. Setzt sie nur,
    falls sie nicht schon vom Aufrufer/der Umgebung vorgegeben ist."""
    os.environ.setdefault(HAILO_MONITOR_ENV_VAR, "1")


def read_hailo_utilization():
    """
    Best-effort-Auswertung einer HailoRT-Monitor-Datei.

    Rückgabe: dict mit "verfuegbar": True + Rohdaten (Schema nicht
    dokumentiert-stabil, daher unausgewertet durchgereicht) ODER
    "verfuegbar": False + Begründung. NIE ein geratener Auslastungswert.
    """
    kandidaten = sorted(glob.glob(_HAILO_MONITOR_GLOB), key=os.path.getmtime, reverse=True)
    if not kandidaten:
        return {"verfuegbar": False,
                "grund": "keine HailoRT-Monitor-Datei gefunden unter "
                         f"{_HAILO_MONITOR_GLOB} (HAILO_MONITOR=1 gesetzt? "
                         "unterstuetzt die installierte HailoRT-Version das Feature?)"}
    pfad = kandidaten[0]
    try:
        with open(pfad) as f:
            rohdaten = json.load(f)
    except (OSError, ValueError) as exc:
        return {"verfuegbar": False,
                "grund": f"Monitor-Datei {pfad} nicht lesbar ({exc})",
                "rohdatei": pfad}

    return {"verfuegbar": True, "rohdatei": pfad, "rohdaten": rohdaten}


class BenchmarkSession:
    """
    Bündelt Frame-Timing + Ressourcen-Sampling + (experimentelle) Hailo-
    Auslastung für einen Lauf und schreibt am Ende einen Bericht.

    Wird von core.py nur angelegt, wenn der Mitschnitt tatsächlich
    erfolgreich in die Pipeline eingehängt wurde (siehe core.py,
    __main__-Block) — kein Benchmark ohne zugehöriges Video.
    """

    def __init__(self):
        self.timing = FrameTimingTracker()
        self.resources = ResourceSampler()
        self.started_at = None
        self.ended_at = None

    def start(self):
        enable_hailo_monitor_env()
        self.started_at = datetime.now()
        self.resources.start()

    def stop(self):
        self.resources.stop()
        self.resources.join(timeout=SAMPLE_INTERVAL_SECONDS + 1)
        self.ended_at = datetime.now()

    def build_report(self):
        dauer_s = ((self.ended_at - self.started_at).total_seconds()
                   if self.started_at and self.ended_at else None)
        return {
            "erzeugt_am": datetime.now().isoformat(timespec="seconds"),
            "lauf_start": self.started_at.isoformat(timespec="seconds") if self.started_at else None,
            "lauf_ende": self.ended_at.isoformat(timespec="seconds") if self.ended_at else None,
            "laufzeit_sekunden": round(dauer_s, 1) if dauer_s is not None else None,
            "frame_timing": self.timing.as_dict(),
            "system_ressourcen": self.resources.as_dict(),
            "hailo_beschleuniger": {
                **read_hailo_utilization(),
                "hinweis": ("Experimentell, nicht an echter Hardware verifiziert — "
                            "siehe docs/entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md."),
            },
        }

    def write_report(self, target_dir, name_prefix="lauf"):
        """Schreibt den Bericht als JSON + kurze .txt-Zusammenfassung ins
        Aufnahmeverzeichnis (dieselbe, in der auch das Video liegt).
        Rückgabe: Pfad der JSON-Datei, oder None bei Schreibfehler."""
        report = self.build_report()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = os.path.join(target_dir, f"{name_prefix}_{timestamp}_benchmark.json")
        txt_path = os.path.join(target_dir, f"{name_prefix}_{timestamp}_benchmark.txt")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(_format_report_text(report))
        except OSError as exc:
            print(f"WARNUNG: Benchmark-Bericht konnte nicht geschrieben werden: {exc}")
            return None
        return json_path


def _format_stat_line(label, stats_or_text, unit=""):
    if isinstance(stats_or_text, dict):
        return (f"  {label}: min {stats_or_text['min']}{unit}  "
                f"max {stats_or_text['max']}{unit}  "
                f"Ø {stats_or_text['durchschnitt']}{unit}  "
                f"({stats_or_text['anzahl_messwerte']} Messwerte)")
    return f"  {label}: {stats_or_text}"


def _format_report_text(report):
    zeitraum = f"{report['lauf_start']} – {report['lauf_ende']}"
    lines = [
        "Benchmark-Bericht",
        "=" * 60,
        f"Erzeugt am: {report['erzeugt_am']}",
        f"Lauf: {zeitraum} ({report['laufzeit_sekunden']} s)",
        "",
        "Frame-Verarbeitung",
        "-" * 60,
    ]
    ft = report["frame_timing"]
    lines.append(f"  Frames gemessen: {ft['frames_gemessen']}")
    vz = ft["verarbeitungszeit_ms"]
    lines.append(f"  Verarbeitungszeit je Frame: min {vz['min']} ms  "
                 f"max {vz['max']} ms  Ø {vz['durchschnitt']} ms")
    lines.append(f"  Effektive Bildrate: {ft['effektive_bildrate_fps']} fps")
    lines.append(f"  Leere Puffer: {ft['leere_puffer']}")
    lines.append(f"  Mögliche Aussetzer: {ft['moegliche_aussetzer']}")
    lines.append(f"  ({ft['hinweis']})")

    lines += ["", "System-Ressourcen (Raspberry Pi)", "-" * 60]
    sr = report["system_ressourcen"]
    lines.append(_format_stat_line("CPU-Auslastung", sr["cpu_auslastung_prozent"], " %"))
    lines.append(_format_stat_line("SoC-Temperatur", sr["soc_temperatur_celsius"], " °C"))
    lines.append(_format_stat_line("Leistungsaufnahme", sr["leistungsaufnahme_watt"], " W"))

    lines += ["", "Hailo-Beschleuniger (experimentell)", "-" * 60]
    hb = report["hailo_beschleuniger"]
    if hb.get("verfuegbar"):
        lines.append(f"  Rohdaten: {hb['rohdatei']} (siehe JSON-Bericht für den Inhalt)")
    else:
        lines.append(f"  Nicht verfügbar: {hb.get('grund', '?')}")
    lines.append(f"  ({hb['hinweis']})")

    return "\n".join(lines) + "\n"
