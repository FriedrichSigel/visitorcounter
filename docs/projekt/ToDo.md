# ToDo – Personenzähl-Prototyp (Stadtwerke Potsdam)

Stand: 19.07.2026 — Bezug: `core/` (app.py, roi_config_app.py, ui_utils.py, config.py, tracking.py, counting.py, visualization.py, logging_utils.py, csv_utils.py, core.py, auto_config.py, auto_config_clustering.py, lora_message.py, lora_send_loop.py) sowie `tests/` (Kamera- und LoRa-Hardware-Tests)

**Praxis ab sofort:** Lösungen, die auf recherchierten externen Quellen beruhen,
werden mit Quellenlink notiert — auch wenn sie noch nicht fertig funktionieren.

## 🔒 Dauerregel — Bildmaterial

**Normalbetrieb: keine Bildspeicherung.** Der Mitschnitt (`recording.py`,
Tab 3, Checkbox ganz oben) ist ein reines Benchmark-Werkzeug und
standardmässig aus. Vor jedem Feldeinsatz prüfen, dass er aus ist; nach jedem
Laborlauf das Material nach der Auswertung löschen. Begründung und Regeln:
[`../entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md`](../entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md).

## 🚨 Sofort erledigen — wirkt sich JETZT auf die Messung aus

- [ ] **IN-Feld in der Gerätekonfiguration setzen.** Geprüft am Stand vom
      18.07.: `roi_config.json` auf dem Gerät steht auf `multi_roi` mit den
      Flächen `Berlin`/`Potsdam`, aber `in_field` ist **nicht gesetzt**
      (`None`). Folge: **der LoRa-Versand überträgt durchgehend Nullwerte** —
      die Uplinks kommen an, enthalten aber keine Zählungen. Behebung: App →
      Tab 2 (Konfiguration), Modus „Mehrere Flächen", am Ende das IN-Feld
      auswählen und speichern. Danach einen Uplink im TTN gegenprüfen.
