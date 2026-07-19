# HANDOFF — Personenzähl-Prototyp (Stadtwerke Potsdam)

**Zuletzt aktualisiert: 19.07.2026 (Mitschnitt für Benchmarkläufe ergänzt; Befund: IN-Feld nicht gesetzt)**
*(Dieses Datum bei jeder inhaltlichen Änderung mit hochziehen — siehe Hinweis ganz unten.)*

Diese Datei ist der schnelle Einstieg ins Projekt: Was ist das, wo liegt was,
was funktioniert gerade, was ist als Nächstes dran. Details stehen in
`ToDo.md` (Implementierung, gleicher Ordner) und
`../abschlussarbeit/Statusbericht_Gliederung_Checkliste.md`
(Bachelorarbeit).

**Praxis ab sofort:** Wenn eine Lösung auf recherchierten externen Quellen
beruht (Hailo-Community, GitHub-Docs o. ä.), wird die Quelle direkt bei der
Lösung mit notiert — auch bei Zwischenständen, die noch nicht fertig
funktionieren. Spart beim nächsten Anlauf die erneute Suche.

## 0. Grundregel zum Bildmaterial

**Im Normalbetrieb speichert der Sensor keine Bilddaten.** Frames werden auf
dem Gerät verarbeitet und verworfen; nach aussen gehen ausschliesslich
aggregierte Zählwerte. Das ist kein Nebenaspekt, sondern das
Privacy-by-Design-Argument, auf dem die Architekturentscheidung (Edge statt
Cloud) in der Arbeit beruht.

Seit dem 19.07. gibt es eine **Mitschnittfunktion** (`recording.py`), die
parallel zum Zähllauf Video aufzeichnet. Sie ist **ausschliesslich für
Benchmarkläufe** gedacht — also für die Frage, wie genau der Sensor zählt —
und standardmässig **abgeschaltet**. Sie darf im Feldeinsatz nicht verwendet
werden. Regeln, Konfiguration und die Formulierung für die Arbeit:
[`../entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md`](../entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md).

## 1. Worum geht's

Bachelorarbeit: *Entwicklung eines Computer-Vision-basierten Sensors zur
automatisierten Besucherzählung*, Praxispartner Stadtwerke Potsdam,
Anwendungsfall Volkspark Biosphäre (17 Eingänge). Methodik: Design Science
Research Methodology (DSRM). Läuft auf Raspberry Pi 5 (8 GB) mit
Hailo-8-KI-Beschleuniger, YOLO-Objekterkennung über GStreamer.

Abgabetermin (Annahme, bitte bestätigt halten): **31.07.2026**.

## 2. Wo liegt was

```
core/                   ← Hauptordner auf dem Pi, läuft aktuell dort
├── app.py                      ← ZENTRALE STEUER-APP (CustomTkinter, Sidebar-Navigation) — Standard-Einstieg
├── core.py                     ← Einstiegspunkt der Pipeline: Pipeline-Klasse, Pro-Frame-Callback, __main__
├── tracking.py                 ← TrackingState-Klasse: Tracks anlegen/aktualisieren/flushen, finalize()
├── counting.py                 ← Zähllogik: LineCounter/RoiCounter/MultiRoiCounter, Geometrie-Helfer, build_counter()
├── visualization.py            ← Live-Overlay (OpenCV) + Bewegungsbilder (Pillow) + Zählgeometrie zeichnen
├── logging_utils.py            ← Schreibt ergebniss.csv (Zwischenspeicher aller Tracks) und zaehlung.csv
├── csv_utils.py                 ← Schema-Sicherheitsprüfung für alle CSV-Schreiber (verhindert Spalten-Drift)
├── cleanup_utils.py             ← archive_previous_run(): räumt Artefakte des Vorlaufs beim Start weg
├── config.py                   ← Zentrale Konstanten, lädt roi_config.json, per Env-Var überschreibbare Werte
├── frame_utils.py               ← GUI-freie Frame-/Auflösungsbeschaffung aus Datei (nur cv2+os)
├── roi_config_app.py           ← Zählgeometrie-Werkzeug (CustomTkinter), eigenständig ODER in app.py Seite 2 eingebettet (nimmt frame_width für feste Layout-Breite)
├── ctk_dialogs.py               ← CustomTkinter-Dialoge (Ersatz für tkinter.messagebox/simpledialog, im dunklen App-Design)
├── ui_utils.py                  ← make_scrollable() — gemeinsame CTkScrollableFrame-Hilfsfunktion für app.py + roi_config_app.py
├── auto_config.py              ← Paket 1+2: Datensammlung (auto_config_points.csv) + Batch-Einteilung
├── auto_config_clustering.py   ← Paket 3+4: DBSCAN-Clustering ODER Randraster + Cluster→Zählgeometrie (GUI-frei, nutzt frame_utils)
├── lora_message.py             ← LoRa-Nachrichtenformat (18-Byte v2): Frame bauen, IN/OUT aus zaehlung.csv lesen, Hinweistext für Tab 3, decode_frame() als Referenz-Decoder. Nur Standardbibliothek.
├── lora_send_loop.py           ← LoRa-Sender, läuft als eigener Subprozess (--live-counts). Liest nur zaehlung.csv, sendet per AT+SENDB an den LA66.
│
├── docs/                       ← GESAMTE Dokumentation, thematisch sortiert (Wegweiser: docs/README.md)
│   ├── projekt/                    HANDOFF.md (diese Datei) + ToDo.md — der laufende Stand
│   ├── abschlussarbeit/            Gliederung (DSRM), Statusbericht, Zeitplan, Architekturentwurf, Abbildungen
│   ├── einrichtung/                Gerät aufsetzen, LA66 einrichten, eigenes Git-Repository
│   ├── lora/                       Nachrichtenformat-SPEZIFIKATION (verbindlich), Integrations-Changelog, Recherche
│   └── entwicklung/                Änderungshistorie, gelöste Probleme, Analysen
│
└── tests/                      ← Diagnose- und Hardware-Testskripte, NICHT Teil des Normalbetriebs (siehe tests/README.md)
    ├── kamera/                     camera_test.py — Kamera ohne Hailo prüfen
    └── lora_hardware/              LA66-/Sonel-Sondierung, Offline- und TTN-Test, historische Serialisierung,
                                    sowie ttn_payload_decoder.js (im TTN hinterlegt, Empfängerseite)
```

