# Implementierungs-Bestandsaufnahme (IST-Zustand)

Erzeugt durch Code-Audit am 04.08.2026, ergänzend zu `ARCHITEKTUR_IST.md`
(Commit `1a7f5819fc4565fa917ef8c2a1ad7b9e3c635c80`). Dieses Dokument dupliziert
**nicht** die Schichten-/Modul-Auflistung, Datenformate oder Delta-Logik aus
`ARCHITEKTUR_IST.md` — dort wird verwiesen, hier stehen ausschließlich
Implementierungs-, Betriebs- und Testfakten, die für Kapitel "Prototyping und
Demonstration" gebraucht werden. Gleiche Regel wie dort: jede Aussage ist an
Code/Config/Skript belegt; alles, was sich nur am realen Gerät oder im
separaten Server-Repo prüfen lässt, ist als
**NICHT VERIFIZIERT (nur am Gerät prüfbar)** markiert.

---

## 1. Hardware-Stückliste und physischer Aufbau

Es existiert **keine strukturierte Stückliste/BOM-Datei** (kein `*.csv`,
`*.xlsx` oder `*.md` mit Teil/Modell/Preis/Link) im Repository — durchsucht
wurde `docs/` vollständig nach "Stückliste", "BOM", "Teileliste",
"Einkaufsliste", "Preisliste". Die einzige gefundene `.xlsx`-Datei ist
`docs/abschlussarbeit/Zeitplan_bis_Abgabe.xlsx` (Zeitplan, keine Stückliste).

