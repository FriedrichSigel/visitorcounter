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
| PyGObject (`gi`) | Version des Pi-OS-Pakets | apt |
| GStreamer 1.0 | Version des Pi-OS-Pakets, **≥ 1.26.3 empfohlen** | apt |

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
`hailo-apps-infra`. Anschliessend läuft `hailo-post-install`: dieser Schritt
lädt die Modelle nach `/usr/local/hailo/resources`, **kompiliert die
C++-Postprocessing-Bibliotheken** und schreibt die `.env`. Er dauert auf dem Pi
einige Minuten und ist nicht optional — ohne ihn fehlt
`libyolo_hailortpp_postprocess.so` mit dem Symbol `filter_letterbox`, und die
Pipeline stirbt mit einem Segfault. Am Ende läuft ein Selbsttest aller Importe
(`numpy`, `cv2`, `hailo`, `hailo_apps`, …) und eine Prüfung auf diese
Bibliothek.

Einzeln nachholen lassen sich die Schritte mit:

```bash
hailo-download-resources --all   # Modelle/HEF
hailo-compile-postprocess        # C++-Bibliotheken
hailo-set-env                    # .env schreiben
```

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
attribute 'get_value'` aus `buffer_utils.py`. Das ist ein Fehler in
**GStreamer 1.26.2**: `Gst.Caps.get_structure()` liefert dort einen
`StructureWrapper`, der die Methoden des eigentlichen `Gst.Structure` nicht
durchreicht. Behoben ist er in **GStreamer 1.26.3**
([Quelle](https://discourse.gstreamer.org/t/python-get-structure-api-change/4767)).

Das Projekt fängt das in [`utils/hailo_compat.py`](utils/hailo_compat.py) ab
(eigene `get_caps_from_pad()`, die den Wrapper auspackt). Sobald alle Geräte
auf GStreamer ≥ 1.26.3 laufen — `sudo apt upgrade` — kann diese Funktion dort
entfallen. Eigene GStreamer-Version prüfen:

```bash
gst-launch-1.0 --version | head -1
```

**Modulpfade von `hailo_apps`.** Zwischen 25.7.0 und 26.03.x wurde das Paket
umstrukturiert (`hailo_app_python/` → `python/`, `apps/` → `pipeline_apps/`).
`utils/hailo_compat.py` probiert das neue Layout zuerst und fällt auf das alte
zurück, sodass beide Versionen funktionieren. Bei
`ModuleNotFoundError: No module named 'hailo_apps.hailo_app_python'` ist also
nicht der Code kaputt, sondern eine neue `hailo_apps`-Version installiert.

**Paketeigene Dateien nie per `rm` löschen.** Wer z. B.
`/usr/bin/hailortcli` oder `/usr/lib/aarch64-linux-gnu/hailo` direkt löscht,
hinterlässt dpkg im Glauben, alles sei installiert — `apt install` meldet dann
`already the newest version` und installiert nichts nach. Erkennen und
reparieren:

```bash
dpkg -V 'hailo*'      # listet fehlende Dateien
sudo apt install --reinstall -y hailort hailo-tappas-core python3-hailort
```

`/usr/local/hailo` (die HEF-Modelle) gehört dagegen keinem Paket und wird von
`hailo_apps` verwaltet — neu holen mit `hailo-download-resources --all`. Der
Ordner muss dem Benutzer gehören, sonst scheitert der Download an
`Errno 13 Permission denied`:

```bash
sudo mkdir -p /usr/local/hailo/resources
sudo chown -R "$USER":"$USER" /usr/local/hailo
```

**Bestandsaufnahme.** [`hailo_inventar.sh`](hailo_inventar.sh) listet alle
installierten Hailo-, GStreamer- und Python-Bestandteile samt Versionen auf
und zeigt auf Wunsch die Deinstallationsbefehle:

```bash
bash hailo_inventar.sh                  # nur anzeigen
bash hailo_inventar.sh --abzug          # zusaetzlich in Datei (Geraetevergleich)
bash hailo_inventar.sh --plan-entfernen # Deinstallationsbefehle anzeigen
bash hailo_inventar.sh --entfernen      # stufenweise entfernen, mit Rueckfrage
```

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

## Laufende Prozesse prüfen

Ob der Sensor gerade arbeitet, beantwortet:

```bash
bash hailo_inventar.sh --status
```

Das zeigt laufende Projekt-Prozesse (`core.py`, `app.py`, Aufwärmlauf,
LoRa-/MQTT-Sender), wer `/dev/hailo0` und die Kamera belegt, die Auslastung des
Beschleunigers und ob ein Autostart-Eintrag existiert.

Die einzelnen Handgriffe, falls du sie direkt brauchst:

```bash
pgrep -af core/core.py            # laeuft die Zähl-Pipeline?
pgrep -af core/app.py             # laeuft die Steuer-App?
sudo fuser -v /dev/hailo0         # welcher Prozess belegt den Beschleuniger?
sudo fuser -v /dev/video0         # welcher Prozess belegt die Kamera?
hailortcli monitor                # Live-Auslastung (Strg+C beendet)
```

`/dev/hailo0` kann immer nur **ein** Prozess gleichzeitig benutzen. Wenn ein
Start mit einer Geraetefehlermeldung abbricht, laeuft meist noch eine alte
Instanz. Sauber beenden:

```bash
pkill -INT -f core/core.py        # SIGINT — core.py raeumt dann selbst auf
sleep 3; pgrep -af core/core.py   # leer = beendet
pkill -TERM -f core/core.py       # nur falls noch etwas haengt
```

SIGINT ist wichtig: nur darauf schreibt `core.py` seine CSV-Dateien und das
Bewegungsbild noch fertig. `kill -9` verliert die Daten des laufenden Laufs.

## Autostart beim Booten

Der Sensor startet **nicht** per systemd, sondern über einen
Desktop-Autostart-Eintrag. Grund: `core/app.py` ist eine Tkinter-Oberfläche und
die Pipeline endet in einem Videofenster — beides braucht eine laufende
Desktop-Sitzung. Ein systemd-Service startet zu früh, hat kein `DISPLAY` und
scheitert daran.

### Was beim Booten passiert

```
Autologin in die Desktop-Sitzung
        ↓
