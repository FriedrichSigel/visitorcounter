# Architektur-Bestandsaufnahme (IST-Zustand)

Erzeugt durch Code-Audit am 04.08.2026. Quelle ausschließlich der tatsächliche
Code, Konfigurations- und Skriptdateien in diesem Repository (`visitorcounter`,
Commit `1a7f5819fc4565fa917ef8c2a1ad7b9e3c635c80`, siehe Abschnitt 9). Wo eine
Aussage nicht aus dem Code hervorgeht, ist sie ausdrücklich als
**NICHT VERIFIZIERT** markiert. Dieses Dokument beschreibt den Sensor
(`visitorcounter`); das separate Server-Repository (`stadtwerke-server`) ist
nicht Teil dieses Repos und wird nur dort erwähnt, wo der Sensor-Code
unmittelbar mit ihm interagiert (Netzwerk-Schnittstelle).

---

## 1. Hardware (soweit aus Code/Config/Skripten ableitbar)

- **Board:** Im Code an mehreren Stellen als "Pi 5" referenziert, aber nur in
  Kommentaren, nicht als geprüfte Laufzeitbedingung:
  - `recording.py:46,162`: "Der Pi 5 hat KEINEN Hardware-H.264-Encoder mehr"
    (Begründung für Software-Encoding in der Mitschnittfunktion).
  - `config.py:200`: "Der Pi 5 encodiert in Software".
  - **RAM-Größe:** kommt im Code/in Konfigurationsdateien **nicht** vor.
    **NICHT VERIFIZIERT** (im Code) — die Dokumentation (`docs/projekt/HANDOFF.md:37`,
    `docs/projekt/Architektur.md:17`) nennt "Raspberry Pi 5, 8 GB", das ist aber
    eine Doku-Aussage, kein Code-Fakt.
- **KI-Beschleuniger:** Hailo-Produktreihe, angesprochen über die Fremdbibliothek
  `hailo` und `hailo_apps` (`core.py:19,21,22`: `import hailo`,
  `from hailo_apps.hailo_app_python...`). Das konkrete Chip-Modell (z. B.
  Hailo-8 vs. Hailo-8L) wird **nicht** im eigenen Code festgelegt, sondern von
  `hailo_apps` zur Laufzeit erkannt (Fremdcode, außerhalb dieses Repos) —
  **NICHT VERIFIZIERT im eigenen Code**, welches genaue Modell.
- **Kamera:** USB-Kamera über `--input usb`, angesprochen über die
  Hailo/GStreamer-Pipeline (Fremdcode, `GStreamerDetectionApp` aus
  `hailo_apps`). Eigener Code kennt zusätzlich `--input rpi` (Pi-Kamera) als
  Eingabeoption, siehe `roi_config_app.py` (`load_first_frame()`) und
  `tabs/input_tab.py` (Radiobuttons "USB-Kamera"/"Raspberry-Pi-Kamera"). Das
  genaue Kameramodell ist **NICHT VERIFIZIERT** im Code (Kamera wird generisch
  über den v4l2/Pi-Kamera-Pfad der Hailo-Pipeline angesprochen, kein
  modellspezifischer Code im Repo).
- **LoRa-Adapter — eindeutig geklärt:** Der **aktive** Produktivcode
  (`lora_send_loop.py`) spricht ausschließlich den **Dragino LA66** an:
  - Docstring `lora_send_loop.py:3`: "für den LA66 USB Adapter V2".
  - AT-Befehl `AT+SENDB=<confirm>,<Fport>,<len>,<hexdata>`
    (`lora_send_loop.py:151`).
  - Standard-Port ein CP2102-USB-UART-Bridge-Gerätepfad:
    `/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0`
    (`lora_send_loop.py:54-56`), Baudrate `9600` (`DEFAULT_BAUD`,
    `lora_send_loop.py:57`).
  - Status-Abfrage über `AT+NJS=?` (`lora_send_loop.py:128`).
  - **Sonel LORA-S1** kommt im aktiven Produktivpfad **nicht** vor. Referenzen
    existieren ausschließlich in `tests/lora_hardware/` (historische
    Sondierungs-/Probe-Skripte: `la66_probe.py`, `lora_hardware_probe.py`,
    `test_lora_transmitter.py`) — das sind separate, nicht von `app.py` oder
    `lora_send_loop.py` importierte Diagnoseskripte, kein aktiver Code.
