# ToDo – Personenzähl-Prototyp (Stadtwerke Potsdam)

Stand: 10.08.2026 — Bezug: `core/` (app.py, roi_config_app.py, ui_utils.py, config.py, tracking.py, counting.py, visualization.py, logging_utils.py, csv_utils.py, core.py, auto_config.py, auto_config_clustering.py, lora_message.py, lora_send_loop.py, warmup.py, benchmark.py) sowie `tests/` (Kamera- und LoRa-Hardware-Tests)

**Praxis ab sofort:** Lösungen, die auf recherchierten externen Quellen beruhen,
werden mit Quellenlink notiert — auch wenn sie noch nicht fertig funktionieren.

## 🔒 Dauerregel — Bildmaterial

**Normalbetrieb: keine Bildspeicherung.** Der Mitschnitt (`recording.py`,
Tab 3, Checkbox ganz oben) ist ein reines Benchmark-Werkzeug und
standardmässig aus. Vor jedem Feldeinsatz prüfen, dass er aus ist; nach jedem
Laborlauf das Material nach der Auswertung löschen. Begründung und Regeln:
[`../entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md`](../entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md).

## 🚨 Sofort erledigen — wirkt sich JETZT auf die Messung aus

- [x] **IN-Feld gesetzt (24.07.).** Die Gerätekonfiguration steht jetzt auf
      `multi_roi` mit vier Flächen (`office`/`ausgang`/`Vorlesung`/`Anlage`),
      `in_field = office`, `snap_to_nearest = true`. Der frühere Nullwerte-Fehler
      (IN-Feld `None`) ist damit erledigt.
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

## 🔌 LoRa-Übertragung — funktioniert grundsätzlich, scheitert aber am Standort (24.07.)

**Status: Code funktioniert, Funkstrecke am aktuellen Standort nicht.**
Vom 18.–22.07. kamen echte Zählwerte per LoRa in TTN an (FPort 2). Ab dem 24.07.
hängt das Modul in einer **Join-Schleife**: alle ~148 s ein Join-Versuch, jedes
Mal eine neue DevAddr, **kein einziger Uplink**.

**Ursache gefunden: RSSI ≈ −130 dBm** — praktisch die Nachweisgrenze (LoRa
schafft theoretisch bis etwa −137 dBm). Die Uplinks quetschen sich gerade noch
durch, aber der Join-Accept-**Downlink** vom Gateway erreicht das Modul nie.
Deshalb meldet sich das Gerät endlos neu an, ohne je zu senden. Das ist **kein
Softwarefehler**: `lora_send_loop.py` löst nie selbst einen Join aus (sendet nur
`AT+SENDB`); die Joins kommen vom Modul selbst.

**Konsequenz: Wechsel auf MQTT** als Übertragungsweg (siehe eigener Abschnitt
unten). LoRa bleibt für die Arbeit als Vergleichsfall wertvoll — es zeigt, dass
OTAA von einer funktionierenden Downlink-Richtung abhängt, die bei fremder
Gateway-Infrastruktur nicht garantiert ist.

**Am Code ergänzt (24.07.):** `open_serial()` öffnet die serielle Schnittstelle
ohne DTR/RTS (pyserial setzt sonst über den CP2102 das Modul bei jedem
Skriptstart zurück und erzwingt einen Join); `query_join_status()` fragt
`AT+NJS=?` beim Start und nach je drei Fehlversuchen ab und schreibt das Ergebnis
ins Protokoll — so ist sofort sichtbar, ob das Modul überhaupt am Netz ist.

Der ursprüngliche Integrationsstand darunter gilt weiter:

**Status der Integration: funktioniert.** Der Versand ist in `core/` integriert
und in Tab 3 der App zuschaltbar.

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
- [x] **Auto-Modi ohne IN-Feld — durch Ausblenden erledigt (03.08.).** Die
      beiden Auto-Modi sind über `config.SHOW_AUTO_CONFIG = False` aktuell aus
      der UI ausgeblendet (Code bleibt erhalten), betrifft LoRa/MQTT also
      derzeit nicht. Bei Reaktivierung erneut prüfen. Details:
      `entwicklung/AENDERUNGEN-mehrere-inout-lightmode-autostart.md`.
