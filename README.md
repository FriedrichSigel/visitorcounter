# Besucherzählsensor — core

Computer-Vision-basierter Sensor zur automatisierten Besucherzählung auf
Raspberry Pi 5 mit Hailo-8-Beschleuniger. Dieser Ordner ist eigenständig
lauffähig — er enthält die komplette Anwendung (Objekterkennung, Tracking,
Zähllogik, Konfigurations-GUI, LoRaWAN-Anbindung).

## Voraussetzungen (System)

- Raspberry Pi 5 mit Hailo-8 (Firmware 4.23.0 getestet)
- Raspberry Pi OS (64-bit), Python 3.11
- **Hailo-Software installiert** (HailoRT + Tappas + `hailo_apps`-Framework).
  Diese Pakete kommen NICHT über `requirements.txt`, sondern über die
  Hailo-Installation. Siehe die offizielle Anleitung von
  `hailo-rpi5-examples` bzw. das dort enthaltene `install.sh` /
  `hailo_python_installation.sh`.
- GStreamer + PyGObject (`gi`) als System-Pakete:
  ```bash
  sudo apt install -y python3-gi python3-gst-1.0 gstreamer1.0-plugins-good python3-tk
  ```

Die drei nicht-pip-Bausteine (`hailo`, `hailo_apps`, `gi`) sind der Grund, warum
die virtuelle Umgebung Zugriff auf die System-/SDK-Pakete braucht
(`--system-site-packages` oder die vom Hailo-Setup erzeugte venv).

## Installation (nur mit diesem Ordner)

```bash
# 1. In den core-Ordner wechseln
cd core

# 2. Virtuelle Umgebung anlegen — mit Zugriff auf die System-/Hailo-Pakete
python3 -m venv --system-site-packages venv_hailo_rpi_examples

# 3. Environment einrichten (venv aktivieren + PYTHONPATH setzen)
source setup_env.sh

# 4. Python-Abhängigkeiten installieren
pip install -r requirements.txt
```

Ist die Hailo-venv bereits zentral vorhanden (vom `hailo-rpi5-examples`-Setup),
kann Schritt 2 entfallen — `setup_env.sh` findet eine venv auch im
Elternverzeichnis oder im `$HOME`.

## Nutzung

```bash
# Environment aktivieren (in jeder neuen Terminal-Sitzung)
source setup_env.sh

# Steuer-App starten (empfohlen — bündelt alles über eine Oberfläche)
python app.py
```

Die App führt durch fünf Seiten: Input wählen → Konfiguration (Zählgeometrie)
→ Start → Live-Auswertung → Auto-Konfiguration. Standard-Input ist die
USB-Kamera.

Einzelne Bestandteile lassen sich auch direkt starten:

```bash
python core.py --input usb              # nur die Zähl-Pipeline
python roi_config_app.py --input usb    # nur das Zählgeometrie-Werkzeug
python auto_config_clustering.py --input camera_raw.png --border --save
```

## Module (Kurzüberblick)

| Datei | Aufgabe |
|---|---|
| `app.py` | Zentrale Steuer-App (GUI, fünf Seiten) |
| `core.py` | Pipeline-Steuerung, Frame-Callback |
| `tracking.py` | Track-Verwaltung, Flush/Finalize, avg_confidence |
| `counting.py` | Zähllogik (Linie / ROI / Mehrere Flächen) |
| `visualization.py` | Live-Overlay + Bewegungsbilder |
| `logging_utils.py` | Schreibt `ergebniss.csv` und `zaehlung.csv` |
| `csv_utils.py` | Schema-Schutz der CSV-Dateien |
| `cleanup_utils.py` | Start-Cleanup (archiviert Vorlauf-Artefakte) |
| `config.py` | Zentrale Konstanten, lädt `roi_config.json` |
| `roi_config_app.py` | Zählgeometrie-Werkzeug (auch in app.py eingebettet) |
| `ctk_dialogs.py` | CustomTkinter-Dialoge (dunkles Design) |
| `ui_utils.py` | Gemeinsame GUI-Hilfsfunktionen |
| `frame_utils.py` | GUI-freie Frame-/Auflösungsbeschaffung |
| `auto_config.py` | Datensammlung + Batch-Einteilung |
| `auto_config_clustering.py` | DBSCAN / Randraster → Zählgeometrie |

## Ausgaben

Werden bei jedem Lauf im Arbeitsverzeichnis erzeugt (per `.gitignore`
ausgeschlossen): `ergebniss.csv` (Track-Zwischenspeicher mit `avg_confidence`),
`zaehlung.csv` (Zählereignisse), `bewegungsbild_*_flush.png` /
`_finalize.png`. Beim Start werden Artefakte des Vorlaufs nach
`vorherige_laeufe/<Zeitstempel>/` verschoben.

## Konfiguration

`roi_config.json` (Zählgeometrie) ist geräte-/standortspezifisch und wird über
das Konfig-Tool erzeugt — nicht im Repo. Als Muster liegt
`roi_config.example.json` bei; die echte Datei entsteht beim ersten Speichern
in Tab 2. Für 17 Eingänge bekommt jedes Gerät
seine eigene. Details zum Geräte-Setup:
`docs/einrichtung/GERAETE_EINRICHTUNG.md`, zur LoRa-Hardware:
`docs/einrichtung/EINRICHTUNG_LA66.md`.

## Dokumentation

Die gesamte Dokumentation liegt in `docs/`, thematisch sortiert. Wegweiser mit
Kurzbeschreibung jeder Datei: **[`docs/README.md`](docs/README.md)**.

| Ordner | Inhalt |
|---|---|
| `docs/projekt/` | Einstieg (`HANDOFF.md`) und offene Punkte (`ToDo.md`) — der laufende Stand |
| `docs/abschlussarbeit/` | Gliederung, Statusbericht, Zeitplan, Architekturentwurf, Abbildungen |
| `docs/einrichtung/` | Gerät aufsetzen, LA66 einrichten, eigenes Git-Repository |
| `docs/lora/` | Verbindliche Nachrichtenformat-Spezifikation, Integrations-Changelog, Recherche |
| `docs/entwicklung/` | Änderungshistorie, gelöste Probleme, Analysen |

`tests/` enthält Diagnose- und Hardware-Testskripte, die **nicht** zum
Normalbetrieb gehören (Kamera-Test, LoRa-Hardware-Erprobung, TTN-Decoder) —
siehe [`tests/README.md`](tests/README.md).