- **Übertragungs-Hardware für MQTT:** Im Code wird ausschließlich die
  IP-Adresse eines Brokers konfiguriert (`mqtt_send_loop.py`, Default
  `STANDARD_BROKER = "localhost"`, App-seitiger Vorgabewert
  `"192.168.0.50"` in `tabs/settings_store.py` DEFAULTS). Welche physische
  Netzwerkschnittstelle (WLAN, Ethernet, LTE-Modem) das Betriebssystem dafür
  nutzt, wird im Code nicht festgelegt — bestätigt durch den Kommentar
  `mqtt_send_loop.py:17-19`: "Der Sendeweg (WLAN oder LTE-Dongle) spielt für
  dieses Skript keine Rolle". **NICHT VERIFIZIERT**, welche konkrete Hardware
  tatsächlich verbaut ist.

---

## 2. Softwarearchitektur — Schichten und Module

Alle Module unten sind **Eigencode** in diesem Repo, sofern nicht ausdrücklich
als Fremdcode markiert.

### UI-/Steuerschicht
| Datei | Aufgabe |
|---|---|
| `app.py` (407 Zeilen) | Fenster-Klammer: Sidebar, Seitennavigation, Autostart/Aufwärmlauf-Anstoß, Design-Umschaltung. `class MainApp` erbt von allen unten stehenden `tabs/`-Mixins. |
| `tabs/input_tab.py` | Seite 1: Input-Quelle wählen (`InputTabMixin`). |
| `tabs/config_tab.py` | Seite 2: bettet `RoiConfigApp` ein (`ConfigTabMixin`). |
| `tabs/recording_controls.py` | Mitschnitt-Abschnitt von Seite 3 (`RecordingControlsMixin`). |
| `tabs/lora_controls.py` | LoRa-Abschnitt von Seite 3 (`LoraControlsMixin`). |
| `tabs/mqtt_controls.py` | MQTT-Abschnitt von Seite 3 (`MqttControlsMixin`). |
| `tabs/pipeline_control.py` | Start/Stopp von `core.py` als Subprozess (`PipelineControlMixin`). |
| `tabs/start_tab.py` | Seite-3-Layout, bindet die drei Abschnitte oben ein (`StartTabMixin`). |
| `tabs/output_tab.py` | Seite 4: Live-Konsole + Zählerstände (`OutputTabMixin`). |
| `tabs/autoconfig_tab.py` | Seite 5: Auto-Konfiguration-Datensammlung (`AutoConfigTabMixin`). |
| `tabs/constants.py` | Gemeinsame Pfad-/Layout-Konstanten für `app.py` + `tabs/*`. |
| `tabs/settings_store.py` | Lädt/schreibt `app_settings.json` (Input-Quelle, Seite-3-Optionen, Design). |
| `roi_config_app.py` | Zählgeometrie-Werkzeug (eigenständig aufrufbar ODER in Tab 2 eingebettet), `class RoiConfigApp`. |
| `ui_utils.py` | `make_scrollable()` — gemeinsame CTkScrollableFrame-Hilfsfunktion. |
| `ctk_dialogs.py` | CustomTkinter-Dialoge als Ersatz für `tkinter.messagebox`/`simpledialog`. |

Framework: `customtkinter` (siehe `import customtkinter as ctk` in `app.py`).

### Konfigurationsschicht
| Datei | Aufgabe |
|---|---|
| `config.py` | Lädt `roi_config.json`, exponiert Modulkonstanten (`COUNTING_MODE`, `TRACKED_LABELS`, `FRAMES_UNTIL_GONE` etc.), Fallback auf `_DEFAULT_ROI_CONFIG` (`config.py:64-79`). |
| `frame_utils.py` | GUI-freie Frame-/Auflösungsbeschaffung aus Datei (laut Docstring: "nur cv2+os"). |
| `auto_config.py` | Datensammlung (Paket 1) + Batch-Einteilung (Paket 2) für die Auto-Konfiguration. |
| `auto_config_clustering.py` | DBSCAN-Clustering (Paket 3) + Cluster→Zählgeometrie (Paket 4). |

### Pipeline-/Erfassungsschicht
| Datei | Aufgabe |
|---|---|
| `core.py` | Einstiegspunkt: `class MyDetectionApp(GStreamerDetectionApp)` (Fremdbasisklasse aus `hailo_apps`), `app_callback()` (Pro-Frame-Callback), `__main__`-Block. |

`GStreamerDetectionApp` selbst ist **Fremdcode** aus dem Paket `hailo_apps`
(`core.py:22`: `from hailo_apps.hailo_app_python.apps.detection.detection_pipeline import GStreamerDetectionApp`),
nicht Teil dieses Repos.