**Wichtig zur Orientierung:** `tests/lora_hardware/` enthält *Vorstufen*.
Produktiv gelten `lora_message.py` und `lora_send_loop.py` im Hauptordner; die
alte `lora_transmitter.py` und `lora_send_loop_STAND_vor_integration.py` liegen
nur noch als Nachweis des Vorgehens dort.

Ausführen (Standardweg, alles über die App):
```bash
pip install customtkinter --break-system-packages   # einmalig
python app.py
```
Seite 1 (Input) → Seite 2 (Konfiguration, inkl. Auto-Verfahren-Auswahl) → Seite 3 (Start/Stopp) → Seite 4 (Live-Auswertung) → Seite 5 (Auto-Konfiguration: Datensammlung).

Für die automatische Wegerkennung (Auto-Konfiguration) siehe Abschnitt 3 —
kompletter Befehlsablauf dort. Die Einzelskripte (`core.py`, `roi_config_app.py`,
`auto_config.py`, `auto_config_clustering.py`) bleiben auch eigenständig auf der
Kommandozeile nutzbar, `app.py` bündelt sie nur.

Weitere relevante Dateien im Repo:
- `roi_config.json` — von `roi_config_app.py` oder `auto_config_clustering.py --save` geschrieben, von `config.py` beim Start gelesen. Enthält `mode` ("line", "roi" oder "multi_roi"), `points` (2 Punkte bei Linie, 3+ bei einzelner Fläche), `regions` (nur bei "multi_roi": Liste benannter Flächen `{"name", "points"}`), `classes`, `reverse_direction`, `snap_to_nearest` (nur "multi_roi": Punkte außerhalb aller Flächen der nächstgelegenen zuordnen). Alle Koordinaten normalisiert 0.0-1.0. Fehlt die Datei, greifen Defaults in `config.py` (horizontale Linie, alle 6 Klassen).
- `ergebniss.csv` — **Zwischenspeicher aller Tracks des aktuellen Laufs** (wird beim Start frisch angelegt, siehe `vorherige_laeufe/` unten). Eine Zeile pro abgeschlossenem Track. Spalten: display_id, kind (FLUSH/FINALIZE), track_id, label, start_x/y, end_x/y, **avg_confidence** (über alle Frames des Tracks gemittelte Erkennungskonfidenz 0.0-1.0, leer wenn kein Wert vorlag), first/last_timestamp. Nur Klassen aus `TRACKED_LABELS`. Für spätere Auswertung, z. B. Nearest-Neighbor-Clustering der Start-/Endpunkte. **`ergebniss.txt` gibt es nicht mehr** — die maschinenlesbare CSV ist die einzige Track-Ausgabe.
- `zaehlung.csv` — ein Eintrag pro Zähl-Ereignis (timestamp, display_id, label, direction, **is_transition**). `is_transition=False` kennzeichnet Fälle, die protokolliert aber NICHT gezählt wurden (z. B. bei `multi_roi`: Start und Ende im selben Bereich, "A (kein Wechsel)")
- `vorherige_laeufe/<Zeitstempel>/` — beim Start eines echten Zähllaufs (nicht im Snapshot-Modus) verschiebt `cleanup_utils.archive_previous_run()` alle Artefakte des Vorlaufs hierher (ergebniss.csv, zaehlung.csv, Bewegungsbilder, auto_config_points.csv, Kontrollbilder). **Bewahrt** bleiben `roi_config.json` und `camera_raw.png`. Sauberer Erststart erzeugt keinen Ordner.
- `*_altes_format_<Zeitstempel>.csv` — von `csv_utils.py` automatisch archivierte Dateien, wenn ihre Kopfzeile nicht mehr zum aktuellen Spaltenschema passt (siehe Abschnitt 4a). Reine Backups, keine Track-Daten für den laufenden Betrieb.
- `auto_config_points.csv` — nur wenn `AUTO_CONFIG_COLLECTION_ENABLED = True`: Start- und Endpunkt jedes Tracks als zwei Zeilen (timestamp, display_id, label, point_type, x, y) — Rohdaten für die Auto-Konfiguration
- `camera_raw.png` — von `roi_config_app.py --input usb` geschrieben, **immer überschrieben**: letztes aufgenommenes Kamerabild
- `auto_config_clusters.png` — von `auto_config_clustering.py` geschrieben, **immer überschrieben**: Kontrollbild mit allen Punkten (farblich je Cluster, grau = Ausreißer) und den daraus gebildeten Flächen — vor `--save` anschauen
- `bewegungsbild_<Zeitstempel>_flush.png` / `bewegungsbild_<Zeitstempel>_finalize.png` — zwei Bewegungsbilder je Lauf, in Video-Auflösung, mit lesbaren Labels wie `car_ID_3`. **flush**: alle während des Laufs per Timeout geflushten Tracks; **finalize**: alle beim Programmende noch aktiven Tracks. Beide werden am Programmende erzeugt.
- `auto_config_border.png` — von `auto_config_clustering.py --border` geschrieben, **immer überschrieben**: Kontrollbild für den Randraster-Modus (grün = gewertete Überquerung, grau = aussortiert)
- LoRa schreibt **keine** eigene Ausgabedatei: der Sender protokolliert nach stdout, was `app.py` mit `[LoRa]`-Präfix in die Live-Konsole (Tab 4) leitet. Gesendet wird ausschließlich aus `zaehlung.csv`.
- `VideoApp.py` — **veraltet**, durch `roi_config_app.py` ersetzt (war komplett isoliert, `core.py` hat nie etwas aus ihr gelesen). Kann aus dem Repo entfernt werden.