- [ ] Verhalten über längere Zeit im Feld beobachten (Duty-Cycle, Paketverluste,
      Sequenznummern-Überlauf bei 255).
- [x] **Fehlendes IN-Feld sichtbarer machen — gelöst über Speicher-Validierung
      (03.08.).** `multi_roi` speichert jetzt nicht mehr ohne gültige
      IN/OUT-Aufteilung (mindestens eine Fläche IN, mindestens eine OUT wird
      beim Speichern erzwungen) — der stille Nullwerte-Fall kann dadurch gar
      nicht mehr entstehen. `in_field` ist außerdem auf eine Liste umgestellt
      (mehrere IN-Flächen möglich, Standard: zuerst angelegte Fläche = IN).
      Details: `entwicklung/AENDERUNGEN-mehrere-inout-lightmode-autostart.md`.

## 📡 MQTT-Übertragung + Stadtwerke-Server — IN BETRIEB, LÄUFT (28.07.)

**Status: erfolgreich in Betrieb genommen.** Sensor sendet über MQTT an den
Server-Pi, der Server empfängt, dekodiert und zeigt die Daten im Dashboard an —
end-to-end auf der echten Hardware bestätigt. Ersatz für LoRa am aktuellen
Standort.

**Zwei Nachrichtenformate:**
- **Format 2 (LoRa, 18 Byte):** je Klasse ein IN/OUT-Paar bezogen aufs IN-Feld.
- **Format 3 (MQTT, JSON):** die **vollständige Übergangsmatrix** — je Paar
  (von-Feld, nach-Feld) und Klasse die Anzahl im Intervall. Über MQTT gibt es
  die 18-Byte-Grenze nicht. Als Liste umgesetzt (nur belegte Kombinationen),
  weil die volle Matrix fast leer wäre (~11 von 72 Kombinationen belegt).
  `summen{}` bleibt für die Vergleichbarkeit mit LoRa erhalten.

