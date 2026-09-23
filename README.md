# Besucherzählsensor — core

Computer-Vision-basierter Sensor zur automatisierten Besucherzählung auf
Raspberry Pi 5 mit Hailo-8-Beschleuniger. Dieser Ordner ist eigenständig
lauffähig — er enthält die komplette Anwendung (Objekterkennung, Tracking,
Zähllogik, Konfigurations-GUI, LoRaWAN-Anbindung).

## Voraussetzungen (System)

- Raspberry Pi 5 mit Hailo-8 (Firmware 4.23.0 getestet)
- Raspberry Pi OS (64-bit), Debian 13 "trixie", Python 3.13
- **Hailo-Systempakete installiert** — kommen NICHT über `requirements.txt`,
  sondern per `apt` direkt von Raspberry Pi OS:
  ```bash
  sudo apt install -y hailo-all
  ```
  Das Metapaket zieht `hailort`, `hailo-tappas-core`, `hailort-pcie-driver`,
  `python3-hailort` und `python3-hailo-tappas` mit. Verifizieren:
  ```bash
  hailortcli fw-control identify   # muss "Device Architecture: HAILO8" zeigen
  ```
- GStreamer, PyGObject (`gi`) und Tkinter/Pillow-Tk-Unterstützung als
  System-Pakete:
  ```bash
  sudo apt install -y python3-gi python3-gst-1.0 gstreamer1.0-plugins-good \
                       python3-tk python3-pil python3-pil.imagetk python3-venv
  ```
  `python3-pil.imagetk` ist kein optionales Extra — ohne das Paket fehlt
  `PIL.ImageTk`, und die GUI startet nicht. `python3-venv` wird für den
  nächsten Schritt gebraucht (ohne das Paket entsteht eine venv ohne eigene
  `pip`, was zum bekannten `externally-managed-environment`-Fehler führt).

Das `hailo_apps`-Python-Framework kommt dagegen NICHT über `apt`, sondern wird
im nächsten Schritt automatisch per `pip` aus dem offiziellen
`hailo-apps-infra`-Repository installiert — ein separates Klonen von
`hailo-rpi5-examples` oder `hailo-apps` ist für den Betrieb **nicht** nötig.

## Ersteinrichtung eines neuen Geräts (von Grund auf)

Reihenfolge für ein komplett neues Raspberry Pi 5 + Hailo-8-Setup:

1. **Hailo initialisieren** — Pi OS (64-bit) aufsetzen, System updaten, PCIe-
   Speed über `raspi-config` (Advanced Options → PCIe Speed) auf Gen3
   stellen, neu starten, dann `sudo apt install hailo-all` und mit
   `hailortcli fw-control identify` verifizieren.
2. **Dieses Repo klonen** — kein weiteres Hailo-Repo nötig, siehe oben.
3. **Abhängigkeiten installieren** — siehe „Installation" unten
   (`bash create_venv.sh` erledigt venv + `requirements.txt` + `hailo_apps`
   in einem Schritt).
4. **Hardware verbinden** — USB-Kamera, LoRa-Modul (LA66 USB Adapter, meldet
   sich als `/dev/ttyUSB0` über den im Kernel enthaltenen `cp210x`-Treiber,
   kein manueller Treiber nötig) und LTE-Stick per USB an den Pi anschließen.

Ausführliche Schritt-für-Schritt-Befehle (inkl. Fixes für bekannte
Stolpersteine bei der Hailo-Installation) sind absichtlich nicht Teil dieses
öffentlichen READMEs, da sie stark geräte-/setup-spezifisch sind — die
LoRa-Modul-Einrichtung ist in
[`tests/lora_hardware/Anleitung_LA66_TTN_Verbindung.md`](tests/lora_hardware/Anleitung_LA66_TTN_Verbindung.md)
dokumentiert.

## Installation

```bash
# 1. Repo klonen
git clone https://github.com/FriedrichSigel/visitorcounter.git
cd visitorcounter

# 2. venv anlegen + Python-Abhängigkeiten + hailo_apps installieren
bash create_venv.sh

# 3. Environment aktivieren (venv aktivieren + PYTHONPATH setzen)
source setup_env.sh
```