### Zähl-/Trackingschicht
| Datei | Aufgabe |
|---|---|
| `tracking.py` | `class TrackingState(app_callback_class)` — Track-Verwaltung: anlegen (`update_track()`), flushen (`flush_stale()`), abschließen (`finalize()`). |
| `counting.py` | `LineCounter`, `RoiCounter`, `MultiRoiCounter`, `build_counter()`, Geometrie-Helfer (`point_in_polygon`, `segments_intersect` etc.). |

### Persistenz-/Visualisierungsschicht
| Datei | Aufgabe |
|---|---|
| `logging_utils.py` | Schreibt `ergebniss.csv` (`log_track_event_csv()`) und `zaehlung.csv` (`log_count_event()`). |
| `csv_utils.py` | `ensure_current_schema()` — Schema-Sicherung gegen Spalten-Drift. |
| `cleanup_utils.py` | `archive_previous_run()` — verschiebt Artefakte des Vorlaufs. |
| `visualization.py` | Live-Overlay (OpenCV) + Bewegungsbilder (Pillow). |
| `recording.py` | Optionaler Benchmark-Mitschnitt (nicht Normalbetrieb, siehe Abschnitt 4/config.py:173-185). |

### Übertragungsschicht
| Datei | Aufgabe |
|---|---|
| `lora_message.py` | 18-Byte-Frame bauen/lesen, `normalize_in_fields()`, `describe_structure()`/`describe_multi_roi_structure()`. |
| `lora_send_loop.py` | LoRa-Sender-Subprozess, `class LivePayloadProvider`, `class StaticProvider`. |
| `mqtt_send_loop.py` | MQTT-Sender-Subprozess, nutzt `LivePayloadProvider`/`UebergangsProvider` wieder. |
| `uebergangs_payload.py` | `class UebergangsProvider` — volle Übergangsmatrix als JSON (Format 3). |
| `konfig_payload.py` | Sendet Konfigurations-Eckdaten (Format 4, siehe Abschnitt 6). |
| `lora_spiegel.py` | Spiegelt LoRa-Nachrichten zur Kontrolle zusätzlich über MQTT (laut Docstring "NUR im Zusatz-Feature"). |

### Betriebsschicht
| Datei | Aufgabe |
|---|---|
| `warmup.py` | Aufwärmlauf einmal pro Systemstart (`needs_warmup()`, `run_warmup()`). |
| `start_app.sh` | Autostart-Einstiegspunkt (siehe Abschnitt 7). |
| `setup_env.sh` | venv aktivieren + `PYTHONPATH` setzen. |
| `create_venv.sh` | Legt `venv_visitorcounter` an, installiert `requirements.txt` + `hailo_apps`. |

### Aktuell deaktivierte/ausgeblendete Module (Code vorhanden, UI-Zugriff gesperrt)

Gesteuert durch das Flag **`config.SHOW_AUTO_CONFIG`** (`config.py:62`, Wert
`False`):
- `app.py:55` (`PAGE_NAMES.append("5. Auto-Konfiguration")` nur wenn Flag `True`)
  und `app.py:209` (Tab 5 wird nur gebaut, wenn Flag `True`) — betrifft
  `tabs/autoconfig_tab.py`.
- `roi_config_app.py:318` — die beiden Radiobuttons "Auto: Clustering (DBSCAN)"
  und "Auto: Randraster" werden nur angezeigt, wenn das Flag `True` ist; sonst
  fehlen sie in der Modusauswahl von Tab 2.
- Betroffener, aber weiterhin vollständig vorhandener Code: `auto_config.py`,
  `auto_config_clustering.py`, `tabs/autoconfig_tab.py`.

---

## 3. Datenfluss (pro Frame / pro Track)

Realer Aufrufpfad, Reihenfolge wie im Code:

1. **`core.py:app_callback(pad, info, user_data)`** — wird von GStreamer pro
   Frame aufgerufen (`core.py:191`). Liest Detections aus dem Hailo-ROI
   (`hailo.get_roi_from_buffer(buffer)`, `core.py:228`).
2. Für jede Detection, deren Label in `TRACKED_LABELS` liegt und deren
   Konfidenz `>= COUNTING_MIN_CONFIDENCE` ist (`core.py:237,246`):
   `user_data.update_track(...)` → **`tracking.py:97 TrackingState.update_track()`**.
   Diese Methode vergibt bei neuen Tracks eine lesbare `display_id`
   (klassengetrennt hochzählend, z. B. `"car_ID_3"`).
3. **`core.py:287 user_data.flush_stale(current_frame)`** — jeden Frame
   aufgerufen → **`tracking.py:198 TrackingState.flush_stale()`**: entfernt und
   protokolliert Objekte, die seit **`FRAMES_UNTIL_GONE` (= `30`, `config.py:151`)**
   Frames nicht mehr gesehen wurden (Vergleich `current_frame - data["last_seen_frame"] >= FRAMES_UNTIL_GONE`,
   `tracking.py:204`).
