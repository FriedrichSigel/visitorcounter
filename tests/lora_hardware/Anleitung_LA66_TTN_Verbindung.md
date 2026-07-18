# LA66 USB Adapter V2 mit The Things Network (TTN) verbinden
## Schritt-für-Schritt-Anleitung mit projektbezogenen Tests

**Stand 17.07.2026.** Für den Besucherzählsensor (Raspberry Pi 5, `stadtwerke2`).
Ziel: Das Dragino LA66-V2 per OTAA in TTN registrieren und den 18-Byte-Uplink
(Zählformat v2) end-to-end bis in die TTN-Konsole nachweisen.

Angaben aus der offiziellen Dragino-Doku (LA66 USB Adapter V2 User Manual) und
den TTN-Foren; an den bereits verifizierten Gerätestand angepasst (LA66 antwortet
auf AT @ 9600 Baud an `/dev/ttyUSB0`, LoRaWAN v1.0.3, werkseitige OTAA-Keys).

> **Voraussetzung Gateway:** OTAA-Join funktioniert nur, wenn ein TTN-Gateway in
> Funkreichweite ist. In Potsdam gibt es öffentliche TTN-Gateways — vor dem Test
> auf der TTN-Karte (ttnmapper.org bzw. der Gateway-Liste der Konsole) prüfen, ob
> am Teststandort Abdeckung besteht. Ohne erreichbares Gateway scheitert der Join
> unabhängig von der Konfiguration. **Am Volkspark selbst muss die Abdeckung mit
> den Stadtwerken geklärt werden** — dieser Test dient dem Funktionsnachweis am
> Uni-/Wohnstandort.

---

## Phase 1 — Keys vom LA66 auslesen

Der LA66 bringt werkseitig eindeutige OTAA-Keys mit. Diese müssen ausgelesen und
in TTN eingetragen werden (nicht umgekehrt).

### 1.1 Serielle Verbindung herstellen
```bash
# Port bestätigen (stabiler by-id-Pfad, überlebt Neustarts/Umstecken)
ls -l /dev/serial/by-id/
# erwartet: ...CP2102...  ->  ../../ttyUSB0

# Terminalprogramm öffnen (9600 Baud ist zwingend)
sudo apt install -y minicom
minicom -D /dev/ttyUSB0 -b 9600
```
Alternativ ohne Installation mit Python (siehe euer `la66_probe.py`).

> **Stolperstein (aus TTN-Forum):** Nur bei **9600 Baud** reagiert das Modul.
> Bei falscher Baudrate kommt „AT_ERROR" oder gar keine Antwort. In minicom
> ggf. lokales Echo einschalten (`Strg-A E`), damit man die Eingabe sieht, und
> „Add Carriage Return" aktivieren.

### 1.2 Grundfunktion prüfen
```
AT              # -> OK
AT+VER          # -> Firmware-Version + Frequenzband (muss EU868 sein!)
```
**Wenn hier EU868 nicht bestätigt wird, stoppen** — ein US915/AS923-Modul
joint in Europa nicht. (War bei euch bereits als EU868 verifiziert.)

### 1.3 Die drei OTAA-Werte auslesen
```
AT+DEUI         # Device EUI    (16 Hex-Zeichen)  -> für TTN "DevEUI"
AT+APPEUI       # Application EUI/JoinEUI          -> für TTN "JoinEUI/AppEUI"
AT+APPKEY       # Application Key (32 Hex-Zeichen) -> für TTN "AppKey"
```
Alle drei **notieren** (Foto/Copy). Diese Werte sind Geheimnisse —
**niemals ins Git-Repository** (die `.gitignore` schützt `roi_config.json`, aber
Keys gehören generell nicht in Dateien im Repo).

