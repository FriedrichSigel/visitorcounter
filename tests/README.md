# Tests und Diagnosewerkzeuge

Stand: 18.07.2026

Eigenständige Skripte, die **nicht** Teil der laufenden Anwendung sind: Sie
haben Hardware geprüft, Fehler eingegrenzt oder Vorstufen der heutigen
Implementierung getestet. Für die Abschlussarbeit sind sie der Nachweis des
methodischen Vorgehens — deshalb bleiben sie erhalten, auch wenn sie ihren
Zweck erfüllt haben.

**Keines dieser Skripte wird im Normalbetrieb gebraucht.** Die App startet über
`python app.py` im übergeordneten Ordner.

## ⚠️ Nicht verwechseln

`lora_hardware/lora_send_loop_STAND_vor_integration.py` ist der **alte** Stand
(157 Zeilen, fester Test-Frame, kein `--live-counts`) und wurde nur zur
Unterscheidung umbenannt — ursprünglich hieß er ebenfalls `lora_send_loop.py`.

**Produktiv ist `../lora_send_loop.py`** (393 Zeilen, baut den Frame live aus
Konfiguration und Zählwerten). Nur diese Datei wird von der App gestartet.

Ebenso ist `lora_hardware/lora_transmitter.py` die **historische** Serialisierung.
Verbindlich ist heute `../lora_message.py`, gemäß
`../docs/lora/LoRa_Nachrichtenformat_Spezifikation.md`.

## `kamera/`

- **`camera_test.py`** — prüft Kamera-Zugriff und Auflösung völlig unabhängig
  von Hailo und `core/`. Nützlich, wenn unklar ist, ob ein Problem an der
  Kamera oder an der Erkennungs-Pipeline liegt.

  ```bash
  python tests/kamera/camera_test.py
  ```

## `lora_hardware/`

Die Hardware-Erprobung in der Reihenfolge, in der sie stattfand:

| Datei | Zweck | Ergebnis |
|---|---|---|
| `lora_hardware_probe.py` | Generisches Sondieren unbekannter LoRa-USB-Geräte (mehrere Baudraten × Testbefehle) | Sonel LORA-S1 antwortete auf nichts → als ungeeignet ausgeschlossen |
| `la66_probe.py` | Dasselbe gezielt für den Dragino LA66 | Adapter antwortet auf AT-Befehle → brauchbar |
| `test1_offline/` | Senden ohne Netzanbindung (Format und AT-Kommandos prüfen) | siehe `test1_ergebnis.md` |
| `test2_ttn/` | Vollständige Kette bis The Things Network | erfolgreich; enthält den Payload-Decoder |
| `lora_send_loop_STAND_vor_integration.py` | Zyklischer Sendetest mit festem Frame | Vorstufe des heutigen Senders |
| `lora_transmitter.py` | Erste Serialisierung samt Transport-Abstraktion | durch `../lora_message.py` abgelöst |
| `test_lora_transmitter.py` | Unit-Test dazu (aus `LoRa2.zip` gerettet) | historisch; passt nicht mehr zur heutigen API |
| `Anleitung_LA66_TTN_Verbindung.md` | Schritt-für-Schritt LA66 ↔ TTN | weiterhin gültig |

### `test2_ttn/ttn_payload_decoder.js` — weiterhin aktiv genutzt

Das ist der Decoder, der **in The Things Network hinterlegt** ist und die
empfangenen Bytes in lesbare Felder übersetzt. Er ist damit kein reines
Testartefakt, sondern Teil der Empfängerseite im Betrieb.

**Wichtig:** Er liest Byte 3 als `interval_min` und Byte 4 als `status`-Bitfeld,
genau wie die Spezifikation. Die Sender-Seite hatte diese beiden Bytes
ursprünglich vertauscht belegt; das ist seit dem 18.07. korrigiert. Uplinks von
**vor** dieser Korrektur zeigen im TTN daher Intervall `0` und alle Status-Bits
auf `false` — **die Zählwerte selbst waren immer korrekt.**

## Verhältnis zur Anwendung

Diese Skripte importieren nichts aus dem übergeordneten `core`-Ordner und
werden von dort auch nicht importiert. Sie lassen sich also gefahrlos
ausführen, verschieben oder archivieren, ohne die Anwendung zu beeinflussen.
