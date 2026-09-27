# Besucherzählsensor

Computer-Vision-basierter Sensor zur automatisierten Besucherzählung auf
Raspberry Pi 5 mit Hailo-8-Beschleuniger. Das Repository ist eigenständig
lauffähig — es enthält die komplette Anwendung (Objekterkennung, Tracking,
Zähllogik, Konfigurations-GUI, LoRaWAN-Anbindung).

## Versionsstand

Alle Python-Abhängigkeiten sind exakt gepinnt, damit jedes Gerät identisch
aufgebaut wird. Stand der Tabelle: **27.09.2026** — jeweils die zu diesem
Zeitpunkt aktuellste Veröffentlichung.

| Komponente | Version | Bezug |
|---|---|---|
| Python | 3.13.x (Pi OS trixie) | System; aktuellste Reihe ist 3.14.x |
| numpy | 2.5.3 | pip (`requirements.txt`) |
| opencv-python | 5.0.0.93 | pip |
| Pillow | 12.3.0 | pip |
| customtkinter | 6.0.0 | pip |
| scikit-learn | 1.9.1 | pip |
| scipy | 1.18.1 | pip |
| hailo-apps-infra (`hailo_apps`) | 26.03.1 | pip aus Git (`create_venv.sh`) |
| hailort / hailo-tappas-core / `hailo` | Version des Pi-OS-Pakets | apt (`hailo-all`) |
| PyGObject (`gi`), GStreamer 1.0 | Version des Pi-OS-Pakets | apt |

Die apt-Pakete werden bewusst nicht gepinnt — sie müssen zum Kernel und zum
PCIe-Treiber des jeweiligen Pi-OS-Stands passen und kommen deshalb immer aus
der Distribution.

**Aktualisieren:** `pip list --outdated` in der aktivierten venv, neue
Versionen in [`requirements.txt`](requirements.txt) eintragen, diese Tabelle
nachziehen. Für `hailo_apps` das neueste Release unter
<https://github.com/hailo-ai/hailo-apps-infra/releases> nachsehen und den Tag
in [`create_venv.sh`](create_venv.sh) (`HAILO_APPS_VERSION`) setzen.