## 3. Aktueller Stand (Kurzfassung — Details in `ToDo.md`)

**Funktioniert:**
- Hailo-8 + YOLO-Erkennung für person, bicycle, car, motorcycle, bus, truck
- Alle Klassen werden korrekt einzeln getrackt (nicht mehr nur "person") — `hailotracker` läuft mit `class-id=-1`
- Pro Klasse getrennte, lesbare IDs (`car_ID_1`, `person_ID_1`, ...) statt der rohen, klassenübergreifend geteilten Hailo-ID
- Automatisches Flushen nach 30 Frames ohne Sichtung
- Zwei Bewegungsbilder (in echter Videoauflösung) pro Lauf — je eins für Flush- und Finalize-Tracks — und `ergebniss.csv` als Track-Zwischenspeicher (kein `ergebniss.txt` mehr)
- Programm stoppt automatisch nach einem Videodurchlauf bei Datei-Input (siehe Abschnitt 4a)
- Code modularisiert (siehe Ordnerstruktur oben)
- **CSV-Schreiber sind schema-sicher** (`csv_utils.py`) — verhindert Spalten-Drift (siehe 4a)
- **Auto-Konfiguration komplett gebaut**, zwei Verfahren: DBSCAN-Clustering ODER festes Randraster (Randraster empfohlen, wenn die Objekterkennung Tracks öfter verliert und dadurch Geister-Startpunkte in der Bildmitte entstehen — Randraster ordnet Punkte stattdessen der nächstgelegenen Randfläche zu und filtert zu kurze/unplausible "Überquerungen" heraus). Beide Verfahren jetzt als gleichwertiger Zählmodus direkt in `roi_config_app.py` (nicht mehr separates Kommandozeilen-Tool).
- **`app.py` — zentrale Steuer-App**, ersetzt den Bedarf, mehrere Skripte von Hand zu koordinieren. Fünf Seiten über eine Sidebar-Navigation: Input wählen → Konfiguration (bettet `roi_config_app.py` komplett ein, inkl. beider Auto-Modi zur Auswertung) → Start/Stopp (startet `core.py` als normalen Zähllauf, standardmäßig OHNE Zeitlimit) → Live-Auswertung (Konsole + aktuelle Zählerstände live) → Auto-Konfiguration (Datensammlung mit Zeitlimit, danach in Seite 2 auswerten). Layout mit festen Breitenverhältnissen (1/5 Sidebar, ~3/5 Frame, ~1/5 Konfig-Spalte), Fenster in der Breite fixiert.
- **UI-Bibliothek umgestellt auf CustomTkinter** (dunkles Theme, blaue Akzente) — sieht deutlich moderner aus als das alte Tkinter-Grau. **Laut Nutzer-Feedback noch verbesserungsbedürftig** (Details noch nicht spezifiziert, siehe ToDo.md).
- **USB-/Pi-Kamera-Referenzbild kommt jetzt aus der echten Pipeline** (`CORE_SNAPSHOT_ONLY`-Modus in `core.py`, angestoßen von `roi_config_app.py`), nicht mehr aus einer unabhängigen `cv2.VideoCapture()`-Aufnahme — behebt eine bestätigte Diskrepanz, bei der Konfigurationstool und Live-Bild unterschiedliche Auflösungen/Bildausschnitte zeigten (siehe 4a).

**Kompletter Befehlsablauf Auto-Konfiguration (Kurzfassung, jetzt über die App):**
1. `pip install scikit-learn --break-system-packages` (einmalig)
2. App starten, Seite 5 (Auto-Konfiguration): Sammeldauer setzen, „Datensammlung starten"
3. Seite 2: Zählmodus „Auto: Clustering" oder „Auto: Randraster" wählen, Parameter setzen, „Auswerten" (zeigt Kontrollbild direkt im Canvas), „Speichern"
4. Seite 3: normalen Zähllauf starten — nutzt automatisch die neu erzeugten Flächen

**LoRa-Übertragung — INTEGRIERT UND IM ECHTBETRIEB BESTÄTIGT (18.07.):**
Sensordaten kommen online per LoRa an. Der Versand ist Teil von `core/` und in
Tab 3 der App zuschaltbar.

> ⚠️ **Aber: aktuell werden Nullwerte übertragen.** Die Gerätekonfiguration
> steht auf `multi_roi` (Berlin/Potsdam), hat aber **kein `in_field` gesetzt**.
> Ohne IN-Feld kann der Sender keine IN/OUT-Werte ableiten und schickt formal
> korrekte Frames mit lauter Nullen — im TTN kommen also Uplinks an, die nichts
> aussagen. Behebung: Tab 2 → Modus „Mehrere Flächen" → IN-Feld auswählen und
> speichern. Siehe `ToDo.md`, Abschnitt „Sofort erledigen".
- **Hardware: Dragino LA66 USB LoRaWAN Adapter** (EU868), eingerichtet nach
  `EINRICHTUNG_LA66.md`. AT-Format: `AT+SENDB=<confirm>,<Fport>,<len>,<hexdata>`,
  FPort 2, unbestätigte Uplinks.