**Server (zweiter Pi 5, „stadtwerke-server"):** eigenes Repo `zaehlsensor-server`,
Flask + zwei MQTT-Empfänger in einem Prozess. Empfängt über **TTN** (stellt selbst
einen MQTT-Broker bereit) **und** direkt per **lokalem MQTT**. Dashboard mit
Kennzahlen, Verlaufsdiagramm, Übergangsmatrix, LED je Empfangsweg. SQLite-Ablage.
Beide Formate laufen parallel, Erkennung automatisch.

- [x] **MQTT auf dem Sensor in Betrieb genommen (28.07.).** Über den Block
      „Daten per MQTT senden" in Tab 3 der App. Broker = feste Server-IP
      (192.168.0.50), Port 1883, Sensor-ID passend.
- [x] **Server-Pi eingerichtet (28.07.).** Eigenes Repo geklont, Mosquitto fürs
      Netz geöffnet (`/etc/mosquitto/conf.d/netz.conf`: `listener 1883` +
      `allow_anonymous true`), TTN-Zugangsdaten in `konfiguration.ini`.
- [x] **paho-mqtt-Version geprüft.** Ist 1.6.1 — passt, kein Downgrade nötig.
- [x] **tls-Bug in `ingest.py` behoben (28.07.).** `configparser` liefert
      `tls = false` als **String** „false", und der ist in Python wahr → der
      MQTT-Empfänger schaltete fälschlich TLS ein und hing still beim Verbinden
      zum unverschlüsselten Broker (nur „verbinde mit", nie „verbunden"). Fix:
      Helfer `_als_wahrheitswert()` an beiden tls-Stellen (TTN + MQTT). Sofort-
      Umgehung ohne Codeänderung: in `konfiguration.ini` `tls =` leer lassen.
- [x] **Datenbank-Schema-Fehler behoben.** Alte `sensordaten.sqlite` hatte noch
      kein `felder`/`in_feld` → beim Speichern „table uplinks has no column".
      Alte DB weggeräumt, Server legt sie mit vollem Schema neu an.
- [ ] **systemd-Unit anpassen.** `zaehlsensor-server.service` steht noch auf
      Benutzer `fritz`; auf dem Server-Pi heißt der Benutzer `stadtwerke-server`
      — `User=` und `WorkingDirectory=` ändern. (Für den Dauerbetrieb; im
      Handbetrieb per `python server.py` läuft es schon.)
- [ ] **`konfiguration.ini` säubern:** im `[mqtt]`-Abschnitt `benutzer`/`passwort`
      leer lassen (lokaler Broker läuft anonym) und den in einer Zwischenversion
      eingetragenen TTN-API-Schlüssel in der TTN-Konsole zurückziehen + neu
      erzeugen (war kurzzeitig im Klartext sichtbar).
- [ ] **In der Arbeit begründen:** Format 3 erhöht den Detailgrad bewusst von
      „hinein/hinaus" auf „von wo nach wo". Das ist eine Entwurfsentscheidung,
      keine technische Notwendigkeit — bei sehr kurzen Intervallen beschreibt eine
      Nachricht mit genau einem Übergang faktisch eine einzelne Person, daher ist
      die Intervalllänge auch eine Frage der Datensparsamkeit.
- [x] **MQTT sendete seit der IN/OUT-je-Fläche-Umstellung nichts mehr an
      (04.08.), Ursache im Server gefunden und behoben.** `in_field`
      kommt vom Sensor seit 03.08. als Liste statt String; der Server
      (`stadtwerke-server/datenbank.py`) band den Rohwert direkt als
      SQLite-Parameter (`in_feld TEXT`) — eine Python-Liste lässt sich dort
      nicht binden, `sqlite3.InterfaceError` unbehandelt in `ingest.py`,
      `paho-mqtt` schluckt das nur als Log-Zeile. Nachrichten kamen nachweislich
      an (`mosquitto_pub`/`sub`-Test bestätigt), scheiterten aber beim
      Speichern. Fix: `_in_feld_text()`-Normalisierung vor dem Insert
      (`datenbank.py`, zwei Stellen) plus Mengen-Vergleich statt
      String-Vergleich in `dekoder.py::_summen_aus_uebergaengen()`. Getestet
      end-to-end (`decode_json` → `uplink_speichern`) mit Listen-Format.
      **Noch zu tun:** Fix liegt bisher nur lokal, muss noch auf den
      Server-Pi (git push/pull, je nachdem wie das Server-Repo dort verwaltet
      wird).

## 🗺️ Urbane Datenplattform Potsdam — Datenveröffentlichung (04.08., Recherche)

Ziel: die vom Sensor/Server bereitgestellten Daten in einem Format anbieten,
das zu den bestehenden Datensätzen auf
[ckan.urbanedatenplattform-potsdam.de](https://ckan.urbanedatenplattform-potsdam.de)
passt. Recherche-Stand:

- **Plattform läuft auf CKAN**, Standard-CKAN-API verfügbar
  (`docs.ckan.org/en/2.11/api/`). 17 thematische Gruppen, u. a. „Verkehr" (8
  Datensätze), „SWP" (5, Stadtwerke Potsdam), sowie eine eigene **„LoRaWAN"-
  Gruppe, die aktuell noch KEINE Datensätze enthält** — für die Arbeit
  erwähnenswert (früher/einziger LoRaWAN-Sensordatensatz auf der Plattform,
  falls wir dort veröffentlichen).
- **Übliches Format-Bündel:** die meisten Geo-Datensätze bieten dieselbe
  Formatpalette parallel an: CSV, XLS, GeoJSON, JSON, Parquet, SHP, KML,
  FlatGeobuf, GPX. Für einen Zählsensor sind davon realistisch nur
  **CSV + JSON (+ optional GeoJSON für den Standort)** relevant — die
  Geo-Exportformate (SHP/KML/GPX/FlatGeobuf) passen zu Flächen-/Routendaten,
  nicht zu einer Zeitreihe.
- **Vergleichbarer Zähldatensatz „Verkehrszählungen"** (Gruppe „Verkehr", LHP):
  ist selbst nur ein **Standort-Index** (Spalten: `Geo Point`, `Geo Shape`,
  `OBJECTID`, `KPNR`, `Name`, `ODP`, `Zählpläne`) — die eigentlichen
  Zeitreihen liegen als ZIP-Archive hinter einem Link je Zählstelle
  (`Zählpläne`-Spalte). Übertragen auf uns: ein Datensatz „unsere Sensoren"
  (ein Punkt je Sensor/Eingang, mit Standort + Link zu den Zählwerten) plus
  ein zweiter, laufend aktualisierter Datensatz mit den eigentlichen
  Zählwerten.