> **Hinweis:** Die Versionen sind auf Aktualität gewählt, nicht auf geprüfte
> Kompatibilität untereinander. Insbesondere die Kombination aus einem neuen
> `hailo_apps` und der PyGObject-Version des Systems ist eine bekannte
> Bruchstelle — siehe [Bekannte Stolpersteine](#bekannte-stolpersteine).

## Voraussetzungen (System)

- Raspberry Pi 5 mit Hailo-8 (Firmware 4.23.0 getestet)
- Raspberry Pi OS (64-bit), Debian 13 "trixie"
- **Hailo-Systempakete** — kommen NICHT über `requirements.txt`, sondern per
  `apt` direkt von Raspberry Pi OS:
  ```bash
  sudo apt update && sudo apt install -y hailo-all
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

## Ersteinrichtung eines neuen Geräts

1. **Hailo initialisieren** — Pi OS (64-bit) aufsetzen, System updaten, PCIe-
   Speed über `raspi-config` (Advanced Options → PCIe Speed) auf Gen3 stellen,
   neu starten, dann `sudo apt install hailo-all` und mit
   `hailortcli fw-control identify` verifizieren.
2. **Repo klonen** — kein weiteres Hailo-Repo nötig, siehe oben.
3. **Abhängigkeiten installieren** — siehe [Installation](#installation).
4. **Hardware verbinden** — USB-Kamera, LoRa-Modul (LA66 USB Adapter, meldet
   sich als `/dev/ttyUSB0` über den im Kernel enthaltenen `cp210x`-Treiber,
   kein manueller Treiber nötig) und LTE-Stick per USB anschliessen.

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
(damit `hailo` und `gi` aus dem System sichtbar bleiben), installiert
`requirements.txt` und danach `hailo_apps` per `pip` direkt aus
`hailo-apps-infra`. Am Ende läuft ein Selbsttest aller Importe (`numpy`,
`cv2`, `hailo`, `hailo_apps`, …).

Eine andere `hailo_apps`-Version installieren:

```bash
HAILO_APPS_VERSION=25.7.0 bash create_venv.sh
```

Schlägt die Online-Installation fehl, bindet das Skript als Rückfall eine
bestehende `hailo-rpi5-examples`-venv per `.pth` ein — Pfad dafür über
`HAILO_VENV=<pfad>` setzen.

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
python core/core.py --input usb                      # nur die Zähl-Pipeline
python config_tool/roi_config_app.py --input usb     # nur das Zählgeometrie-Werkzeug
python config_tool/auto_config_clustering.py --input camera_raw.png --border --save
```

## Bekannte Stolpersteine

**Pipeline friert nach dem ersten Frame ein.** Ursache ist in aller Regel eine
Exception im GStreamer-Frame-Callback: ein Pad-Probe-Callback, der eine
Exception wirft, gibt effektiv `PadProbeReturn.DROP` zurück, wodurch jeder
Buffer verworfen wird. Der Traceback erscheint dabei nur einmal, es sieht also
nach einem einmaligen Fehler aus, obwohl jeder Frame scheitert. Erste Prüfung:

```bash
python core/core.py --input usb 2>&1 | head -40
```

Ein bekannter Fall ist `AttributeError: 'StructureWrapper' object has no
attribute 'get_value'` aus `hailo_apps/.../buffer_utils.py`: neuere PyGObject-
Versionen liefern `Gst.Structure` als `StructureWrapper`, den der Hailo-Helper
nicht kennt. Hier hilft eine `hailo_apps`-Version, die zur PyGObject-Version
des Systems passt.

**Setups zweier Geräte vergleichen.** Wenn dasselbe Repo auf einem Gerät
läuft und auf einem anderen nicht, auf beiden einen Abzug erzeugen und diffen:

```bash
cd ~/visitorcounter && source setup_env.sh
{
  echo "### OS";     head -3 /etc/os-release; uname -a
  echo "### apt";    dpkg -l | grep -E 'hailo|python3-gi|gir1.2-gst|python3-gst|libgst' | awk '{print $2, $3}'
  echo "### python"; python -V; python -c "import gi; print('pygobject', gi.__version__)"
  echo "### hailo";  hailortcli fw-control identify 2>&1 | grep -Ei 'firmware|architecture'
  echo "### pip";    pip freeze | sort
} > ~/abzug_$(hostname).txt 2>&1
```

**Kamera prüfen.** Die Pipeline fordert MJPG 1280x720 @ 30 fps an; dass die
Kamera das diskret anbietet, zeigt `v4l2-ctl -d /dev/video0 --list-formats-ext`.

**Start über SSH.** Die Pipeline endet in `fpsdisplaysink → autovideosink` und
braucht ein Display. Ohne gesetztes `DISPLAY` blockiert der Sink:
`DISPLAY=:0 python core/core.py --input usb`.

## Autostart beim Booten

Kein systemd-Service, sondern ein Desktop-Autostart-Eintrag + Autologin:

1. **Autologin einrichten** (`sudo raspi-config` → System Options → Boot /
   Autologin → Desktop Autologin). Auf Raspberry Pi OS "trixie" ist die
   Desktop-Session standardmässig `rpd-labwc` (Wayland/labwc statt LXDE).
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
> `docs/entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md` (nicht im
> öffentlichen Repo, siehe [Dokumentation](#dokumentation))

## Konfiguration

`roi_config.json` (Zählgeometrie) und `app_settings.json` (zuletzt genutzter
Input, LoRa-/MQTT-Einstellungen, Design) sind geräte-/standortspezifisch und
werden von der App selbst erzeugt — nicht im Repo, per `.gitignore`
ausgeschlossen. `roi_config.json` entsteht beim ersten Speichern in Tab 2, als
Muster liegt `roi_config.example.json` bei. Jedes Gerät bekommt beim
Ersteinrichten seine eigene.

## Dokumentation

Die ausführliche Projektdokumentation liegt in `docs/` und ist **nicht Teil
dieses öffentlichen Repositories** — sie enthält geräte- und
standortspezifische Angaben. Aufbau:

| Ordner | Inhalt |
|---|---|
| `docs/projekt/` | Einstieg (`HANDOFF.md`) und offene Punkte (`ToDo.md`) — der laufende Stand |
| `docs/abschlussarbeit/` | Gliederung, Statusbericht, Zeitplan, Architekturentwurf, Abbildungen |
| `docs/einrichtung/` | Gerät aufsetzen, LA66 einrichten, eigenes Git-Repository |
| `docs/entwicklung/` | Änderungshistorie, gelöste Probleme, Analysen — u. a. Mitschnitt: Benchmark vs. Normalbetrieb |
| `docs/lora/` | Verbindliche Nachrichtenformat-Spezifikation, Integrations-Changelog, Recherche |

Ebenfalls nicht im öffentlichen Repo: `tests/` mit Diagnose- und
Hardware-Testskripten, die **nicht** zum Normalbetrieb gehören (Kamera-Test,
LoRa-Hardware-Erprobung, TTN-Decoder).
