# LoRaWAN-Nachrichtenformat für den Besucherzählsensor
## Spezifikation, Begründung nach Industriestandards, Encoder + Decoder

**Stand 15.07.2026. Für Kapitel 4.b.viii (Datenübertragung) und 3.e.iii.**

Entwurf eines Uplink-Nachrichtenformats für die zyklische Übertragung
aggregierter Zählwerte (Intervall 5 min) über LoRaWAN an die Urbane
Datenplattform Potsdam. Das Format orientiert sich an etablierten Konventionen
und ist gegen diese begründet.

---

## 1. Anforderungen an das Format

| Anforderung | Quelle |
|---|---|
| Zyklischer Uplink alle 5 min mit Übergängen des Intervalls | Nutzervorgabe |
| Unterscheidung nach Objektklassen (person, bicycle, car, …) | Nutzervorgabe |
| Richtungsdifferenzierung (in/out je Klasse) | Zähllogik (`is_transition`, `direction`) |
| SF12-tauglich (≤ 51 Byte Nutzlast, EU868) | LoRaWAN-Regionalparameter |
| Duty-Cycle-schonend (1 % EU868) | ETSI/LoRaWAN |
| Robust gegen Uplink-Wiederholungen (keine Doppelzählung) | PCR2-Konvention |
| Auf der UDP eindeutig dekodierbar | Betrieb |

---

## 2. Orientierung an Standards (für die Arbeit zitierbar)

Drei etablierte Konventionen prägen den Entwurf:

**(a) Cayenne Low Power Payload (LPP)** — myDevices, basierend auf den
**IPSO Smart Objects Guidelines** (die wiederum auf OMA-/IEC-nahe
Objektmodelle zurückgehen). Kernprinzip: Jeder Messwert wird als Tripel
`[Kanal | Typ | Wert]` kodiert; der Datentyp „Digital Input" (Typ 0x00) ist die
Standardrepräsentation für Zählerwerte. Cayenne LPP ist in The Things Stack
nativ als Payload-Formatter hinterlegt. (myDevices o. J.; The Things Industries
o. J.)

**(b) PCR2 People Counter Radar** (pmx systems) — ein kommerzieller
LoRaWAN-Personenzähler. Zwei übernommene Konzepte:
- **Frame-/Data-Counter (DCNT):** eine mit jedem Uplink hochzählende Nummer, mit
  der der Network Server **Wiederholungen** (bei ausbleibendem ACK) erkennt und
  ignoriert — verhindert Doppelzählung. (pmx systems o. J.)
- Kompakte Festpayload (dort 10 Byte) für den Betrieb in allen Regionen.

**(c) TTN Normalized Payload** — The Things Stack normalisiert Zählwerte auf das
Feld `action.motion.count` bzw. allgemein `"count"`. Der hier gelieferte Decoder
gibt Felder aus, die sich in dieses Schema überführen lassen. (The Things
Industries o. J.)

**Design-Konflikt und Entscheidung:** Eine *strikte* Cayenne-LPP-Kodierung
(jedes `[Kanal|Typ|2-Byte-Wert]`) bräuchte für 6 Klassen × 2 Richtungen
6 × 8 = 48 Byte allein für die Zählwerte — plus Header über der SF12-Grenze
(51 Byte). Deshalb wird ein **kompaktes Festformat** gewählt, das die
Cayenne-*Prinzipien* (Kanal = Klasse, feste Typ-Semantik, MSB-first/big-endian)
übernimmt, aber ohne die pro-Wert-Wiederholung von Kanal/Typ-Bytes auskommt.
Das ist die gleiche Abwägung, die auch PCR2 trifft (Festpayload statt
selbstbeschreibendem LPP). Für maximale Interoperabilität ist zusätzlich eine
**optionale reine Cayenne-LPP-Variante** für ≤ 3 Klassen dokumentiert (Abschnitt 6).

---

## 3. Nachrichtenformat (Festformat, big-endian / MSB-first)