4. Beim Abschluss eines Tracks (Flush oder `finalize()` bei Programmende,
   `tracking.py:215`) wird intern die Zählentscheidung getroffen (über
   `counting.build_counter()` — `counting.py:118` — je nach `COUNTING_MODE`)
   und anschließend geschrieben:
   - **`logging_utils.py:44 log_track_event_csv()`** → `ergebniss.csv`
   - **`logging_utils.py:80 log_count_event()`** → `zaehlung.csv`

### Geschriebene CSV-Dateien und Spalten (exakt aus `logging_utils.py`)

**`ergebniss.csv`** (`RESULTS_FILE_CSV`, `logging_utils.py:17,20-25`):
```
display_id, kind, track_id, label, start_x, start_y, end_x, end_y,
avg_confidence, first_timestamp, last_timestamp
```

**`zaehlung.csv`** (`COUNTS_FILE_CSV`, `logging_utils.py:18,27`):
```
timestamp, display_id, label, direction, is_transition
```
`is_transition=False` kennzeichnet protokollierte, aber nicht gezählte
Ereignisse (z. B. "A (kein Wechsel)" bei `MultiRoiCounter`, siehe
`logging_utils.py:88-91`).

Beide Dateien werden über **`csv_utils.ensure_current_schema()`**
(`logging_utils.py:60,93`) vor jedem Schreiben gegen Spalten-Drift geprüft.

---

## 4. Zähllogik und Konfiguration

### Zählmodi (exakte String-Werte im Code)

Definiert als Klassenattribut `mode` in `counting.py`:
- `"line"` — `class LineCounter` (`counting.py:154`)
- `"roi"` — `class RoiCounter` (`counting.py:222`)
- `"multi_roi"` — `class MultiRoiCounter` (`counting.py:291`)

Ausgewertet in **`counting.py:118 build_counter(mode, geometry, labels, reverse=False, snap_to_nearest=False)`**:
`if mode == "multi_roi": ...` (`counting.py:132`), `if mode == "roi": ...`
(`counting.py:134`), sonst `LineCounter`.

Zusätzlich existieren die Werte `"auto_cluster"` und `"auto_border"`
(`roi_config_app.py:103`, `AUTO_MODES`) — das sind **UI-Modi** in
`roi_config_app.py`, die beim Speichern auf `mode="multi_roi"` abgebildet
werden (`roi_config_app.py:1202`: `saved_mode = "multi_roi" if mode in AUTO_MODES else mode`).
`counting.py` selbst kennt nur die drei oben genannten Modi.

### `roi_config.json` — vollständige Feldliste (aus `config.py:64-79`, Default-Werte)

| Feld | Typ | Bedeutung |
|---|---|---|
| `mode` | str | `"line"` \| `"roi"` \| `"multi_roi"` (siehe oben) |
| `points` | Liste `[[x,y], ...]`, normalisiert 0.0–1.0 | bei `line`: 2 Punkte; bei `roi`: ≥3 Punkte (Polygon) |
| `regions` | Liste von `{"name", "points", "direction", "snap"}` | nur bei `multi_roi` (siehe unten) |
| `classes` | Liste von COCO-Klassennamen (str) | getrackte Klassen, Default alle sechs (`config.py:68`) |
| `reverse_direction` | bool | kehrt IN/OUT um (nur `line`/`roi`) |
| `snap_to_nearest` | bool | globaler Schalter: Punkte ohne Treffer der nächsten Fläche zuordnen (nur `multi_roi`) |
| `min_confidence` | float 0.0–1.0 | Mindest-Konfidenz zum Zählen, Default `0.5` |
| `in_field` | str **oder** Liste von str | Namen der IN-Flächen (nur `multi_roi`); Liste = aktuelles Format, einzelner String = altes Format (siehe unten) |

`config.py:82 _load_roi_config()` liest die Datei; fehlt sie oder ist sie
fehlerhaft, greift `_DEFAULT_ROI_CONFIG` unverändert (`config.py:90-92`).

Pro Region (`regions[i]`, nur `multi_roi`, siehe `roi_config_app.py:1234-1238`):
- `name` (str), `points` (normalisierte Liste), `snap` (bool, Default `True`),
  `direction` (str, `"in"` oder `"out"`, siehe unten).

### IN/OUT-Bestimmung je Fläche

- Jede Region trägt ein Feld `region["direction"]` (`"in"`/`"out"`), gesetzt
  über eine Checkbox je Fläche in `roi_config_app.py`
  (`_refresh_direction_fields()`/`_on_direction_field_toggle()`,
  `roi_config_app.py:549-587`). Beim Anlegen einer neuen Fläche gilt: die
  zuerst angelegte ist automatisch `"in"`, alle weiteren `"out"`
  (`roi_config_app.py:948-949`).