- **Nachrichtenformat: `lora_message.py`** — 18-Byte-Zählformat v2 (Header 6 Byte
  + 6 Klassen x [IN][OUT]). Das ist die **eine** Stelle, an der das Format
  definiert ist; `decode_frame()` dort dient als Referenz-Decoder für die
  Empfängerseite. Ein einziges Format für alle Zählmodi.
- **Sender: `lora_send_loop.py --live-counts`** läuft als **eigener Subprozess**
  und liest nur die von `core.py` geschriebene `zaehlung.csv`. `core.py` und
  `tracking.py` sind bewusst unangetastet — ein LoRa-Fehler kann die
  Zähl-Pipeline nicht gefährden. Ausgabe erscheint mit `[LoRa]`-Präfix in der
  Live-Konsole (Tab 4).
- **Kein Datenverlust bei Funklöchern:** gesendet wird der Zuwachs seit dem
  letzten *erfolgreichen* Uplink; der Referenzstand wird erst nach Bestätigung
  nachgezogen. Ein misslungenes Intervall kommt beim nächsten Erfolg mit.
- **Mehrere-Flächen-Modus:** über ein in Tab 2 gewähltes **IN-Feld**
  (`"in_field"` in `roi_config.json`) auf dasselbe IN/OUT-Format abgebildet —
  Übergang `X -> IN-Feld` = IN, `IN-Feld -> X` = OUT, andere Übergänge zählen
  nicht.
- **Offen:** Header-Bytes 3–4 (im alten Test-Frame `05 07`) sind nur in
  `lora_transmitter.py` definiert, die nicht in `core/` vorliegt — aktuell als
  Status/reserviert belegt, bei Wiederauffinden gegenprüfen. Ebenso setzen die
  Auto-Modi noch kein `in_field`.
- Historisch: Sonel LORA-S1 war ein Sackgassen-Fund (`bInterfaceClass 255`,
  proprietär, keine Antwort auf Probe-Skript) — siehe Abschnitt 4a.

**Fehlt noch (Details/Priorisierung in `ToDo.md`):**
Die drei aktuellen Arbeitspakete (Stand 18.07.):
1. **Konfigurationen genau durchgehen** — alle Modi systematisch prüfen: was
   wird gespeichert, was liest `core.py` wirklich, wo weichen Tool und
   Laufzeit voneinander ab
2. **UI-Probleme beheben** — erneut aufgetreten, konkrete Symptome noch nicht
   festgehalten (beim nächsten Auftreten Tab + Verhalten notieren!)
3. **Genauigkeit untersuchen, Einfluss der Confidence** — inhaltlich der
   wichtigste Punkt für die Arbeit: Ground Truth erstellen, Confidence-Schwelle
   variieren (Ansatzpunkt `counting.should_count_track()`), Fehlerarten
   getrennt auswerten

Danach/parallel:
4. Kreuzungserkennung mit echten Tracking-Daten verifizieren — weiterhin offen
5. Datensammlung (`AUTO_CONFIG_COLLECTION_ENABLED`-Workflow) anpassen
6. Live-Bild-Spiegelung bei `--input usb` weiterhin ungelöst (siehe 4b)
7. Aggregierte Zählerstände über einen ganzen Betriebstag persistieren
8. Gehäuse, finale Hardware-Beschaffung
9. Labor-/Realtest (an der Uni vorgeschlagen, siehe Statusmail an Betreuer)

**In Arbeit, noch nicht zuverlässig (Details in Abschnitt 4b):**
- Zweites Anzeigefenster unterdrücken (nur "User Frame" behalten)
- Live-Bild bei `--input usb` ist gespiegelt (Fix als Option vorhanden, Wirksamkeit unbestätigt)

## 4a. Bereits gelöste Probleme (nicht nochmal debuggen)