`create_venv.sh` legt `venv_visitorcounter` mit `--system-site-packages` an
(damit `hailo`/`gi` aus dem System sichtbar bleiben), installiert
`requirements.txt` und danach `hailo_apps` per `pip` direkt aus
`hailo-apps-infra` (Tag konfigurierbar über `HAILO_APPS_VERSION`, Standard
siehe Kopf des Skripts). Am Ende läuft ein Selbsttest aller Importe
(`numpy`, `cv2`, `hailo`, `hailo_apps`, …) — schlägt `hailo_apps` dort fehl,
sag Bescheid, dafür gibt es einen `.pth`-Fallback über `HAILO_VENV=<pfad>`
auf eine bestehende `hailo-rpi5-examples`-venv.

## Nutzung

```bash
# Environment aktivieren (in jeder neuen Terminal-Sitzung)
source setup_env.sh

# Steuer-App starten (empfohlen — bündelt alles über eine Oberfläche)
python core/app.py
```

Die App führt durch fünf Seiten: Input wählen → Konfiguration (Zählgeometrie)
→ Start → Live-Auswertung → Auto-Konfiguration. Standard-Input ist die
USB-Kamera.

Einzelne Bestandteile lassen sich auch direkt starten:

```bash
python core/core.py --input usb                     # nur die Zähl-Pipeline
python config_tool/roi_config_app.py --input usb     # nur das Zählgeometrie-Werkzeug
python config_tool/auto_config_clustering.py --input camera_raw.png --border --save
```

## Autostart beim Booten

Kein systemd-Service, sondern ein Desktop-Autostart-Eintrag + Autologin:

1. **Autologin einrichten** (`sudo raspi-config` → System Options → Boot /
   Autologin → Desktop Autologin). Auf Raspberry Pi OS "trixie" ist die
   Desktop-Session standardmäßig `rpd-labwc` (Wayland/labwc statt LXDE).
2. **Autostart-Eintrag anlegen**: `~/.config/autostart/visitorcounter.desktop`
   ```ini
   [Desktop Entry]
   Type=Application
   Name=Besucherzähler
   Comment=Startet die Personenzähl-App automatisch beim Hochfahren
   Exec=lxterminal --working-directory=/home/<user>/visitorcounter -e bash -c "./start_app.sh; exec bash"
   X-GNOME-Autostart-enabled=true
   ```
   Pfad in `Exec=` an das tatsächliche Home-Verzeichnis anpassen.
   `start_app.sh` macht einen Aufwärmlauf (`utils/warmup.py`) und startet
   danach `core/app.py --autostart`, das automatisch mit dem zuletzt in der
   App gewählten Input (`app_settings.json`) startet.

## Module (Kurzüberblick)

Die Python-Dateien sind nach Funktionsbereich in Unterordnern sortiert:

| Ordner | Datei | Aufgabe |
|---|---|---|
| `core/` | `app.py` | Zentrale Steuer-App (GUI, fünf Seiten) |
| `core/` | `core.py` | Pipeline-Steuerung, Frame-Callback |
| `core/` | `tracking.py` | Track-Verwaltung, Flush/Finalize, avg_confidence |
| `core/` | `counting.py` | Zähllogik (Linie / ROI / Mehrere Flächen) |
| `core/` | `recording.py` | Benchmark-Mitschnitt (Video, nur Laborläufe) |
| `core/` | `config.py` | Zentrale Konstanten, lädt `roi_config.json` |
| `config_tool/` | `roi_config_app.py` | Zählgeometrie-Werkzeug (auch in app.py eingebettet) |
| `config_tool/` | `auto_config.py` | Datensammlung + Batch-Einteilung |
| `config_tool/` | `auto_config_clustering.py` | DBSCAN / Randraster → Zählgeometrie |
| `config_tool/` | `ctk_dialogs.py` | CustomTkinter-Dialoge (dunkles Design) |
| `lora/` | `lora_message.py`, `lora_send_loop.py` | LoRa-Zählnachricht + Sendeschleife |
| `lora/` | `konfig_payload.py`, `uebergangs_payload.py`, `lora_spiegel.py` | Zusatzformate / MQTT-Spiegelung |
| `lora/` | `mqtt_send_loop.py` | Gegenstück zu `lora_send_loop.py`, über MQTT |
| `utils/` | `visualization.py` | Live-Overlay + Bewegungsbilder |
| `utils/` | `logging_utils.py` | Schreibt `ergebniss.csv` und `zaehlung.csv` |
| `utils/` | `csv_utils.py` | Schema-Schutz der CSV-Dateien |
| `utils/` | `cleanup_utils.py` | Start-Cleanup (archiviert Vorlauf-Artefakte) |
| `utils/` | `ui_utils.py` | Gemeinsame GUI-Hilfsfunktionen |
| `utils/` | `frame_utils.py` | GUI-freie Frame-/Auflösungsbeschaffung |
| `utils/` | `warmup.py` | Aufwärmlauf beim Systemstart |
| `utils/` | `benchmark.py` | Leistungskennzahlen für Benchmark-/Laborläufe |
| `tabs/` | — | Einzelne Seiten der Steuer-App (Mixins), eingebunden von `core/app.py` |

