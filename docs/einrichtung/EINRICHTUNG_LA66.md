# Einrichtungsprotokoll — Dragino LA66 USB LoRaWAN Adapter V2 (EU868)

**Zweck:** Reproduzierbare Neueinrichtung eines LoRa-Senders auf einem
Raspberry Pi. Alle hier gelisteten Befehle wurden auf dem Referenzgerät
(`stadtwerke2`, Raspberry Pi 5 8 GB, Nutzer `fritz`) tatsächlich ausgeführt
und verifiziert. Bei jedem weiteren Gerät (Volkspark Biosphäre: bis zu 17
Sensoren) diese Schritte in gleicher Reihenfolge durchgehen.

**Pflege:** Dieses Dokument wird fortlaufend mitgeführt. Jeder neue
Einrichtungsschritt wird hier ergänzt — mit Befehl, Zweck und erwartetem
Ergebnis. Einmalige Debug-Kommandos kommen in den Abschnitt „Diagnose",
dauerhafte Einrichtung in „Setup".

**Stand:** 14.07.2026 — Erstinbetriebnahme LA66 auf `stadtwerke2` abgeschlossen
(Test 1 offline).

---

## 1. Setup — einmalig pro Gerät

### 1.1 Python-Abhängigkeit installieren

```bash
pip install pyserial --break-system-packages
```

- **Zweck:** Serielle Kommunikation mit dem LA66 (AT-Protokoll über USB).
- **Hinweis:** `--break-system-packages` ist auf Raspberry Pi OS (Bookworm)
  nötig, weil das System-Python gegen pip-Installationen geschützt ist
  (PEP 668). Alternative wäre eine venv — im Projekt wird systemweit
  installiert, damit auch systemd-Services ohne venv-Aktivierung laufen.
- **Erwartung:** `Successfully installed pyserial-…`

### 1.2 Zugriffsrechte auf die serielle Schnittstelle

```bash
sudo usermod -aG dialout $USER
sudo reboot
```

- **Zweck:** `/dev/ttyUSB*` gehört `root:dialout` (Modus `crw-rw----`).
  Ohne Mitgliedschaft in `dialout` scheitert jeder Zugriff mit
  `Permission denied`.
- **WICHTIG:** Das `-a` (append) niemals weglassen — `usermod -G` ohne `-a`
  entfernt den Nutzer aus allen anderen Gruppen, inkl. `sudo`
  (Selbstaussperrung!).
- **Wirksamkeit:** Erst nach Neuanmeldung/Neustart. Auf dem Referenzgerät
  wurde neu gestartet.
- **Verifikation:**
  ```bash
  groups            # muss "dialout" enthalten
  ```

### 1.3 Hardware anschließen und identifizieren

LA66 mit montierter Antenne in einen USB-Port des Pi stecken (direkt am Pi,
nicht über unversorgte Hubs). Dann:

```bash
lsusb
# Erwartung: "Silicon Labs CP210x UART Bridge"  (VID:PID 10c4:ea60)

ls -l /dev/serial/by-id/
# Erwartung (Referenzgerät):
# usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 -> ../../ttyUSB0
```

- **Zweck:** Eindeutige Zuordnung Gerät ↔ Port. Die Nummer `ttyUSB0` ist
  **nicht stabil** (hängt von der Erkennungsreihenfolge ab); der
  by-id-Pfad ist es.
- **Für den Dauerbetrieb daher immer den by-id-Pfad verwenden:**
  ```bash
  export LORA_PORT=/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0
  ```
  (Suffix `0001` ist die Seriennummer des CP2102 und kann pro Stick
  abweichen — immer aus der eigenen `ls -l`-Ausgabe übernehmen.
  Dauerhaft: Zeile in `~/.bashrc` bzw. später in die systemd-Unit.)

---

## 2. Funktionsprüfung — einmal pro Gerät nach dem Setup

### 2.1 Manueller Kurztest (optional, aber empfohlen)

```bash
sudo apt install -y picocom
picocom -b 9600 /dev/ttyUSB0
```

Im Terminal `AT` + Enter tippen.

- **Erwartung:** `OK`
- **Befund Referenzgerät (14.07.2026):** Modul antwortet bei **9600 Baud**.
  Die AT-Konsole war **nicht passwortgeschützt** — die Eingabe von `123456`
  ergab `AT_ERROR` (Firmware interpretiert es als unbekanntes Kommando),
  ein direktes `AT` liefert `OK`. Der Dragino-Passwortschutz (Standard
  `123456`) kann je nach Firmwarestand aktiv sein; die Projektskripte
  probieren beides automatisch.
- **Beenden:** `Strg+A`, dann `Strg+X` — **zwingend**, sonst blockiert
  picocom den Port für alle nachfolgenden Skripte.

### 2.2 Automatisierter Offline-Test (Test 1)

```bash
cd lora_hardware_test/test1_offline
python3 test1_offline.py
```

- **Zweck:** Prüft Port, AT-Kontakt, Auslesbarkeit der Keys, Band (EU868),
  Join-Status, 25-Byte-Serialisierung, Transmitter-Logik und SENDB-Syntax —
  ohne Network Server.