- **Frame-Anzeige-Crash geklärt (15.07.)** — der Absturz `std::system_error: Invalid argument` nach mehreren tausend Frames hängt an der **Live-Vorschau** (`--use-frame`/View-Fenster), NICHT am Tracking. Ohne View läuft die Pipeline durch. Konsequenz: Für Dauerläufe die Vorschau deaktiviert lassen; der Produktivbetrieb am Volkspark läuft ohnehin headless. App-seitig abgefedert (siehe nächster Punkt).
- **App hing nach nativem Crash auf „läuft (PID …)" (15.07.)** — `app.py` verließ sich allein auf das stdout-Signal `__PROCESS_ENDED__`, das bei hartem C++-Absturz nie kam. Fix: Liveness-Check per `process.poll()` im Poll-Loop erkennt toten Prozess auch ohne stdout; Status zeigt „ABGESTÜRZT (Signal N)"; Stop eskaliert SIGINT→SIGTERM→SIGKILL. Kein hängender Zombie mehr. Zusätzlich `flushed_objects` als `deque(maxlen=MAX_FLUSHED_OBJECTS)` gegen unbegrenztes Speicherwachstum bei Langläufen.
- **Zeitlimit galt versehentlich für ALLE Läufe (15.07.)** — `RUN_DURATION_SECONDS` hatte Default 300, wodurch auch normale Zählläufe nach 5 min stoppten. Default jetzt `None` (kein Limit). Zeitlimit nur noch: optionales Feld in Tab 3 (leer = kein Limit) und Sammeldauer in Tab 5.
- **Auto-Config-Datensammlung in eigenen Tab 5 isoliert (15.07.)** — die Datensammlung (früher als Block in Tab 3) ist jetzt ein eigener Tab „5. Auto-Konfiguration" mit eigener Sammeldauer. Die Verfahrens-Auswertung (Clustering/Randraster) bleibt in Tab 2. Normale Läufe (Tab 3) haben mit den Auto-Verfahren nichts mehr zu tun und laufen ohne Zeitlimit.
- **UI-Dialoge im App-Design (15.07.)** — alle `tkinter.messagebox`/`simpledialog`-Aufrufe (Warnungen, Fehler, Ja/Nein, Flächen-Namenseingabe) laufen jetzt über `ctk_dialogs.py` (CustomTkinter, dunkles Design, modal, Enter/Escape). Signatur-kompatibel, daher minimaler Umbau an den 20 Aufrufstellen. `filedialog` bleibt nativ.
- **Festes Layout 1/5–3/5–1/5, Fenster nicht breiter ziehbar (15.07.)** — alle Breiten aus `WINDOW_WIDTH` (1280) abgeleitet; Sidebar `//5`, Content mit `pack_propagate(False)`, Fenster per `maxsize` in der Breite fixiert. Der Frame-Canvas bekommt seine Breite von außen (`RoiConfigApp(frame_width=…)`) statt selbst die Fensterbreite zu diktieren. USB ist Standard-Input (oben in der Liste, vorausgewählt).
- **Ergebnis-Ausgabe umgebaut (15.07.)** — `ergebniss.txt` entfällt komplett; `ergebniss.csv` ist jetzt Track-Zwischenspeicher (bei Start frisch, siehe Cleanup) mit neuer Spalte `avg_confidence` (laufender Durchschnitt über alle Frames). Zwei getrennte Bewegungsbilder `bewegungsbild_<ts>_flush.png` / `_finalize.png` statt `tracked_objects_*` / `*_ENDE.png`. **An echten Daten verifiziert** (Lauf 12:27–12:31, 64 Tracks): ergebniss.csv ↔ zaehlung.csv 1:1-konsistent, avg_confidence korreliert klar mit Track-Qualität (lange Durchfahrten Ø 0.72, kurze Artefakt-Tracks Ø 0.43 — nutzbar als späterer Filter in `should_count_track()`).
- **Start-Cleanup (15.07.)** — `cleanup_utils.archive_previous_run()` verschiebt beim Start eines echten Laufs alle Vorlauf-Artefakte nach `vorherige_laeufe/<Zeitstempel>/` (bewahrt `roi_config.json` + `camera_raw.png`). Im Snapshot-Modus deaktiviert. Verifiziert.
- **Auto-Konfiguration von der GUI entkoppelt (15.07.)** — neue Datei `frame_utils.py` (nur cv2+os) übernimmt die Frame-/Auflösungsbeschaffung; `auto_config_clustering.py` importiert nicht mehr `roi_config_app` (tkinter/customtkinter). Auto-Config läuft damit ohne Display / in schlanker venv. `config.py` bleibt bewusst gemeinsame Parameterquelle. End-to-End mit echten Punkten getestet (DBSCAN + Randraster).
- **UI: Bedienfelder verschwanden beim Frame-Laden (15.07.)** — Ursache: Canvas wuchs beim Laden auf Frame-Größe und schob im grid die rechte Spalte aus dem Fenster. Fix in `roi_config_app.py`: feste Anzeigebox 1200×675, Frame wird immer seitenverhältnistreu hineinskaliert (auch hochskaliert) und zentriert; Klickkoordinaten um den Zentrier-Offset korrigiert. Layout/Fenstergröße bleiben jetzt konstant.
- **bus/truck erschienen trotz (vermeintlichem) Fehlen in `classes` — GEKLÄRT (kein Bug):** Der frühere Testlauf lief mit einer älteren `roi_config.json` ohne bus/truck. Die aktuelle Config enthält `person, bicycle, car, bus, truck`; der Klassenfilter (`if label not in TRACKED_LABELS: continue` in `core.py`) arbeitet korrekt — nur diese Klassen landen in den Ergebnissen.

- **Video lief nach Ende automatisch weiter ("Video rewound successfully...")**: lag an `on_eos()` in der Basisklasse, die bei Datei-Input absichtlich zurückspult. Fix: `on_eos()` in `MyDetectionApp` überschreiben statt `on_bus_message()`.
  Quelle: https://community.hailo.ai/t/stop-processing-video-files/11231
- **Nur "person" bekam echte Tracker-IDs, alle anderen Klassen immer `ID: 0`**: `hailotracker` trackt in der Basis-Pipeline standardmäßig nur eine Klasse (`class-id=1`). Fix: `class-id` auf `-1` setzen (`app.pipeline.get_by_name("hailo_tracker").set_property("class-id", -1)`, vor `app.run()`).
  Quellen: https://community.hailo.ai/t/how-to-change-the-class-hailo-tracker-is-tracking/12693 und https://github.com/hailo-ai/tappas/blob/master/docs/elements/hailo_tracker.rst
