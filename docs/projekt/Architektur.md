# System- und Softwarearchitektur

**Stand: 03.08.2026.** Technische Referenz für den aktuellen Aufbau — was läuft
wo, welches Modul macht was, wie hängen die Teile zusammen. Ergänzt
`HANDOFF.md` (laufender Projektstand) und
`../abschlussarbeit/Entwurf_Systemarchitektur_Sensor.md` (akademische
Einordnung nach Sensormodellen für die Bachelorarbeit) — dort steht das
literaturgestützte "Warum ist das ein Sensor", hier steht das "wie ist es
tatsächlich gebaut".

---

## 1. Systemarchitektur (Hardware + Netzwerk)

```
┌─────────────────────────────────────────────────────────────┐
│  Sensor-Gerät (Raspberry Pi 5, 8 GB, pro Eingang eins)       │
│                                                               │
│  USB-Kamera ──▶ Hailo-8 (KI-Beschleuniger, YOLO-Erkennung)   │
│                       │                                      │
│                       ▼                                      │
│              Zähl-Software (core.py + Module, dieses Repo)   │
│                       │                                      │
│              ┌────────┴────────┐                             │
│              ▼                 ▼                             │
│      zaehlung.csv       ergebniss.csv + Bewegungsbilder      │
│      (Zählereignisse)   (Track-Zwischenspeicher, lokal)      │
│              │                                                │
└──────────────┼────────────────────────────────────────────────┘
               │  LoRaWAN (Dragino LA66, EU868)   und/oder  MQTT
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Server-Pi ("stadtwerke-server", eigenes Repo                │
│  zaehlsensor-server): Flask-Dashboard, MQTT-/TTN-Empfänger,  │
│  SQLite-Ablage                                                │
└─────────────────────────────────────────────────────────────┘
```

**Warum Edge statt Cloud:** Bilddaten verlassen das Sensor-Gerät nie — die
Hailo-Pipeline verarbeitet und verwirft Frames lokal, übertragen werden
ausschließlich aggregierte Zählwerte. Das ist die Privacy-by-Design-Grundlage
des Projekts, siehe `../entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md`.

**Zwei unabhängige Übertragungswege** (können parallel laufen, siehe
`ToDo.md` für den aktuellen Betriebsstatus beider Wege):
- **LoRaWAN** — funkbasiert, ohne lokale Netzinfrastruktur, aber auf eine
  ausreichende Funkstrecke zum Gateway angewiesen (18-Byte-Binärformat,
  begrenzte Bandbreite).
- **MQTT** — über das lokale Netz, keine Bandbreitenbegrenzung wie bei LoRa
  (volle Übergangsmatrix statt nur IN/OUT-Summen).

**Betriebsstart:** Ein Sensor-Gerät bootet, öffnet automatisch ein Terminal
(Desktop-Autostart-Eintrag), wärmt die Pipeline einmalig auf und startet die
Zählung — kein manueller Eingriff am Gerät nötig. Details: Abschnitt 5.

---

## 2. Softwarearchitektur — Schichten