~/.config/autostart/visitorcounter.desktop   öffnet ein Terminal mit
        ↓
start_app.sh
        ↓  1. source setup_env.sh          venv aktivieren, PYTHONPATH setzen
        ↓  2. python utils/warmup.py        Aufwärmlauf: startet core.py
        ↓                                   nacheinander mit --input usb und
        ↓                                   mit dem zuletzt gewählten Input,
        ↓                                   wartet je bis Bilder fließen, und
        ↓                                   beendet sauber per SIGINT
        ↓  3. python core/app.py --autostart
        ↓
App startet die Zähl-Pipeline selbst
(core.py --input <app_settings.json>, mit roi_config.json)
```

Der Aufwärmlauf ist kein Selbstzweck: der allererste Hailo-Start nach dem
Booten dauert deutlich länger (Firmware laden, HEF initialisieren). `warmup.py`
nimmt diese Wartezeit vorweg, damit der eigentliche Zähllauf sofort steht. Er
läuft nur einmal pro Bootvorgang — gemerkt über die Boot-ID in
`.warmup_state`.

Welchen Input die App startet, steht in `app_settings.json` (zuletzt in Tab 1
gewählt), die Zählgeometrie in `roi_config.json`. Beide werden von der App
selbst geschrieben; der Autostart übernimmt sie unverändert.

### Einrichten

**1. Autologin aktivieren**

```bash
sudo raspi-config
```

→ `System Options` → `Boot / Auto Login` → **`Desktop Autologin`**.
Ohne Autologin bleibt der Pi am Anmeldebildschirm stehen und nichts startet.

**2. Vorher pruefen, dass der Ablauf von Hand funktioniert**

```bash
cd ~/visitorcounter
bash start_app.sh
```

Erst wenn das durchläuft, lohnt der Autostart-Eintrag — sonst suchst du den
Fehler später in einem Terminal, das beim Booten kurz aufblitzt und wieder weg
ist.

**3. Autostart-Eintrag anlegen**

```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/visitorcounter.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Besucherzähler
Comment=Startet die Personenzähl-App automatisch beim Hochfahren
Exec=lxterminal --working-directory=$HOME/visitorcounter -e bash -c "./start_app.sh; exec bash"
X-GNOME-Autostart-enabled=true
EOF
chmod +x ~/visitorcounter/start_app.sh
```

Das `$HOME` wird beim Schreiben der Datei aufgelöst — kontrollieren mit
`cat ~/.config/autostart/visitorcounter.desktop`.

Das `exec bash` am Ende hält das Terminal offen, wenn die App beendet wird oder
abstürzt. So bleibt die Fehlermeldung sichtbar, statt mit dem Fenster zu
verschwinden. Für den Dauerbetrieb ohne Bildschirm kann es entfallen.

**4. Neustart und Kontrolle**

```bash
sudo reboot
# nach dem Hochfahren:
bash ~/visitorcounter/hailo_inventar.sh --status
```

### Abschalten oder ändern

```bash
# vorübergehend abschalten
mv ~/.config/autostart/visitorcounter.desktop ~/.config/autostart/visitorcounter.desktop.aus

# ganz entfernen
rm ~/.config/autostart/visitorcounter.desktop
```

Soll beim Booten ein anderer Input verwendet werden, startest du die App
einmal von Hand, wählst ihn in Tab 1 und beendest sie — die Wahl landet in
`app_settings.json` und gilt ab dem nächsten Autostart.

### Wenn der Autostart nicht greift

| Symptom | Ursache / Pruefung |
|---|---|
| Nichts passiert, Anmeldebildschirm | Autologin nicht auf *Desktop* Autologin gesetzt |
| Terminal blitzt auf und schliesst | `exec bash` fehlt — Fehlermeldung nicht lesbar |
| `venv nicht gefunden` | `bash create_venv.sh` nie gelaufen, oder falscher Pfad in `Exec=` |
| `lxterminal: command not found` | `sudo apt install -y lxterminal` |
| App startet, Pipeline nicht | `roi_config.json` fehlt — erst in Tab 2 Zählgeometrie speichern |
| Geraetefehler beim Start | alte Instanz laeuft noch, siehe [Laufende Prozesse prüfen](#laufende-prozesse-prüfen) |

Auf Raspberry Pi OS "trixie" ist die Desktop-Sitzung standardmässig
`rpd-labwc` (Wayland/labwc statt LXDE). Der Autostart-Ordner
`~/.config/autostart/` wird dort weiterhin ausgewertet.

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