- **Bewegungsbild wurde manchmal leer überschrieben / Race Condition bei gleichzeitigen Aufrufen**: `finalize()` konnte zweimal (teils sogar gleichzeitig aus zwei Threads) laufen. Fix: `self.finalized`-Check-and-Set liegt jetzt *innerhalb* des Locks in `TrackingState.finalize()`, nicht davor — mit 20 gleichzeitigen Testaufrufen verifiziert, dass der Body garantiert nur einmal läuft.
- **Bekannte, noch offene Einschränkung**: `track_id` fällt auf `0` zurück, wenn der Tracker keine ID liefert. Durch die Klassentrennung in `tracking.py` kollidieren verschiedene Klassen dadurch nicht mehr; zwei ungetrackte Objekte *derselben* Klasse gleichzeitig könnten aber weiterhin kollidieren. Für die Arbeit als Limitation dokumentieren.
- **`VideoApp.py` war komplett isoliert von `core.py`**: Ersetzt durch `roi_config_app.py`, das `roi_config.json` schreibt; `config.py` lädt diese Datei automatisch beim Start (mit Fallback auf Standardwerte, falls sie fehlt).
- **`cv2.VideoCapture()` konnte auf dem Pi manche Videos nicht öffnen** (`roi_config_app.py`, Fehler "Konnte keinen Frame aus Video lesen"): vermutlich unvollständige FFmpeg-Unterstützung im installierten `opencv-python`. Fix: `load_first_frame()` versucht jetzt mehrere Backends nacheinander (Standard, FFMPEG, GSTREAMER) und gibt bei komplettem Fehlschlag einen konkreten ffmpeg-Workaround aus (Frame als Bild extrahieren, `--input frame.png` statt Video). Keine externe Quelle nötig, selbst gelöst.
- **Bei `multi_roi`: Start und Ende eines Tracks im selben Bereich wurden stillschweigend verworfen** (keine Zeile in `zaehlung.csv`), obwohl das potenziell interessant ist (z. B. Track bewegte sich A→außerhalb→A, aber die reine Start/Ende-Betrachtung sah nur "A==A"). Fix: `check_crossing()` gibt jetzt überall `(text, ist_übergang)` zurück statt nur einen String; bei `ist_übergang=False` wird trotzdem protokolliert (`zaehlung.csv`, neue Spalte `is_transition`), aber nicht mitgezählt.
- **🔴 CSV-Schema-Drift in `ergebniss.csv` und `zaehlung.csv`** (beim Code-Review am 05.07. entdeckt und in den echten Dateien auf dem Pi bestätigt: `ergebniss.csv` hatte 129 Zeilen mit 9 und 381 Zeilen mit 10 Spalten unter einer 9-Spalten-Kopfzeile; `zaehlung.csv` genauso 4 vs. 5 Spalten). Ursache: Die Kopfzeile wird nur beim allerersten Anlegen der Datei geschrieben — als später `display_id`/`is_transition` als Spalten ergänzt wurden, haben bereits bestehende Dateien einfach mit mehr Spalten weiterbekommen. Für jede spätere Auswertung (pandas o. ä.) wären das unsichtbar falsch einsortierte Werte gewesen. Fix: neue Datei `csv_utils.py` mit `ensure_current_schema()` — prüft einmal pro Programmlauf, ob eine bestehende Datei zum aktuellen Format passt, archiviert sie sonst automatisch (umbenannt, nicht gelöscht) und legt sie sauber neu an. Direkt gegen die echten kaputten Dateien getestet.
- **`roi_config_app.py --input usb` funktionierte nicht**: `cv2.VideoCapture("usb")` kann mit dem String "usb" nichts anfangen (das ist nur für die Hailo-Pipeline gedacht). Fix: Sonderfall in `load_first_frame()` — nimmt bei `--input usb` direkt ein Bild von einer angeschlossenen USB-Kamera auf (probiert Geräteindizes 0–3, verwirft 5 Warmup-Frames), speichert es immer überschreibend als `camera_raw.png`. Mit simulierter Kamera getestet, echte Hardware auf dem Pi noch zu bestätigen.
- **🔴 Konfigurationstool und Live-Fenster zeigten unterschiedliche Bildgröße UND Ausrichtung bei `--input usb`** (vom Nutzer per Screenshot bestätigt: 640×480 im Konfigurationstool vs. deutlich breiteres Seitenverhältnis im "User Frame"). Ursache: `roi_config_app.py` nahm den Referenzframe über eine EIGENE, unabhängige `cv2.VideoCapture()`-Aufnahme auf — konnte in Auflösung/Bildausschnitt vom tatsächlich von Hailos Pipeline verarbeiteten Frame abweichen. Fix: neuer Snapshot-Modus in `core.py` (`CORE_SNAPSHOT_ONLY`-Umgebungsvariable, siehe `config.py`) — speichert beim allerersten echten Frame ein Referenzbild und beendet sich sofort danach. `roi_config_app.py` stößt das für `--input usb`/`rpi` jetzt über einen kurzen `core.py`-Subprozessaufruf an, statt selbst auf die Kamera zuzugreifen — garantiert identische Auflösung/Bildausschnitt zum späteren Live-Betrieb, weil es exakt dieselbe Pipeline ist. Mit simuliertem `core.py` (bewusst andere Auflösung als Test) verifiziert.
- **Sonel LORA-S1 als LoRa-Hardware bestätigt ungeeignet**: `lsusb -v` zeigt `bInterfaceClass 255 (Vendor Specific)` — kein serielles USB-Gerät, keine öffentliche Protokolldokumentation. Mit `lora_hardware_probe.py` (5 Baudraten × 4 Testbefehle) keine einzige Antwort erhalten; das gefundene serielle Gerät (`/dev/ttyAMA10`) war eine unabhängige, unbenutzte Onboard-UART des Pi, nicht das Sonel-Gerät. Für diesen Zweck aufgegeben, siehe Abschnitt 3 für Kaufempfehlung (Dragino LA66).
- **`HAILO_OUT_OF_PHYSICAL_DEVICES(74)`-Fehler blockierte jeden core.py-Start**: Ursache war `subprocess.run(..., timeout=X)` in `roi_config_app.py`s Snapshot-Aufruf — bei Zeitüberschreitung schickt das automatisch SIGKILL, was den Hailo-8-Beschleuniger in einem gesperrten Zustand zurücklassen konnte, wenn `core.py` gerade mitten in der Geräte-Initialisierung war. Fix: `_capture_snapshot_via_core()` nutzt jetzt `subprocess.Popen` + eigenes Timeout-Handling — bei Zeitüberschreitung erst SIGINT (sauberes Herunterfahren über den bestehenden `finally`-Pfad abwarten), SIGKILL nur als letzter Ausweg nach 15s Gnadenfrist. Mit simuliertem Prozess (reagiert korrekt auf SIGINT bzw. ignoriert es testweise) verifiziert. Akutes Freiräumen eines bereits blockierten Chips bleibt manuell nötig (`ps aux | grep hailo`, betroffene Prozesse killen, ggf. `sudo systemctl restart hailort`, im Zweifel Neustart).
- **`--input usb`-Kaltstart wurde durch zu knappes Timeout abgeschnitten**: Nutzer-Beobachtung — "Frame laden" schlägt fehl, funktioniert aber, wenn vorher einmal die Pipeline über Seite 3 gestartet UND wieder gestoppt wurde. Ursache: Der allererste `core.py`-Aufruf seit dem letzten Pi-Neustart (HailoRT-/PCIe-Verbindung aufbauen, Modell laden) dauert deutlich länger als jeder folgende — Seite 3 ("Start") hat kein Timeout und lässt den Kaltstart durchlaufen, der Snapshot-Aufruf dagegen hatte ein festes Timeout (zuletzt 120s), das genau diesen Kaltstart abschnitt. Fix: Timeout auf 240s erhöht und nach `config.py` verschoben (`SNAPSHOT_TIMEOUT_SECONDS`, leicht anpassbar). **Wirksamkeit vom Nutzer noch zu bestätigen** — falls 240s immer noch nicht reichen, Wert weiter hochsetzen.

