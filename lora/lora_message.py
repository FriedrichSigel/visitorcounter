"""
lora_message.py — Aufbau der LoRa-Nachricht (18-Byte-Zählformat v2) aus der
aktuellen Konfiguration und den Live-Zählerständen.

Bewusst abhängigkeitsfrei (nur Standardbibliothek), damit dasselbe Modul
sowohl von app.py (GUI) als auch vom eigenständigen Sender lora_send_loop.py
in einer schlanken Umgebung importiert werden kann.

Das Format ist identisch zu dem Test-Frame, den lora_send_loop.py bislang
statisch versendet hat (siehe dortige Dokumentation):

    18 Byte = Header(6) + 6 Klassen x (IN, OUT)

    Byte 0     Format-Version (0x02)
    Byte 1     Sensor-ID (0-255)
    Byte 2     Sequenznummer (0-255, läuft pro Uplink hoch)
    Byte 3     Status (0 = ok)
    Byte 4     reserviert (0)
    Byte 5     Klassen-Bitmaske — 1 Bit je Klasse, markiert die aktiven
    Byte 6-17  je Klasse 2 Byte: [IN][OUT], jeweils 0-255, feste Reihenfolge

Die "Struktur" der Nachricht richtet sich damit direkt nach roi_config.json:
welche Klassen aktiv sind, bestimmt die Bitmaske (Byte 5) und welche der
sechs IN/OUT-Slots echte Zählwerte tragen. Die Bytefolge bleibt fix 18 Byte,
damit sie in jede LoRaWAN-Spreizfaktor-Konfiguration passt.

WICHTIG: Die Header-Felder 3/4 (Status/Reserve) sind gemäß dem vorhandenen
Test-Frame belegt. Sobald die verbindliche Serialisierung aus
lora_transmitter.py vorliegt, hier gegenprüfen und ggf. angleichen — dieses
Modul ist die eine Stelle, an der das Format definiert ist.
"""

import csv
import os

# Kanonische Klassenreihenfolge. Muss zur Reihenfolge passen, in der die
# sechs IN/OUT-Slots im Frame liegen — NICHT alphabetisch, sondern die feste
# Projektreihenfolge (identisch zu config._DEFAULT_ROI_CONFIG["classes"] und
# zum Test-Frame in lora_send_loop.py: person, bicycle, car, motorcycle,
# bus, truck).
CANONICAL_CLASSES = ["person", "bicycle", "car", "motorcycle", "bus", "truck"]

# --- Nachrichtentyp (Byte 0) ---
# 0x02 = Linien-/ROI-/multi_roi-Format (IN/OUT je Klasse, 18 Byte fix).
# multi_roi wird über ein gewähltes "IN-Feld" auf dieses Format abgebildet
# (Übergang in das Feld = IN, aus dem Feld heraus = OUT).
MSG_LINE_ROI = 0x02

FORMAT_VERSION = MSG_LINE_ROI   # Byte 0 des Frames
HEADER_LEN = 6          # Byte 0-5
FRAME_LEN = HEADER_LEN + 2 * len(CANONICAL_CLASSES)   # = 18
FPORT = 2               # LoRaWAN Fport (wie in EINRICHTUNG_LA66.md)

# --- status-Bitfeld (Byte 4), gemäß LoRa_Nachrichtenformat_Spezifikation.md ---
STATUS_CAMERA_OK = 1 << 0   # Kamera liefert Bilder
STATUS_ACCEL_OK  = 1 << 1   # KI-Beschleuniger (Hailo) aktiv
STATUS_CONFIG_OK = 1 << 2   # Konfiguration geladen
STATUS_BUFFERED  = 1 << 3   # Werte seit letztem bestätigten Uplink gepuffert
STATUS_PARTIAL   = 1 << 4   # Intervall unvollständig (Start mitten im Intervall)
# Bit 5-7 reserviert
STATUS_OK = 0

# multi_roi: das Sentinel für "in keiner Fläche" (muss zu
# counting.MultiRoiCounter.OUTSIDE passen).
OUTSIDE_NAME = "außerhalb"