- **Wichtigster Fund: „Parking Echtzeit"** (Gruppe „Verkehr", ebenfalls LHP)
  registriert als CSV-Ressource keine hochgeladene Datei, sondern eine
  **live abrufbare URL** auf Stadtwerke-Potsdam-eigener Infrastruktur
  (`https://cs1-swp.westeurope.cloudapp.azure.com:8443/parking_csv`) — CKAN
  zeigt/verlinkt diese Live-Quelle, statt dass jemand die Datei manuell
  aktuell halten muss. **Das ist bereits unser Fall:** `server.py` hat mit
  `/api/export.csv` und `/api/uebersicht` (JSON) schon passende Endpunkte —
  diese könnten direkt nach diesem Muster als CKAN-Ressourcen-URLs
  eingetragen werden, ohne zusätzlichen Exportmechanismus zu bauen.
- **Metadaten bei bestehenden Datensätzen eher dünn:** Lizenz meist „keine
  Lizenz angegeben", Update-Frequenz selten dokumentiert, Spaltenbeschreibungen
  fehlen oft auf der Übersichtsseite (nur in den Dateien selbst). Für unseren
  Datensatz lohnt es sich, das **besser** zu machen (Lizenz, Update-Takt,
  Spaltenbeschreibung mit angeben) — im Sinne von Kapitel 6/7 als positives
  Abgrenzungsmerkmal dokumentierbar.
- [ ] **Nächster Schritt (offen):** entscheiden, ob wir einen eigenen
      Datensatz in der Gruppe „Verkehr" oder „LoRaWAN" anlegen wollen, welche
      Formate wir tatsächlich anbieten (CSV + JSON reicht vermutlich),
      Kontakt für Veröffentlichung: `smartcity@swp-potsdam.de`.

## 💡 Ideen / Überlegungen (noch nicht entschieden, nicht umsetzen ohne Rücksprache)

- [ ] **Zusätzliche MQTT-Statusmeldungen** (04.08., reine Überlegung von
      Friedrich, noch nicht spezifiziert): über die reinen Zählwerte hinaus
      Ereignis-Nachrichten senden, z. B. wenn die Konfiguration (`roi_config.json`)
      geändert wurde, oder wenn der Sensor abgestürzt war und wieder hochfährt
      (Neustart-/Recovery-Meldung). Format 4 (Konfiguration) und Format 5
      (LoRa-Kontrolle) existieren im Server (`dekoder.py`) bereits als
      Sonderformate — eine „Sensor neu gestartet"-Meldung wäre vermutlich ein
      weiteres, eigenes Format. Vor der Umsetzung klären: welche Ereignisse
      genau, wie oft (Flut von Meldungen bei instabiler Verbindung vermeiden?),
      und ob das eher in `warmup.py`/`app.py` (Sensorseite) oder rein
      serverseitig (aus Verbindungsabbrüchen ableiten) ansetzen sollte.

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
- [x] **IN/OUT je Fläche im Mehrere-Flächen-Modus (03.08.).** Statt eines
      einzelnen IN-Feld-Dropdowns eine Checkbox je Fläche; Standard: zuerst
      angelegte Fläche IN, Rest OUT. Speichern ohne mindestens eine IN- und
      eine OUT-Fläche wird verhindert. Details:
      `entwicklung/AENDERUNGEN-mehrere-inout-lightmode-autostart.md`.