## 4b. Bekannte offene technische Probleme (in Arbeit, noch nicht gelöst)

- **Zwei Anzeigefenster ("User Frame" + "Hailo Detection App")**: Versuch, das `hailo_display`-Element (fpsdisplaysink) per `set_property("video-sink", fakesink)` auf lautlos zu schalten. Laut Nutzer-Feedback funktioniert das noch nicht zuverlässig — nächster Schritt: prüfen, ob das Element in der installierten Version wirklich `hailo_display` heißt (z. B. mit `--dump-dot`, siehe `running_applications.md`), oder ob `video-sink` als Property so nicht greift.
  Konsultierte Quellen: https://community.hailo.ai/t/how-can-i-stop-displaying-the-main-frame-in-detection-py-in-hailo-rpi5-examples/3020 , https://github.com/hailo-ai/hailo-apps/blob/main/doc/user_guide/running_applications.md
- **`std::system_error: Invalid argument` bei Langläufen**: Inzwischen eingegrenzt auf die **Live-Vorschau** (`--use-frame`), nicht auf das Zeitlimit oder das Tracking (siehe 4a). Ohne View läuft die Pipeline durch. Offen bleibt die eigentliche native Ursache (vermutlich Ressourcenerschöpfung in der Hailo/GStreamer-Ebene bei aktivem View-Fenster) — für den unbeaufsichtigten Dauerbetrieb ist ein Prozess-Watchdog (systemd `Restart=on-failure`) vorgesehen; die App-seitige saubere Absturzerkennung ist dafür schon vorhanden. Falls der Crash je ohne View auftritt: Thread-/FD-Zahl während des Laufs beobachten (`ls /proc/$(pgrep -f core.py)/task | wc -l`).
- **🔴 Live-Bild bei `--input usb` ist horizontal gespiegelt.** Vom Nutzer per Screenshot bestätigt: `camera_raw.png` (Referenzaufnahme) zeigt die Szene korrekt, das "User Frame"-Live-Fenster zeigt sie gespiegelt — **obwohl beide jetzt aus derselben Pipeline stammen** (seit dem Snapshot-Fix oben), was zunächst überraschend war. Aufgeklärt durch einen Nutzer-Screenshot einer Fehlermeldung, die Hailos tatsächlichen GStreamer-Pipeline-String zeigte: enthält explizit `videoflip name=videoflip video-direction=horiz` — Hailos eigene Pipeline-Konstruktion für `--input usb` spiegelt also aktiv, bestätigt statt nur vermutet. Warum der Snapshot (der denselben Frame VOR diesem Flip-Schritt aus dem Buffer liest, siehe `SNAPSHOT_ONLY`-Code in `core.py`) trotzdem unspiegelt bleibt: unser Snapshot greift auf `get_numpy_from_buffer()` zu, was vermutlich VOR dem `videoflip`-Element in der Pipeline sitzt. Fix bereitgestellt, aber **Wirksamkeit unbestätigt**: `LIVE_PREVIEW_HORIZONTAL_FLIP = True` in `config.py` spiegelt NUR das "User Frame"-Anzeigefenster zurück (nach unseren eigenen Overlays, betrifft die Zähllogik nicht). Laut jüngstem Nutzer-Feedback ("Das Bild ist immer noch gespiegelt") entweder noch nicht ausprobiert oder wirkungslos — als Nächstes klären, ob der Schalter überhaupt aktiviert wurde, bevor tiefer gesucht wird.
  Untersuchte Alternativen (siehe Chatverlauf): V4L2-Treiber-Flip (`v4l2-ctl --list-ctrls`, auf diesem Gerät vermutlich nicht vorhanden, ungetestet), `v4l2loopback` mit vorgeschaltetem spiegelnden GStreamer-Pipeline (funktioniert sicher, aber deutlich mehr Aufwand), ein `--hflip`/`--vflip`-CLI-Flag in hailo-apps existiert nur als **unfertiger, nicht gemergter Pull Request** und deckt ohnehin nur die Pi-Kamera ab, nicht USB.