```
┌───────────────────────────────────────────────────────────────┐
│ UI-/Steuerschicht           app.py, roi_config_app.py,         │
│                              ui_utils.py, ctk_dialogs.py        │
│  Bündelt den kompletten Arbeitsablauf (Input → Konfiguration    │
│  → Start/Stopp → Live-Auswertung) ohne Kommandozeile, startet   │
│  core.py und die Übertragungs-Skripte als Subprozesse.          │
├───────────────────────────────────────────────────────────────┤
│ Konfigurationsschicht        config.py, frame_utils.py,         │
│                              auto_config.py,                    │
│                              auto_config_clustering.py           │
│  Liest/schreibt roi_config.json (Zählgeometrie, Klassen,        │
│  IN/OUT je Fläche, Konfidenz-Schwelle). Zwei Wege, die           │
│  Geometrie zu erzeugen: manuell (roi_config_app.py) oder         │
│  automatisch (Datensammlung + Clustering/Randraster, derzeit    │
│  über config.SHOW_AUTO_CONFIG in der UI ausgeblendet, Code       │
│  bleibt erhalten).                                               │
├───────────────────────────────────────────────────────────────┤
│ Pipeline-/Erfassungsschicht  core.py                             │
│  Hailo/GStreamer-Pipeline (Kamera → YOLO-Inferenz → Tracking),  │
│  Pro-Frame-Callback als Andockpunkt für die eigene Logik.        │
│  Fremdcode: hailo-rpi5-examples (GStreamerDetectionApp).         │
├───────────────────────────────────────────────────────────────┤
│ Zähl-/Trackingschicht        tracking.py, counting.py            │
│  Track-Verwaltung (anlegen/aktualisieren/flushen), Zähl-         │
│  entscheidung (Linie / ROI / mehrere Flächen mit IN/OUT je       │
│  Fläche).                                                         │
├───────────────────────────────────────────────────────────────┤
│ Persistenz-/Visualisierungsschicht  logging_utils.py,            │
│                              csv_utils.py, cleanup_utils.py,      │
│                              visualization.py, recording.py       │
│  Schreibt zaehlung.csv/ergebniss.csv schema-sicher, zeichnet     │
│  Live-Overlay + Bewegungsbilder, räumt Artefakte des Vorlaufs    │
│  weg, optionaler Benchmark-Mitschnitt (nur Laborläufe).          │
├───────────────────────────────────────────────────────────────┤
│ Übertragungsschicht          lora_message.py, lora_send_loop.py, │
│                              mqtt_send_loop.py,                  │
│                              uebergangs_payload.py,               │
│                              konfig_payload.py, lora_spiegel.py   │
│  Eigene Subprozesse, lesen ausschließlich zaehlung.csv/           │
│  roi_config.json — core.py/tracking.py bleiben unangetastet,     │
│  ein Übertragungsfehler kann die Zähl-Pipeline nicht gefährden.  │
├───────────────────────────────────────────────────────────────┤
│ Betriebsschicht               warmup.py, start_app.sh,           │
│                              setup_env.sh, create_venv.sh         │
│  Autostart beim Hochfahren, Aufwärmlauf, venv-Aktivierung.        │
└───────────────────────────────────────────────────────────────┘
```

**Leitprinzip Entkopplung:** Jede Schicht kommuniziert mit der nächsten fast
ausschließlich über **Dateien** (`roi_config.json`, `zaehlung.csv`,
`ergebniss.csv`), nicht über direkte Funktionsaufrufe oder gemeinsamen
Prozessspeicher. Konkret heißt das: die Übertragungsskripte laufen als eigene
Subprozesse und lesen nur die von `core.py` geschriebene `zaehlung.csv`;
`app.py` startet `core.py` ebenfalls als Subprozess statt es zu importieren.
Ein Fehler in der Übertragung oder der UI kann dadurch die eigentliche
Zählung nicht zum Absturz bringen, und jede Schicht lässt sich einzeln auf
der Kommandozeile testen, ohne die anderen zu starten.

---

## 3. Datenfluss im Betrieb (pro Frame / pro Track)

```
Kamera-Frame
   │
   ▼
core.py: app_callback()  ──▶ Hailo-Metadaten (Detections + Tracker-IDs)
   │
   ▼
tracking.py: TrackingState.update_track()
   │  legt Track an / aktualisiert ihn, vergibt lesbare display_id
   │  (z. B. "person_ID_3"), klassengetrennt
   ▼
   ├─▶ visualization.py: Live-Overlay auf den Frame zeichnen (nur --use-frame)
   │
   └─▶ bei Track-Abschluss (Flush nach 30 Frames ohne Sichtung, oder
       Programmende):
          │
          ▼
       counting.py: build_counter().check_crossing()
          │  Linienquerung / ROI-Ein-Austritt / Zonenübergang A->B,
          │  inkl. IN/OUT-Bestimmung je Fläche (Mehrere-Flächen-Modus)
          ▼
       logging_utils.py ──▶ zaehlung.csv   (jedes Zählereignis, auch
       │                                    "kein Wechsel"-Fälle, markiert
       │                                    über is_transition)
       └────────────────▶ ergebniss.csv    (Track-Zusammenfassung inkl.
                                             avg_confidence)
```

**Übertragung (unabhängiger, langsamerer Takt, z. B. alle 5 Minuten):**

```
zaehlung.csv (neue Zeilen seit letztem erfolgreichen Versand)
   │
   ├─▶ lora_send_loop.py ──▶ lora_message.py (18-Byte-Format, IN/OUT
   │                          über die je Fläche markierten IN-Flächen)
   │                          ──▶ LA66 (AT+SENDB) ──▶ LoRaWAN-Gateway
   │
   └─▶ mqtt_send_loop.py ──▶ uebergangs_payload.py (volle Übergangsmatrix,
                              JSON) ──▶ MQTT-Broker ──▶ Server-Pi

roi_config.json ──▶ konfig_payload.py ──▶ (bei Bedarf mitgesendet, damit
                     der Server die Zonen kennt, ohne sie manuell nachzupflegen)
```