- Beim Speichern wird daraus die Liste `config["in_field"]` gebildet:
  `[r["name"] for r in self.regions if r.get("direction","out")=="in"]`
  (sinngemäß, siehe `roi_config_app.py` Speicherlogik um Zeile 1230-1240).
- Validierung beim Speichern: mindestens eine Fläche muss `"in"`, mindestens
  eine `"out"` sein (`roi_config_app.py:1173`:
  `richtungen = {r.get("direction","out") for r in self.regions}`, geprüft
  gegen `{"in","out"}`).
- Downstream-Konsum (Übertragung): `lora_message.normalize_in_fields()` und
  eine gleichnamige Methode in `uebergangs_payload.py` lesen `in_field`
  sowohl als Liste als auch als einzelnen String (Rückwärtskompatibilität zu
  älteren `roi_config.json`-Dateien).

### Auto-Konfiguration

- **Verfahren 1 — DBSCAN-Clustering:** `auto_config_clustering.py`, Parameter
  `AUTO_CONFIG_DBSCAN_EPS_PIXELS = 50`, `AUTO_CONFIG_DBSCAN_MIN_SAMPLES = 3`
  (`config.py:247-248`).
- **Verfahren 2 — Randraster:** ebenfalls `auto_config_clustering.py` (Modus
  `--border`), Parameter `AUTO_CONFIG_BORDER_SEGMENTS_PER_EDGE = 4`,
  `AUTO_CONFIG_BORDER_DEPTH_RATIO = 0.08`,
  `AUTO_CONFIG_MIN_TRACK_DISTANCE_PIXELS = 40` (`config.py:256-262`).
- Datensammlung: `auto_config.py`, gesteuert über
  `AUTO_CONFIG_COLLECTION_ENABLED` (Env-Var oder `config.py:233` Default `False`).
- **Aktueller Aktiv-Status:** in der UI **ausgeblendet** — siehe Abschnitt 2,
  gesteuert durch `config.SHOW_AUTO_CONFIG = False`. Der Code selbst ist
  vollständig vorhanden und lauffähig, nur nicht über die GUI erreichbar.

---

## 5. Bedienoberfläche

- **GUI-Framework:** `customtkinter` (`import customtkinter as ctk`, u. a.
  `app.py`).
- **Einstiegsdatei:** `app.py`, Funktion `main()` (`app.py`, letzter Abschnitt):
  erstellt `ctk.CTk()`-Root, instanziiert `MainApp(root, autostart=...)`,
  startet `root.mainloop()`.
- **Struktur:** `class MainApp` in `app.py` erbt von neun Mixin-Klassen aus
  `tabs/` (vollständige Liste siehe Abschnitt 2, Tabelle "UI-/Steuerschicht").
  Jede Seite/jeder Bedienabschnitt ist ein eigenes Modul.
- **Zählgeometrie in der GUI:** ja — `tabs/config_tab.py` bettet
  `roi_config_app.RoiConfigApp` in Tab 2 ein (`ConfigTabMixin._build_config_tab()`).
  `roi_config_app.py` ist zusätzlich eigenständig auf der Kommandozeile
  aufrufbar (`if __name__ == "__main__": main()` mit `argparse`, siehe
  Docstring "Nutzung: python roi_config_app.py --input ...").
