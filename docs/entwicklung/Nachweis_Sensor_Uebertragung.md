# Nachweis Sensor & Übertragung — Besucherzählsensor

Erstellt durch Lesen des Repository-Codes und der Dokumentation (kein Code
verändert). Stand: 19.08.2026. Alle Angaben sind mit Datei/Zeilen- bzw.
Dateibezug versehen; wo im Repository nichts dazu steht, ist das ausdrücklich
als "nicht im Repo dokumentiert" vermerkt statt geraten. Geheimnisse
(Zugangsdaten, Schlüssel, Kennungen, Adressen) sind durch `[REDACTED]`
ersetzt bzw. wurden im Repository ohnehin nicht gefunden (siehe Abschnitt
„Einschränkungen").

---

## Zweck

Dieses Repository ist die Sensor-Software für einen Computer-Vision-basierten
Besucherzähler auf Raspberry Pi 5 mit Hailo-8-Beschleuniger (`README.md:1-6`).
Der Sensor erkennt und zählt Objekte (Personen, Fahrräder, Fahrzeuge) über ein
konfigurierbares Zählverfahren (Linie / Fläche / mehrere Flächen) und
überträgt ausschließlich aggregierte Zählwerte — keine Bilder, keine
Einzelereignisse mit Zeitstempel oder Position — per MQTT und/oder LoRaWAN an
einen externen Server (`config.py:176-183`, `uebergangs_payload.py:42-47`).
Laut Nutzerkontext läuft der MQTT-Pfad aktuell gegen einen Testserver und der
LoRaWAN-Pfad über The Things Stack (TTS); das produktive Netz der Stadtwerke
Potsdam läuft über ChirpStack. Diese Aussage stammt aus dem Nutzerkontext
dieser Anfrage, nicht aus dem Repository-Code selbst — im Code/den
Dokumenten kommt "ChirpStack" nicht vor, "TTN"/"The Things Network" schon
(siehe Abschnitt Übertragung).

---

## Hardware und Software

### Hardware (soweit aus Repo/Konfiguration ersichtlich)

| Komponente | Angabe | Quelle |
| --- | --- | --- |
| Recheneinheit | Raspberry Pi 5 mit Hailo-8-Beschleuniger | `README.md:3-4` |
| Hailo-Firmware | 4.23.0 (getestet) | `README.md:10` |
| Betriebssystem | Raspberry Pi OS (64-bit), Python 3.11 | `README.md:11` |
| Kamera | generisch über `--input usb` bzw. `--input rpi`; konkretes Modell **nicht im Repo dokumentiert** (nur der generische Eingabepfad) | `config.py` (kein Kameramodell), `tabs/input_tab.py` |
| LoRa-Adapter | Dragino LA66 USB Adapter V2 (seriell, CP2102-USB-UART-Bridge) | `lora_send_loop.py:49-52`, `docs/einrichtung/EINRICHTUNG_LA66.md` |
| LTE/Mobilfunk-Stick | erwähnt im Kontext des Dauerbetriebs, aber **kein Verweis im Python-Code** auf ein konkretes Modell oder eine Netzwerkkonfiguration gefunden — **nicht im Repo dokumentiert** | — |

### Software-Stack

| Baustein | Verwendung | Quelle |
| --- | --- | --- |
| `hailo`, `hailo_apps` | Hailo-Python-SDK + App-Framework (nicht über `requirements.txt`, kommt mit der Hailo-Installation) | `requirements.txt:9-11`, `README.md:12-16` |
| GStreamer + PyGObject (`gi`) | Pipeline-Framework für die Objekterkennung | `README.md:17-20` |
| `numpy<2.0.0` | Numerik; Version gedeckelt wegen HailoRT/OpenCV-ABI | `requirements.txt:16` |
| `opencv-python` (cv2) | Frame-Handling, Zeichnen, Kamerazugriff | `requirements.txt:17` |
| `Pillow` | Bewegungsbilder, Vorschau im Konfig-Tool | `requirements.txt:18` |
| `customtkinter` | GUI (dunkles Design) für `app.py`/`roi_config_app.py` | `requirements.txt:21` |
| `scikit-learn`, `scipy` | DBSCAN-Clustering / ConvexHull für die (aktuell in der GUI ausgeblendete) Auto-Konfiguration | `requirements.txt:25-26` |
| `pyserial` | serielle Kommunikation mit dem LA66-Adapter | `lora_send_loop.py:41` |
| `paho-mqtt` | MQTT-Client für den MQTT-Sendeweg | `mqtt_send_loop.py:35` |

Erkennungsmodell: über die Hailo-Pipeline (`hailo_apps`), standardmäßig deren
automatisch gewähltes Standardmodell passend zur erkannten Hailo-Architektur;
seit 19.08.2026 optional per GUI (Tab 1) ein eigenes `.hef`-Modell wählbar
(`--hef-path`-Argument von `hailo_apps`, siehe `tabs/pipeline_control.py:88-98`,
`tabs/input_tab.py`). Welches konkrete Modell (Architektur/Trainingsdaten) im
Dauerbetrieb 18.08.–23.08.2026 tatsächlich lief, ist **nicht im Repo
dokumentiert** (kein `--hef-path` fest im Code hinterlegt, Standardauswahl
liegt bei `hailo_apps`).

---

## Übertragung

Zwei unabhängige, parallel nutzbare Übertragungswege. Beide lesen dieselbe
Zähllogik-Ausgabe (`zaehlung.csv`) und dieselbe Zählgeometrie-Konfiguration
(`roi_config.json`), und beide senden ausschließlich aggregierte Zählwerte
seit dem letzten erfolgreichen Uplink (Delta-Prinzip) — kein Einzelereignis
mit Zeitstempel oder Position verlässt den Sensor (`uebergangs_payload.py:42-53`).

### MQTT

- **Skript:** `mqtt_send_loop.py`, läuft auf dem Sensor selbst
  (`mqtt_send_loop.py:4`).
- **Topic:** `zaehlsensor/{sensor_id}/zaehlwerte`, `{sensor_id}` durch die
  konfigurierte Sensor-ID ersetzt (`mqtt_send_loop.py:56`, Standard-Broker
  `localhost:1883` als Skript-Default — der tatsächliche Broker wird über
  `--broker`/GUI-Feld gesetzt, siehe unten). Konkrete Broker-Adresse(n) des
  Testservers sind **nicht im Repo hinterlegt** (Nutzereingabe zur
  Laufzeit) — an dieser Stelle wäre ohnehin `[REDACTED]` einzusetzen.
- **Sende-Intervall:** über die GUI einstellbar (Tab 3, `tabs/mqtt_controls.py`),
  Standardwert 5 Minuten (`tabs/settings_store.py`, `"mqtt_interval": "5"`).
  Das Skript selbst nutzt `--pause` in Minuten zwischen zwei Sendungen
  (`mqtt_send_loop.py:116-117`).
- **Payload-Formen:** drei mögliche Inhalte, je nach Startoption:
  1. **18-Byte-Frame als JSON-Hülle** (Standard, `--live-counts` ohne
     `--uebergaenge`): `{"payload": "<hex>", "gesendet_am": "<ISO-Zeit>"}` —
     derselbe 18-Byte-Frame wie über LoRa, siehe Payload-Struktur unten
     (`mqtt_send_loop.py:79-89`).
  2. **18 Byte roh** (`--roh`): dieselben Bytes ohne JSON-Hülle
     (`mqtt_send_loop.py:84-85`).
  3. **Vollständige Übergangsmatrix als JSON** (`--uebergaenge`, "Format 3"):
     nur über MQTT sinnvoll, da eine vollständige Von-Feld/Nach-Feld-Matrix
     nicht in ein 18-Byte-LoRa-Telegramm passt (`uebergangs_payload.py:6-14`,
     Struktur siehe eigener Abschnitt unten).
- **QoS:** 1 (Broker bestätigt Empfang, erst danach schiebt der Sender seinen
  internen "zuletzt gesendet"-Merker nach) — bewusst kein QoS 0, weil sonst
  Zählwerte bei Verlust ohne Nachweis verloren gingen (`mqtt_send_loop.py:96-98`).
- **Bestätigung/Wiederholung:** `client.publish(...).wait_for_publish(timeout=10)`
  (`mqtt_send_loop.py:87-88`). Erst nach Erfolg wird der Referenzstand
  (Delta-Basis) nachgeschoben (`provider.commit()`); bei Fehlschlag bleiben
  die Werte stehen und werden beim nächsten Zyklus mitgesendet
  (`mqtt_send_loop.py:201-210`).
- **Authentifizierung:** optional Benutzername/Passwort
  (`--benutzer`/`--passwort`) und optional TLS (`--tls`), beides nur als
  CLI-Parameter im Skript vorgesehen — keine Zugangsdaten im Repository
  hinterlegt (`mqtt_send_loop.py:110-112, 163-166`).

### LoRaWAN

- **Skript:** `lora_send_loop.py`, läuft auf dem Sensor
  (`lora_send_loop.py:1-3`).
- **Adapter:** Dragino LA66 USB Adapter V2, angesprochen über AT-Befehle auf
  einer seriellen Schnittstelle (`lora_send_loop.py:49-53`, Standardport
  `/dev/serial/by-id/usb-Silicon_Labs_CP2102_...` — Geräte-ID, kein Geheimnis,
  aber geräteabhängig).
- **Sendebefehl:** `AT+SENDB=<confirm>,<Fport>,<len>,<hexdata>`
  (`lora_send_loop.py:150-153`).
- **FPort:** 2, fest im Code (`lora_send_loop.py:61`, `lora_message.py:52`).
- **Bestätigungsmodus:** `CONFIRM = 0` — unbestätigte Uplinks (kein Netz-ACK
  angefordert), (`lora_send_loop.py:62`).
- **Sende-Intervall:** `--pause` in Minuten NACH jedem erfolgreichen Uplink,
  Standard 5 Minuten (`lora_send_loop.py:55, 344-345`); bei Fehlschlag wird
  alle `--retry` Sekunden (Standard 60 s) erneut versucht
  (`lora_send_loop.py:54, 342-343`). Begründung: EU868-Duty-Cycle-Schonung
  (1 %) (`lora_send_loop.py:7-8`).
- **Netzwerk-Server:** Registrierung laut `docs/einrichtung/EINRICHTUNG_LA66.md:124-125`
  über "TTN zum Testen, produktiv: Stadtwerke Potsdam" — die dortige Anleitung
  nennt DevEUI/AppEUI/AppKey als Registrierungsfelder, aber **keine
  tatsächlichen Werte** (Platzhalter-Anleitung, keine Geheimnisse im Repo
  gefunden, siehe Einschränkungen). "ChirpStack" als Bezeichnung des
  produktiven Netzes kommt im Repository-Text nicht vor — das ist laut
  Aufgabenstellung Kontextwissen von außerhalb des Repos.
- **Join-Verfahren:** Das Sendeskript selbst löst NIE einen Join aus, sondern
  fragt nur den Anmeldestatus ab (`AT+NJS=?`) und sendet ausschließlich
  `AT+SENDB` (`lora_send_loop.py:114-124`). Ein automatischer Join-Vorgang
  bei fehlender Anmeldung erfolgt modul-intern (LA66-Firmware), nicht durch
  dieses Skript.
- **Betriebsarten:** statisch (immer derselbe Test-Frame) oder
  `--live-counts` (Frame wird vor jedem Sendeversuch neu aus
  `roi_config.json` + `zaehlung.csv` gebaut, `lora_send_loop.py:10-20`). Der
  Live-Betrieb wird von `app.py` (Tab 3) verwendet.
- **Delta-/Bestätigungslogik:** identisch zum MQTT-Weg — `build()` liefert das
  Delta seit dem letzten bestätigten Uplink, `commit()` schiebt den
  Referenzstand erst NACH bestätigtem `txDone` nach
  (`lora_send_loop.py:196-213, 288-319`).

---

## Payload-Struktur

### Format 2 (0x02) — kompakter 18-Byte-Frame (LoRaWAN und Standard-MQTT-Payload)

Quelle: `lora_message.py:12-25, 90-122` (Aufbau), `lora_message.py:337-362`
(Referenz-Decoder).

18 Byte = 6 Byte Header + 6 Klassen × 2 Byte (IN, OUT). Feste kanonische
Klassenreihenfolge: `person, bicycle, car, motorcycle, bus, truck`
(`lora_message.py:41`).

| Byte(s) | Feld | Bedeutung |
| --- | --- | --- |
| 0 | Format-Version | `0x02` = Linien-/ROI-/multi_roi-Format (feste Konstante `MSG_LINE_ROI`) |
| 1 | Sensor-ID | 0–255, konfigurierbar über GUI/CLI (`--sensor-id`) |
| 2 | Sequenznummer (`frame_counter`) | 0–255, läuft pro Uplink um 1 hoch (Überlauf auf 0) |
| 3 | `interval_min` | Länge des Aggregationsintervalls in Minuten (0–255) |
| 4 | Status-Bitfeld | Bit 0 Kamera ok, Bit 1 KI-Beschleuniger (Hailo) aktiv, Bit 2 Konfiguration geladen, Bit 3 Werte seit letztem bestätigten Uplink gepuffert (vorheriger Sendeversuch fehlgeschlagen), Bit 4 Teilintervall (Start mitten im Intervall), Bit 5–7 reserviert (`lora_message.py:54-61`) |
| 5 | Klassen-Bitmaske | 1 Bit je Klasse in kanonischer Reihenfolge (Bit 0 = `person` … Bit 5 = `truck`); markiert, welche Klassen laut Konfiguration aktiv sind |
| 6–7 | `person` [IN][OUT] | je 1 Byte, 0–255, bei Überlauf auf 255 gekappt (kein Wrap-Around) |
| 8–9 | `bicycle` [IN][OUT] | wie oben |
| 10–11 | `car` [IN][OUT] | wie oben |
| 12–13 | `motorcycle` [IN][OUT] | wie oben |
| 14–15 | `bus` [IN][OUT] | wie oben |
| 16–17 | `truck` [IN][OUT] | wie oben |

Regeln:
- Inaktive Klassen (laut `roi_config.json`) belegen ihren Slot immer mit
  `00 00`, unabhängig von etwaigen internen Zählwerten
  (`lora_message.py:98-99` Docstring, `lora_message.py:117-118` Code).
- Übertragen wird je aktiver Klasse der **Zuwachs (Delta)** an IN/OUT seit dem
  letzten erfolgreich bestätigten Uplink, nicht der Gesamtstand
  (`lora_message.py:207-213`).
- `multi_roi` (mehrere benannte Flächen) wird über ein konfiguriertes
  IN-Feld (`roi_config.json` → `in_field`) auf dasselbe Format abgebildet:
  Übergang aus einer Nicht-IN-Fläche in eine IN-Fläche = IN, umgekehrt = OUT,
  alle anderen Übergänge werden nicht gewertet (`lora_message.py:251-261,
  296-334`).

### Format 3 — Übergangsmatrix als JSON (nur MQTT)

Quelle: `uebergangs_payload.py:16-53, 207-224`.

```json
{
  "format": 3,
  "sensor_id": 1,
  "sequenz": 7,
  "gesendet_am": "2026-07-24T13:05:00Z",
  "intervall_min": 5,
  "status": {
    "kamera_ok": true,
    "beschleuniger_ok": true,
    "konfig_ok": true,
    "gepuffert": false,
    "teilintervall": false
  },
  "felder": ["office", "ausgang", "Vorlesung", "Anlage"],
  "in_feld": ["office"],
  "uebergaenge": [
    { "von": "Anlage", "nach": "office", "klasse": "person", "anzahl": 3 }
  ],
  "summen": { "person": { "in": 5, "out": 2 } }
}
```

Felder:

| Feld | Bedeutung |
| --- | --- |
| `format` | Konstante `3` |
| `sensor_id` | wie im 18-Byte-Format |
| `sequenz` | 0–65535, läuft je erfolgreichem Versand hoch, Überlauf auf 0 (`uebergangs_payload.py:258`) |
| `gesendet_am` | UTC-Zeitstempel des Sendezeitpunkts (nicht der Einzelereignisse) |
| `intervall_min` | Aggregationsintervall in Minuten |
| `status.*` | dieselbe Bedeutung wie die Statusbits im 18-Byte-Format, hier als benannte Booleans |
| `felder` | Namen aller konfigurierten Flächen |
| `in_feld` | Liste der als IN markierten Flächen |
| `uebergaenge` | Liste von `{von, nach, klasse, anzahl}` — nur Kombinationen mit `anzahl > 0`, keine volle Matrix (Begründung: bei 4 Feldern × 6 Klassen wären 72 mögliche Kombinationen fast alle leer, `uebergangs_payload.py:34-37`) |
| `summen` | dasselbe IN/OUT-Faltungsschema wie Format 2, zur Vergleichbarkeit mit den LoRa-Nachrichten (`uebergangs_payload.py:226-250`) |

Datenschutzhinweis aus dem Code: übertragen werden ausschließlich
abgezählte Übergänge pro Intervall, keine Einzelereignisse (keine
Zeitpunkte einzelner Personen, keine Kennungen, keine Koordinaten, keine
Bilder) — bei sehr kurzen Intervallen mit nur einem Übergang entspricht die
Nachricht faktisch der Bewegung einer einzelnen Person, weshalb ein
Intervall von mehreren Minuten auch aus Datensparsamkeit gewählt wird
(`uebergangs_payload.py:42-53`).

---

## Zähl- und Flush-/Finalize-Logik

### Zählmodi (`counting.py`)

| Modus | Klasse | Kurzbeschreibung |
| --- | --- | --- |
| `line` | `LineCounter` (`counting.py:141`) | Zwei Punkte definieren eine virtuelle Linie; Kreuzungstest zwischen Start- und Endposition eines Tracks (`counting.py:168`) |
| `roi` | `RoiCounter` (`counting.py:209`) | Ein Polygon (≥3 Punkte); zählt Betreten/Verlassen der Fläche (`counting.py:232`) |
| `multi_roi` | `MultiRoiCounter` (`counting.py:269`) | Mehrere benannte Flächen; zählt Übergänge zwischen ihnen als `"A->B"` (`counting.py:340`) |

`multi_roi` kennt zusätzlich das Sentinel `OUTSIDE = "außerhalb"` für Punkte
außerhalb aller definierten Flächen (`counting.py:292`), optional per
`snap_to_nearest` der nächstgelegenen Fläche zugeordnet statt als "außerhalb"
gezählt (`config.py:115-118`).

### Feld `in_field`

`roi_config.json` → `in_field`: Liste von Flächennamen, die als IN-Bereich
gelten (`config.py:73-78`). Ältere Konfigurationsdateien speichern hier einen
einzelnen String statt einer Liste; beide Formen werden über
`normalize_in_fields()`/`_in_felder_normalisieren()` vereinheitlicht gelesen
(`lora_message.py:264-274`, `uebergangs_payload.py:117-127`). Nur relevant
für `mode="multi_roi"` — bestimmt, wie die Übergangsmatrix auf das IN/OUT-Schema
für Format 2 (18-Byte) bzw. `summen` in Format 3 gefaltet wird.

### Flush-Logik (`tracking.py`)

`flush_stale(current_frame)` (`tracking.py:198-217`) entfernt und protokolliert
Objekte, die seit `FRAMES_UNTIL_GONE = 30` Frames nicht mehr gesehen wurden
(`config.py:151`), pro Klasse getrennt. Für jeden geflushten Track:
1. Durchschnittskonfidenz anhängen (`_attach_avg_confidence`).
2. Optional (nur wenn `DEBUG_FILES_ENABLED`) Eintrag in `ergebniss.csv`
   (`log_track_event_csv("FLUSH", ...)`) — Debug-Datei, standardmäßig aus
   im Feldbetrieb, siehe `config.py:210-222`.
3. `_check_counting(data)`: prüft, ob die Strecke Start→Ende die
   Zählgeometrie kreuzt, und schreibt das Ergebnis **immer** (unabhängig vom
   Debug-Schalter) nach `zaehlung.csv` (`tracking.py:162-196`,
   `config.py:217-220`).

### Finalize-Logik

`finalize()` (`tracking.py:219 ff.`) wird bei EOS oder Strg-C aufgerufen,
schreibt alle noch aktiven (nicht geflushten) Tracks ebenfalls über denselben
`_check_counting()`-Pfad nach `zaehlung.csv`, erzeugt eine
Konsolen-Zusammenfassung und (sofern `DEBUG_FILES_ENABLED`) das
Bewegungsbild. Race-Condition-Schutz: `self.finalized`-Flag wird **innerhalb**
des Locks geprüft und gesetzt, damit zwei nahezu gleichzeitige Aufrufe (z. B.
echtes EOS und ein manuell ausgelöster Shutdown) sich nicht gegenseitig
überschreiben (`tracking.py:225-241`).

### `zaehlung.csv` — maßgebliche Quelle für die Übertragung

Spalten: `timestamp, display_id, label, direction, is_transition`
(`logging_utils.py:27`). Beide Sendewege (`lora_message.py`,
`uebergangs_payload.py`) lesen ausschließlich Zeilen mit `is_transition ==
True` (`lora_message.py:153`, `uebergangs_payload.py:190`) — Zeilen mit
`is_transition == False` (protokolliert, aber kein echter Übergang, z. B. bei
`multi_roi` Start und Ende im selben Bereich) fließen NICHT in die
Zählwerte ein.

---

## Dauerbetrieb 18.08.–23.08.2026

Im Repository selbst findet sich **keine Log- oder Betriebsdatei mit
konkreten Zeitstempeln** für diesen Zeitraum (Laufzeit-Ausgaben wie
`zaehlung.csv`, `ergebniss.csv`, `app_settings.json` sind laut `.gitignore`
bewusst nicht versioniert, siehe `.gitignore`). Die folgenden Angaben
beschreiben deshalb nur die **Konfigurationsmechanik**, mit der ein
Dauerbetrieb in diesem Zeitraum gelaufen sein könnte — nicht den tatsächlich
gelaufenen Betrieb selbst:

- **Autostart:** `start_app.sh` — aktiviert die venv (`setup_env.sh`), wärmt
  die Pipeline einmalig auf (`python warmup.py`, sequenziell USB-Kamera UND
  der zuletzt in der App gewählte Input, siehe `warmup.py`), startet dann
  `python app.py --autostart` (`start_app.sh:1-28`). Der GUI-seitige
  Autostart-Mechanismus (z. B. `--autostart`-Flag in `app.py`) startet beim
  Hochfahren automatisch die Zähl-Pipeline mit dem zuletzt konfigurierten
  Input. Der eigentliche Desktop-Autostart-Eintrag (`.desktop`-Datei bzw.
  Systemdienst), der `start_app.sh` beim Booten aufruft, liegt **nicht im
  Repository** (weder als `.desktop`- noch als `.service`-Datei gefunden) —
  laut Kommentar in `start_app.sh:5` wird er separat als
  "Desktop-Autostart-Eintrag" eingerichtet, dessen genaue Konfiguration ist
  **nicht im Repo dokumentiert**.
- **Reporting-Zyklus:** über die GUI (Tab 3) konfigurierbar, persistiert in
  `app_settings.json` (nicht im Repo, geräte-/nutzerspezifisch,
  `.gitignore`). Als Vorbelegung für eine frische Installation gelten die
  Werte aus `tabs/settings_store.py` (`DEFAULTS`): MQTT-Intervall 5 Minuten
  (`"mqtt_interval": "5"`), LoRa-Intervall 5 Minuten
  (`"lora_interval": "5"`), Debug-Funktionen standardmäßig AUS
  (`"debug_enabled": False`). Ob und mit welchen tatsächlich abweichenden
  Werten im Zeitraum 18.08.–23.08.2026 gesendet wurde, ist **nicht im Repo
  dokumentiert** (die tatsächlich genutzte `app_settings.json` des Geräts ist
  nicht Teil des Repositories).
- **Persistenz gegen Stromausfall:** alle Einstellungen (inkl. Reporting-
  Intervalle) werden sofort bei jeder Änderung geschrieben, nicht erst beim
  Beenden (`app.py::_wire_settings_autosave()`, laut Commit-Historie/ToDo.md
  ergänzt, um einen Dauerbetrieb ohne sauberes Herunterfahren zu überstehen).

---

## Einschränkungen

- **Kein pandoc/Dokumenten-Tool nötig gewesen** — alle Angaben stammen
  direkt aus dem gelesenen Quellcode und den Markdown-Dokumenten des
  Repositories; die `.docx`/Serverseite dieses Projekts wurden hier nicht
  einbezogen.
- **Keine Laufzeitdaten geprüft.** `zaehlung.csv`, `ergebniss.csv`,
  Log-Dateien, `app_settings.json` und `roi_config.json` sind laut
  `.gitignore` bewusst nicht im Repository (geräte-/laufspezifisch) — die
  konkreten Zählwerte, Sensor-IDs, Broker-Adressen und tatsächlich gesendeten
  Payloads des Dauerbetriebs 18.08.–23.08.2026 konnten deshalb nicht aus dem
  Repo belegt werden.
- **Keine Geheimnisse im Repository gefunden.** Eine gezielte Suche nach
  Passwort-/Token-/Schlüsselfeldern (`password`, `token`, `secret`,
  `apikey` u. ä.) in allen `.py`-Dateien ergab nur Code-Stellen, die solche
  Werte als **Laufzeit-Parameter entgegennehmen** (z. B.
  `mqtt_send_loop.py --benutzer/--passwort`) oder aktiv **redigieren**
  (`tests/lora_hardware/la66_probe.py`, maskiert DEUI/APPEUI/APPKEY/NWKSKEY/
  APPSKEY/DADDR in seiner eigenen Ausgabe). Es waren daher keine Werte durch
  `[REDACTED]` zu ersetzen; sollten künftig doch konkrete Zugangsdaten,
  IP-Adressen, Hostnamen oder WLAN-Namen ins Repository gelangen, sind sie
  vor jeder Weitergabe entsprechend zu maskieren.
- **Kameramodell, LTE-Stick-Modell und produktives Netz (ChirpStack)** sind
  ausschließlich Kontextwissen aus der Aufgabenstellung, nicht aus dem
  Repository-Code oder dessen Dokumentation belegbar — im Text entsprechend
  als "nicht im Repo dokumentiert" gekennzeichnet.
- **Erkennungsmodell (konkretes `.hef`)** im Dauerbetrieb: nicht aus dem Repo
  ableitbar, da `hailo_apps` ohne explizite Angabe automatisch ein
  Standardmodell wählt und keine feste Modelldatei im Code hinterlegt ist.