**Gesamtlänge: 18 Byte** (Header 6 + 6 Klassen × 2). Big-endian, weil das die
verbreitete Konvention in LoRaWAN-Payloads ist (u. a. Cayenne LPP, „MSB first").

```
 Offset  Größe  Feld              Typ     Bedeutung
 ------  -----  ----------------  ------  ------------------------------------------
   0       1    version           u8      Formatversion (aktuell 2)
   1       1    sensor_id         u8      Eingang 1..17 (Volkspark Biosphäre)
   2       1    frame_counter     u8      0..255, +1 je Uplink (Wiederholungs-Erkennung)
   3       1    interval_min      u8      Länge des Aggregationsintervalls in Minuten (5)
   4       1    status            u8      Bitfeld (siehe unten)
   5       1    class_mask        u8      Welche Klassen-Slots belegt sind (Bit 0..5)
 ------  Header = 6 Byte -----------------------------------------------------------
   6       1    person_in         u8      Übergänge "in" im Intervall, Klasse person
   7       1    person_out        u8      Übergänge "out"
   8       1    bicycle_in        u8
   9       1    bicycle_out       u8
  10       1    car_in            u8
  11       1    car_out           u8
  12       1    motorcycle_in     u8
  13       1    motorcycle_out    u8
  14       1    bus_in            u8
  15       1    bus_out           u8
  16       1    truck_in          u8
  17       1    truck_out         u8
 ------  Gesamt = 18 Byte --------------------------------------------------------
```

**status-Bitfeld** (wie bei Smart-Sensoren üblich, vgl. PCR2-Statusbyte):
```
Bit 0  Kamera liefert Bilder
Bit 1  KI-Beschleuniger (Hailo) aktiv
Bit 2  Konfiguration geladen
Bit 3  Werte seit letztem bestätigten Uplink gepuffert (Nachsendung)
Bit 4  Intervall unvollständig (Sensor erst während des Intervalls gestartet)
Bit 5-7 reserviert
```

**class_mask:** Bit i = 1 bedeutet, dass Klasse i im Sensorprofil aktiv gezählt
wird (entspricht `TRACKED_LABELS`). So kann die UDP „Klasse nicht konfiguriert"
(Wert immer 0, Bit=0) von „konfiguriert, aber 0 Übergänge" (Wert 0, Bit=1)
unterscheiden — wichtig für die Auswertung über 17 heterogene Standorte.

### Designentscheidungen im Detail

- **uint8 pro Richtung (0..255):** Bei 5-Minuten-Intervallen ist ein Zählwert
  > 255 pro Klasse und Richtung an einem Parkeingang praktisch ausgeschlossen.
  Falls doch (z. B. Autozählung an einer Durchfahrtsstraße), Sättigung bei 255
  + Status-Bit, oder Intervall verkürzen. **Alternative uint16** in Abschnitt 6,
  falls nötig — kostet 6 Byte mehr (24 Byte gesamt, weiterhin SF12-tauglich.)
- **Feste Klassen-Reihenfolge** (person, bicycle, car, motorcycle, bus, truck) =
  COCO-Klassen des Detektors, deckungsgleich mit `TRACKED_LABELS`. Reihenfolge
  ist Teil der Spezifikation und ändert sich nur mit der Formatversion.
- **frame_counter statt Zeitstempel:** Der frühere 4-Byte-Unix-Timestamp entfällt
  — die **Empfangszeit stempelt der Network Server** (Standardverhalten, spart
  4 Byte und braucht keine RTC am Sensor). Der frame_counter dient nur der
  Wiederholungs-Erkennung (PCR2-Muster).
- **Zurücksetzen der Zähler:** Intervallwerte werden nach jedem Uplink auf 0
  gesetzt. Bei bestätigten Uplinks (confirmed) erst nach ACK zurücksetzen (PCR2:
  „Counting values are only reset when PCR2 received an ACK for not loosing
  data") → verlustfreie Übertragung bei Funkstörung.

---

## 4. Beispiel (echter Testlauf-Bezug)

Intervall mit 8 Personen rein / 3 raus, 2 Fahrräder rein / 1 raus, 5 Autos rein /
6 raus (angelehnt an die Größenordnung des Laufs vom 15.07.), Sensor 3, alle 6
Klassen aktiv, Frame 42, alles ok:

```
Feld            Wert    Hex
version         2       02
sensor_id       3       03
frame_counter   42      2A
interval_min    5       05
status          0b00000111  07
class_mask      0b00111111  3F
person_in       8       08
person_out      3       03
bicycle_in      2       02
bicycle_out     1       01
car_in          5       05
car_out         6       06
motorcycle_*    0,0     00 00
bus_*           0,0     00 00
truck_*         0,0     00 00

Payload (hex): 02 03 2A 05 07 3F 08 03 02 01 05 06 00 00 00 00 00 00
AT-Kommando:   AT+SENDB=00,02,18,02032A05073F0803020105060000000000
```

---

## 5. Referenz-Codecs

### 5.1 Encoder (Sensor-Seite, Python) — für `lora_transmitter.py`

```python
import struct

MSG_VERSION = 2
CLASSES = ["person", "bicycle", "car", "motorcycle", "bus", "truck"]

STATUS_CAMERA_OK   = 1 << 0
STATUS_ACCEL_OK    = 1 << 1
STATUS_CONFIG_OK   = 1 << 2
STATUS_BUFFERED    = 1 << 3
STATUS_PARTIAL     = 1 << 4


def encode_counts(sensor_id, frame_counter, interval_min, status,
                  active_classes, counts):
    """
    counts: dict {klasse: (in, out)} — fehlende Klassen werden als 0 kodiert.
    active_classes: iterable der konfigurierten Klassennamen (für class_mask).
    Gibt exakt 18 Byte zurück.
    """
    def u8(v): return max(0, min(255, int(v)))

    class_mask = 0
    for i, c in enumerate(CLASSES):
        if c in active_classes:
            class_mask |= (1 << i)

    payload = bytearray(struct.pack(
        ">BBBBBB",
        MSG_VERSION, u8(sensor_id), u8(frame_counter),
        u8(interval_min), u8(status), class_mask,
    ))
    for c in CLASSES:                       # feste Reihenfolge = Teil der Spec
        cin, cout = counts.get(c, (0, 0))
        payload.append(u8(cin))
        payload.append(u8(cout))
    assert len(payload) == 18
    return bytes(payload)
```

### 5.2 Decoder (Network Server, JavaScript) — TTN / ChirpStack / UDP

```javascript
// Uplink-Decoder, 18-Byte-Festformat v2. In TTN unter
// Payload formatters -> Uplink -> Custom Javascript einfügen.
function decodeUplink(input) {
  var b = input.bytes;
  if (b.length !== 18) return { errors: ["Erwartet 18 Byte, bekommen " + b.length] };
  if (b[0] !== 2)      return { errors: ["Unbekannte Formatversion: " + b[0]] };

  var classes = ["person","bicycle","car","motorcycle","bus","truck"];
  var status = b[4];
  var mask = b[5];

  var counts = {};
  var total_in = 0, total_out = 0;
  for (var i = 0; i < 6; i++) {
    var cin  = b[6 + i*2];
    var cout = b[7 + i*2];
    var active = (mask & (1 << i)) !== 0;
    counts[classes[i]] = { in: cin, out: cout, active: active };
    total_in  += cin;
    total_out += cout;
  }

  return {
    data: {
      version:        b[0],
      sensor_id:      b[1],
      frame_counter:  b[2],      // für Wiederholungs-Erkennung (siehe unten)
      interval_min:   b[3],
      status: {
        camera_ok: (status & 0x01) !== 0,
        accel_ok:  (status & 0x02) !== 0,
        config_ok: (status & 0x04) !== 0,
        buffered:  (status & 0x08) !== 0,
        partial:   (status & 0x10) !== 0
      },
      counts: counts,            // pro Klasse {in, out, active}
      total: { in: total_in, out: total_out },
      // TTN-normalisierbar: action.motion.count
      count: total_in            // Haupt-Zählwert (Eintritte)
    }
  };
}
```

**Wiederholungs-Erkennung auf dem Server (PCR2-Muster):** Bei jedem Uplink
prüfen, ob `frame_counter` sich gegenüber dem gespeicherten Wert geändert hat.
Nur bei Änderung die Zählwerte in die Datenbank aufsummieren; unveränderter
Counter = Wiederholung → ignorieren. Verhindert Doppelzählung bei
Funk-Retransmissions.

---

## 6. Dokumentierte Varianten (für Diskussion in der Arbeit)

- **uint16 pro Richtung** (24 Byte): falls Zählwerte > 255/Intervall möglich
  (Autodurchfahrten). Format identisch, Werte als `>H` statt `>B`. Weiterhin
  SF12-tauglich.
- **Strikte Cayenne LPP** (nur ≤ 3 Klassen sinnvoll): pro Richtung ein Kanal
  mit `LPP_DIGITAL_INPUT`. Beispiel Kanal-Belegung: Kanal 0 = person_in,
  Kanal 1 = person_out, … Vorteil: nativer TTN-Cayenne-Formatter ohne eigenen
  Decoder. Nachteil: 8 Byte/Klasse → Skaliert nicht auf 6 Klassen.
- **Mehrflächen-Erweiterung:** Der aktuelle Zähler kennt benannte Übergänge
  (`Potsdam->Berlin`). Für das Uplink-Format wird das auf in/out abgebildet
  (eine Fläche = „innen"). Für > 2 benannte Flächen bräuchte es einen eigenen
  Nachrichtentyp (neue Formatversion) — als Ausblick benennen.

---

## 7. Quellen (Harvard)

- myDevices (o. J.) *Cayenne Low Power Payload (LPP).* Verfügbar unter:
  https://docs.mydevices.com/docs/lorawan/cayenne-lpp (Zugriff: 15.07.2026).
- IPSO Alliance / OMA SpecWorks *Smart Objects Guidelines* — Grundlage der
  Cayenne-LPP-Datentypen.
- pmx systems (o. J.) *PCR2 LoRaWAN Payload Documentation.* Verfügbar unter:
  https://docs.pmx.systems/pcr2/manuals/lora_payload/ (Zugriff: 15.07.2026).
- The Things Industries (o. J.) *Uplink Payload Formatters / Normalized Payload.*
  Verfügbar unter:
  https://www.thethingsindustries.com/docs/integrations/payload-formatters/
  (Zugriff: 15.07.2026).

> **Wissenschaftliche Einordnung für die Arbeit:** Die Payload-Kodierung
> selbst ist Ingenieurspraxis, keine Forschungsleistung — aber die *begründete
> Auswahl* (kompaktes Festformat als Abwägung zwischen Selbstbeschreibung/Cayenne
> und Airtime/SF12, mit Frame-Counter-Robustheit nach PCR2) ist ein sauber
> dokumentierter Design-Schritt der DSRM-Aktivität 3. Genau so darstellen: nicht
> „ich habe Bytes definiert", sondern „das Format leitet sich aus etablierten
> LPWAN-Konventionen ab und wägt deren Zielkonflikte für den konkreten Fall ab".
