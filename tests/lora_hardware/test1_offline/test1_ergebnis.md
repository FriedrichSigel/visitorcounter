# Test 1 — Ergebnisprotokoll (offline, ohne Network Server)

Datum: 14.07.2026 18:42  
Ergebnis: **3 von 7 Teiltests bestanden**

| Test | Pruefpunkt | Ergebnis |
|---|---|---|
| T1.1 | Serieller Port vorhanden | ✅ bestanden |
| T1.2 | AT-Protokoll antwortet | ❌ fehlgeschlagen |
| T1.3 | Konfiguration lesbar | ❌ fehlgeschlagen |
| T1.4 | Join-Status abfragbar | ❌ fehlgeschlagen |
| T1.7 | SENDB syntaktisch akzeptiert | ❌ fehlgeschlagen |
| T1.5 | 25-Byte-Format, Round-Trip pack/unpack | ✅ bestanden |
| T1.6 | Transmitter: Queue, Verdraengung, Stopp | ✅ bestanden |

## Details

### T1.1 — Serieller Port vorhanden
bestanden
```
Gefunden: /dev/ttyUSB0
```

### T1.2 — AT-Protokoll antwortet
**fehlgeschlagen**
```
Keine AT-Antwort — Bootmodus? Rechte (dialout)?
```

### T1.3 — Konfiguration lesbar
**fehlgeschlagen**
```
uebersprungen — kein AT-Kontakt
```

### T1.4 — Join-Status abfragbar
**fehlgeschlagen**
```
uebersprungen — kein AT-Kontakt
```

### T1.7 — SENDB syntaktisch akzeptiert
**fehlgeschlagen**
```
uebersprungen — kein AT-Kontakt
```

### T1.5 — 25-Byte-Format, Round-Trip pack/unpack
bestanden
```
Laenge 25 Byte, Payload 01016a5666ea0007000500780076012c020207101b00000000
```

### T1.6 — Transmitter: Queue, Verdraengung, Stopp
bestanden
```
Gesendet (simuliert): 3
```