Beide Sender arbeiten **lieferbestätigt mit Delta-Versand**: übertragen wird
der Zuwachs seit dem letzten *erfolgreichen* Uplink, der Referenzstand wird
erst nach bestätigtem Senden nachgezogen. Ein fehlgeschlagenes Intervall geht
dadurch nicht verloren, sondern kommt beim nächsten Erfolg mit.

---

## 4. Konfiguration (vor dem Betrieb)

```
roi_config_app.py (manuell, per Mausklick)
   │  Referenzbild kommt aus core.py selbst (CORE_SNAPSHOT_ONLY-Modus) —
   │  garantiert identische Auflösung wie im späteren Live-Betrieb, statt
   │  einer unabhängigen cv2.VideoCapture()-Aufnahme
   ▼
roi_config.json
   mode: "line" | "roi" | "multi_roi"
   points / regions (je Fläche: name, points, direction: "in"|"out", snap)
   classes, reverse_direction, snap_to_nearest, min_confidence
   in_field: Liste der IN-Flächennamen (nur multi_roi; ältere
             Konfigurationen mit einzelnem String werden automatisch als
             Ein-Element-Liste gelesen)
   ▼
config.py lädt die Datei beim Start von core.py (Fallback auf
Standardwerte, falls sie fehlt)
```

Alternativ (Code vorhanden, in der UI derzeit über `config.SHOW_AUTO_CONFIG`
ausgeblendet): **automatische Wegerkennung** — `auto_config.py` sammelt
Start-/Endpunkte während eines Laufs, `auto_config_clustering.py` leitet
daraus per DBSCAN-Clustering oder festem Randraster Zonen ab und schreibt sie
im selben `roi_config.json`-Format.

`app.py` bündelt den gesamten Ablauf (Input wählen → Frame laden →
Zählgeometrie setzen → Zähllauf starten/stoppen → Live-Auswertung
mitverfolgen) über eine Sidebar-Navigation, inkl. Light-/Dark-Mode
(Auswahl gespeichert in `ui_settings.json`).

---

## 5. Betrieb: Autostart und Aufwärmlauf

```
Gerät bootet
   │
   ▼
Desktop-Autostart-Eintrag (~/.config/autostart/visitorcounter.desktop)
   │  öffnet ein Terminal, führt start_app.sh aus
   ▼
start_app.sh
   1. source setup_env.sh          venv aktivieren, PYTHONPATH setzen
   2. python warmup.py --input usb  core.py einmalig kurz hochfahren,
                                      warten bis Bilder fließen, sauber
                                      per SIGINT beenden — der allererste
                                      echte Start nach dem Booten dauert
                                      sonst bis zu zwei Minuten
                                      (Hailo-Firmware/Modell laden)
   3. python app.py --autostart     Oberfläche öffnet sich UND startet
                                      selbst automatisch die Zählung mit
                                      USB-Input (app.py:
                                      _maybe_autostart_pipeline())
```

`warmup.py` merkt sich den Aufwärmlauf über die Kernel-Boot-ID (läuft nur
einmal pro Systemstart); `app.py` hat denselben Mechanismus zusätzlich intern
eingebaut (`_maybe_run_warmup`) als Sicherheitsnetz, falls die App unabhängig
von `start_app.sh` gestartet wird.

---

## 6. Verzeichnisstruktur (Kurzreferenz)

Vollständige, kommentierte Dateiliste in `HANDOFF.md`, Abschnitt 2. In Kürze:

```
app.py, roi_config_app.py, ui_utils.py, ctk_dialogs.py       UI
core.py                                                        Pipeline
tracking.py, counting.py                                       Zähllogik
logging_utils.py, csv_utils.py, cleanup_utils.py,
visualization.py, recording.py                                 Persistenz/Anzeige
config.py, frame_utils.py, auto_config.py,
auto_config_clustering.py                                      Konfiguration
lora_message.py, lora_send_loop.py, mqtt_send_loop.py,
uebergangs_payload.py, konfig_payload.py, lora_spiegel.py       Übertragung
warmup.py, start_app.sh, setup_env.sh, create_venv.sh           Betrieb
docs/                                                           Dokumentation
tests/                                                           Diagnose-/Hardware-Tests
```

---

## Pflegehinweis

Bei Änderungen an Modulgrenzen, Datenformaten (`roi_config.json`,
`zaehlung.csv`) oder der Übertragungs-/Autostart-Kette diese Datei mit
aktualisieren — sie soll den *aktuellen* Aufbau zeigen, nicht den
historischen Verlauf (der steht in `../entwicklung/`). Datum oben mitziehen.