- **UI (CustomTkinter) laut Nutzer noch verbesserungsbedürftig** — konkrete Punkte noch nicht spezifiziert. Bereits behoben: Emoji im Sidebar-Titel entfernt (wurde als Platzhalter-Kästchen dargestellt), `CTkCheckBox` akzeptiert kein `justify` (Absturz behoben). Nächster Schritt: Nutzer nach konkreten Kritikpunkten fragen (Layout? Farben? Bedienbarkeit? Größen?).
- **Datensammlung (`AUTO_CONFIG_COLLECTION_ENABLED`-Workflow) muss laut Nutzer nochmal angepasst werden** — konkrete Punkte noch nicht spezifiziert, im nächsten Gespräch klären.
- **`tests/kamera/camera_test.py` (eigenständiges Kamera-Diagnoseskript, keine Hailo-Abhängigkeit) bereitgestellt, aber Ergebnis vom Nutzer noch nicht zurückgemeldet** — sobald verfügbar, hilft das einzugrenzen, ob verbleibende Kamera-Probleme an der Kamera/dem Treiber liegen oder spezifisch an der Hailo-Pipeline.

## 5. Bezug zur Bachelorarbeit

Siehe `../abschlussarbeit/Statusbericht_Gliederung_Checkliste.md` für:
- Vollständige Gliederung (7 Kapitel nach DSRM)
- Kapitel-für-Kapitel-Status (inhaltlich vorbereitet? / geschrieben?)
- Offene Fragen an Betreuer und Stadtwerke Potsdam
- Zeitplan bis zur Abgabe (Detailversion: `../abschlussarbeit/Zeitplan_bis_Abgabe.xlsx`)

Relevant für Kapitel 5 (Design & Entwicklung): die Architektur aus Abschnitt 2
oben kann direkt als Grundlage für 5.3 Systemarchitektur dienen — insbesondere
die Zählgeometrie-Konfiguration (`roi_config_app.py`, jetzt in `app.py`
eingebettet) passt gut zur "Manuelle Konfiguration" aus dem
Anforderungsinterview, und die Auto-Konfiguration (DBSCAN ODER Randraster) zur
"Auto-Konfiguration"/"Teil-Auto-Konfiguration" aus demselben Interview. Die
zentrale Steuer-App (`app.py`) selbst eignet sich als Beleg für die
Umsetzung der Anforderung "einfache Bedienbarkeit ohne Kommandozeile". Die
Sonel-LORA-S1-Sackgasse (Abschnitt 3/4a) ist ein gutes, konkretes Beispiel für
6.4/7.2 (Grenzen der Hardware-Auswahl, Bedeutung offener vs. proprietärer
Schnittstellen). Die gelösten Probleme aus Abschnitt 4a eignen sich für 6.4 /
die Limitationen in Kapitel 7.2, die noch offenen Punkte aus 4b für die
kritische Reflexion in 7.2. Die CSV-Exportstruktur (`ergebniss.csv`,
`zaehlung.csv`, `auto_config_points.csv`) ist die Datengrundlage für den in
5.4 bzw. 6 zu beschreibenden Clustering-Ansatz.

**Neu ab 18.07. — für Kapitel 6 (Evaluation) zentral:** Die anstehende
Genauigkeitsuntersuchung (Einfluss der Confidence-Schwelle) liefert das
eigentliche empirische Ergebnis der Arbeit. Datengrundlage ist bereits
vorhanden: `ergebniss.csv` enthält `avg_confidence` je Track, `zaehlung.csv`
die daraus abgeleiteten Zählereignisse. Geplantes Vorgehen: Ground Truth per
manueller Auszählung eines Referenzvideos, dann Auswertung bei mehreren
Schwellen, mit getrennter Betrachtung der Fehlerarten (verpasst / doppelt
gezählt / falsche Klasse / falsche Richtung) statt nur der Gesamtabweichung.
Der Filterpunkt im Code ist `counting.should_count_track()`.

Die **LoRa-Übertragung** (Abschnitt 3) ist seit dem 18.07. im Echtbetrieb
bestätigt und belegt die Anforderung „Datenübertragung ohne
Netzwerkinfrastruktur vor Ort". Für 5.3 interessant ist die bewusste
Entkopplung (eigener Subprozess, Kommunikation nur über `zaehlung.csv`) als
Architekturentscheidung, und für 6.4/7.2 der Umgang mit Funklöchern
(Delta-Versand, Referenzstand erst nach bestätigtem Uplink).

## 6. Sicherheitshinweis (dauerhaft relevant)

Keine Zugangsdaten (SSH-/WLAN-Passwörter, GitHub-Tokens, API-Keys) in Code
oder Markdown-Dateien im Repo speichern — auch nicht in privaten Repos, da
sie in der Git-Historie bleiben, selbst wenn sie später gelöscht werden.

## 7. Wie diese Datei aktuell halten

Nach jeder Session mit größeren Änderungen kurz aktualisieren:
- Abschnitt 3 ("Aktueller Stand"), wenn etwas aus `ToDo.md` erledigt wurde
- Abschnitt 4a, wenn ein neues Problem *gelöst* wurde (kurz, mit Ursache + Fix + Quelle, nicht der ganze Debugging-Weg)
- Abschnitt 4b, wenn an einem Problem gearbeitet wurde, es aber noch nicht fertig ist (mit den bereits konsultierten Quellen, damit die nächste Session nicht wieder bei null anfängt)
- Datum oben
- `ToDo.md` bleibt die Detail-Quelle — hier nur die Kurzfassung synchron halten, nicht duplizieren