Kostenangaben existieren nur als **Fließtext in einem Entwurfskapitel**
(`docs/abschlussarbeit/ba_kapitel_3_4_5.md:172`: "Materialkosten pro Standort
auf unter 250 Euro"; Zeile 846: "Materialkosten pro Einheit liegen bei unter
250 Euro") — keine Einzelpositionen, keine Modellnummern mit Preisen, keine
Quellenlinks. Das ist ein **Entwurfstext für die Arbeit selbst**, keine
verifizierte technische Dokumentation — als Beleg für eine reale Stückliste
nicht geeignet.

| Komponente | Im Code? | In der Doku? | Fund |
|---|---|---|---|
| Board (Raspberry Pi 5) | nein (nur Kommentare "Pi 5", siehe `ARCHITEKTUR_IST.md` Abschnitt 1) | ja | `docs/projekt/HANDOFF.md:37`, `docs/einrichtung/GERAETE_EINRICHTUNG.md`, `docs/einrichtung/EINRICHTUNG_LA66.md:5` |
| KI-Beschleuniger (Hailo-8) | ja, als Bibliotheksimport (`hailo`, `hailo_apps`), Modell/Anbindung nicht im eigenen Code | ja | `docs/einrichtung/GERAETE_EINRICHTUNG.md` Abschnitt 1 nennt "Hailo-8 über M.2/PCIe (AI Kit)" und Firmware "4.23.0" — **Doku-Aussage, nicht aus Code verifizierbar** |
| Kamera (Typ/Modell) | nur generischer Pfad `--input usb`/`rpi`, kein Modellname | Platzhalter, nicht ausgefüllt | `docs/einrichtung/GERAETE_EINRICHTUNG.md:91`: **"Verbaut: USB-Kamera (✅ in Betrieb; genaues Modell hier nachtragen: ______)"** — das Feld ist im Dokument selbst leer gelassen |
| LoRa-Adapter (Dragino LA66) | ja, eindeutig (siehe `ARCHITEKTUR_IST.md` Abschnitt 1) | ja | `docs/einrichtung/EINRICHTUNG_LA66.md:1`: "Dragino LA66 USB LoRaWAN Adapter V2 (EU868)", Anbindung **USB** (Titel + `lora_send_loop.py` Portpfad `/dev/serial/by-id/...CP2102...`) |
| MQTT-Netzweg (physische Schnittstelle) | nein — Code kennt nur eine IP-Adresse, keine Schnittstellenwahl (siehe `ARCHITEKTUR_IST.md` Abschnitt 1, Beleg `mqtt_send_loop.py:17-19`) | nein | — |
| Stromversorgung (Solar/Akku) | nein | nur als **Argumentationstext im Entwurfskapitel** (`ba_kapitel_3_4_5.md:172`: "stabiler Solarbetrieb mit einer Pufferbatterie geringer Kapazität") | **Widerspruch/offener Punkt:** `docs/projekt/ToDo.md:372` listet "Stromausfallresistenz (Pufferung/USV) festlegen" ausdrücklich als **offenen, noch nicht entschiedenen Punkt** — die Solar-/Akku-Aussage im Entwurfskapitel ist zum jetzigen Codestand nicht als umgesetzt zu belegen |
| Gehäuse | nein | nein umgesetzt | `docs/projekt/ToDo.md:370`: "Sensorgehäuse auswählen/entwerfen (wetterfest, Außeneinsatz an den 17 Eingängen)" — als **offener Punkt**, nicht als vorhanden gelistet |
| Montage | nein | nein | keine Fundstelle in Code oder Doku |

### LA66-Anbindung im Detail (aus Code)

- Verbindungsart: **USB**, seriell über CP2102-USB-UART-Brücke
  (`lora_send_loop.py:54-56`, Portpfad enthält
  `usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller...`).
- Baudrate `9600` (`lora_send_loop.py:57`, `DEFAULT_BAUD`).
- Nutzergruppe für den Zugriff: `dialout` (laut Setup-Doku
  `docs/einrichtung/EINRICHTUNG_LA66.md`: `sudo usermod -aG dialout $USER`;
  **das ist eine Doku-Anweisung, keine Code-Prüfung**).

### Gerätebefehle zur eigenen Verifikation (Vorschlag, NICHT ausgeführt)

Auf dem realen Raspberry Pi, zur Klärung der `ARCHITEKTUR_IST.md`-Punkte
"RAM-Größe", "Hailo-Modell", "Kameramodell":

```bash
# Board-Modell (enthält i. d. R. auch die RAM-Variante im Modellnamen)
cat /proc/device-tree/model
# RAM-Größe direkt
free -h
# Hailo-Chip + Firmware
hailortcli fw-control identify
# Angeschlossene Kameras
ls /dev/video*
v4l2-ctl --list-devices        # falls v4l-utils installiert
# USB-Geräte inkl. Kamera-/LA66-Bezeichnung laut USB-Deskriptor
lsusb
# Serielle Schnittstellen (LA66)
ls -l /dev/serial/by-id/
```

---

## 2. Tatsächlich laufendes CV-Modell

- **Kein `.hef`-Modellpfad, kein Modellname im eigenen Code oder in
  `roi_config.json`/`config.py`.** Durchsucht: alle `*.py`-Dateien im
  Repo-Root auf `.hef`, `hef-path`, `hef_path`, `model`, `yolov8` — keine
  Treffer.
- Bestätigt durch `docs/einrichtung/EIGENES_REPOSITORY.md:22`, das als
  Kriterium für "eigenständiges Repo" explizit nennt: "keine `.hef`-Modelldateien,
  keine fest verdrahteten Videopfade" — d. h. die Modellwahl liegt bewusst
  außerhalb dieses Repos.
- Die Modelldatei wird stattdessen vom **Fremdcode** `GStreamerDetectionApp`
  (Paket `hailo_apps`) beim Pipeline-Aufbau bestimmt (siehe
  `ARCHITEKTUR_IST.md` Abschnitt 1/3). In einem während dieser Sitzung vom
  Nutzer bereitgestellten, realen Konsolen-Log eines tatsächlichen Laufs auf
  dem Sensor-Pi (nicht Teil dieses Repos, nur als Chat-Nachricht in dieser
  Sitzung sichtbar) tauchte die Zeile
  `hef-path=/usr/local/hailo/resources/models/hailo8/yolov8m.hef` auf sowie
  `Auto-detected Hailo architecture: hailo8` — das ist ein **beobachteter
  Laufzeitwert von einem realen Gerät, keine Aussage aus diesem Repo-Code**.
  **NICHT VERIFIZIERT im Repo** (nur am Gerät/durch erneuten Lauf mit Log
  reproduzierbar).
- Der Entwurfstext `docs/abschlussarbeit/ba_kapitel_3_4_5.md:366` behauptet
  ebenfalls "Das Element `hailonet` lädt die kompilierte Modelldatei
  (`yolov8m.hef`)" — deckt sich mit dem oben genannten Log, ist aber
  ebenfalls Doku-/Entwurfstext, kein Code-Beleg aus diesem Repo.

### Getrackte COCO-Klassen (exakt aus dem Code)

Default (`config.py:68`, `_DEFAULT_ROI_CONFIG["classes"]`), greift, wenn
`roi_config.json` keine `classes` liste oder die Datei fehlt:
```
person, bicycle, car, motorcycle, bus, truck
```
Tatsächlich aktiv ist `TRACKED_LABELS = set(_roi_config["classes"])`
(`config.py:103`) — abhängig vom Inhalt der jeweiligen `roi_config.json`
auf dem Gerät. Dieselben sechs Klassen sind zusätzlich hart als
`CANONICAL_CLASSES` in `lora_message.py` und `dekoder.py`-Pendant (Server,
nicht Teil dieses Repos) für die feste Byte-Reihenfolge im 18-Byte-Frame
verankert (`lora_message.py`, `CANONICAL_CLASSES`).

### Abgleich mit dem Ultralytics-Leitfaden "Steps of a CV Project"

Geprüft gegen `docs.ultralytics.com/de/guides/steps-of-a-cv-project`
(externe Quelle, im Entwurfskapitel `ba_kapitel_3_4_5.md:191` als
"Gestaltungsrichtlinien von Ultralytics für Computer-Vision-Projekte" (vgl.
Jocher et al. 2023) referenziert). Der Leitfaden beschreibt einen
vollständigen ML-Projektzyklus (Ziel definieren → Daten sammeln/annotieren →
Splitten/Augmentieren → Training → Evaluation/Feintuning → Test →
Deployment → Monitoring/Wartung). Abgleich Schritt für Schritt, was davon in
diesem Repo tatsächlich stattfindet:

| Schritt laut Leitfaden | In diesem Projekt umgesetzt? | Beleg |
|---|---|---|
| 1. Projektziel/Aufgabe festlegen, Modell für Aufgabe + Deployment-Umgebung wählen | **ja** — Aufgabe ist Objekterkennung, Modellwahl fiel auf ein **vortrainiertes** YOLOv8m statt Training von Grund auf (Transfer-/Direktnutzung, keine eigene Trainingsentscheidung im Sinne von "eigenes Modell trainiert") | Abschnitt 2 oben: kein `.hef`, kein Trainingscode; Klassen sind die **Standard-COCO-Klassen** (`person, bicycle, car, motorcycle, bus, truck`), kein eigenes Klassenschema |
| 2. Daten sammeln + annotieren | **nein, entfällt** — es wird kein eigener Trainingsdatensatz gesammelt/annotiert; das Modell nutzt die vortrainierten COCO-Gewichte | keine Annotationsdateien, kein Datensatz-Ordner, kein Annotationswerkzeug im Repo |
| 3. Datensplit + Augmentierung vor dem Training | **nein, entfällt** (kein Training) | — |
| 4. Modelltraining (Umgebung, GPU, Trainingsschleife) | **nein** — kein `train.py`, keine Epochen-/Trainings-Konfiguration, kein GPU-Trainingscode irgendwo im Repo | durchsucht: keine Treffer für `train`, `epochs` in `*.py` |
| 5. Evaluation/Feintuning (Precision/Recall/F1, Hyperparameter-Suche) | **nein, im Sinne klassischer ML-Metriken nicht umgesetzt** — es gibt **keine** Precision-/Recall-/F1-Berechnung im Code. Stattdessen ein **eigener, anwendungsspezifischer Parameter**: `min_confidence`/`COUNTING_MIN_CONFIDENCE`, ein Schwellwert-Filter auf die Erkennungskonfidenz vor dem Zählen | `config.py:126`, angewendet in `core.py` direkt nach `detection.get_confidence()` (siehe `ARCHITEKTUR_IST.md` Abschnitt 4); Herkunft/Zweck dokumentiert in `docs/projekt/ToDo.md:341-344` |
| 6. Modelltest auf ungesehenen Testdaten (Cross-Validation, Over-/Underfitting) | **nein, entfällt** (kein trainiertes/feingetuntes Modell) — stattdessen ein **eigenes, anderes Prüfkonzept**: manuelle Ground-Truth-Auszählung eines realen Videos zum Abgleich der End-to-End-**Zähl**genauigkeit (nicht der Modell-Erkennungsgüte selbst) | `docs/projekt/ToDo.md:340`: "Ground-Truth-Referenz anlegen ... als Vergleichsmaßstab" — laut demselben Dokument **als offener Punkt (`[ ]`) markiert, nicht abgeschlossen**; Werkzeug dafür vorbereitet: `tests/vergleich_app.py` |
| 7. Deployment (Modell in Zielformat exportieren: ONNX/TensorRT/CoreML) | **nicht in diesem Repo** — die Hailo-spezifische `.hef`-Kompilierung liegt außerhalb dieses Repos (siehe Abschnitt 2 oben); kein Export-Code (`onnx`, `tensorrt`, `coreml`) im Repo gefunden | durchsucht: keine Treffer in `*.py` |
| 8. Monitoring/Wartung/Dokumentation nach Deployment (Drift-Erkennung, regelmäßiges Neu-Training, Doku) | **teilweise** — kein automatisches Drift-Monitoring oder Neu-Training-Mechanismus im Code; **Dokumentation** dagegen umfangreich vorhanden (gesamter `docs/`-Baum, siehe `ARCHITEKTUR_IST.md`/`IMPLEMENTIERUNG_IST.md` selbst) | kein Retraining-/Monitoring-Code gefunden; `docs/` als Gegenbeleg für den Dokumentationsteil |

**Einordnung:** Der Ultralytics-Leitfaden beschreibt den Zyklus für ein
**eigenes, zu trainierendes** CV-Modell. Dieses Projekt **trainiert kein
eigenes Modell** — es setzt ein vortrainiertes YOLOv8m auf Hailo-8-Hardware
ein (Schritte 2-4 und 6-7 des Leitfadens entfallen dadurch strukturell,
nicht aus Nachlässigkeit). Übernommen wurden erkennbar die **Rahmen-
Prinzipien** (Schritt 1: Aufgaben-/Modellwahl bewusst getroffen und
begründet; sinngemäß Schritt 5/6: ein Schwellwert-Parameter zur
Qualitätskontrolle plus ein geplanter, aber noch offener Ground-Truth-
Abgleich; Schritt 8: Dokumentation). Das entspricht eher einer **angepassten
Anwendung der Leitgedanken auf ein Edge-Deployment-Szenario mit
vortrainiertem Modell** als einer wörtlichen Schritt-für-Schritt-Befolgung
des vollen Trainingszyklus — für die Arbeit ist diese Unterscheidung
(Trainings-Leitfaden vs. Deployment-mit-Fremdmodell-Realität) vermutlich
selbst ein dokumentierenswerter Punkt.

---

## 3. Pipeline- und Datenfluss-Referenz (für ein Diagramm aufbereitet)

Nummerierte Schrittfolge, Eigencode klar von Fremdcode (`hailo_apps`,
grau/kursiv markiert) getrennt. Vollständige Zeilenbelege bereits in
`ARCHITEKTUR_IST.md` Abschnitt 3 — hier nur die für ein Diagramm nötige,
knappe Fassung.

| # | Schritt | Eingang | Verarbeitung | Ausgang | Code |
|---|---|---|---|---|---|
| 0 | *Kamera → Rohframe* | USB-/Pi-Kamera-Signal | *GStreamer-Pipeline (Fremdcode: `hailo_apps.GStreamerDetectionApp`)*: Decodierung, Skalierung, Inferenz auf dem Hailo-Chip, Tracking (`hailotracker`) | Frame + Detections + Tracker-IDs im Buffer | *fremd* |
| 1 | Pro-Frame-Callback | GStreamer-Buffer | `core.py: app_callback()` liest Detections (`hailo.get_roi_from_buffer`), filtert nach `TRACKED_LABELS` und `COUNTING_MIN_CONFIDENCE` | gefilterte Detections je Frame | `core.py:191-284` |
| 2 | Track aktualisieren | gefilterte Detection + Position | `tracking.py: TrackingState.update_track()` legt Track an/aktualisiert ihn, vergibt `display_id` | aktualisierter Track-Zustand im Speicher | `tracking.py:97` |
| 3 | Flush (Timeout) | aktueller Frame-Index | `tracking.py: TrackingState.flush_stale()` entfernt Tracks ohne Sichtung seit `FRAMES_UNTIL_GONE=30` Frames | abgeschlossener Track | `tracking.py:198`, Wert `config.py:151` |
| 3b | Finalize (Programmende) | laufende Tracks | `tracking.py: TrackingState.finalize()` schließt alle verbleibenden Tracks ab | abgeschlossene Tracks | `tracking.py:215` |
| 4 | Zählentscheidung | abgeschlossener Track (Start-/Endposition) | `counting.py: build_counter()` → `LineCounter`/`RoiCounter`/`MultiRoiCounter`.`check_crossing()` je nach `COUNTING_MODE` | Richtungstext (z. B. `"A->B"`) + `is_transition`-Flag | `counting.py:118` ff. |
| 5a | Persistenz Zählereignis | Zählentscheidung | `logging_utils.log_count_event()` | Zeile in `zaehlung.csv` | `logging_utils.py:80` |
| 5b | Persistenz Track-Zusammenfassung | Track-Feature-Daten | `logging_utils.log_track_event_csv()` | Zeile in `ergebniss.csv` | `logging_utils.py:44` |
| 6 | Übertragung (unabhängiger, langsamerer Takt) | `zaehlung.csv` (Delta seit letztem Erfolg) | `lora_send_loop.py`/`mqtt_send_loop.py` bauen Frame/JSON, senden, bestätigen | LoRaWAN-Uplink (18 Byte) bzw. MQTT-Publish (JSON) | siehe `ARCHITEKTUR_IST.md` Abschnitt 6 |

**Fremdcode-Grenze:** Schritt 0 (komplette Bild-/Inferenz-/Tracker-Pipeline
bis einschließlich `hailotracker`) ist vollständig `hailo_apps`
(`GStreamerDetectionApp`, importiert in `core.py:22`). Alles ab Schritt 1
(`app_callback()` und alles Nachgelagerte) ist Eigencode dieses Repos. Die
einzige Ausnahme innerhalb der Fremdcode-Grenze: `core.py` konfiguriert das
Fremd-Pipeline-Element `hailo_tracker` per `set_property("class-id", -1)`
nach dessen Erzeugung (`core.py:354-356`) — eine Parametrisierung des
Fremdelements, kein eigener Pipeline-Code.

### Abgleich mit dem offiziellen Hailo-Entwicklerguide

Geprüft gegen `hailo-ai/hailo-apps`, `doc/developer_guide/app_development.md`
(externes Dokument, nicht Teil dieses Repos — Abgleich per Einzelbeleg im
eigenen Code, keine wörtliche Zitatprüfung des Guide-Originaltexts).

| Vorgabe des Guides | Umsetzung | Beleg |
|---|---|---|
| "Development Path 1" (Callback-basiert) statt eigener `GStreamerApp`-Unterklasse mit `get_pipeline_string()` | `core.py` nutzt die vorgefertigte Pipeline-Klasse `GStreamerDetectionApp`, keine eigene Pipeline-Topologie | `core.py:22` |
| Eigene Datenklasse von `app_callback_class` erben, um Zustand über Frames zu halten | `TrackingState` erbt exakt davon | `tracking.py:17,31` |
| Callback muss nicht-blockierend sein, lange Aufgaben auslagern | LoRa-/MQTT-Versand laufen als **eigene Subprozesse** (`subprocess.Popen`), nicht im Callback | `tabs/lora_controls.py`, `tabs/mqtt_controls.py` |
| Metadaten über `hailo.get_roi_from_buffer()` lesen | identisch umgesetzt | `core.py:228` |
| Callback gibt `Gst.PadProbeReturn.OK` zurück | identisch | `core.py:317` |
| `gi.require_version('Gst', '1.0')` vor dem GStreamer-Import | identisch | `core.py:14-16` |
| Pipeline-Architektur-Patterns (Single Network/Wrapped/Cascaded/Parallel/Tiled) als Entscheidungsgrundlage | explizit referenziert und mit Begründung übernommen ("Single Network", erweitert um `hailotracker`) | `docs/abschlussarbeit/Entwurf_Systemarchitektur_Sensor.md`, Abschnitt B, mit Quellenangabe auf denselben Guide |

**Über die reine Callback-Empfehlung hinausgehend (bewusst, mit Quelle
belegt, keine Abweichung vom Grundprinzip):** Der Guide favorisiert
Callback-Logik gegenüber eigenen GStreamer-Elementen für die Anwendungslogik.
`core.py` greift an zwei Stellen zusätzlich **nach** der Pipeline-Erzeugung
direkt auf das Pipeline-Objekt zu (per `pipeline.get_by_name(...)`, nicht
über `get_pipeline_string()`):
- Umkonfiguration von `hailo_tracker` (`class-id=-1`, `core.py:354-356`,
  mit Quellenangabe auf einen Hailo-Community-Forumsbeitrag im Kommentar).
- Umbiegen des `hailo_display`-Sinks auf `fakesink` + optionaler
  Mitschnitt-`tee` (`core.py:377-386`, ebenfalls mit
  Community-Forums-Quellenangabe im Kommentar).

Beide Eingriffe sind Parametrisierungen/Umverdrahtungen bestehender
Fremdelemente nach deren Erzeugung, kein eigener Pipeline-String — insofern
kein Widerspruch zum "Path 1"-Prinzip, aber auch kein rein deklaratives
Callback-only-Vorgehen.

**Ein nicht abschließend geklärter Punkt:** Eine automatisierte
Zusammenfassung des externen Guide-Textes (nicht wörtliches Zitat) enthielt
den Hinweis, die Frame-Zählung laufe automatisch im Framework und solle
nicht manuell inkrementiert werden. `core.py:196` ruft jedoch explizit
`user_data.increment()` auf `TrackingState` auf (geerbt von
`app_callback_class`, `tracking.py:31`). Dieses Muster entspricht dem in den
offiziellen Hailo-Beispielskripten (z. B. `detection.py` in
`hailo-rpi5-examples`) durchgängig verwendeten Boilerplate — die oben
genannte Zusammenfassung ist daher wahrscheinlich ungenau, wurde aber
**nicht am Original-Markdown des Guides wortwörtlich gegengeprüft**.
**NICHT VERIFIZIERT (nur durch erneutes Lesen des Original-Guide-Texts
klärbar).**

---

## 4. Bedienoberfläche — Bedienablauf und Ansichten

Seiten in der Reihenfolge der Sidebar-Navigation (`app.py`, `PAGE_NAMES`,
Modulzuordnung siehe `ARCHITEKTUR_IST.md` Abschnitt 2):

### Seite 1 — Input (`tabs/input_tab.py`)
- **Sieht:** drei Radiobuttons ("USB-Kamera", "Raspberry-Pi-Kamera",
  "Videodatei"), bei "Videodatei" zusätzlich ein Dateiauswahl-Knopf und der
  gewählte Pfad, eine Statuszeile ("Input gesetzt: ...").
- **Kann:** Input-Quelle wählen; bei "Videodatei" eine Datei über den
  System-Dateidialog auswählen (`_choose_file()`, `tabs/input_tab.py`).

### Seite 2 — Konfiguration (`tabs/config_tab.py` + eingebettetes `roi_config_app.RoiConfigApp`)
- **Sieht:** Knopf "Frame laden", Knopf "Aktuelle Konfiguration laden",
  eingebetteten Canvas mit dem zuletzt geladenen Kamerabild, rechts eine
  Bedienspalte mit Moduswahl (Linie/Fläche/Mehrere Flächen), Klassen-Checkboxen,
  Konfidenz-Feld, IN/OUT-Checkboxen je Fläche (nur `multi_roi`), Speichern-Knopf.
- **Kann:** ein Referenzbild laden (nutzt den Input von Seite 1), per
  Mausklick Zähllinie/-fläche(n) setzen, Klassen wählen, Mindest-Konfidenz
  einstellen, bei `multi_roi` je Fläche IN/OUT markieren, speichern nach
  `roi_config.json`. Die zuletzt gespeicherte Konfiguration wird beim
  App-Start automatisch (still) in den Editor geladen
  (`tabs/config_tab.py`, `_build_config_tab()`, Aufruf
  `self.roi_config_widget.load_config(silent=True)`).

### Seite 3 — Start (`tabs/start_tab.py` + `recording_controls.py`/`lora_controls.py`/`mqtt_controls.py`/`pipeline_control.py`)
- **Sieht:** Mitschnitt-Checkbox mit Zielordner/Bitrate/FPS/Segmentlänge,
  Live-Vorschau-Checkbox, LoRa-Block (Checkbox, Intervall, Sensor-ID,
  Struktur-Hinweisbox), MQTT-Block (Checkbox, Broker/Port, Intervall,
  Sensor-ID, "Vollständige Übergänge senden"-Checkbox), optionales
  Zeitlimit-Feld, Start-/Stopp-Knöpfe, Statuszeile.
- **Kann:** alle genannten Optionen einstellen und die Pipeline starten
  (`_start_pipeline()`, `tabs/pipeline_control.py:24`) bzw. stoppen.

### Seite 4 — Live-Auswertung (`tabs/output_tab.py`)
- **Sieht:** Live-Konsolenausgabe (Textbox, grüner Text auf dunklem Grund,
  zeigt `core.py`-Ausgabe sowie `[LoRa]`/`[MQTT]`/`[Aufwärmlauf]`-präfixierte
  Zeilen), darunter aktuelle Zählerstände aus `zaehlung.csv` (nur echte
  Übergänge, `is_transition=True`).
- **Kann:** nur beobachten (kein Bedienelement außer der Sidebar-Navigation).

### Seite 5 — Auto-Konfiguration (`tabs/autoconfig_tab.py`)
- **Nur sichtbar, wenn `config.SHOW_AUTO_CONFIG = True`** (aktuell `False`,
  siehe `ARCHITEKTUR_IST.md` Abschnitt 2) — im derzeitigen Auslieferungsstand
  für den Nutzer **nicht erreichbar**.

### Klick-Ablauf einer Erstinbetriebnahme (aus dem Code abgeleitet, kein separates Ablaufdiagramm im Repo gefunden)

1. Seite 1: Input-Quelle wählen (Standard bereits "USB-Kamera" vorbelegt,
   `tabs/settings_store.py` DEFAULTS `"input_mode": "usb"`).
2. Seite 2: "Frame laden" klicken → Referenzbild wird aufgenommen
   (`tabs/config_tab.py: _load_config_frame()`); Zählmodus wählen, Geometrie
   per Mausklick setzen, Klassen/Konfidenz einstellen, "Speichern".
3. Seite 3: gewünschte Übertragungswege (LoRa/MQTT) und Mitschnitt
   einstellen, "▶ Pipeline starten" (`_start_pipeline()`).
4. App wechselt automatisch zu Seite 4 (`tabs/pipeline_control.py`, letzte
   Zeile von `_start_pipeline()`: `self._show_page("4. Live-Auswertung")`) —
   Live-Konsole und Zählerstände live mitverfolgen.

### Für die Arbeit sinnvolle Screenshot-Ansichten (nur benannt, nicht erzeugt)

- Seite 1 (Input-Auswahl) — zeigt den Einstieg ohne Kommandozeile.
- Seite 2 mit geladenem Referenzbild und gesetzter `multi_roi`-Geometrie
  inkl. IN/OUT-Checkboxen — zentrale Konfigurationsansicht.
- Seite 3 mit aktivierten LoRa- und MQTT-Blöcken (zeigt die
  Struktur-Hinweisbox mit der Byte-Tabelle).
- Seite 4 während eines laufenden Zähllaufs (Live-Konsole + Zählerstände).
- Der Umschalt-Knopf für Hell-/Dunkel-Design (Sidebar oben rechts),
  idealerweise Vorher/Nachher.

---

## 5. Datenspeicherung und Übertragung — Betriebssicht

Formate/Felder: siehe `ARCHITEKTUR_IST.md` Abschnitt 6, hier ausschließlich
Betriebsstatus.

### LoRa — Betriebsstatus

- **Keine TODO/FIXME/"experimentell"-Marker im Code selbst** (durchsucht:
  `lora_send_loop.py`, `lora_message.py`, `tabs/lora_controls.py`).
- Betriebsstatus ist in `docs/projekt/ToDo.md:78-80` dokumentiert:
  **"Status: Code funktioniert, Funkstrecke am aktuellen Standort nicht."**
  Ursache laut selbem Dokument: unzureichender Empfang beim Gateway
  (Join-Accept-Downlink kommt nicht an), keine Software-Ursache.
- Dazu passend beobachtete Laufzeit-Ausgabe (vom Nutzer in dieser Sitzung
  geteilt, nicht Teil des Repos): `ACHTUNG: LA66 ist NICHT angemeldet
  (NJS=0)` — diese Meldung selbst stammt aus Code
  (`lora_send_loop.py:415`, Text "ACHTUNG: LA66 ist NICHT angemeldet
  (NJS=0)..."), ihr tatsächliches Auftreten am Gerät ist aber ein
  Laufzeitzustand, kein statischer Code-Fakt.

### MQTT — Betriebsstatus

- **Keine TODO/FIXME/"experimentell"-Marker im Code** (durchsucht:
  `mqtt_send_loop.py`, `uebergangs_payload.py`, `konfig_payload.py`,
  `tabs/mqtt_controls.py`).
- Laut `docs/projekt/ToDo.md:162-164`: **"Status: erfolgreich in Betrieb
  genommen."**
- Ergänzung aus dieser Sitzung (nicht in `ARCHITEKTUR_IST.md`, da nach dessen
  Erstellung gefunden und behoben): ein serverseitiger Fehler
  (`stadtwerke-server/datenbank.py`, außerhalb dieses Repos) verhinderte
  zeitweise die Speicherung eingehender MQTT-Nachrichten, weil `in_field`
  seit der Umstellung auf eine Liste (siehe `ARCHITEKTUR_IST.md` Abschnitt 4)
  nicht mehr direkt als SQLite-Textspalte bindbar war. Der sensor-seitige
  Code in diesem Repo war davon nicht betroffen; behoben wurde ausschließlich
  im Server-Repo. Siehe `docs/projekt/ToDo.md` (Eintrag "MQTT sendete seit
  der IN/OUT-je-Fläche-Umstellung nichts mehr an").

### Server-Gegenstelle als Schnittstelle (nur aus Sensor-Code ableitbar, kein Zugriff auf Server-Repo nötig)

- **Topic:** `STANDARD_TOPIC = "zaehlsensor/{sensor_id}/zaehlwerte"`
  (`mqtt_send_loop.py:56`), `{sensor_id}` wird durch die konkrete
  Sensor-ID ersetzt (`.format(sensor_id=args.sensor_id)`,
  `mqtt_send_loop.py:133`).
- **Port:** Default `1883` (`STANDARD_PORT`, `mqtt_send_loop.py:55`),
  App-seitiger Vorgabewert ebenfalls `"1883"`
  (`tabs/settings_store.py` DEFAULTS).
- **Broker-Erwartung:** Standardmäßig `localhost`
  (`STANDARD_BROKER`, `mqtt_send_loop.py:54`) beim eigenständigen
  Skriptaufruf; App-seitiger Vorgabewert `"192.168.0.50"`
  (`tabs/settings_store.py` DEFAULTS) — die feste IP-Adresse des
  Server-Pi laut Kommentar `tabs/mqtt_controls.py:27-28`.
- **Payload-Erwartung (drei mögliche Formen, je nach Aufrufmodus):**
  1. `--uebergaenge` (Standard in der App-UI): JSON-Objekt der vollen
     Übergangsmatrix (Format 3), direkt als MQTT-Payload
     (`mqtt_send_loop.py: senden_json()`, `uebergangs_payload.py:169-224`).
  2. `--live-counts`: JSON-Hülle `{"payload": "<hex>", "gesendet_am": "..."}`
     um den 18-Byte-Frame, oder roher Hex-Text mit `--roh`
     (`mqtt_send_loop.py: senden()`, Zeilen 65-89).
  3. Ohne beide Flags: statischer Test-Frame (`STANDARD_TESTFRAME`,
     `mqtt_send_loop.py:58`).
- **QoS:** `qos=1` für beide Sendearten (`mqtt_send_loop.py:87,101`) —
  Broker bestätigt den Empfang, bevor der Sender den Zählstand als
  gesendet vermerkt (siehe Delta-Logik, `ARCHITEKTUR_IST.md` Abschnitt 6).

---

## 6. Testung und Diagnose

### Vollständige Auflistung `tests/`

| Datei | Art | Prüft |
|---|---|---|
| `tests/kamera/camera_test.py` | manuelles Diagnoseskript | Kamera-Zugriff/Auflösung, unabhängig von Hailo/`core/` (laut Docstring) |
| `tests/lora_hardware/la66_probe.py` | manuelles Diagnoseskript | LA66-Erreichbarkeit über AT-Befehle, Portsuche |
| `tests/lora_hardware/lora_hardware_probe.py` | manuelles Diagnoseskript | **Sonel LORA-S1** — historische Sondierung, laut Docstring, weil das Gerät laut Herstellerdoku "kein offen dokumentierter LoRaWAN-USB-Adapter" ist |
| `tests/lora_hardware/lora_send_loop_STAND_vor_integration.py` | manuelles Skript, kein Test | **alter, nicht mehr produktiver Stand** von `lora_send_loop.py` (fester Test-Frame, kein `--live-counts`) — laut `tests/README.md` nur zur Unterscheidung erhalten |
| `tests/lora_hardware/lora_transmitter.py` | Modul (kein Test) | **historische** Frame-Serialisierung, laut `tests/README.md` durch `lora_message.py` abgelöst |
| `tests/lora_hardware/test_lora_transmitter.py` | **automatisierter Test** (`unittest`, `def test_...`, `unittest.main()`) | testet **`lora_transmitter.py`** (siehe oben — das historische, nicht mehr produktive Modul), NICHT das aktuell produktive `lora_message.py` |
| `tests/vergleich_app.py` | manuelles Auswertungswerkzeug (GUI) | gleicht `zaehlung.csv` und `ergebniss.csv` eines Laborlaufs visuell gegen `roi_config.json` ab |

`tests/lora_hardware/README.md` und `tests/README.md` bestätigen diese
Einordnung explizit (`tests/README.md`: "Eigenständige Skripte, die **nicht**
Teil der laufenden Anwendung sind", Abschnitt "⚠️ Nicht verwechseln" nennt
`lora_send_loop_STAND_vor_integration.py` und `lora_transmitter.py`
ausdrücklich als abgelöst).

### Automatisierte Tests / Abdeckung

- **Einzige Datei mit automatisierten Tests im gesamten Repo:**
  `tests/lora_hardware/test_lora_transmitter.py` (`unittest`,
  `TestCase`-Klassen `TestEncodeDecodeRoundTrip`, `TestPayloadSizeBudget`,
  `TestLoRaReporter`, `TestBuildTransport`).
- **Diese Tests decken nicht die aktuell aktiven Module ab** — sie testen
  `lora_transmitter.py` (historisch, siehe oben), nicht `lora_message.py`
  oder `lora_send_loop.py`.
- **Kernmodule ohne jeden automatisierten Test** (durchsucht: kein
  `test_*.py`/`*_test.py` mit `def test_` importiert diese Module):
  `counting.py` (Zähllogik: `LineCounter`, `RoiCounter`, `MultiRoiCounter`,
  Geometrie-Helfer), `tracking.py`, `lora_message.py`,
  `uebergangs_payload.py`, `csv_utils.py`, `config.py`, alle `tabs/*.py`,
  `app.py`, `roi_config_app.py`.
- Es existiert **kein** `pytest.ini`/`pyproject.toml`/`tox.ini` mit
  Testkonfiguration, kein CI-Workflow-Verzeichnis (`.github/workflows/`
  nicht vorhanden — geprüft).

### Dokumentierte manuelle/Feld-Tests und Testprotokolle in `docs/`

- `docs/entwicklung/Datenfluss_Verifikation_20260715.md` — Prüfung eines
  echten Laufs (15.07.2026, 12:27–12:31) gegen die erzeugten Ausgabedateien:
  Schema-Korrektheit, Track-Konsistenz (64 ↔ 64 zwischen `ergebniss.csv` und
  `zaehlung.csv`), FLUSH/FINALIZE-Verteilung (60/4), Klassenfilter. Reine
  **Funktionsprüfung** ("läuft, erzeugt korrekte Dateien"), keine
  Genauigkeits-/FPS-Messung.
- `docs/abschlussarbeit/Echter_Testlauf_20260715_Zuordnung.md` — Zuordnung
  echter Artefakte eines Laufs (15.07.2026, 10:36–10:38, 28 Tracks) zu einem
  Datenflussdiagramm. Ebenfalls **Funktionsprüfung**, keine Metrik.
- `docs/abschlussarbeit/Datenartefakte_Beispiel_Potsdam_Berlin.md` — laut
  Dateiname Beispiel-Datenartefakte für den Mehrere-Flächen-Modus
  (Inhalt hier nicht im Detail geprüft, da für Testung/Diagnose nicht
  zentral).
- **Labortest mit Kennzahlen** laut `docs/projekt/ToDo.md`
  (Abschnitt "Tests", Eintrag "Labortest durchgeführt — erfolgreich
  (20.–22.07.)"): "228 Datensätze, 34 gezählte Übergänge". Das ist eine
  **Mengenangabe aus einem realen Lauf**, keine Genauigkeits-/FPS-Metrik im
  Sinne einer Evaluation — die eigentliche Auswertung (Soll-/Ist-Abgleich)
  wird laut demselben Dokument über `tests/vergleich_app.py` unterstützt,
  ihr Ergebnis ist in `docs/projekt/ToDo.md` als **"in Arbeit"** vermerkt
  (nicht Teil dieses Audits, gehört in die Evaluation).
- **Benchmark-Mitschnitt** (`recording.py`): laut Docstring
  (`recording.py:1-9`) "NUR FÜR BENCHMARKLÄUFE — NICHT FÜR DEN
  NORMALBETRIEB", dient als "Referenz (Ground Truth), um die
  Zählgenauigkeit unter Laborbedingungen zu messen". Standardmäßig
  deaktiviert (`config.py:184-185`, `RECORDING_ENABLED` Default `False`).
  Regeln dazu in `docs/entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md`.
  Ob/wie oft der Mitschnitt tatsächlich zur Genauigkeitsmessung genutzt
  wurde, ist **NICHT VERIFIZIERT (nur am Gerät/in den Aufnahmen prüfbar)** —
  Aufnahmen selbst sind laut `.gitignore` nicht Teil des Repos.

### Klare Trennung Funktionstest vs. Metrik-Messung

- **Funktionstests (im Repo dokumentiert):** die beiden 15.07.-Protokolle
  oben, die Datenmengen-Angabe des Labortests (228/34), der einzige
  `unittest`-Testsatz (deckt aber ein abgelöstes Modul ab).
- **Metrik-Messungen (FPS, Erkennungsgenauigkeit, mAP):** kommen in diesem
  Repo **nicht als Messwerte vor** — Zahlen wie "30 FPS", "26 TOPS",
  "3-5 FPS auf der CPU" stehen ausschließlich im Entwurfskapitel
  `docs/abschlussarbeit/ba_kapitel_3_4_5.md` als **Literatur-/Herstellerangaben
  bzw. Argumentation**, nicht als im Repo gemessene/protokollierte
  Prototyp-Werte. Eine eigene FPS-/Genauigkeitsmessung des Prototyps ist im
  Code/in `docs/` **nicht** belegt — gehört, wie vom Auftrag vorgegeben, in
  die Evaluation und wird hier nicht bewertet.

---

## 7. Reproduzierbarkeit / Setup

Exakte Reihenfolge aus `create_venv.sh` und `setup_env.sh` (beide vollständig
gelesen):

1. **Hailo-/System-spezifisch, außerhalb dieses Repos** (laut
   `requirements.txt`-Kopfkommentar und `docs/einrichtung/GERAETE_EINRICHTUNG.md`,
   nicht durch `create_venv.sh` automatisiert): Raspberry Pi OS Bookworm
   64-bit, `sudo apt install -y hailo-all` (HailoRT-Treiber, Firmware,
   GStreamer-Plugins), PCIe-Gen-3-Aktivierung — **diese Schritte prüft/führt
   `create_venv.sh` selbst nicht aus**, sie werden vorausgesetzt.
2. `bash create_venv.sh` (Repo-Root):
   a. legt `venv_visitorcounter` an mit
      `python3 -m venv --system-site-packages "$VENV_DIR"` — **`--system-site-packages`
      ist laut Kommentar zwingend**, weil `hailo` (HailoRT-Bindings) und `gi`
      (PyGObject/GStreamer) Systempakete sind, nicht per `pip` installierbar
      (`create_venv.sh`, Kommentar direkt über dem Aufruf).
   b. `python -m pip install --upgrade pip`
   c. `python -m pip install -r requirements.txt` — pip-Pakete, siehe
      `ARCHITEKTUR_IST.md` Abschnitt 9 für die vollständige Liste
      (`numpy<2.0.0`, `opencv-python`, `Pillow`, `customtkinter`,
      `scikit-learn`, `scipy`).
   d. `hailo_apps` installieren via
      `pip install "hailo-apps @ git+https://github.com/hailo-ai/hailo-apps-infra.git@${HAILO_APPS_VERSION}"`,
      Standard-Tag **`25.7.0`** (`create_venv.sh`,
      `HAILO_APPS_VERSION="${HAILO_APPS_VERSION:-25.7.0}"`). Bei
      Fehlschlag (Netzwerk/SSH-Key): Rückfall über eine `.pth`-Datei, die auf
      eine vorhandene `hailo_apps`-Installation (z. B. aus
      `hailo-rpi5-examples`) verweist.
   e. Selbsttest: importiert `numpy, cv2, PIL, customtkinter, sklearn, scipy,
      gi, hailo, hailo_apps` und meldet je Paket `OK`/`FEHLT`
      (`create_venv.sh`, letzter Abschnitt "Selbsttest der Importe").
3. `source setup_env.sh`:
   a. Kernel-Kompatibilitätsprüfung: bekannte inkompatible Kernel-Versionen
      `6.12.21`–`6.12.25` werden per Warnung gemeldet (`setup_env.sh`,
      `INVALID_KERNELS`-Liste), falls `uname -a` "Linux raspberrypi" enthält.
   b. Setzt `PYTHONPATH` auf den Projektordner.
   c. Aktiviert die venv (Suchreihenfolge: `VENV_NAME`-Ordner im Projekt,
      im Elternverzeichnis, in `$HOME`; Default-`VENV_NAME` =
      `venv_visitorcounter`, siehe `setup_env.sh:18`).
4. `python app.py` (manueller Start) **oder** `bash start_app.sh`
   (Autostart-Kette, siehe `ARCHITEKTUR_IST.md` Abschnitt 7).

### pip vs. apt/System — Abgrenzung

| Abhängigkeit | Quelle | Beleg |
|---|---|---|
| `numpy`, `opencv-python`, `Pillow`, `customtkinter`, `scikit-learn`, `scipy` | `pip` (`requirements.txt`) | `requirements.txt` |
| `hailo` (HailoRT-Bindings), `gi`/PyGObject/GStreamer | **System-Pakete (`apt`)**, kommen mit der Hailo-Installation | `requirements.txt`-Kopfkommentar: "nicht per pip installierbar" |
| `hailo_apps` | `pip`, aber **aus Git-Quelle**, nicht PyPI | `create_venv.sh`, Tag `25.7.0` |
| `pyserial` | laut `docs/einrichtung/EINRICHTUNG_LA66.md` separat: `pip install pyserial --break-system-packages` — **nicht in `requirements.txt` gelistet** | siehe Abschnitt 8, Widerspruch |

---

## 8. Ergänzende offene Punkte (neu, nicht in `ARCHITEKTUR_IST.md`)

- **`pyserial` fehlt in `requirements.txt`.** `lora_send_loop.py` importiert
  `serial` (`import serial`, `lora_send_loop.py:44`) und ist damit für den
  LoRa-Versand zwingend erforderlich, taucht aber in `requirements.txt`
  nicht auf — dort nur der Kommentarblock zu Hailo/`gi`. Die einzige
  Installationsanweisung dafür steht in
  `docs/einrichtung/EINRICHTUNG_LA66.md` (`pip install pyserial
  --break-system-packages`) und widerspricht damit dem venv-basierten
  Ansatz von `create_venv.sh` (`--break-system-packages` ist explizit ein
  Workaround für System-Python OHNE venv). Wer nur `create_venv.sh` +
  `requirements.txt` befolgt, bekommt kein `pyserial` und `lora_send_loop.py`
  scheitert beim Import.
- **Einziger automatisierter Test deckt ein abgelöstes Modul ab**
  (`tests/lora_hardware/test_lora_transmitter.py` testet
  `lora_transmitter.py`, nicht `lora_message.py` — siehe Abschnitt 6). Für
  eine Aussage wie "die Zähl-/Payload-Logik ist getestet" in der Arbeit wäre
  das **nicht** als Beleg für den aktuell produktiven Code verwendbar.
- **Kein CI/Workflow-Verzeichnis** (`.github/workflows/` nicht vorhanden) —
  Tests laufen ausschließlich manuell (`python tests/.../test_lora_transmitter.py`
  oder `python -m unittest`), keine automatisierte Ausführung bei Commits
  verifizierbar.
- **Kameramodell-Feld im Setup-Protokoll bewusst leer** (`docs/einrichtung/GERAETE_EINRICHTUNG.md:91`,
  Platzhalter `______`) — im Gegensatz zu anderen Positionen in derselben
  Tabelle (die mit ✅ bestätigt sind), ist dieses Feld erkennbar nie
  nachgetragen worden.
- **Solar-/Akkubetrieb ist Argumentation, keine Implementierung.** Der
  Entwurfstext (`ba_kapitel_3_4_5.md:172`) beschreibt einen funktionierenden
  Solarbetrieb im Präsens ("Dies ermöglicht einen stabilen Solarbetrieb"),
  während `docs/projekt/ToDo.md:372` Stromausfallresistenz/Pufferung
  ausdrücklich als noch **zu klärenden, offenen Punkt** führt — dieser
  Widerspruch zwischen Entwurfstext und Implementierungs-ToDo sollte vor
  Übernahme in die Arbeit aufgelöst werden (entweder Formulierung im
  Kapiteltext auf "vorgesehen"/"geplant" abschwächen, oder Umsetzung
  nachholen).

---

## Zu verifizierende Punkte — Kurzliste

Vor Übernahme in die Arbeit an realem Gerät bzw. im Server-Repo zu prüfen:

1. **RAM-Größe** des eingesetzten Raspberry Pi 5 (`free -h` am Gerät) — im
   Code nicht vorhanden, nur als Doku-Behauptung "8 GB".
2. **Exaktes Hailo-Chipmodell und Firmware-Version** (`hailortcli fw-control
   identify`) — im eigenen Code nicht festgelegt.
3. **Geladenes `.hef`-Modell** (z. B. via Log-Zeile `hef-path=...` bei einem
   erneuten Lauf, oder `hailortcli` während laufender Pipeline) — nur aus
   einem einmalig gesehenen Chat-Log bekannt (`yolov8m.hef`), nicht aus
   diesem Repo reproduzierbar belegt.
4. **Kameramodell** — im Setup-Protokoll selbst als offen markiert.
5. **Tatsächlich installierte `pyserial`-Version/-Quelle** auf den
   Produktivgeräten, da nicht in `requirements.txt` — prüfen, ob alle Geräte
   sie konsistent (venv vs. `--break-system-packages`) installiert haben.
6. **Ob und wie oft der Benchmark-Mitschnitt (`recording.py`) tatsächlich für
   eine Genauigkeitsmessung genutzt wurde** — Aufnahmen sind nicht im Repo
   (`.gitignore`), nur am Gerät/in vorhandenen Aufnahme-Ordnern prüfbar.
7. **Serverseitiges Verhalten** (Datenbankschema, Dashboard-Darstellung,
   ob der in dieser Sitzung gefundene und dort gefixte `in_field`-Bug bereits
   auf den Server-Pi ausgerollt wurde) — separates Repo, hier nicht auditiert.
8. **Ob der in `docs/einrichtung/GERAETE_EINRICHTUNG.md` beschriebene
   Desktop-Autostart-Eintrag** auf dem/den Produktivgerät(en) tatsächlich in
   der dokumentierten Form existiert — die `.desktop`-Datei liegt nicht im
   Repo (siehe `ARCHITEKTUR_IST.md` Abschnitt 8).
9. **Genaue Aussage des Hailo-Entwicklerguides zur Frame-Zählung** (Abschnitt
   3, "Abgleich mit dem offiziellen Hailo-Entwicklerguide") — am
   Original-Markdown (`hailo-ai/hailo-apps`,
   `doc/developer_guide/app_development.md`) wortwörtlich gegenprüfen, ob
   `user_data.increment()` (`core.py:196`) tatsächlich dem empfohlenen Muster
   entspricht oder einer veralteten Praxis folgt.