- [ ] **Zeilenenden vereinheitlichen (CRLF → LF).** Die Dateien auf dem Gerät
      haben Windows-Zeilenenden. Git meldet dadurch Dateien als geändert, die
      nie angefasst wurden (`LICENSE`, `depth.py`, `VideoApp.py` u. a. — bei
      `LICENSE` z. B. 21 „geänderte" Zeilen, die inhaltlich identisch sind).
      Im neuen Repository gleich eine `.gitattributes` mit `* text=auto eol=lf`
      anlegen, siehe `../einrichtung/EIGENES_REPOSITORY.md`.
- [ ] **Alte Ordnerkopien aufräumen.** Auf dem Rechner liegt zusätzlich eine
      Kopie des Projektstands vom **16.07.** (vor der LoRa-Arbeit: `app.py` mit
      26 KB statt 36 KB, ohne `lora_message.py`/`lora_send_loop.py`). Solche
      Doppelgänger sind die häufigste Ursache dafür, dass versehentlich am
      falschen Stand gearbeitet wird — löschen, sobald das neue Repository
      steht und einen Testlauf bestanden hat.

## ⚠️ Höchste Priorität — die drei aktuellen Arbeitspakete (18.07.)

Vom Nutzer als nächste Schritte benannt, nachdem LoRa steht:

- [ ] **1. Konfigurationen nochmal genau durchgehen.** Die Konfigurationsmodi
      (Linie, ROI, Mehrere Flächen, die beiden Auto-Verfahren) systematisch
      durchprüfen: Was wird gespeichert, was liest `core.py` tatsächlich, wo
      weichen Konfigurationstool und Laufzeitverhalten voneinander ab? Offene
      Detailpunkte, die dabei mit erledigt werden können: `in_field` fehlt in
      den Auto-Modi (siehe LoRa-Abschnitt); `AUTO_CONFIG_DBSCAN_EPS_PIXELS`/
      `MIN_SAMPLES` bzw. Randraster-Parameter mit echten Daten feinjustieren.
      **Konkreter Anlass:** genau hier ist am 18.07. aufgefallen, dass eine
      gespeicherte Konfiguration ohne `in_field` stillschweigend Nullwerte
      sendet. Beim Durchgehen also nicht nur prüfen, *ob* gespeichert wird,
      sondern ob der Laufzeitcode mit unvollständigen Konfigurationen sichtbar
      umgeht statt still weiterzulaufen.
- [ ] **2. UI-Probleme beheben.** Es sind erneut Probleme aufgetreten —
      **konkrete Punkte sind noch nicht festgehalten**. Beim nächsten Mal
      zuerst notieren, welches Fenster/welcher Tab betroffen ist und was genau
      passiert (falsche Darstellung? Absturz? Element reagiert nicht?), sonst
      ist der Fehler schwer zu reproduzieren. Bekannte Altlasten in diesem
      Bereich: Live-Bild-Spiegelung bei `--input usb` (siehe unten),
      Datensammlungs-Workflow (Tab 5).
- [ ] **3. Genauigkeit des Sensors untersuchen — Einfluss der Confidence.**
      Kern der inhaltlichen Bewertung für die Arbeit. Ansatz: `ergebniss.csv`
      enthält bereits `avg_confidence` je Track, `zaehlung.csv` die gezählten
      Ereignisse — daraus lässt sich auswerten, wie sich ein
      Confidence-Schwellwert auf Über-/Unterzählung auswirkt. Vorgehen:
      Referenzvideo mit manuell ausgezählter Wahrheit (Ground Truth) aufnehmen,
      dann denselben Lauf bei verschiedenen Schwellen auswerten und
      Genauigkeit/Fehlerarten (verpasste vs. doppelt gezählte Objekte)
      gegenüberstellen. Der Platzhalter `counting.should_count_track()` ist
      genau der Ort, an dem ein Confidence-Filter greifen würde — bislang
      akzeptiert er jeden Track.

### Ältere offene Punkte aus dieser Kategorie

- [ ] **Live-Bild-Spiegelung bei `--input usb` beheben.** `LIVE_PREVIEW_HORIZONTAL_FLIP = True` in `config.py` wurde bereitgestellt (spiegelt nur das Anzeigefenster zurück, nach unseren eigenen Overlays, betrifft die Zähllogik nicht), aber laut jüngstem Nutzer-Feedback ist das Bild weiterhin gespiegelt. Erster Schritt: prüfen, ob der Schalter überhaupt auf `True` gesetzt wurde. Falls ja und es hilft trotzdem nicht: Alternativen sind V4L2-Treiber-Flip (`v4l2-ctl --list-ctrls` prüfen) oder `v4l2loopback` mit vorgeschalteter spiegelnder GStreamer-Pipeline (siehe HANDOFF.md Abschnitt 4b für Details).
- [x] **CustomTkinter-UI poliert (15.07.).** Gemeldete Punkte behoben: feste Layout-Verhältnisse (1/5 Sidebar, ~3/5 Frame, ~1/5 Konfig), Fenster in der Breite fixiert (1280px, wächst nie), Frame-Vorschau skaliert seitenverhältnistreu in feste Box, alle Dialoge/Popups im dunklen App-Design (`ctk_dialogs.py`), USB als Standard-Input. Früher behoben: Emoji im Sidebar-Titel, `CTkCheckBox`-`justify`-Absturz. **Hinweis: laut Nutzer sind am 18.07. erneut UI-Probleme aufgetreten — siehe Punkt 2 oben.**
- [ ] **Datensammlung (`AUTO_CONFIG_COLLECTION_ENABLED`-Workflow) anpassen.** Nutzer hat gemeldet, dass hier nochmal ran muss — konkrete Punkte noch nicht spezifiziert, im nächsten Gespräch klären (z. B.: Sammeldauer-Handhabung? Reset zwischen Sessions? UI-Rückmeldung während der Sammlung?).
- [ ] **`--input usb`-Kaltstart-Timeout verifizieren.** Nutzer-Beobachtung: "Frame laden" schlägt fehl, geht aber, wenn vorher einmal über Seite 3 gestartet+gestoppt wurde — Ursache identifiziert (allererster `core.py`-Lauf seit Neustart dauert deutlich länger als das Snapshot-Timeout). Fix: Timeout 120s -> 240s, nach `config.py` verschoben (`SNAPSHOT_TIMEOUT_SECONDS`). **Nutzer-Bestätigung, ob 240s jetzt reichen, steht noch aus.**
- [ ] **Kreuzungserkennung mit echten Tracking-Daten verifizieren.** Weiterhin offen (seit mehreren Sessions) — Geometrie-Logik synthetisch durchgetestet und korrekt, echter Betrieb auf dem Pi noch nicht bestätigt.

## 🔌 LoRa-Übertragung — INTEGRIERT UND IM BETRIEB BESTÄTIGT (18.07.)

**Status: funktioniert.** Sensordaten kommen online per LoRa an. Der Versand ist
in `core/` integriert und in Tab 3 der App zuschaltbar.

- [x] Nachrichtenformat: 18-Byte-Zählformat v2 (Header 6 Byte + 6 Klassen x
      [IN][OUT]), definiert in `lora_message.py` — die eine Stelle, an der das
      Format festgelegt ist. Enthält auch `decode_frame()` als Referenz-Decoder
      für die Empfängerseite.
- [x] **Dragino LA66 USB LoRaWAN Adapter beschafft, eingerichtet und im
      Echtbetrieb bestätigt** (Einrichtung siehe `EINRICHTUNG_LA66.md`).
      AT-Befehlsformat: `AT+SENDB=<confirm>,<Fport>,<len>,<hexdata>`, FPort 2,
      unbestätigte Uplinks.
- [x] Sonel LORA-S1 als Kandidat ausgeschlossen (`bInterfaceClass 255`, kein
      serielles Gerät, keine Antwort auf 5 Baudraten × 4 Testbefehle).
- [x] **In `core/` integriert (Tab 3):** Checkbox „Daten per LoRa senden (LA66)",
      Sende-Intervall (Minuten) und Sensor-ID, plus Hinweisfeld mit der
      Nachrichtenstruktur (richtet sich nach der Konfiguration). Der Sender
      läuft als **eigener Subprozess** (`lora_send_loop.py --live-counts`), der
      nur die von core.py geschriebene `zaehlung.csv` liest — `core.py` und
      `tracking.py` sind bewusst unangetastet, damit ein LoRa-Fehler die
      Zähl-Pipeline nicht gefährdet. Ausgabe läuft mit `[LoRa]`-Präfix in die
      Live-Konsole (Tab 4).
- [x] **Warteschlange/Wiederholung gelöst.** Übertragen wird der Zuwachs seit
      dem letzten *erfolgreichen* Uplink; der Referenzstand wird erst nach
      bestätigtem Senden nachgezogen. Ein fehlgeschlagenes Intervall geht
      dadurch nicht verloren, sondern kommt beim nächsten Erfolg mit.
- [x] **Mehrere-Flächen-Modus kompatibel gemacht.** Statt eines eigenen
      Nachrichtentyps wird in Tab 2 eine Fläche als **IN-Feld** gewählt
      (gespeichert als `"in_field"` in `roi_config.json`): Übergang
      `X -> IN-Feld` = IN, `IN-Feld -> X` = OUT, andere Übergänge werden nicht
      gewertet. Damit nutzen alle Modi dasselbe Format.
- [x] **Header-Bytes 3–4 geklärt und korrigiert (18.07., zweite Sitzung).** Die
      Spezifikation lag im alten Ordner (`basic_pipelines/core/`) und ist jetzt
      nach `docs/LoRa_Nachrichtenformat_Spezifikation.md` gerettet. Verbindlich
      gilt: **Byte 3 = `interval_min`** (Aggregationsintervall in Minuten),
      **Byte 4 = `status`-Bitfeld** (Bit0 Kamera, Bit1 Hailo, Bit2 Konfiguration,
      Bit3 gepuffert, Bit4 Teilintervall). Die erste Implementierung hatte beide
      Bytes falsch belegt (Status in Byte 3, Byte 4 leer) — korrigiert in
      `lora_message.py`; der erzeugte Frame ist jetzt byte-identisch mit dem
      Referenz-Frame der Spezifikation. **Der TTN-Decoder
      (`docs/ttn_payload_decoder.js`) hat die alten Frames deshalb falsch
      interpretiert (Intervall 0, alle Status-Bits aus) — die Zählwerte selbst
      waren immer korrekt.** Uplinks vor dieser Korrektur entsprechend bewerten.
- [ ] **Auto-Modi ohne IN-Feld.** `auto_cluster`/`auto_border` speichern als
      `multi_roi`, setzen aber noch kein `in_field` — die Auswahl erscheint nur
      im manuellen Modus. Nachziehen, falls auch diese Modi per LoRa senden
      sollen.
- [ ] Verhalten über längere Zeit im Feld beobachten (Duty-Cycle, Paketverluste,
      Sequenznummern-Überlauf bei 255).
- [ ] **Fehlendes IN-Feld sichtbarer machen.** Steht `multi_roi` ohne
      `in_field`, sendet der Sender formal korrekte Frames mit lauter Nullen und
      loggt nur eine Warnzeile. Im Betrieb ist das leicht zu übersehen (genau so
      passiert, siehe Abschnitt „Sofort erledigen"). Überlegen: Start des
      LoRa-Versands in Tab 3 blockieren, solange kein IN-Feld gesetzt ist, statt
      Nullwerte zu senden.

## ✅ Bereits funktionsfähig

- [x] Hailo-8-Beschleuniger auf Raspberry Pi 5 installiert und lauffähig (Firmware 4.23.0)
- [x] YOLO-basierte Objekterkennung über die Hailo-Pipeline (Klassen: person, bicycle, car, motorcycle, bus, truck)
- [x] Alle Klassen werden korrekt einzeln getrackt, nicht nur "person" (`hailotracker` `class-id=-1`). Quelle: https://community.hailo.ai/t/how-to-change-the-class-hailo-tracker-is-tracking/12693
- [x] Individuelle, pro Klasse hochzählende, lesbare TrackIDs (`car_ID_1`, `person_ID_1`, ...) statt der rohen, klassenübergreifend geteilten Hailo-ID
- [x] Automatisches Entfernen ("Flushen") von Objekten nach 30 Frames ohne Sichtung
- [x] Ergebnis-Ausgabe: `ergebniss.csv` als Track-Zwischenspeicher mit `avg_confidence` (kein `ergebniss.txt` mehr), zwei Bewegungsbilder (Flush/Finalize) je Lauf in echter Videoauflösung, Start-Cleanup nach `vorherige_laeufe/` (15.07.)
- [x] Auto-Konfiguration von der GUI entkoppelt (`frame_utils.py`), UI-Anzeigefix (feste Box, zentriertes Skalieren); Auto-Config-Datensammlung in eigenen Tab 5 isoliert; Zeitlimit von normalen Läufen entkoppelt (Default kein Limit) (15.07.)
- [x] Programm stoppt automatisch nach einem Durchlauf eines Test-Videos (`on_eos()`-Fix). Quelle: https://community.hailo.ai/t/stop-processing-video-files/11231
- [x] Code modularisiert (siehe HANDOFF.md Abschnitt 2 für die vollständige Dateiliste)
- [x] Race Condition in `finalize()` behoben (Check-and-Set innerhalb des Locks, mit 20 gleichzeitigen Aufrufen getestet)
- [x] Zähllogik implementiert — Linien-Modus, einzelner ROI-Modus, Mehrere-Flächen-Modus (Übergänge wie `A->B`), `snap_to_nearest`-Option, "Kein Wechsel"-Fall wird protokolliert statt verworfen (`is_transition`-Spalte)
- [x] **CSV-Schema-Drift behoben** — `csv_utils.py` archiviert automatisch veraltete Dateien bei Formatwechsel, gegen echte kaputte Dateien auf dem Pi getestet
- [x] **Auto-Konfiguration komplett implementiert, ZWEI Verfahren**: DBSCAN-Clustering (Zonen aus Punkten ableiten) UND Randraster (feste Zonen am Bildrand + Mindestbewegungs-Filter — auf Nutzerwunsch ergänzt, nachdem Clustering bei Track-Verlust zu Geister-Startpunkten in der Bildmitte führte). Beide jetzt gleichwertiger Zählmodus direkt in `roi_config_app.py`, kein separates Tool mehr.
- [x] **`app.py` — zentrale Steuer-App gebaut**: vier Seiten (Input/Konfiguration/Start/Live-Auswertung) über Sidebar-Navigation, bündelt den kompletten Arbeitsablauf ohne Kommandozeile.
- [x] **UI auf CustomTkinter umgestellt** (dunkles Theme) — läuft, aber laut Nutzer noch nicht fertig poliert (siehe oben).
- [x] **USB-/Pi-Kamera-Snapshot kommt jetzt aus der echten Pipeline** (`CORE_SNAPSHOT_ONLY`-Modus), nicht mehr aus unabhängiger `cv2.VideoCapture()` — behebt bestätigte Auflösungs-/Ausschnitts-Diskrepanz zwischen Konfigurationstool und Live-Bild.
- [x] Subprozess-Timeout-Handling auf SIGINT-zuerst umgestellt (`roi_config_app.py`s Snapshot-Aufruf) — verhindert, dass ein zu knappes Timeout den Hailo-Chip in gesperrtem Zustand zurücklässt (`HAILO_OUT_OF_PHYSICAL_DEVICES`-Fehler, echt aufgetreten und behoben).
- [x] `tests/kamera/camera_test.py` — eigenständiges, Hailo-unabhängiges Kamera-Diagnoseskript bereitgestellt (Ergebnis vom Nutzer noch ausstehend).
- [x] **LoRa-Versand integriert und im Echtbetrieb bestätigt (18.07.)** — Dragino LA66, 18-Byte-Format, in Tab 3 zuschaltbar, entkoppelter Subprozess, Delta-Versand ohne Verlust bei fehlgeschlagenen Uplinks, alle Zählmodi über das IN-Feld abgedeckt. Details siehe LoRa-Abschnitt oben und `docs/AENDERUNGEN-lora-integration.md`.
- [x] Performance-Tests auf Laptop und Raspberry Pi 5 (8 GB) dokumentiert
- [x] **Dokumentation und Tests neu strukturiert (18.07.)** — alle Markdown-Dokumente aus den früheren Ablageorten (`basic_pipelines/Commando/`, `basic_pipelines/core/`, `basic_pipelines/lora_hardware_test/`) in `docs/` zusammengeführt und thematisch sortiert (`projekt/`, `abschlussarbeit/`, `einrichtung/`, `lora/`, `entwicklung/`), Wegweiser in `docs/README.md`. Test- und Diagnoseskripte nach `tests/` (`kamera/`, `lora_hardware/`) mit eigener `tests/README.md`. Veraltete Doppelfassungen von HANDOFF/ToDo entfernt.
- [x] Code in privatem GitHub-Repository versioniert

## 🔧 In Arbeit, noch nicht zuverlässig

- [ ] **Zweites Anzeigefenster unterdrücken.** Ziel: nur noch "User Frame" statt zusätzlich "Hailo Detection App". `hailo_display`-Element per `fakesink` stummschalten funktioniert laut Test noch nicht zuverlässig — nächster Schritt: mit `--dump-dot` prüfen, ob das Element wirklich so heißt.
  Quellen: https://community.hailo.ai/t/how-can-i-stop-displaying-the-main-frame-in-detection-py-in-hailo-rpi5-examples/3020 , https://github.com/hailo-ai/hailo-apps/blob/main/doc/user_guide/running_applications.md
- [~] **`std::system_error: Invalid argument` bei Langläufen — eingegrenzt (15.07.).** Ursache ist die Live-Vorschau (`--use-frame`), nicht Zeitlimit/Tracking; ohne View läuft die Pipeline durch. App fängt Absturz jetzt sauber ab (poll-Liveness-Check, SIGINT→SIGTERM→SIGKILL). Offen: native Grundursache (Hailo/GStreamer bei aktivem View); für Dauerbetrieb Prozess-Watchdog (systemd) vorsehen.

## ⬜ Als Nächstes zu implementieren

### Kernfunktion: Zählung erweitern
- [ ] Track-Filter vor der Zählung konkretisieren — Platzhalter `counting.should_count_track()` existiert bereits, akzeptiert aktuell jeden Track (hängt direkt an der Confidence-Untersuchung, siehe „Genauigkeit & Auswertung")
- [ ] Aggregierte Zählerstände über mehrere Programmläufe/einen ganzen Betriebstag hinweg persistieren
- [ ] `AUTO_CONFIG_DBSCAN_EPS_PIXELS`/`MIN_SAMPLES` bzw. Randraster-Parameter mit echten Daten feinjustieren

### Genauigkeit & Auswertung (neu, 18.07.)
- [ ] Ground-Truth-Referenz anlegen: kurzes Video an einem realistischen Standort, Objekte manuell auszählen (je Klasse und Richtung) als Vergleichsmaßstab
- [ ] Confidence-Schwellwert als Parameter einführen (Ansatzpunkt: `counting.should_count_track()`, plus Wert in `config.py`) — aktuell wird jeder Track gezählt
- [ ] Auswertung fahren: denselben Lauf bei mehreren Schwellen (z. B. 0.3 / 0.4 / 0.5 / 0.6 / 0.7) gegen die Ground Truth stellen; `avg_confidence` aus `ergebniss.csv` nutzen
- [ ] Fehlerarten getrennt erfassen statt nur Gesamtabweichung: verpasste Objekte, doppelt gezählte (Track-Verlust und Neuvergabe), falsche Klasse, falsche Richtung
- [ ] Ergebnis als Tabelle/Diagramm für die Arbeit aufbereiten und einen begründeten Standardwert für die Schwelle festlegen
- [ ] Dabei mitprüfen: hängt die optimale Schwelle vom Zählmodus oder von der Kameraperspektive ab?

### Konfiguration
- [ ] Live-Vorschau in `roi_config_app.py` (Linie/Fläche schon beim Klicken mitzeichnen) — bewusst aus dem MVP rausgelassen
- [ ] Mehrere unabhängige Zählgeometrien gleichzeitig (z. B. mehrere Eingänge in einem Video) — zu unterscheiden vom bestehenden "Mehrere Flächen"-Modus, der Übergänge *zwischen* Flächen zählt, nicht unabhängige Eingänge

### Hardware
- [ ] Sensorgehäuse auswählen/entwerfen (wetterfest, Außeneinsatz an den 17 Eingängen)
- [ ] Finale Hardware-Beschaffung mit den Stadtwerken klären (inkl. LoRa-Modul, siehe oben)
- [ ] Stromausfallresistenz (Pufferung/USV) festlegen

### Bekannte Einschränkungen / kleinere Bugs
- [ ] `track_id`-Fallback auf `0` bei fehlender Tracker-ID — zwei ungetrackte Objekte *derselben Klasse* gleichzeitig könnten weiterhin kollidieren
- [ ] Verhalten bei Tag/Nacht- und Wetterwechsel noch nicht getestet
- [ ] `VideoApp.py` kann aus dem Repo entfernt werden (durch `roi_config_app.py`/`app.py` ersetzt)

### Tests
- [ ] Labortest unter kontrollierten Bedingungen formal durchführen und dokumentieren
- [ ] Realtest — Vorschlag an Betreuer geschickt: erst an der Uni (bester Zugriff), danach ggf. Volkspark Biosphäre. Antwort steht noch aus.

## Priorisierung für die kommenden Wochen

0. **Zuerst der Abschnitt „Sofort erledigen"** — vor allem das IN-Feld. Solange
   es fehlt, sind alle übertragenen Werte Nullen; jede Messung in dieser Zeit
   ist wertlos, obwohl im TTN Uplinks ankommen.
1. **Die drei aktuellen Arbeitspakete** — Konfigurationen durchgehen,
   UI-Probleme beheben, Genauigkeit/Confidence untersuchen. Punkt 3 ist der
   inhaltlich wichtigste für die Arbeit selbst: eine belastbare Aussage zur
   Zählgenauigkeit ist das eigentliche Ergebnis, nicht die Lauffähigkeit.
2. **Bei den UI-Problemen zuerst die Symptome festhalten**, bevor gefixt wird —
   ohne Notiz, welcher Tab und welches Verhalten, geht Zeit beim Reproduzieren
   verloren.
3. Kreuzungserkennung mit echten Tracking-Daten verifizieren — die letzte
   größere inhaltliche Verifikation, die noch aussteht.
4. LoRa: kein akuter Handlungsbedarf mehr (läuft). Offen bleiben nur die
   Header-Bytes 3–4 und das fehlende `in_field` in den Auto-Modi.
5. Die zwei länger offenen technischen Probleme (zweites Anzeigefenster,
   `std::system_error` bei aktiver Live-Vorschau) sind unabhängig und
   blockieren nichts anderes — für Dauerbetrieb ist ein systemd-Watchdog
   vorgesehen.
6. Hardware/Gehäuse und der Realtest sind die größeren Themen für die
   verbleibende Zeit bis zur Abgabe — Priorisierung beim Betreuer-/
   Stadtwerke-Gespräch abstimmen.