- **Erwartung:** 7/7 bestanden. T1.4 meldet dabei „nicht gejoint" — das
  **ist** das erwartete Ergebnis, solange die Keys bei keinem Network
  Server registriert sind.
- **Protokoll:** `test1_ergebnis.md` entsteht im selben Ordner → ins Repo
  committen (Keys sind darin automatisch maskiert).

### 2.3 Keys für die Registrierung auslesen

```bash
python3 la66_probe.py --show-keys
```

- **Zweck:** DevEUI / AppEUI / AppKey für die Registrierung beim Network
  Server (TTN zum Testen, produktiv: Stadtwerke Potsdam).
- **SICHERHEIT:** Ausgabe nur lokal verwenden. Keys nie ins Repo, nie in
  Screenshots, nie in die Arbeit. Übergabe an die Stadtwerke über einen
  sicheren Kanal (Absprache mit Titus Tomascik / Andreas Becker).

---

## 3. Ende-zu-Ende-Test (Test 2, optional via TTN)

Nur wenn ein TTN-Gateway in Reichweite ist (vorher prüfen:
[ttnmapper.org](https://ttnmapper.org)). Vollständiger Ablauf inkl.
TTN-Registrierung: `test2_ttn/ANLEITUNG_TEST2.md`.

```bash
python3 test2_ttn/test2_ttn.py
```

Nach bestandenem Test 2: Gerät in TTN **löschen**, bevor es bei den
Stadtwerken registriert wird (ein Gerät kann nur bei einem Network Server
aktiv sein).

---

## 4. Betriebskonfiguration (Umgebungsvariablen)

Der produktive Sender (`lora_transmitter.py`) wird ausschließlich über
Umgebungsvariablen konfiguriert — keine Keys, keine Ports im Code:

| Variable | Standard | Bedeutung |
|---|---|---|
| `LORA_ENABLED` | `0` | `1` = echter LA66-Transport; sonst DummyTransport (nur Log) |
| `LORA_PORT` | `/dev/ttyUSB0` | serieller Port — **by-id-Pfad verwenden**, s. 1.3 |
| `LORA_BAUD` | `9600` | Baudrate (Referenzgerät: 9600 bestätigt) |
| `LORA_FPORT` | `2` | LoRaWAN Fport |
| `LORA_CONFIRMED` | `0` | `1` = bestätigte Uplinks (kostet Duty Cycle) |
| `LORA_MIN_INTERVAL_S` | `120` | Mindestabstand Uplinks (Duty Cycle EU868, 1 %) |
| `LORA_AT_PASSWORD` | `123456` | AT-Konsolen-Passwort, falls Firmware gesperrt ist |

---

## 5. Diagnose — Befehle für die Fehlersuche (nicht Teil des Setups)

| Befehl | Zweck |
|---|---|
| `lsusb` | Ist der CP210x überhaupt am Bus? |
| `dmesg \| tail -20` | Kernel-Meldung beim Einstecken (`cp210x converter now attached to ttyUSB0`) |
| `dmesg -w` | Live mitlesen beim Aus-/Einstecken → eindeutige Port-Zuordnung |
| `ls -l /dev/ttyUSB0` | Rechte prüfen (`crw-rw---- root dialout`) |
| `groups` | Ist `dialout` in der aktiven Sitzung geladen? |
| `python3 la66_probe.py` | Stufendiagnose: Port → AT → Konfiguration → Join-Status |
| `python3 la66_probe.py --join` | Join-Versuch auslösen (braucht registrierte Keys + Gateway) |
| picocom + RST-Taste am Adapter | Boot-Text erzwingen; Zeichensalat = falsche Baudrate |

**Gelernte Stolpersteine (Referenzgerät):**

1. `dialout`-Mitgliedschaft wirkt erst nach Neuanmeldung/Neustart — ein
   Testlauf davor schlägt bei T1.2 fehl, obwohl Hardware und Code in
   Ordnung sind (so geschehen beim ersten Lauf am 14.07.2026, 18:42).
2. picocom nach dem Handtest immer sauber beenden (`Strg+A`, `Strg+X`),
   sonst ist der Port für die Skripte blockiert.
3. `AT_ERROR` als Antwort ist kein Defekt, sondern ein Lebenszeichen:
   Die Konsole ist erreichbar und hat lediglich ein unbekanntes Kommando
   abgewiesen.

---

## 6. Checkliste Neueinrichtung (Kurzfassung zum Abhaken)

```
[ ] pip install pyserial --break-system-packages
[ ] sudo usermod -aG dialout $USER  →  Neustart
[ ] LA66 mit Antenne einstecken
[ ] ls -l /dev/serial/by-id/  →  by-id-Pfad notieren
[ ] LORA_PORT auf by-id-Pfad setzen (~/.bashrc)
[ ] python3 test1_offline/test1_offline.py  →  7/7, Protokoll committen
[ ] python3 la66_probe.py --show-keys  →  Keys an Network-Server-Betreiber
[ ] Nach Registrierung: python3 la66_probe.py --join  →  AT+NJS=1
[ ] Betrieb: LORA_ENABLED=1 + Variablen aus Abschnitt 4
```
