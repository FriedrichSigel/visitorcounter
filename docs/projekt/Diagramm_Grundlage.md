# Grundlage für Architektur-/Datenfluss-Diagramme

**Zweck dieser Datei:** In einen neuen Chat einfügen mit einer Bitte wie
*"Erstelle mir aus dieser Grundlage ein Diagramm der Hardware-/Netzwerk-
architektur"* (bzw. Software­architektur / Datenfluss). Die drei Abschnitte
unten sind bewusst so aufbereitet, dass sich daraus direkt Kästen, Pfeile und
Beschriftungen ableiten lassen — Fakten aus dem tatsächlichen Code, Stand
10.08.2026 (Details/Belege: `ARCHITEKTUR_IST.md`, `IMPLEMENTIERUNG_IST.md`
im Repo-Root).

Stellen mit **[NICHT VERIFIZIERT]** sind Unsicherheiten, die nur am realen
Gerät zu klären sind (z. B. RAM-Größe) — im Diagramm entweder weglassen oder
sichtbar als offen markieren, nicht als Fakt darstellen.

---

## 1. Hardware- und Netzwerkarchitektur

**Ein Sensor-Gerät** (mehrfach ausgerollt, ein Gerät pro Eingang):

```
Knoten:
  Raspberry Pi 5 [RAM-Variante NICHT VERIFIZIERT]
    ├─ Hailo-8 KI-Beschleuniger (M.2/PCIe, "AI Kit")  — Anbindung: PCIe
    ├─ USB-Kamera  [genaues Modell NICHT VERIFIZIERT]  — Anbindung: USB
    └─ Dragino LA66 USB LoRaWAN-Adapter V2 (EU868)     — Anbindung: USB
                                                          (seriell, CP2102-Bridge)

Kanten vom Sensor-Gerät nach außen:
  Sensor-Gerät --LoRaWAN (Funk, EU868, unbestätigt)--> LoRaWAN-Gateway --> Network Server (TTN)
  Sensor-Gerät --MQTT (TCP/IP, Port 1883, WLAN/Ethernet [Schnittstelle NICHT VERIFIZIERT])--> Server-Pi

Server-Pi ("stadtwerke-server", separates Repo):
  ├─ MQTT-Broker (empfängt lokal) + TTN-Anbindung (empfängt über LoRaWAN-Weg)
  ├─ Flask-Webserver (Dashboard)
  └─ SQLite-Datenbank
```

**Warum zwei Übertragungswege:** LoRaWAN funkbasiert ohne lokale Netz-
infrastruktur, aber auf Funkempfang beim Gateway angewiesen; MQTT über das
lokale Netz, keine Bandbreitengrenze wie LoRaWAN (18 Byte). Beide können am
selben Gerät gleichzeitig aktiv sein.

**Datenschutz-relevant fürs Diagramm:** Zwischen Kamera und "Sensor-Gerät
verarbeitet" sollte im Bild deutlich werden, dass **keine Bilddaten den
Sensor verlassen** — nur die beiden Pfeile nach außen (LoRaWAN, MQTT) tragen
Daten, und die sind bereits aggregierte Zählwerte, keine Bilder.

---

## 2. Softwarearchitektur (Schichten)

