# Test 2 — Ende-zu-Ende über TTN (The Things Network)

**Ziel:** Nachweisen, dass die komplette Kette funktioniert:
*Zählnachricht → LA66 → Funk → Gateway → Network Server → dekodierte Daten.*
TTN ersetzt dabei den Network Server der Stadtwerke — die Architektur ist
identisch, nur der Betreiber ein anderer. Ein bestandener Test 2 bedeutet:
Für die Stadtwerke-Anbindung fehlt **nur noch die Registrierung dort**,
kein Code.

**Einordnung in die Arbeit:** Kapitel 4.c.iii (Labortest der Übertragungs-
strecke) und Vorstufe zu 5.d (Bewertung der Datenübertragung).

**Vorbedingung:** Test 1 vollständig bestanden.

---

## Teil A — Vorbereitung (einmalig, ~20 min)

### A.1 Gateway-Abdeckung prüfen — ZUERST!

Bevor du irgendetwas registrierst: [ttnmapper.org](https://ttnmapper.org)
öffnen und prüfen, ob am Teststandort (Wohnung/Uni) ein TTN-Gateway in
Reichweite ist. **Kein Gateway = Test 2 kann nicht gelingen**, egal wie
korrekt alles konfiguriert ist. In dem Fall: Standort wechseln oder Test 2
überspringen und direkt mit den Stadtwerken testen.

### A.2 TTN-Konto und Application anlegen

1. Konto auf [console.cloud.thethings.network](https://console.cloud.thethings.network)
   → Cluster **Europe 1 (eu1)** wählen.
2. **Create application** → ID z. B. `ba-personenzaehlung-test`.

### A.3 End Device registrieren

Keys vom Gerät auslesen (lokal, Klartext nur am eigenen Terminal):

```bash
python3 ../la66_probe.py --show-keys
```

Dann in der TTN-Konsole: Application → **Register end device**
→ **Enter end device specifics manually**:

| Feld | Wert |
|---|---|
| Frequency plan | **Europe 863–870 MHz (SF9 for RX2 – recommended)** |
| LoRaWAN version | **1.0.3** (Firmware des LA66) |
| JoinEUI | AppEUI vom Gerät |
| DevEUI | DevEUI vom Gerät |
| AppKey | AppKey vom Gerät |

> Alternativ per QR-Code auf dem Gerät („scan end device QR code") — falls
> dein „Registration Key" ein Claim-Code ist, ist das genau sein Einsatzort.

### A.4 Payload-Decoder einrichten

Application → **Payload formatters** → **Uplink** → Formatter type
**Custom Javascript** → Inhalt von `ttn_payload_decoder.js` einfügen → Save.

Damit zeigt die Live-Ansicht statt Hex direkt `count_in`, `count_out`,
`mode_name` usw. — und der Decoder ist gleichzeitig die getestete Referenz,
die du später den Stadtwerken übergibst.

---

## Teil B — Testdurchführung (~10 min + Sendeintervalle)

1. TTN-Konsole öffnen: Application → **Live data** (sichtbar lassen).
2. Auf dem Pi:

```bash
cd lora_hardware_test/test2_ttn
python3 test2_ttn.py
```

Optionen:

```bash
python3 test2_ttn.py --interval 60      # Abstand Serien-Uplinks (Standard 60 s)
python3 test2_ttn.py --skip-series      # nur Join + ein Uplink (schnell)
python3 test2_ttn.py --join-timeout 180 # laengeres Join-Fenster
```

3. Das Skript sendet Testnachrichten mit `sensor_id=99` und aufsteigendem
   `count_in` (1, 2, 3, 4) — so sind sie in der Live-Ansicht eindeutig
   zuzuordnen.
4. Am Ende fragt das Skript, ob alle Payloads in TTN sichtbar und korrekt
   dekodiert sind (T2.5) → mit `j`/`n` beantworten.
5. Protokoll `test2_ergebnis.md` prüfen und committen.

---

## Die fünf Teiltests

| Test | Prüfpunkt | Beweist |
|---|---|---|
| T2.1 | AT-Kontakt | Vorbedingung (wie Test 1) |
| T2.2 | OTAA-Join gelingt | Keys korrekt registriert **und** Gateway in Reichweite |
| T2.3 | Einzel-Uplink | `AT+SENDB` transportiert das 25-Byte-Format über Funk |
| T2.4 | Serien-Uplink (3×) | `LoRaTransmitter` (Queue, Duty-Cycle-Bremse) funktioniert am echten Gerät |
| T2.5 | Manuelle Bestätigung | Ende-zu-Ende: Daten kommen an **und** dekodieren korrekt |

## Wenn der Join scheitert (T2.2)

In dieser Reihenfolge prüfen:

1. **Keys**: In TTN Zeichen für Zeichen mit `--show-keys`-Ausgabe vergleichen.
   Häufigster Fehler: DevEUI und AppEUI vertauscht.
2. **LoRaWAN-Version**: muss 1.0.3 sein, nicht 1.1.
3. **Gateway**: TTN-Konsole → Gateways in der Nähe online? TTN Mapper prüfen.
4. **Physik**: Antenne fest? Ans Fenster. Bei Stahlbeton hilft nur raus.
5. **Frequenzplan**: Europe 863–870, nicht US915 o. ä.

## Duty Cycle beachten

EU868 erlaubt 1 % Sendezeit. Das Skript hält standardmäßig 60 s Abstand —
**nicht** auf wenige Sekunden reduzieren, sonst drosselt entweder die Firmware
oder du verstößt gegen die Funkregulierung. Für die Arbeit ist das der Beleg,
warum aggregiert (Intervallwerte) statt ereignisbasiert (pro Person) gesendet
wird.

---

## Nach bestandenem Test 2 → Übergabe an die Stadtwerke

1. Gerät in TTN **löschen** (End device → General settings → Delete) —
   ein Gerät kann nur bei einem Network Server aktiv sein.
2. An Titus Tomascik / Andreas Becker senden:
   - DevEUI, AppEUI, AppKey (sicherer Kanal, nicht unverschlüsselt per Mail
     wenn vermeidbar — nachfragen, wie sie es haben wollen)
   - `ttn_payload_decoder.js` als Decoder-Referenz
   - Formatdokumentation (Kommentarkopf aus `lora_transmitter.py`)
   - Frage: LoRaWAN-Abdeckung am Volkspark Biosphäre vorhanden?
3. Optional neuen AppKey setzen (`AT+APPKEY=...`), falls die Stadtwerke
   frische Credentials verlangen.