## Ausgaben

Werden bei jedem Lauf im Arbeitsverzeichnis erzeugt (per `.gitignore`
ausgeschlossen): `ergebniss.csv` (Track-Zwischenspeicher mit `avg_confidence`),
`zaehlung.csv` (Zählereignisse), `bewegungsbild_*_flush.png` /
`_finalize.png`. Beim Start werden Artefakte des Vorlaufs nach
`vorherige_laeufe/<Zeitstempel>/` verschoben.

### Bilddaten — Normalbetrieb vs. Benchmarklauf

**Im Normalbetrieb speichert der Sensor keine Bilder.** Frames werden
verarbeitet und verworfen, gespeichert werden nur die aggregierten Zählwerte in
`zaehlung.csv` bzw. das anonyme Bewegungsbild. Das ist die Grundlage des
Privacy-by-Design-Ansatzes (DSGVO Art. 25).

Für die **Messung der Zählgenauigkeit** gibt es zusätzlich eine
Mitschnittfunktion (`recording.py`, Tab 3 der App, Checkbox ganz oben). Sie
zeichnet parallel zum Zähllauf Video mit eingebrannter Uhrzeit auf, damit sich
die gezählten Ereignisse gegen das Bildmaterial prüfen lassen.

> Diese Funktion ist **standardmässig aus**, wird bei jedem App-Start
> zurückgesetzt und ist **ausschliesslich für Laborläufe** vorgesehen — nicht
> für den Feldeinsatz. Regeln zum Umgang mit dem Material:
> [`docs/entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md`](docs/entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md)

## Konfiguration

`roi_config.json` (Zählgeometrie) und `app_settings.json` (zuletzt genutzter
Input, LoRa-/MQTT-Einstellungen, Design) sind geräte-/standortspezifisch und
werden von der App selbst erzeugt — nicht im Repo, per `.gitignore`
ausgeschlossen. `roi_config.json` entsteht beim ersten Speichern in Tab 2, als
Muster liegt `roi_config.example.json` bei. Jedes Gerät bekommt beim
Ersteinrichten seine eigene.

## Dokumentation

Die gesamte Dokumentation liegt in `docs/`, thematisch sortiert. Wegweiser mit
Kurzbeschreibung jeder Datei: **[`docs/README.md`](docs/README.md)**.

| Ordner | Inhalt |
|---|---|
| `docs/projekt/` | Einstieg (`HANDOFF.md`) und offene Punkte (`ToDo.md`) — der laufende Stand |
| `docs/abschlussarbeit/` | Gliederung, Statusbericht, Zeitplan, Architekturentwurf, Abbildungen |
| `docs/einrichtung/` | Gerät aufsetzen, LA66 einrichten, eigenes Git-Repository |
| `docs/entwicklung/` | Änderungshistorie, Analysen — u. a. **Mitschnitt: Benchmark vs. Normalbetrieb** |
| `docs/lora/` | Verbindliche Nachrichtenformat-Spezifikation, Integrations-Changelog, Recherche |
| `docs/entwicklung/` | Änderungshistorie, gelöste Probleme, Analysen |

`tests/` enthält Diagnose- und Hardware-Testskripte, die **nicht** zum
Normalbetrieb gehören (Kamera-Test, LoRa-Hardware-Erprobung, TTN-Decoder) —
siehe [`tests/README.md`](tests/README.md).