- **Ohne Kommandozeile:** `app.py` bündelt Input-Wahl, Konfiguration,
  Start/Stopp, Live-Auswertung über eine Sidebar-Navigation
  (`PAGE_NAMES`, `app.py:53-55`) — bestätigt durch den Docstring am
  Dateianfang ("ein Fenster mit Sidebar-Navigation ... ohne zwischen mehreren
  Terminals/Skripten zu wechseln"). `core.py`, `roi_config_app.py` und
  `auto_config*.py` bleiben laut demselben Docstring zusätzlich einzeln auf
  der Kommandozeile nutzbar.
- **Autostart-Verhalten:** siehe Abschnitt 7.

---

## 6. Datenspeicherung und Datenübertragung

### Lokale Speicherung

| Datei | Format | Schreibende Stelle |
|---|---|---|
| `zaehlung.csv` | CSV, Spalten siehe Abschnitt 3 | `logging_utils.log_count_event()` |
| `ergebniss.csv` | CSV, Spalten siehe Abschnitt 3 | `logging_utils.log_track_event_csv()` |
| `roi_config.json` | JSON, Felder siehe Abschnitt 4 | `roi_config_app.py` (Speichern-Button) bzw. `auto_config_clustering.py --save` |
| `app_settings.json` | JSON | `tabs/settings_store.save_settings()` |
| `camera_raw.png` | PNG | `core.py` (Snapshot-Modus, `SNAPSHOT_ONLY`) |
| `.uebergaenge_gesendet` | JSON (Marker) | `uebergangs_payload.UebergangsProvider._marker_schreiben()` |
| `.warmup_state` | Text (Boot-ID) | `warmup.mark_warmed_up()` |

### LoRaWAN-Weg

- **Modul:** `lora_message.py` (Frame bauen) + `lora_send_loop.py` (Versand).
- **Payload-Format:** exakt **18 Byte fix**
  (`FRAME_LEN = HEADER_LEN + 2 * len(CANONICAL_CLASSES)` = `6 + 2*6` = `18`,
  `lora_message.py:50-51`).
- **Kodierte Felder** (`lora_message.py`, Header `HEADER_LEN = 6`):
  Byte 0 Format-Version (`MSG_LINE_ROI = 0x02`), Byte 1 Sensor-ID, Byte 2
  Sequenznummer, Byte 3 `interval_min`, Byte 4 Status-Bitfeld, Byte 5
  Klassen-Bitmaske, Byte 6-17 je Klasse 2 Byte `[IN][OUT]` für die sechs
  `CANONICAL_CLASSES`.
- **LoRaWAN-Fport:** `FPORT = 2` (`lora_message.py:52`).
- **Sendeaufruf:** `AT+SENDB=<confirm>,<Fport>,<len>,<hexdata>` gebaut in
  `lora_send_loop.py:151 build_command()`, geschrieben über `pyserial`
  (`ser.write(...)`, LA66 an `DEFAULT_PORT`, `9600` Baud).

### MQTT-Weg

- **Format 3 (Übergangsmatrix, JSON):** Modul `uebergangs_payload.py`,
  `class UebergangsProvider.build()` (`uebergangs_payload.py:169`). Struktur
  laut Docstring (`uebergangs_payload.py:18-32`):
  ```
  {format, sensor_id, sequenz, gesendet_am, intervall_min, status{},
   felder[], in_feld, uebergaenge[{von,nach,klasse,anzahl}], summen{}}
  ```
  Nur Einträge mit `anzahl > 0` werden übertragen (nicht die volle
  Kombinationsmatrix, siehe Kommentar `uebergangs_payload.py:34-37`).
- **Format 4 (Konfiguration):** Modul `konfig_payload.py` — sendet
  Eckdaten der Konfiguration (`mode`, `in_field`, `felder`, `klassen`,
  `snap_to_nearest`, optional die volle `roi_config.json` bei
  `umfang="voll"`).
- **Versandskript:** `mqtt_send_loop.py`, nutzt wahlweise `--uebergaenge`
  (Format 3, Standard in der App-UI laut `tabs/settings_store.py` DEFAULTS
  `"mqtt_transitions": True`) oder `--live-counts` (18-Byte-kompatibles
  Format über `LivePayloadProvider`, wiederverwendet aus `lora_send_loop.py`).
- **Client:** `paho.mqtt.client` (`mqtt_send_loop.py:35`).

### Delta-/Bestätigungs-Logik (belegt)

**LoRa** (`lora_send_loop.py`, `class LivePayloadProvider`):
- `build()` (`lora_send_loop.py:288`) liest aktuelle kumulierte Zählwerte
  (`cur_in, cur_out`), bildet `_delta(cur_in, self._acked_in)` /
  `_delta(cur_out, self._acked_out)` (`lora_send_loop.py:277-286,294-295`) —
  das Delta seit dem letzten bestätigten Stand.
- `commit()` (`lora_send_loop.py:310`) zieht den Referenzstand erst NACH
  bestätigtem Versand nach: `self._acked_in = dict(self._pending_cur_in)`.
- Schlägt der Versand fehl, bleibt `_acked_in`/`_acked_out` unverändert — das
  nächste `build()` liefert wieder das (jetzt größere) Delta.

**MQTT/Übergänge** (`uebergangs_payload.py`, `class UebergangsProvider`):
- Zeilenbasiert statt wertbasiert: `self._verarbeitet` = Anzahl bereits
  verarbeiteter Zeilen aus `zaehlung.csv`, persistiert in `.uebergaenge_gesendet`
  (`_marker_lesen()`/`_marker_schreiben()`, `uebergangs_payload.py:97-114`).
- `build()` (`uebergangs_payload.py:169`) liest nur `zeilen[self._verarbeitet:]`
  (Zeile 184).
- `commit()` (`uebergangs_payload.py:253`, "Nur nach BESTÄTIGTEM Versand
  aufrufen") setzt `self._verarbeitet = self._offene_zeile` und schreibt den
  Marker erst dann.

Beide Mechanismen entsprechen damit der Beschreibung "nur der Zuwachs seit
dem letzten bestätigten Uplink wird gesendet" — mit unterschiedlicher
Umsetzung (Wert-Delta bei LoRa, Zeilen-Marker bei MQTT/Übergängen), beide im
jeweiligen Modul belegt.

### Sende-Intervall (konkrete Default-Werte)

- **LoRa:** `DEFAULT_PAUSE_MINUTES = 5` (`lora_send_loop.py`, Standardwerte-
  Abschnitt), App-seitiger Vorgabewert `"lora_interval": "5"`
  (`tabs/settings_store.py` DEFAULTS).
- **MQTT:** `STANDARD_PAUSE_MINUTEN = 5` (`mqtt_send_loop.py:57`), App-seitiger
  Vorgabewert `"mqtt_interval": "5"` (`tabs/settings_store.py` DEFAULTS).
- Beide Werte sind über die GUI (Tab 3) bzw. CLI-Argument `--pause` änderbar,
  kein fest verdrahteter Zwang.

---

## 7. Betrieb / Inbetriebnahme

### Autostart-Kette (Schritt für Schritt, aus `start_app.sh`)

1. Desktop-Autostart-Eintrag (laut Kommentar `start_app.sh:3-4`: "von einem
   Desktop-Autostart-Eintrag ... in einem frisch geöffneten Terminal
   ausgeführt") — **die `.desktop`-Datei selbst liegt nicht in diesem Repo**,
   nur die Anleitung dazu in `docs/einrichtung/GERAETE_EINRICHTUNG.md`
   (Doku, kein Repo-Code — **NICHT VERIFIZIERBAR anhand dieses Repos allein**,
   ob/wie der Eintrag auf einem konkreten Gerät tatsächlich existiert).
2. `start_app.sh:19`: `cd "$(dirname "$0")"` — in den Skript-Ordner wechseln.
3. `start_app.sh:21`: `source setup_env.sh` — venv aktivieren, `PYTHONPATH` setzen.
4. `start_app.sh:23`: `python warmup.py --input usb` — Aufwärmlauf (siehe unten).
5. `start_app.sh:25`: `python app.py --autostart` — Oberfläche öffnet sich und
   startet danach selbst automatisch die Zählung (`app.py`,
   `_maybe_autostart_pipeline()`, aufgerufen `800`/`1000` ms nach Fensteraufbau
   über `root.after(...)`).

### Aufwärmlauf (`warmup.py`)

- **Warum:** laut Docstring (`warmup.py:4-8`) dauert der allererste
  Pipeline-Start nach einem Neustart deutlich länger ("Beobachtet wurden bis
  zu zwei Minuten").
- **Wie lange:** `DEFAULT_TIMEOUT_SECONDS = 240` (`warmup.py:65`), danach
  Abbruch. Nach Sichtung der ersten Frames (`READY_MARKER = "Frame count:"`,
  `warmup.py:61`) wird `SETTLE_SECONDS = 1.0` (`warmup.py:68`) gewartet, dann
  sauber per `SIGINT` beendet (`_stop_process()`, eskaliert zu `SIGTERM`/`SIGKILL`
  bei Ausbleiben der Reaktion).
- **Schutz gegen Mehrfachausführung:** `needs_warmup()` (`warmup.py:102`)
  vergleicht die aktuelle Kernel-Boot-ID
  (`BOOT_ID_PATH = "/proc/sys/kernel/random/boot_id"`, `warmup.py:57`) gegen
  die zuletzt in `.warmup_state` gespeicherte — läuft nur einmal pro
  Systemstart. `app.py` hat zusätzlich einen eigenen, redundanten Aufruf von
  `warmup.needs_warmup()`/`warmup.run_warmup()` (`_maybe_run_warmup()`) als
  Sicherheitsnetz, falls die App unabhängig von `start_app.sh` gestartet wird.

---

## 8. Offene Punkte / Widersprüche

- **RAM 8 GB oder 16 GB?** **NICHT VERIFIZIERT im Code** — kommt in keiner
  `.py`-, `.json`- oder Shell-Datei dieses Repos vor. Die Dokumentation
  (`docs/projekt/HANDOFF.md:37`, `docs/projekt/Architektur.md:17`,
  `docs/einrichtung/GERAETE_EINRICHTUNG.md`) behauptet übereinstimmend "8 GB",
  das ist aber eine Doku-Aussage, kein Code-Fakt — für die Arbeit ggf. am
  realen Gerät (z. B. `free -h` auf dem Pi) gegenprüfen.
- **LA66 oder LORA-S1?** Eindeutig geklärt (siehe Abschnitt 1): der aktive
  Produktivcode (`lora_send_loop.py`) nutzt ausschließlich den **Dragino
  LA66**. "Sonel LORA-S1" taucht nur in historischen Diagnoseskripten unter
  `tests/lora_hardware/` auf, die von keinem Produktivmodul importiert werden
  — kein Widerspruch, aber im Repo unübersehbar zwei Hardware-Namen präsent,
  falls jemand nur grept statt den Importgraphen zu prüfen.
- **Python-Version:** Kein `.python-version`, kein `pyproject.toml`, kein
  `setup.py`/`setup.cfg` im Repo. `create_venv.sh` ruft generisch `python3`
  auf (`create_venv.sh`: `python3 -m venv --system-site-packages "$VENV_DIR"`)
  — die exakte Python-Version auf dem Zielgerät ist **NICHT VERIFIZIERT** im
  Code (abhängig von der auf dem jeweiligen Pi OS installierten `python3`-Version).
- **Kameramodell:** **NICHT VERIFIZIERT** im Code — nur der generische Pfad
  `--input usb`/`--input rpi` ist codiert, kein modellspezifischer Treiber
  oder Produktname.
- **`.desktop`-Autostart-Datei:** existiert nicht als Datei in diesem Repo,
  nur als Anleitung in `docs/einrichtung/GERAETE_EINRICHTUNG.md` und
  `docs/entwicklung/AENDERUNGEN-mehrere-inout-lightmode-autostart.md`. Ob sie
  auf einem konkreten Gerät tatsächlich in dieser Form angelegt wurde, ist
  anhand des Repos **nicht verifizierbar** (liegt außerhalb des
  Versionskontrollierten).
- **`roi_config.json`/`in_field`-Format uneinheitlich dokumentiert:** Der
  Default in `config.py:78` ist eine leere **Liste** (`[]`), einzelne
  ältere, reale Konfigurationsdateien auf Geräten könnten laut den
  Kompatibilitäts-Codepfaden (`lora_message.normalize_in_fields()`,
  `uebergangs_payload.py`) noch einen einzelnen **String** enthalten — beide
  Formate werden vom Code unterstützt, das ist kein Bug, aber beim Lesen
  einer konkreten `roi_config.json`-Datei auf einem Gerät ist ohne Ansicht der
  Datei **nicht verifizierbar**, welches Format dort aktuell vorliegt.
- **Server-Repository (`stadtwerke-server`) nicht Teil dieses Repos:** alle
  Aussagen in diesem Dokument beziehen sich ausschließlich auf den Sensor
  (`visitorcounter`). Server-seitiges Verhalten (Datenbankschema,
  Dashboard) ist hier **nicht auditiert**.

---

## 9. Versions-/Standdaten

- **Commit:** `1a7f5819fc4565fa917ef8c2a1ad7b9e3c635c80` ("config"),
  Datum laut `git log`: 2026-08-04 02:45:35 +0200.
- **Arbeitsverzeichnis beim Audit:** ein unstaged Änderung in
  `docs/projekt/ToDo.md` (laut `git status --short` zum Auditzeitpunkt),
  sonst sauber.
- **Python:** keine Version im Repo festgeschrieben (siehe Abschnitt 8).
  Lokal beim Audit installiert: Python 3.13.2 — das ist die Version auf der
  Audit-Maschine, **nicht notwendigerweise die auf dem Ziel-Pi** (dort
  bestimmt `python3` des jeweiligen Raspberry Pi OS).
- **Zentrale Abhängigkeiten** (`requirements.txt`, vollständig):
  `numpy<2.0.0` (Begründung im Kommentar: "hailort/opencv-Builds erwarten
  noch NumPy-1.x-ABI"), `opencv-python`, `Pillow`, `customtkinter`,
  `scikit-learn`, `scipy`. Explizit **nicht** per `pip` installierbar und
  daher **nicht** in `requirements.txt`: `hailo`/`hailo_apps` (kommen mit der
  Hailo-Installation) sowie `gi`/PyGObject/GStreamer (System-Pakete via
  `apt`) — siehe Kopf-Kommentar von `requirements.txt`.
- **`hailo_apps`-Version laut `create_venv.sh`:** Standard-Git-Tag
  `HAILO_APPS_VERSION="${HAILO_APPS_VERSION:-25.7.0}"` — installiert aus
  `git+https://github.com/hailo-ai/hailo-apps-infra.git@25.7.0`
  (`create_venv.sh`).