- [x] **Light-Mode ergänzt, Auswahl bleibt über Neustarts erhalten (03.08.).**
      Umschalt-Knopf in der Sidebar, Speicherung in `ui_settings.json`.
- [x] **Autostart beim Hochfahren (03.08.).** `start_app.sh` +
      Desktop-Autostart-Eintrag: Terminal öffnet sich automatisch, aktiviert
      die venv, wärmt die Pipeline einmalig auf (`warmup.py`) und startet
      `app.py --autostart`, das dann selbst die Zählung mit USB-Input
      beginnt — kein manuelles Klicken am Gerät mehr nötig.
- [x] **Benchmark-Bericht bei aktivem Mitschnitt (10.08.).** Neues Modul
      `benchmark.py`: schreibt am Lauf-Ende `..._benchmark.json`/`.txt` neben
      das Video — Frame-Verarbeitungszeit (min/max/Ø, effektive fps), leere
      Puffer/mögliche Aussetzer (Heuristik, siehe Modul-Docstring),
      CPU-Auslastung/SoC-Temperatur/Leistungsaufnahme des Pi
      (`/proc/stat`/`vcgencmd`). **Offen:** Hailo-Beschleuniger-Auslastung ist
      nur experimentell über `HAILO_MONITOR` umgesetzt und **nicht an echter
      Hardware verifiziert** — beim nächsten Laborlauf mit Mitschnitt prüfen,
      ob im Bericht `"hailo_beschleuniger": {"verfuegbar": true, ...}` steht
      oder eine Begründung für "nicht verfügbar". Details:
      `entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md`.
- [x] **Debug-Hauptschalter in Tab 3 (10.08.).** Mitschnitt, Live-Vorschau,
      optionales Zeitlimit, Debug-Dateien (`ergebniss.csv`, Bewegungsbilder,
      Benchmark-Bericht) und die detaillierte Konsolenausgabe
      (Frame-/Detection-Zeilen) sind jetzt hinter "Debug-Funktionen
      aktivieren" versteckt, Standard AUS (sauberer Feldbetrieb). LoRa/MQTT
      bleiben davon unberührt, immer sichtbar. `zaehlung.csv` wird bewusst
      **immer** geschrieben (LoRa/MQTT und Tab 4 lesen daraus) —
      ausdrücklich NICHT Teil des Debug-Schalters. Erzwungen sowohl über die
      UI-Sichtbarkeit als auch nochmal beim tatsächlichen Pipeline-Start
      (`tabs/pipeline_control.py`), damit eine im Labor aktivierte, aber
      ausgeblendete Option nicht versehentlich in den Feldeinsatz mitgenommen
      wird.

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
- [x] **Confidence-Schwellwert als Parameter eingeführt (28.07.).** Umgesetzt
      als Filter in `core.py` direkt nach `detection.get_confidence()` (nicht in
      `should_count_track()`, weil dort schon der Track statt der Einzel-Detection
      vorliegt) plus Wert `min_confidence` in `roi_config.json`/`config.py` und
      Eingabefeld in Tab 2. Standard 0.5.
- [ ] Auswertung fahren: denselben Lauf bei mehreren Schwellen (z. B. 0.3 / 0.4 / 0.5 / 0.6 / 0.7) gegen die Ground Truth stellen; `avg_confidence` aus `ergebniss.csv` nutzen
- [ ] Fehlerarten getrennt erfassen statt nur Gesamtabweichung: verpasste Objekte, doppelt gezählte (Track-Verlust und Neuvergabe), falsche Klasse, falsche Richtung
- [ ] Ergebnis als Tabelle/Diagramm für die Arbeit aufbereiten und einen begründeten Standardwert für die Schwelle festlegen
- [ ] Dabei mitprüfen: hängt die optimale Schwelle vom Zählmodus oder von der Kameraperspektive ab?

