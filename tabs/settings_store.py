"""
tabs/settings_store.py — persistiert die in der App gewählten Einstellungen
(Input-Quelle, alle Optionen auf Seite 3, Design) in app_settings.json.

Jede Änderung wird SOFORT geschrieben (siehe MainApp._wire_settings_autosave
in app.py), nicht erst beim Beenden - die App soll auch einen Stromausfall
ohne sauberes Herunterfahren überstehen, ohne die zuletzt gewählten
Einstellungen zu verlieren.

Getrennt von roi_config.json: das ist die Zählgeometrie-Konfiguration
(Linie/Fläche(n), Klassen, IN/OUT-Zuordnung), die roi_config_app.py bereits
eigenständig speichert und die core.py automatisch lädt - hier geht es nur
um die übrigen Bedienelemente der App (Tab 1 + Tab 3 + Design).
"""

import json

SETTINGS_PATH = "app_settings.json"

# Diese Werte gelten sowohl als Vorbelegung eines frisch angelegten
# app_settings.json (siehe load_settings()) als auch inhaltlich als die
# aktuellen Standardwerte der App - identisch mit dem, was vorher direkt als
# StringVar/BooleanVar-Startwert im Code stand.
DEFAULTS = {
    "input_mode": "usb",
    "input_file_path": "",
    # Debug-Hauptschalter (Tab 3): steuert, ob Mitschnitt/Live-Vorschau/
    # Zeitlimit/Debug-Dateien/detaillierte Konsole überhaupt zugänglich sind.
    # Standard AUS = sauberer Feldbetrieb ohne versehentlich aktive
    # Labor-Optionen.
    "debug_enabled": False,
    "debug_files_enabled": False,
    "verbose_console_enabled": False,
    "recording_enabled": False,
    "recording_dir": "auto",
    "recording_bitrate": "2000",
    "recording_fps": "15",
    "recording_segment": "600",
    "use_frame": True,
    "lora_enabled": False,
    "lora_interval": "5",
    "lora_sensor_id": "1",
    "mqtt_enabled": False,
    "mqtt_broker": "192.168.0.50",
    "mqtt_port": "1883",
    "mqtt_interval": "5",
    "mqtt_sensor_id": "1",
    "mqtt_transitions": True,
    "run_duration": "",
    "appearance_mode": "dark",
}


def load_settings():
    """
    Liest app_settings.json. Fehlt die Datei, ist sie unlesbar oder fehlen
    einzelne Schlüssel (z. B. nach einem Update mit neuen Einstellungen),
    werden die fehlenden Werte aus DEFAULTS ergänzt und die Datei sofort
    (neu) geschrieben - eine fehlende Datei bekommt so schon beim ersten
    Start der App die aktuellen Standardwerte als Inhalt, ohne dass jemand
    sie von Hand anlegen muss.
    """
    try:
        with open(SETTINGS_PATH) as f:
            gespeichert = json.load(f)
        if not isinstance(gespeichert, dict):
            gespeichert = {}
    except (OSError, ValueError):
        gespeichert = {}

    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in gespeichert.items() if k in DEFAULTS})

    if merged != gespeichert:
        save_settings(merged)

    return merged


def save_settings(values):
    """Schreibt den kompletten Einstellungsstand auf einmal (nicht nur den
    geänderten Wert) - so bleibt die Datei auch dann vollständig, wenn ein
    Aufrufer nur ein Teil-dict mit den zuletzt bekannten Werten übergibt."""
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(values, f, indent=2)
    except OSError:
        # Nicht schreibbar: Einstellungen gelten dann nur für diese Sitzung.
        pass