Sieben Schichten, jede mit ihren Dateien. Fremdcode (nicht in diesem Repo,
kommt aus dem Paket `hailo_apps`) ist gekennzeichnet.

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. UI-/Steuerschicht                                             │
│    app.py (Fenster-Klammer: Sidebar, Navigation, Autostart)      │
│    tabs/*.py (9 Module, je ein Tab/Abschnitt):                   │
│      input_tab, config_tab, start_tab, recording_controls,       │
│      lora_controls, mqtt_controls, pipeline_control, output_tab, │
│      autoconfig_tab, settings_store, constants                   │
│    roi_config_app.py (Zählgeometrie-Editor, in Tab 2 eingebettet │
│      ODER eigenständig aufrufbar)                                │
│    ctk_dialogs.py, ui_utils.py (Hilfsfunktionen)                 │
├─────────────────────────────────────────────────────────────────┤
│ 2. Konfigurationsschicht                                         │
│    config.py (lädt roi_config.json, zentrale Konstanten)         │
│    frame_utils.py, auto_config.py, auto_config_clustering.py     │
│    (Auto-Konfiguration: Code vorhanden, in der UI aktuell         │
│     ausgeblendet über config.SHOW_AUTO_CONFIG = False)           │
├─────────────────────────────────────────────────────────────────┤
│ 3. Pipeline-/Erfassungsschicht                                   │
│    core.py (Einstiegspunkt, app_callback())                      │
│    [FREMDCODE] hailo_apps.GStreamerDetectionApp — komplette      │
│    Bild-/Inferenz-/Tracker-Pipeline bis hailotracker              │
├─────────────────────────────────────────────────────────────────┤
│ 4. Zähl-/Trackingschicht                                         │
│    tracking.py (TrackingState: Track anlegen/flushen/finalize)   │
│    counting.py (LineCounter, RoiCounter, MultiRoiCounter)        │
├─────────────────────────────────────────────────────────────────┤
│ 5. Persistenz-/Visualisierungs-/Diagnoseschicht                  │
│    logging_utils.py, csv_utils.py, cleanup_utils.py              │
│    visualization.py, recording.py (Benchmark-Mitschnitt)         │
│    benchmark.py (Leistungsbericht bei aktivem Mitschnitt)        │
├─────────────────────────────────────────────────────────────────┤
│ 6. Übertragungsschicht                                           │
│    lora_message.py, lora_send_loop.py                            │
│    mqtt_send_loop.py, uebergangs_payload.py, konfig_payload.py   │
│    lora_spiegel.py (Zusatzfeature: LoRa-Nachrichten zusätzlich    │
│    über MQTT spiegeln)                                            │
├─────────────────────────────────────────────────────────────────┤
│ 7. Betriebsschicht                                                │
│    warmup.py, start_app.sh, setup_env.sh, create_venv.sh          │
└─────────────────────────────────────────────────────────────────┘
```

**Leitprinzip fürs Diagramm — Entkopplung über Dateien statt Funktionsaufrufe:**
Pfeile zwischen den Schichten sollten als **Dateien** beschriftet sein
(`roi_config.json`, `zaehlung.csv`, `ergebniss.csv`), nicht als direkte
Aufrufe. Konkret: `app.py` startet `core.py`, `lora_send_loop.py` und
`mqtt_send_loop.py` als **eigene Subprozesse** (Pfeile mit "startet
Subprozess"), nicht als Funktionsimporte — ein Fehler in der Übertragung
kann die Zählung dadurch nicht zum Absturz bringen.

**Neu seit dem letzten Stand (10.08., für ein aktuelles Diagramm wichtig):**
- `benchmark.py` als neue Datei in Schicht 5.
- In der UI-Schicht gibt es jetzt einen "Debug-Hauptschalter" (Tab 3), der
  Mitschnitt/Live-Vorschau/Zeitlimit/Debug-Dateien/detaillierte
  Konsolenausgabe bündelt — für ein Software-Architekturdiagramm eher
  nebensächlich (UI-Detail), für ein Datenfluss-Diagramm relevant (siehe
  Abschnitt 3, "Debug-Dateien" sind jetzt bedingt).

---

## 3. Datenfluss

### 3a. Pro Frame / pro Track (der Kern-Loop)

```
Kamera-Frame
   │
   ▼
[FREMDCODE] GStreamer/Hailo-Pipeline
   (Decodierung → Skalierung → Hailo-8-Inferenz → hailotracker)
   │  liefert: Frame + Detections + Tracker-IDs
   ▼
core.py: app_callback()
   │  filtert nach TRACKED_LABELS + COUNTING_MIN_CONFIDENCE
   ▼
tracking.py: TrackingState.update_track()
   │  legt Track an / aktualisiert ihn, vergibt display_id (z. B. "car_ID_3")
   ▼
   ├──▶ (nur wenn --use-frame) visualization.py: Live-Overlay zeichnen
   │
   └──▶ bei Track-Abschluss (Flush nach 30 Frames ohne Sichtung, ODER
        Programmende):
           │
           ▼
        counting.py: check_crossing()
           │  Linie / ROI / mehrere Flächen mit IN/OUT je Fläche
           ▼
        ┌─────────────────────────┬─────────────────────────────┐
        ▼                         ▼                              
   logging_utils.py          logging_utils.py                    
   → zaehlung.csv             → ergebniss.csv  [BEDINGT, siehe unten]
   (IMMER geschrieben,                          
    unabhängig vom Debug-                       
    Schalter)                                   
```

**Bedingte Debug-Dateien (neu, 10.08.):** `ergebniss.csv`,
Bewegungsbilder (`visualization.py`) und der Benchmark-Bericht
(`benchmark.py`) werden nur geschrieben, wenn in Tab 3 der
Debug-Hauptschalter **und** die jeweilige Einzeloption aktiv sind
(Umgebungsvariable `DEBUG_FILES_ENABLED`, Default beim direkten
Kommandozeilenaufruf ohne App: an). **`zaehlung.csv` ist davon
ausdrücklich ausgenommen** — die wird immer geschrieben, weil sie die
Datenquelle für den Übertragungsfluss (3b) und für die Live-Anzeige in Tab 4
ist. Für ein Diagramm: `zaehlung.csv` mit durchgezogenem Pfeil, die drei
Debug-Dateien mit gestricheltem Pfeil + Beschriftung "nur wenn Debug aktiv".

### 3b. Übertragung (eigener, langsamerer Takt — z. B. alle 5 Minuten)

```
zaehlung.csv (Delta seit letztem erfolgreichen Versand)
   │
   ├──▶ lora_send_loop.py ──▶ lora_message.py
   │       (18-Byte-Binärformat: Header 6 Byte + 6 Klassen × [IN][OUT])
   │       ──▶ Dragino LA66 (AT+SENDB über USB-seriell)
   │       ──▶ LoRaWAN-Gateway ──▶ Network Server
   │
   └──▶ mqtt_send_loop.py ──▶ uebergangs_payload.py
           (JSON, vollständige Übergangsmatrix: von-Feld → nach-Feld je Klasse)
           ──▶ MQTT-Broker (Topic "zaehlsensor/<sensor_id>/zaehlwerte")
           ──▶ Server-Pi (Flask + SQLite)

roi_config.json ──▶ konfig_payload.py ──▶ MQTT (optional, informiert den
                     Server über die aktuelle Zonen-Konfiguration)
```

**Delta-/Bestätigungslogik (für eine Anmerkung im Diagramm):** Beide Sender
übertragen nur den **Zuwachs seit dem letzten bestätigten Uplink** — schlägt
ein Versand fehl, bleibt der Referenzstand stehen und der Zuwachs kommt beim
nächsten Erfolg mit. Kein Datenverlust bei Funklöchern/Verbindungsabbrüchen.

### 3c. Konfiguration (vor dem Betrieb, kein Dauerbetrieb-Fluss)

```
roi_config_app.py (manueller Klick-Editor, Tab 2 der App)
   │  Referenzbild kommt aus core.py selbst (Snapshot-Modus) — garantiert
   │  identische Auflösung wie im späteren Live-Betrieb
   ▼
roi_config.json
   (Zählmodus, Geometrie, Klassen, Konfidenz-Schwelle, IN/OUT je Fläche)
   ▼
config.py lädt die Datei beim Start von core.py
```

---

## Kurz-Glossar für Beschriftungen

| Begriff im Diagramm | Bedeutung |
|---|---|
| Sensor-Gerät | Raspberry Pi 5 + Hailo-8 + Kamera + LA66, ein Gerät pro Eingang |
| Server-Pi | zweites, separates Gerät ("stadtwerke-server"), eigenes Repo |
| Debug-Hauptschalter | UI-Schalter in Tab 3, bündelt Labor-/Testoptionen |
| Delta-Versand | nur der Zuwachs seit letztem bestätigten Uplink wird gesendet |
| IN/OUT je Fläche | bei "Mehrere Flächen"-Modus: jede Fläche individuell als IN- oder OUT-Bereich markierbar |
