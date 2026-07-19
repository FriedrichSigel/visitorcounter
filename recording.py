"""
Mitschnitt-Zweig für Benchmark-/Laborläufe.

Zweck: Während eines normalen Zähllaufs parallel ein Video mitschreiben, um die
gezählten Ereignisse hinterher gegen das Bildmaterial prüfen zu können
(Ground Truth für die Genauigkeitsuntersuchung).

Warum kein zweiter ffmpeg-Prozess:
    Die Kamera kann nur von EINEM Prozess geöffnet werden. Ein paralleles
    ffmpeg auf dieselbe Quelle scheitert entweder oder entzieht der Pipeline
    Frames. Der Mitschnitt hängt deshalb IN der GStreamer-Pipeline und sieht
    exakt denselben Frame-Strom, den auch der Zähler auswertet — das ist für
    einen Benchmark auch die methodisch saubere Variante.

Einhängepunkt:
    core.py trennt die Verbindung vor dem Element "hailo_display" auf und setzt
    einen tee dazwischen (_attach_recording_tee). Zweig 1 geht weiter wie
    bisher, Zweig 2 in diesen Aufnahme-Bin.

    Der erste Versuch, den Bin einfach als video-sink von fpsdisplaysink zu
    setzen, hat NICHT funktioniert: die Dateien wurden zwar angelegt, es kamen
    aber nie Puffer an — fpsdisplaysink erwartet dort ein echtes Sink-Element
    und behandelt einen Bin nicht zuverlässig als solches. Der tee ist der
    übliche und belastbare Weg.

Aufbau des Bins:
    queue (leaky) -> videorate -> videoconvert -> clockoverlay
                  -> videoconvert -> x264enc -> h264parse -> splitmuxsink

    - queue leaky=downstream: Kann der Encoder die Framerate nicht halten,
      werden Frames im Mitschnitt VERWORFEN statt die Pipeline auszubremsen.
      Der Zähllauf hat immer Vorrang — ein Benchmark, der das Messobjekt
      verlangsamt, misst sich selbst.
    - videorate: reduziert auf RECORDING_FPS. Der Pi 5 hat KEINEN
      Hardware-H.264-Encoder mehr, das Encoding läuft in Software auf der CPU
      neben der Hailo-Inferenz. Weniger Bilder = spürbar weniger Last.
    - clockoverlay: brennt die lokale Uhrzeit ins Bild. Ohne die ist das
      Abgleichen mit zaehlung.csv Handarbeit, mit ihr trivial.
    - splitmuxsink: schneidet in Segmente. Stürzt etwas ab, ist nur das
      laufende Segment beschädigt statt der gesamten Aufnahme; fertige
      Segmente können außerdem schon hochgeladen werden, während weiter
      aufgezeichnet wird.
"""

import datetime
import os
import shutil

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst


# Unter dieser Grenze wird die Aufnahme gar nicht erst gestartet — eine
# volllaufende Platte mitten im Testlauf kostet mehr als ein abgesagter Lauf.
MIN_FREE_GB = 2.0


def find_usb_mount():
    """
    Sucht einen eingehängten Wechseldatenträger.

    Raspberry Pi OS hängt USB-Speicher automatisch unter /media/<benutzer>/<label>
    ein. Gibt den ersten beschreibbaren Fund zurück, sonst None.
    """
    base_dirs = ["/media", "/mnt"]
    for base in base_dirs:
        if not os.path.isdir(base):
            continue
        for entry in sorted(os.listdir(base)):
            user_dir = os.path.join(base, entry)
            if not os.path.isdir(user_dir):
                continue
            # /media/<benutzer>/<label>
            try:
                sub_entries = sorted(os.listdir(user_dir))
            except PermissionError:
                continue
            for sub in sub_entries:
                candidate = os.path.join(user_dir, sub)
                if os.path.isdir(candidate) and os.access(candidate, os.W_OK):
                    return candidate
            # oder direkt /mnt/<label>
            if os.access(user_dir, os.W_OK) and os.path.ismount(user_dir):
                return user_dir
    return None


def free_gb(path):
    """Freier Speicher am angegebenen Pfad in GB."""
    try:
        usage = shutil.disk_usage(path)
        return usage.free / (1024 ** 3)
    except OSError:
        return 0.0


def resolve_target_dir(configured_dir):
    """
    Bestimmt das Zielverzeichnis für den Mitschnitt.

    configured_dir kann sein:
      - ein konkreter Pfad -> wird verwendet (und angelegt)
      - "auto" oder leer   -> USB-Datenträger suchen; nur wenn keiner
                              gefunden wird, auf ./aufnahmen zurückfallen

    Rückgabe: (pfad, hinweistext) oder (None, fehlertext)
    """
    if configured_dir and configured_dir.lower() != "auto":
        target = configured_dir
        note = f"Aufnahmeziel (konfiguriert): {target}"
    else:
        usb = find_usb_mount()
        if usb:
            target = os.path.join(usb, "visitorcounter_aufnahmen")
            note = f"Aufnahmeziel (USB erkannt): {target}"
        else:
            target = os.path.abspath("aufnahmen")
            note = ("WARNUNG: Kein USB-Datenträger gefunden — es wird auf die "
                    f"SD-Karte geschrieben: {target}")

    try:
        os.makedirs(target, exist_ok=True)
    except OSError as exc:
        return None, f"FEHLER: Aufnahmeordner {target} nicht anlegbar ({exc})."

    if not os.access(target, os.W_OK):
        return None, f"FEHLER: Kein Schreibrecht auf {target}."

    available = free_gb(target)
    if available < MIN_FREE_GB:
        return None, (f"FEHLER: Nur {available:.1f} GB frei auf {target} — "
                      f"Aufnahme wird nicht gestartet (Minimum {MIN_FREE_GB} GB).")

    note += f" — {available:.1f} GB frei"
    return target, note