### Konfiguration
- [x] **„Nächste Fläche zuordnen" pro Fläche wählbar (26.07. umgesetzt).**
      Globaler Schalter bleibt Hauptschalter; ist er an, erscheint in Tab 2 eine
      Liste mit einem Häkchen je Fläche. Gespeichert je Region als `"snap"` in
      `roi_config.json`, der alte globale `snap_to_nearest` bleibt aus
      Verträglichkeit erhalten. Das Overlay färbt nur noch markierte Flächen ein,
      und die Zähllogik (`counting.py`) nimmt nur Flächen mit `snap=true` als
      Ziel für Punkte ohne Treffer.
- [x] **Mindest-Konfidenz zum Zählen einstellbar (28.07.).** In Tab 2 unter
      „Richtung umkehren" ein Eingabefeld (Standard 0.5). Erkennungen unterhalb
      dieser Konfidenz werden nicht gezählt. Gespeichert als `min_confidence` in
      `roi_config.json`; wirkt in `core.py` direkt nach `get_confidence()`.
      Damit ist auch der Punkt aus „Genauigkeit & Auswertung" (Confidence-
      Schwelle konfigurierbar) erledigt — offen bleibt nur, einen begründeten
      Standardwert aus den Testdaten abzuleiten.
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
- [x] **Labortest durchgeführt — erfolgreich (20.–22.07.).** Kontrollierter Lauf
      mit 228 Datensätzen, 34 gezählten Übergängen; `zaehlung.csv` + `ergebniss.csv`
      + `roi_config.json` liegen vor. Auswertung läuft noch (siehe unten).
- [ ] **Auswertung des Labortests (in Arbeit).** Vergleichs-Werkzeug gebaut
      (`vergleich/`): Desktop (`vergleich_app.py`) und Tablet-Web (`vergleich_web.html`),
      zeigt jeden Datensatz textlich und grafisch auf der Zählfläche, mit
      „frühere Datensätze einblenden", Filter „nur gezählte Übergänge" und
      deutlicher Warnung bei Datensatz-Abweichung. Abgleich gegen das Video läuft
      manuell; Fehlertaxonomie steht (Erkennung / Tracking / Zählung getrennt).
- [ ] Realtest — Vorschlag an Betreuer geschickt: erst an der Uni (bester Zugriff), danach ggf. Volkspark Biosphäre. Antwort steht noch aus.

## Priorisierung für die kommenden Wochen

0. **Auswertung des Labortests** — der inhaltlich wichtigste Punkt für die
   Arbeit. Die belastbare Aussage zur Zählgenauigkeit ist das eigentliche
   Ergebnis, nicht die Lauffähigkeit. Läuft bereits. Konkret jetzt: den Lauf bei
   mehreren Konfidenz-Schwellen gegen die Ground Truth stellen und daraus einen
   begründeten Standardwert ableiten (das Feld dafür ist jetzt da).
1. ~~MQTT + Server in Betrieb nehmen~~ — **erledigt (28.07.), läuft.**
2. **Verbleibende Arbeitspakete** — UI-Feinschliff, Realtest (Betreuer-Antwort
   abwarten), Genauigkeitsauswertung abschließen. Die Konfig-Wünsche (snap pro
   Fläche, Konfidenz-Schwelle) sind umgesetzt.
3. **Für den Dauerbetrieb** (nicht dringend): systemd-Unit auf Benutzer
   `stadtwerke-server` umstellen, `konfiguration.ini` säubern (siehe
   MQTT-Abschnitt).
3. **Bei den UI-Problemen zuerst die Symptome festhalten**, bevor gefixt wird —
   ohne Notiz, welcher Tab und welches Verhalten, geht Zeit beim Reproduzieren
   verloren.
4. Kreuzungserkennung mit echten Tracking-Daten verifizieren — die letzte
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