def _clamp_byte(value):
    """Begrenzt einen Zählwert auf ein Byte (0-255). Überlauf wird gekappt,
    nicht umgebrochen — ein bei 255 stehender Wert ist ein klar erkennbares
    'mind. 255', kein wieder bei 0 beginnender Zähler."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(255, value))


def class_bitmask(active_classes):
    """Bitmaske über die sechs kanonischen Klassen (Bit 0 = erste Klasse).
    Beispiel: alle sechs aktiv -> 0b00111111 = 0x3F."""
    active = set(active_classes)
    mask = 0
    for i, name in enumerate(CANONICAL_CLASSES):
        if name in active:
            mask |= (1 << i)
    return mask


def build_frame(active_classes, counts_in, counts_out,
                sensor_id=1, sequence=0, interval_min=0, status=STATUS_OK):
    """
    Baut den 18-Byte-Frame gemäß LoRa_Nachrichtenformat_Spezifikation.md.

    active_classes: iterierbar mit Klassennamen, die laut Konfiguration
                    aktiv sind (bestimmt die Bitmaske).
    counts_in/out:  dict {klassenname: anzahl}. Fehlende Klassen = 0.
                    Inaktive Klassen werden immer als 00 00 gesendet,
                    unabhängig von etwaigen Zählwerten.
    interval_min:   Länge des Aggregationsintervalls in Minuten (Byte 3).
    status:         Status-Bitfeld (Byte 4), siehe STATUS_*-Konstanten.
    Rückgabe: bytes der Länge FRAME_LEN.
    """
    active = set(active_classes)
    frame = bytearray()
    frame.append(FORMAT_VERSION & 0xFF)
    frame.append(_clamp_byte(sensor_id))
    frame.append(_clamp_byte(sequence))      # frame_counter
    frame.append(_clamp_byte(interval_min))  # Byte 3 = interval_min
    frame.append(_clamp_byte(status))        # Byte 4 = status-Bitfeld
    frame.append(class_bitmask(active_classes) & 0xFF)

    for name in CANONICAL_CLASSES:
        if name in active:
            frame.append(_clamp_byte(counts_in.get(name, 0)))
            frame.append(_clamp_byte(counts_out.get(name, 0)))
        else:
            frame.append(0)
            frame.append(0)

    assert len(frame) == FRAME_LEN, f"Frame-Länge {len(frame)} != {FRAME_LEN}"
    return bytes(frame)


def frame_to_hex(frame):
    """Frame als Großbuchstaben-Hex ohne Trennzeichen (Format für AT+SENDB)."""
    return frame.hex().upper()


def read_counts_from_zaehlung(path, active_classes):
    """
    Liest die aktuellen IN/OUT-Zählerstände aus zaehlung.csv.

    Gezählt werden nur echte Übergänge (is_transition == True) und nur die
    Richtungen 'in' / 'out' (Groß-/Kleinschreibung egal). Übergänge im
    Mehrere-Flächen-Modus ('Berlin->Potsdam' o. ä.) passen NICHT in dieses
    IN/OUT-Format und werden hier ignoriert — siehe describe_structure() für
    den entsprechenden Hinweis.

    Rückgabe: (counts_in, counts_out) als zwei dicts {klassenname: anzahl}.
    Fehlt die Datei, sind beide leer (alle Klassen 0).
    """
    active = set(active_classes)
    counts_in = {c: 0 for c in active}
    counts_out = {c: 0 for c in active}

    if not path or not os.path.isfile(path):
        return counts_in, counts_out

    try:
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                if str(row.get("is_transition")).strip() != "True":
                    continue
                label = (row.get("label") or "").strip()
                if label not in active:
                    continue
                direction = (row.get("direction") or "").strip().lower()
                if direction == "in":
                    counts_in[label] += 1
                elif direction == "out":
                    counts_out[label] += 1
    except (OSError, csv.Error):
        # Defensive: eine kaputte/halb geschriebene Zeile darf den Sender
        # nicht zum Absturz bringen — im Zweifel mit dem, was gelesen wurde.
        pass

    return counts_in, counts_out


def _active_in_canonical_order(active_classes):
    """Aktive Klassen in kanonischer Reihenfolge (für stabile Anzeige)."""
    active = set(active_classes)
    return [c for c in CANONICAL_CLASSES if c in active]


def describe_structure(config, interval_minutes=None, sensor_id=1,
                       counts_in=None, counts_out=None):
    """
    Baut den Hinweis-Text für die GUI: Struktur der Nachricht, abgeleitet aus
    der Konfiguration, mit Erklärung und (falls übergeben) dem Sende-Intervall.

    config: das geladene roi_config.json als dict (mind. 'mode', 'classes').
    interval_minutes: gewähltes Sende-Intervall in Minuten (oder None).
    sensor_id: für die Byte-1-Zeile.
    counts_in/out: optional die aktuellen Zählerstände, dann werden sie je
                   aktiver Klasse mit angezeigt.
    """
    mode = config.get("mode", "line")

    # multi_roi wird über ein gewähltes IN-Feld auf dasselbe 18-Byte-Format
    # abgebildet — dorthin delegieren.
    if mode == "multi_roi":
        return describe_multi_roi_structure(
            config, interval_minutes=interval_minutes, sensor_id=sensor_id,
            counts_csv=None)

    active_ordered = _active_in_canonical_order(config.get("classes", []))
    mask = class_bitmask(active_ordered)

    lines = []
    lines.append(f"LoRa-Nachricht — kompaktes Binärformat v2, "
                 f"{FRAME_LEN} Byte fix, FPort {FPORT}, unbestätigt.")
    lines.append("")
    lines.append("Aufbau (Header 6 Byte + 6 Klassen x [IN][OUT]):")
    lines.append(f"  Byte 0      Format-Version (0x{FORMAT_VERSION:02X})")
    lines.append(f"  Byte 1      Sensor-ID ({_clamp_byte(sensor_id)})")
    lines.append("  Byte 2      frame_counter (0-255, pro Uplink +1)")
    lines.append(f"  Byte 3      interval_min = {interval_minutes} "
                 f"(Aggregationsintervall in Minuten)")
    lines.append("  Byte 4      status-Bitfeld (Bit0 Kamera, Bit1 Hailo, "
                 "Bit2 Konfig, Bit3 gepuffert, Bit4 Teilintervall)")
    lines.append(f"  Byte 5      Klassen-Bitmaske = 0x{mask:02X} "
                 f"(1 Bit je aktiver Klasse)")
    lines.append("  Byte 6-17   je Klasse 2 Byte: [IN][OUT], je 0-255")
    lines.append("")

    # Slot-Zuordnung je Klasse, damit sichtbar wird, welches Byte-Paar wozu
    # gehört und welche Klassen laut Konfiguration echte Werte tragen.
    lines.append("Klassen-Slots (feste Reihenfolge) — aktiv laut Konfiguration:")
    have_counts = counts_in is not None and counts_out is not None
    for i, name in enumerate(CANONICAL_CLASSES):
        first_byte = HEADER_LEN + 2 * i
        second_byte = first_byte + 1
        is_active = name in set(active_ordered)
        mark = "aktiv " if is_active else "inaktiv"
        line = f"  Byte {first_byte:>2}-{second_byte:<2}  {name:<11} [{mark}]"
        if is_active and have_counts:
            line += (f"  IN={_clamp_byte(counts_in.get(name, 0))} "
                     f"OUT={_clamp_byte(counts_out.get(name, 0))}")
        elif not is_active:
            line += "  -> 00 00"
        lines.append(line)
    lines.append("")

    # Erklärung / Semantik
    lines.append("Übertragen werden je aktiver Klasse die IN- und OUT-Zähler "
                 "seit dem letzten Uplink (0-255, bei 255 gekappt). Inaktive "
                 "Klassen belegen ihren Slot mit 00 00. Die Bitmaske sagt dem "
                 "Empfänger, welche Slots er auswerten muss.")

    if interval_minutes is not None:
        lines.append("")
        lines.append(f"Sende-Intervall: alle {interval_minutes} min nach jedem "
                     f"erfolgreichen Uplink (EU868-Duty-Cycle 1 % — mind. 2 min "
                     f"empfohlen).")

    return "\n".join(lines)


# =====================================================================
# multi_roi über ein gewähltes IN-Feld auf das 18-Byte-Format abbilden
# =====================================================================
#
# Statt eines eigenen Übergangs-Formats wird ein Feld als "IN-Bereich"
# bestimmt (roi_config.json -> "in_field"). Aus den Übergangs-Zeilen in
# zaehlung.csv ("A->B") wird dann pro Klasse gezählt:
#   * Übergang  X -> IN-Feld   =>  IN   (jemand ist in den Bereich gekommen)
#   * Übergang  IN-Feld -> X   =>  OUT  (jemand hat den Bereich verlassen)
#   * alle anderen Übergänge             ignoriert
# Damit passt multi_roi in genau dasselbe IN/OUT-Format wie Linie/ROI.


def normalize_in_fields(raw):
    """
    "in_field" aus roi_config.json einheitlich als Liste von Namen lesen.

    Neue Konfigurationen speichern hier eine Liste (mehrere IN-Flächen
    möglich), ältere einen einzelnen Flächennamen als String.
    """
    if isinstance(raw, list):
        return [n.strip() for n in raw if n and n.strip()]
    raw = (raw or "").strip()
    return [raw] if raw else []


def region_names(config):
    """Namen der benannten Flächen aus roi_config.json (Config-Reihenfolge)."""
    names = []
    for region in config.get("regions", []) or []:
        name = (region.get("name") or "").strip()
        if name and name not in names:
            names.append(name)
    return names


def parse_transition_direction(direction):
    """Zerlegt 'A->B' in (from, to). None, wenn es kein echter Übergang ist
    (z. B. 'A (kein Wechsel)')."""
    if not direction or "->" not in direction:
        return None
    frm, _, to = direction.partition("->")
    return frm.strip(), to.strip()


def read_inout_from_transitions(path, in_fields, active_classes):
    """
    Liest zaehlung.csv und bildet die Übergänge relativ zu den IN-Feldern auf
    IN/OUT je Klasse ab. in_fields: Name einer IN-Fläche (str, Altformat)
    oder Liste von IN-Flächennamen.

    Rückgabe: (counts_in, counts_out) als dicts {klassenname: anzahl}.
    Fehlt die Datei oder ist kein IN-Feld gesetzt, sind beide leer.
    """
    in_set = set(normalize_in_fields(in_fields))
    active = set(active_classes)
    counts_in = {c: 0 for c in active}
    counts_out = {c: 0 for c in active}

    if not path or not in_set or not os.path.isfile(path):
        return counts_in, counts_out

    try:
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                if str(row.get("is_transition")).strip() != "True":
                    continue
                label = (row.get("label") or "").strip()
                if label not in active:
                    continue
                pair = parse_transition_direction(row.get("direction") or "")
                if pair is None:
                    continue
                frm, to = pair
                to_in = to in in_set
                frm_in = frm in in_set
                if to_in and not frm_in:
                    counts_in[label] += 1
                elif frm_in and not to_in:
                    counts_out[label] += 1
    except (OSError, csv.Error):
        pass

    return counts_in, counts_out


def decode_frame(frame):
    """
    Referenz-Decoder fürs 18-Byte-Format (auch für die Empfängerseite / Tests).
    Nimmt bytes und gibt ein dict mit dem Inhalt zurück.
    """
    if not frame or len(frame) != FRAME_LEN:
        raise ValueError(f"Frame muss {FRAME_LEN} Byte haben")
    if frame[0] != MSG_LINE_ROI:
        raise ValueError(f"unbekannter Nachrichtentyp 0x{frame[0]:02X}")
    mask = frame[5]
    classes = {}
    for i, name in enumerate(CANONICAL_CLASSES):
        base = HEADER_LEN + 2 * i
        classes[name] = {"in": frame[base], "out": frame[base + 1],
                         "active": bool(mask & (1 << i))}
    status = frame[4]
    return {"type": "line_roi", "sensor_id": frame[1], "frame_counter": frame[2],
            "interval_min": frame[3], "status": status,
            "status_flags": {
                "camera_ok": bool(status & STATUS_CAMERA_OK),
                "accel_ok":  bool(status & STATUS_ACCEL_OK),
                "config_ok": bool(status & STATUS_CONFIG_OK),
                "buffered":  bool(status & STATUS_BUFFERED),
                "partial":   bool(status & STATUS_PARTIAL),
            },
            "class_bitmask": mask, "classes": classes}


def describe_multi_roi_structure(config, interval_minutes=None, sensor_id=1,
                                 counts_csv=None):
    """Hinweis-Text (Tab 3) für multi_roi: nutzt dasselbe 18-Byte-Format wie
    Linie/ROI, IN/OUT werden über das gewählte IN-Feld bestimmt."""
    names = region_names(config)
    in_fields = normalize_in_fields(config.get("in_field"))
    active_ordered = _active_in_canonical_order(config.get("classes", []))
    mask = class_bitmask(active_ordered)

    lines = []
    lines.append(f"LoRa-Nachricht — {FRAME_LEN} Byte fix, FPort {FPORT}, "
                 f"unbestätigt (dasselbe IN/OUT-Format wie Linie/ROI).")
    lines.append("")

    if not in_fields:
        lines.append("⚠ Kein IN-Feld gewählt. In der Konfiguration (Tab 2, "
                     "Modus 'Mehrere Flächen') mindestens ein Feld als "
                     "IN-Bereich markieren — sonst können keine IN/OUT-Werte "
                     "gesendet werden.")
        if names:
            lines.append(f"   Verfügbare Felder: {', '.join(names)}")
        return "\n".join(lines)

    in_feld_text = ", ".join(in_fields)
    lines.append(f"IN-Felder: {in_feld_text}.")
    lines.append(f"  Übergang  X → ({in_feld_text})   = IN")
    lines.append(f"  Übergang  ({in_feld_text}) → X   = OUT")
    lines.append("  andere Übergänge werden nicht gewertet.")
    lines.append("")
    lines.append("Aufbau (Header 6 Byte + 6 Klassen x [IN][OUT]):")
    lines.append(f"  Byte 0      Format (0x{MSG_LINE_ROI:02X})")
    lines.append(f"  Byte 1      Sensor-ID ({_clamp_byte(sensor_id)})")
    lines.append("  Byte 2      frame_counter (0-255, pro Uplink +1)")
    lines.append(f"  Byte 3      interval_min = {interval_minutes} "
                 f"(Aggregationsintervall in Minuten)")
    lines.append("  Byte 4      status-Bitfeld (Bit0 Kamera, Bit1 Hailo, "
                 "Bit2 Konfig, Bit3 gepuffert, Bit4 Teilintervall)")
    lines.append(f"  Byte 5      Klassen-Bitmaske = 0x{mask:02X}")
    lines.append("  Byte 6-17   je Klasse 2 Byte: [IN][OUT], je 0-255")
    lines.append("")

    have_counts = bool(counts_csv)
    if have_counts:
        counts_in, counts_out = read_inout_from_transitions(
            counts_csv, in_fields, config.get("classes", []))
    lines.append("Klassen-Slots (feste Reihenfolge) — aktiv laut Konfiguration:")
    for i, name in enumerate(CANONICAL_CLASSES):
        first = HEADER_LEN + 2 * i
        is_active = name in set(active_ordered)
        mark = "aktiv " if is_active else "inaktiv"
        line = f"  Byte {first:>2}-{first+1:<2}  {name:<11} [{mark}]"
        if is_active and have_counts:
            line += f"  IN={_clamp_byte(counts_in.get(name,0))} OUT={_clamp_byte(counts_out.get(name,0))}"
        elif not is_active:
            line += "  -> 00 00"
        lines.append(line)
    lines.append("")
    lines.append("Übertragen wird je aktiver Klasse der Zuwachs an IN/OUT seit "
                 "dem letzten Uplink (0-255, bei 255 gekappt).")

    if interval_minutes is not None:
        lines.append("")
        lines.append(f"Sende-Intervall: alle {interval_minutes} min nach jedem "
                     f"erfolgreichen Uplink (EU868-Duty-Cycle 1 %).")
    return "\n".join(lines)