def estimate_hours(target_dir, bitrate_kbps):
    """Grobe Reichweite der Aufnahme in Stunden, für die Startmeldung."""
    gb_per_hour = bitrate_kbps * 3600 / 8 / 1_000_000
    if gb_per_hour <= 0:
        return None
    # 2 GB Reserve nicht mit einrechnen.
    usable = max(free_gb(target_dir) - MIN_FREE_GB, 0)
    return usable / gb_per_hour


def build_recording_bin(target_dir, bitrate_kbps=2000, segment_seconds=600,
                        fps=15, name_prefix="lauf"):
    """
    Baut den Aufnahme-Bin und gibt ihn zurück (oder None bei Fehler).

    Der Bin hat einen Ghost-Pad auf dem Eingang der queue und kann damit
    überall dort eingesetzt werden, wo ein Sink erwartet wird — in core.py
    als video-sink von "hailo_display".
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    location = os.path.join(target_dir, f"{name_prefix}_{timestamp}_%03d.mp4")

    bin_ = Gst.Bin.new("recording_bin")

    elements = {}
    spec = [
        ("queue", "rec_queue"),
        ("videorate", "rec_videorate"),
        ("videoconvert", "rec_convert_in"),
        ("clockoverlay", "rec_clock"),
        ("videoconvert", "rec_convert_out"),
        ("x264enc", "rec_encoder"),
        ("h264parse", "rec_parse"),
        ("splitmuxsink", "rec_sink"),
    ]
    for factory, element_name in spec:
        element = Gst.ElementFactory.make(factory, element_name)
        if element is None:
            print(f"FEHLER: GStreamer-Element '{factory}' nicht verfügbar — "
                  f"Aufnahme deaktiviert. Fehlendes Paket? "
                  f"(x264enc steckt in gstreamer1.0-plugins-ugly, "
                  f"clockoverlay/splitmuxsink in gstreamer1.0-plugins-good)")
            return None
        elements[element_name] = element
        bin_.add(element)

    # Queue: Rückstau darf die Zählpipeline NICHT bremsen — lieber Frames im
    # Mitschnitt verlieren.
    q = elements["rec_queue"]
    q.set_property("max-size-buffers", 60)
    q.set_property("max-size-time", 0)
    q.set_property("max-size-bytes", 0)
    q.set_property("leaky", 2)          # 2 = downstream (älteste verwerfen)

    # Framerate begrenzen (CPU-Entlastung, siehe Modulkommentar).
    elements["rec_videorate"].set_property("drop-only", True)

    # Uhrzeit ins Bild brennen — Ortszeit, damit sie direkt zu den Zeitstempeln
    # in zaehlung.csv passt.
    clock = elements["rec_clock"]
    clock.set_property("time-format", "%Y-%m-%d %H:%M:%S")
    clock.set_property("halignment", 0)     # 0 = left
    clock.set_property("valignment", 2)     # 2 = top
    clock.set_property("shaded-background", True)
    clock.set_property("font-desc", "Monospace 14")

    # Software-Encoder: schnellstes Preset, damit möglichst wenig CPU neben der
    # Hailo-Inferenz verbraucht wird.
    enc = elements["rec_encoder"]
    enc.set_property("bitrate", bitrate_kbps)
    enc.set_property("speed-preset", 1)     # 1 = ultrafast
    enc.set_property("tune", 4)             # 4 = zerolatency
    enc.set_property("key-int-max", fps * 2)

    sink = elements["rec_sink"]
    sink.set_property("location", location)
    sink.set_property("max-size-time", segment_seconds * Gst.SECOND)
    sink.set_property("async-finalize", True)
    sink.set_property("send-keyframe-requests", True)

    # Verkettung: die Framerate-Begrenzung braucht ein Caps-Filter, sonst
    # bleibt videorate wirkungslos.
    caps = Gst.Caps.from_string(f"video/x-raw,framerate={fps}/1")
    if not elements["rec_queue"].link(elements["rec_videorate"]):
        print("FEHLER: Aufnahme-Bin — queue -> videorate fehlgeschlagen.")
        return None
    if not elements["rec_videorate"].link(elements["rec_convert_in"]):
        print("FEHLER: Aufnahme-Bin — videorate -> videoconvert fehlgeschlagen.")
        return None
    if not elements["rec_convert_in"].link_filtered(elements["rec_clock"], caps):
        print("FEHLER: Aufnahme-Bin — Caps-Filter (Framerate) fehlgeschlagen.")
        return None
    chain = ["rec_clock", "rec_convert_out", "rec_encoder", "rec_parse", "rec_sink"]
    for first, second in zip(chain, chain[1:]):
        if not elements[first].link(elements[second]):
            print(f"FEHLER: Aufnahme-Bin — {first} -> {second} fehlgeschlagen.")
            return None

    # Ghost-Pad: macht den Eingang der queue zum Eingang des gesamten Bins.
    sink_pad = elements["rec_queue"].get_static_pad("sink")
    ghost = Gst.GhostPad.new("sink", sink_pad)
    ghost.set_active(True)
    bin_.add_pad(ghost)

    print(f"Mitschnitt aktiv: {location}")
    print(f"  {fps} fps, {bitrate_kbps} kbit/s, Segmente à {segment_seconds} s")
    return bin_
