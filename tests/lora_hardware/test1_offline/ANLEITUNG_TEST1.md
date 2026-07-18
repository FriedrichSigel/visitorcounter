# Test 1 — LA66 offline (ohne TTN, ohne Stadtwerke)

**Ziel:** Nachweisen, dass Hardware (Dragino LA66 USB Adapter V2, EU868) und die
gesamte Software-Kette bis zur Antenne funktionieren — **ohne** dass Keys an
irgendeinen Network Server übermittelt werden.

**Einordnung in die Arbeit:** Kapitel 4.c.ii (Funktionalitätstest der
Einzelkomponenten). Das Ergebnisprotokoll (`test1_ergebnis.md`) ist als
Anhang-Beleg verwendbar. Der Kontrast zur gescheiterten Sonel LORA-S1
(keine AT-Antwort, proprietäre USB-Klasse) gehört in Kapitel 4.d (Iterationen).

---

## Voraussetzungen

- Raspberry Pi 5, LA66 USB Adapter V2 eingesteckt (Antenne montiert!)
- `pip install pyserial --break-system-packages`
- Nutzer in der Gruppe `dialout`:
  ```bash
  sudo usermod -aG dialout $USER   # danach ab- und wieder anmelden
  ```

**Nicht nötig:** TTN-Konto, Gateway, Internetverbindung, Stadtwerke.

---

## Ablauf

### Schritt 1 — Sichtprüfung nach dem Einstecken

```bash
lsusb            # erwartet: "Silicon Labs CP210x UART Bridge"
dmesg | tail -5  # erwartet: "cp210x converter now attached to ttyUSB0"
```

### Schritt 2 — Testlauf

```bash
cd lora_hardware_test/test1_offline
python3 test1_offline.py
```

Ohne Hardware (z. B. am Laptop, nur Software-Kette):

```bash
python3 test1_offline.py --skip-hardware
```

### Schritt 3 — Protokoll prüfen

Das Skript schreibt `test1_ergebnis.md` in diesen Ordner. Datei ins Repo
committen (sie enthält **maskierte** Keys — trotzdem vor dem Commit einmal
draufschauen).

---

## Die sieben Teiltests und ihre Erwartungswerte

| Test | Prüfpunkt | Erwartung | Wenn es fehlschlägt |
|---|---|---|---|
| T1.1 | Serieller Port vorhanden | CP2102 unter `/dev/ttyUSB*` | Kabel/Port wechseln, `dmesg` prüfen |
| T1.2 | AT-Protokoll antwortet | `OK` auf `AT` (9600 Baud) | dialout-Gruppe? BOOT-Pin gebrückt? Direkt am Pi statt Hub |
| T1.3 | Keys + Band lesbar | DevEUI/AppEUI/AppKey gefüllt, Band EU868 | Bei falschem Band: `AT+BAND=` laut Dragino-Handbuch setzen |
| T1.4 | Join-Status abfragbar | `AT+NJS=?` → **0** (nicht gejoint) | **0 ist hier richtig!** Ein Join wäre ohne registrierte Keys unmöglich |
| T1.5 | 25-Byte-Format | pack/unpack Round-Trip identisch | Softwarefehler → melden |
| T1.6 | Transmitter-Logik | Queue, Verdrängung, sauberer Stopp | Softwarefehler → melden |
| T1.7 | SENDB-Syntax | Modul akzeptiert `AT+SENDB=00,02,25,<hex>` ohne Parameterfehler | Antwort notieren — Formatproblem |

**Wichtigste Erkenntnis, wenn alles grün ist:** Die komplette Kette
*Zähllogik → Binärformat → AT-Kommando → Modul* funktioniert. Das Einzige,
was danach noch fehlt, ist die Registrierung bei einem Network Server —
und die liegt außerhalb der eigenen Software.

---

## Abgrenzung: Was Test 1 bewusst NICHT prüft

- ob ein Uplink tatsächlich **über Funk rausgeht** (braucht Join → Test 2)
- ob ein **Gateway in Reichweite** ist (→ Test 2)
- ob die Daten in der **UDP der Stadtwerke** ankommen (→ Realtest mit Stadtwerken)

## Sicherheit

- `--show-keys` beim Probe-Skript nur lokal nutzen, nie in Protokolle/Screenshots.
- Das Ergebnisprotokoll maskiert Keys automatisch (letzte 4 Zeichen sichtbar).
- Keys gehören in keine Datei im Repo — auch nicht in der Git-Historie.