> **Stolperstein (aus TTN-Forum „No join accept"):** DevEUI und JoinEUI/AppEUI
> **nicht verwechseln** — die häufigste Join-Fehlerquelle. Direkt aus der
> AT-Ausgabe kopieren, nicht abtippen.

---

## Phase 2 — Gerät in TTN anlegen

### 2.1 Application anlegen
1. In der TTN-Konsole (eu1.cloud.thethings.network für Europa) anmelden.
2. **Applications → Create application**. ID z. B. `besucherzaehlsensor-potsdam`.

### 2.2 End Device manuell registrieren
1. In der Application: **Register end device → Enter end device specifics manually**.
2. **Frequency plan:** *Europe 863–870 MHz (SF9 for RX2 – recommended)*.
3. **LoRaWAN version:** *LoRaWAN Specification 1.0.3*.
   (LA66 nutzt v1.0.3 — falsche Version = Join scheitert.)
4. **Regional Parameters:** die zu 1.0.3 vorgeschlagene Version (RP001 1.0.3 Rev A).
5. **Activation mode:** *Over the air activation (OTAA)*.
6. Die drei ausgelesenen Werte eintragen:
   - **JoinEUI / AppEUI** = `AT+APPEUI`-Wert
   - **DevEUI** = `AT+DEUI`-Wert
   - **AppKey** = `AT+APPKEY`-Wert
7. **Register end device** klicken.

### 2.3 (Vorbereitung für Phase 4) Payload-Formatter hinterlegen
In der Application: **Payload formatters → Uplink → Custom Javascript formatter**
und den Decoder aus `LoRa_Nachrichtenformat_Spezifikation.md` (Abschnitt 5.2,
`decodeUplink` für das 18-Byte-Format v2) einfügen und speichern. Damit erscheinen
die dekodierten Zählwerte direkt lesbar in der Konsole.

---

## Phase 3 — Join durchführen (TEST 1: Netzbeitritt)

**Ziel:** Der LA66 tritt dem Netz bei ("Join accept"). Nachweis in der
TTN-Live-Ansicht.

1. In der TTN-Konsole das Device öffnen → Tab **Live data** offen lassen.
2. Am LA66 den Join anstoßen:
   ```
   AT+CJOIN=1,0   # OTAA-Join starten (bzw. AT+JOIN je nach Firmware)
   ```
   **LA66-V2 muss NICHT per RST-Knopf zurückgesetzt werden** (im Gegensatz zu V1).
3. Warten (Sekunden bis ~1 Min). Erfolg zeigt sich:
   - **Am LA66:** Ausgabe wie `JOINED` / „Join Success".
   - **In TTN Live data:** Ereignisse `Join request` gefolgt von `Join accept`.

### ✅ Test-1-Kriterium (Netzbeitritt)
> In der TTN-Konsole erscheinen **Join request** UND **Join accept**, und das
> Device zeigt Status „connected"/zuletzt gesehen. Damit ist Funkstrecke +
> Registrierung bewiesen.

**Wenn kein Join accept kommt (häufigste Fälle):**
- Kein Gateway in Reichweite → Standort/Antenne prüfen, näher an bekanntes Gateway.
- JoinEUI/DevEUI vertauscht → in TTN korrigieren.
- Falsche LoRaWAN-Version (nicht 1.0.3) oder falscher Frequency Plan → korrigieren.
- Antenne nicht angeschraubt.

---

## Phase 4 — Nutzdaten senden (projektspezifische Tests)

Ab hier greifen die Tests, die zum Zählsensor passen. Erst ein manueller
Byte-Test, dann der echte Encoder aus dem Projekt.

### TEST 2 — Manueller Roh-Uplink (Format-Sanity-Check)
**Ziel:** Ein von Hand konstruierter 18-Byte-Frame im Format v2 kommt in TTN an
und wird vom hinterlegten Decoder korrekt zerlegt.

Beispiel aus der Formatspezifikation (Sensor 3, Frame 42, 8 Personen rein / 3 raus,
2 Fahrräder rein / 1 raus, 5 Autos rein / 6 raus, alle 6 Klassen aktiv, Status ok):
```
AT+SENDB=00,02,18,02032A05073F0803020105060000000000
```
Format: `AT+SENDB=<confirm>,<Fport>,<len>,<hexdata>` — hier unbestätigt (00),
Port 2, 18 Byte (0x18), dann die 36 Hex-Zeichen.

### ✅ Test-2-Kriterium (Payload-Weg + Decoder)
> In TTN **Live data** erscheint ein **Uplink message** mit 18 Byte Payload, und
> unter „Payload" zeigt der Formatter die dekodierten Felder:
> `person: {in:8, out:3}`, `car: {in:5, out:6}`, `total.in`, `frame_counter:42`,
> `sensor_id:3`. Stimmen die Werte mit dem gesendeten Frame überein, ist die
> gesamte Kette Sensor → Funk → TTN → Decoder bewiesen.

### TEST 3 — Echter Encoder aus dem Projekt (End-to-End)
**Ziel:** Der Python-Encoder `encode_counts()` erzeugt den Frame, `lora_transmitter.py`
sendet ihn, TTN zeigt ihn dekodiert. Das ist der eigentliche Integrationsnachweis.

1. Auf dem Pi (in der venv, Environment via `source setup_env.sh`):
   ```python
   from lora_transmitter import encode_counts   # aus dem Projekt
   frame = encode_counts(
       sensor_id=3, frame_counter=1, interval_min=5,
       status=0b00000111,
       active_classes=["person","bicycle","car","bus","truck"],
       counts={"person": (8,3), "bicycle": (2,1), "car": (5,6)},
   )
   print(frame.hex())   # muss 36 Hex-Zeichen (18 Byte) ergeben
   ```
2. Diesen Hex-Wert per `AT+SENDB=00,02,18,<hex>` senden (bzw. direkt über die
   `LA66Transport`-Klasse des `lora_transmitter.py`, die genau dieses AT-Kommando
   absetzt).

### ✅ Test-3-Kriterium (Projekt-Integration)
> Der vom **Projekt-Encoder** erzeugte Frame erscheint in TTN korrekt dekodiert.
> Damit ist nachgewiesen: Encoder-Format == Decoder-Format == Realübertragung.

### TEST 4 — Zyklischer Betrieb (5-Minuten-Intervall)
**Ziel:** Nachweis des vorgesehenen Betriebsmusters — alle 5 min ein Uplink mit
den Übergängen des Intervalls, `frame_counter` zählt hoch.

1. `lora_transmitter.py` im zyklischen Modus laufen lassen (Queue-Thread,
   Duty-Cycle-Bremse), gespeist aus den aggregierten Zählwerten.
2. Über mehrere Intervalle in TTN beobachten.

### ✅ Test-4-Kriterium (Dauerbetrieb)
> Über ≥ 3 Intervalle erscheinen Uplinks im ~5-Minuten-Takt, der
> `frame_counter` inkrementiert je Nachricht, und der EU868-Duty-Cycle (1 %)
> wird eingehalten (keine „Duty cycle exceeded"-Warnung in TTN). Das ist der
> Betriebsnachweis für das Evaluationskapitel.

---

## Zusammenfassung der Testkette (für die Arbeit)

| Test | Nachweist | TTN-Beleg | Bezug Arbeit |
|---|---|---|---|
| 1 Join | Funkstrecke + Registrierung | Join request + accept | 4.c.iii |
| 2 Roh-Uplink | Payload-Weg + Decoder | Uplink 18 B, dekodiert | 4.b.viii |
| 3 Encoder | Projekt-Format konsistent | Encoder-Frame dekodiert | 4.b.viii / 4.c |
| 4 Zyklus | Betriebsmuster (5 min) | mehrere Uplinks, frame_counter++ | 5.d |

Dieselben Tests laufen bereits skriptgestützt vor: **Test 1 (offline)** in
`test1_offline/` (Software-Teil grün), **Test 2 (TTN)** in `test2_ttn/` mit dem
JS-Decoder `ttn_payload_decoder.js`. Diese Anleitung führt sie am realen Gerät
zusammen.

---

## Nach erfolgreichem Test: Übergang zu den Stadtwerken

TTN und die Urbane Datenplattform der Stadtwerke sind **zwei verschiedene
Network Server**. Das Gerät kann nur bei *einem* gleichzeitig registriert sein
(ein OTAA-Schlüsselsatz). Vorgehen für den Produktivbetrieb:
1. Funktionsnachweis in TTN (diese Anleitung) — schnell, öffentlich, gut zum Debuggen.
2. Für den Echtbetrieb dieselben Keys (DevEUI/JoinEUI/AppKey) an die Stadtwerke
   für deren Network Server übergeben (sicherer Kanal, nicht per Repo/Mail im Klartext).
3. Den JS-Decoder (`decodeUplink`) mitliefern, damit deren Server die 18-Byte-
   Payload interpretieren kann.
4. Gateway-Abdeckung am Volkspark mit den Stadtwerken abklären.

> Für die Setup-Reproduzierbarkeit: erfolgreiche AT-Kommandos und die TTN-
> Registrierungsschritte in `EINRICHTUNG_LA66.md` fortschreiben (ohne die
> geheimen Keys).

## Quellen
- Dragino (o. J.) *LA66 USB Adapter V2 User Manual.* wiki.dragino.com
  (Zugriff: 17.07.2026).
- Dragino (o. J.) *End Device AT Commands and Downlink Command.* wiki.dragino.com
  (Zugriff: 17.07.2026).
- The Things Industries (o. J.) *Adding Devices / Payload Formatters.*
  thethingsindustries.com (Zugriff: 17.07.2026).
