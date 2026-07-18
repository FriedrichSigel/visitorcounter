# LoRa-Hardware-Test (isoliert, ohne core-Projekt)

Dieser Ordner ist komplett unabhängig vom core-Projekt (`personenzaehlung`).
Einzige externe Abhängigkeit: `pyserial` (plus Python-Standardbibliothek).

**Hardware:** Dragino LA66 USB LoRaWAN Adapter V2, EU868.
Der ursprünglich vorgesehene Sonel LORA-S1 ist unbrauchbar (vendor-spezifische
USB-Klasse, keine AT-Antwort — siehe Git-Historie dieses Ordners, relevant für
Kapitel 4.d der Arbeit).

## Struktur

```
lora_hardware_test/
├── README.md                    # diese Datei
├── la66_probe.py                # Diagnose: Port → AT-Ping → Keys → Join-Status
├── lora_transmitter.py          # produktiver Sender (25-Byte-Format, Queue-Thread)
├── test1_offline/
│   ├── ANLEITUNG_TEST1.md       # Ablauf Test 1
│   ├── test1_offline.py         # 7 Teiltests, schreibt test1_ergebnis.md
│   └── test1_ergebnis.md        # entsteht beim Testlauf (committen!)
└── test2_ttn/
    ├── ANLEITUNG_TEST2.md       # Ablauf Test 2 inkl. TTN-Registrierung
    ├── test2_ttn.py             # 5 Teiltests, schreibt test2_ergebnis.md
    ├── ttn_payload_decoder.js   # Payload-Decoder für TTN / Stadtwerke
    └── test2_ergebnis.md        # entsteht beim Testlauf (committen!)
```

## Einrichtung (einmalig)

```bash
pip install pyserial --break-system-packages
sudo usermod -aG dialout $USER    # danach ab- und wieder anmelden
```

## Nutzung

### Schnelldiagnose

```bash
python3 la66_probe.py                # Port, AT-Ping, Konfiguration, Join-Status
python3 la66_probe.py --show-keys    # Keys im Klartext — NUR lokal am Terminal!
python3 la66_probe.py --join         # Join-Versuch auslösen
```

### Test 1 — offline (ohne TTN, ohne Stadtwerke)

Prüft Hardware und komplette Software-Kette bis zur Antenne.
Details: `test1_offline/ANLEITUNG_TEST1.md`

```bash
python3 test1_offline/test1_offline.py                   # am Pi mit Stick
python3 test1_offline/test1_offline.py --skip-hardware   # nur Software-Kette
```

### Test 2 — Ende-zu-Ende über TTN

Voraussetzung: Test 1 bestanden, Gerät in TTN registriert, Gateway in
Reichweite (vorher auf ttnmapper.org prüfen!).
Details: `test2_ttn/ANLEITUNG_TEST2.md`

```bash
python3 test2_ttn/test2_ttn.py
```

### Transmitter-Selbsttest (läuft überall, ohne Hardware)

```bash
python3 lora_transmitter.py    # Serialisierung + Round-Trip + Dummy-Uplink
```

## Nachrichtenformat

25 Byte binär, big endian, Version 1 — vollständige Feldtabelle im
Kommentarkopf von `lora_transmitter.py`. Der JavaScript-Decoder in
`test2_ttn/ttn_payload_decoder.js` ist byte-identisch dazu und dient als
Referenz für den Network Server der Stadtwerke.

25 Byte passen auch bei SF12 in die EU868-Payload-Grenze (51 Byte) — das
Format ist damit unabhängig vom Spreading Factor sendbar.

## Einbindung ins core-Projekt

`lora_transmitter.py` ist so gebaut, dass es unverändert nach `core/`
übernommen werden kann:

```python
from lora_transmitter import build_transmitter, CountMessage

tx = build_transmitter()   # liest LORA_* Umgebungsvariablen
tx.start()
# im Aggregationsintervall:
tx.send_count(CountMessage(sensor_id=3, count_in=..., ...))
```

Konfiguration ausschließlich über Umgebungsvariablen — ohne `LORA_ENABLED=1`
läuft immer der `DummyTransport` (kein Funk, nur Log):

| Variable | Standard | Bedeutung |
|---|---|---|
| `LORA_ENABLED` | `0` | `1` = echter LA66-Transport |
| `LORA_PORT` | `/dev/ttyUSB0` | serieller Port |
| `LORA_BAUD` | `9600` | Baudrate |
| `LORA_FPORT` | `2` | LoRaWAN Fport |
| `LORA_CONFIRMED` | `0` | `1` = bestätigte Uplinks (kostet Duty Cycle) |
| `LORA_MIN_INTERVAL_S` | `120` | Mindestabstand zwischen Uplinks (Duty Cycle EU868) |

## Sicherheit

- DevEUI/AppEUI/AppKey sind Geheimnisse: **nie** ins Repo, nie in Screenshots,
  nie in die Arbeit. Skripte und Testprotokolle maskieren sie automatisch.
- `--show-keys` nur lokal am eigenen Terminal verwenden.
- Übergabe an die Stadtwerke über einen sicheren Kanal (vorher nachfragen,
  wie sie es haben wollen).

## Status / nächste Schritte

- [ ] Test 1 am Pi durchführen, `test1_ergebnis.md` committen
- [ ] TTN-Gateway-Abdeckung am Teststandort prüfen (ttnmapper.org)
- [ ] Test 2 durchführen **oder** direkt Keys an Stadtwerke (Titus Tomascik /
      Andreas Becker) zur Registrierung geben
- [ ] Frage an Stadtwerke: LoRaWAN-Abdeckung am Volkspark Biosphäre?
- [ ] Nach bestandenem Ende-zu-Ende-Test: `lora_transmitter.py` in `core/`
      integrieren und an die Aggregationslogik anschließen
