# Änderungen — LoRa-Versand in Tab 3 integriert

Stand: 18.07.2026 — **im Echtbetrieb bestätigt: Sensordaten kommen online per LoRa an.**

## Was neu ist

Der LoRa-Versand ist jetzt direkt in `app.py` (Tab 3 „Start") wählbar —
zwischen „Live-Vorschau" und „Zeitlimit". Ist er aktiv, werden die
Zählerstände periodisch über den LA66-Adapter gesendet.

**Ein einziges Nachrichtenformat für alle Modi:** das bestehende
18-Byte-Zählformat v2 (Header 6 Byte + 6 Klassen x [IN][OUT]). Auch
`multi_roi` nutzt es — über ein wählbares IN-Feld (siehe unten).

Neu/geändert:

- **`lora_message.py` (neu)** — die eine Stelle, an der das Nachrichtenformat
  definiert ist. Baut den Frame aus der Konfiguration (`roi_config.json`) und
  den Zählerständen (`zaehlung.csv`), erzeugt den Struktur-Hinweistext für die
  GUI und enthält einen Referenz-Decoder (`decode_frame`) für die
  Empfängerseite. Nur Standardbibliothek.
- **`lora_send_loop.py` (erweitert)** — neuer Modus `--live-counts`: baut den
  Frame vor jedem Sendeversuch neu (statt statischem `--payload`). Übertragen
  wird der **Zuwachs seit dem letzten erfolgreichen Uplink** — ein
  fehlgeschlagener Uplink verliert also keine Zählungen (adressiert den
  ToDo-Punkt „verlorene Intervalle"). Der bisherige statische Testbetrieb
  bleibt unverändert erhalten.
- **`roi_config_app.py` (Tab 2)** — im Modus „Mehrere Flächen" gibt es am Ende
  eine **IN-Feld-Auswahl**. Das Menü füllt sich automatisch mit den angelegten
  Flächennamen. Beim Speichern wird geprüft, dass ein gültiges Feld gewählt
  ist; gespeichert wird es als `"in_field"` in `roi_config.json`.
- **`config.py`** — `in_field` im Standard-Schema ergänzt.
- **`app.py` (Tab 3)** — Checkbox „Daten per LoRa senden (LA66)", Felder für
  Sende-Intervall (Minuten) und Sensor-ID, plus ein Hinweisfeld mit der
  Nachrichtenstruktur. Der Hinweis richtet sich nach der Konfiguration und
  aktualisiert sich mit Intervall/Sensor-ID. Bei aktivem LoRa wird beim Start
  ein zweiter Subprozess mitgestartet; dessen Ausgabe läuft mit Präfix
  `[LoRa]` in dieselbe Live-Konsole (Tab 4). Stoppen/Absturz von core.py
  beendet auch den Sender.

## multi_roi über das IN-Feld

`multi_roi` schreibt Übergänge als `"A->B"` in `zaehlung.csv`. Ist eine Fläche
als IN-Feld gewählt (z. B. `Berlin`), gilt:

| Übergang       | Wertung   |
|----------------|-----------|
| `X -> Berlin`  | **IN**    |
| `Berlin -> X`  | **OUT**   |
| alle anderen   | ignoriert |

Damit passt `multi_roi` in genau dasselbe IN/OUT-Format wie Linie/ROI — kein
zweiter Nachrichtentyp, kein separater Decoder auf der Empfängerseite.

Ist kein IN-Feld gesetzt (z. B. alte Konfigurationsdatei), warnt der Hinweis
in Tab 3 und der Sender loggt eine Warnung; gesendet werden dann Nullwerte
statt eines Absturzes.

## Bewusste Designentscheidung: entkoppelt

Der Sender ist ein **eigener Subprozess**, der nur die von core.py
geschriebene `zaehlung.csv` liest. `core.py`/`tracking.py` werden **nicht**
angefasst — die Zähl-Pipeline bleibt unverändert und wird durch einen
LoRa-Fehler nicht gefährdet.

## Offene Punkte / zu prüfen

1. ~~**Header-Bytes 3–4.**~~ **Geklärt und korrigiert (18.07.).** Die
   Spezifikation wurde im alten Ordner `basic_pipelines/core/` gefunden und
   liegt jetzt unter `docs/LoRa_Nachrichtenformat_Spezifikation.md`. Korrekt
   ist: Byte 3 = `interval_min`, Byte 4 = `status`-Bitfeld (Bit0 Kamera,
   Bit1 Hailo, Bit2 Konfiguration, Bit3 gepuffert, Bit4 Teilintervall). Die
   erste Fassung hatte Status in Byte 3 und Byte 4 leer — jetzt behoben,
   Frame byte-identisch mit dem Referenz-Frame der Spezifikation. Das Status-
   Bit „gepuffert" wird jetzt gesetzt, wenn der vorherige Uplink misslang;
   „Teilintervall" beim ersten Uplink nach dem Start. Kamera-/Hailo-Bits setzt
   `app.py` über `--pipeline-ok`, weil der Sender-Subprozess das nicht selbst
   messen kann.
2. **Auto-Modi.** `auto_cluster`/`auto_border` speichern als `multi_roi`,
   setzen aber (noch) kein `in_field` — dort ist die IN-Feld-Auswahl
   nachzuziehen, falls diese Modi per LoRa senden sollen.
3. ~~**Hardware.**~~ **Erledigt (18.07.):** der reale Sendeweg über den LA66
   ist bestätigt, die Daten kommen online an. Offen bleibt nur die
   Langzeitbeobachtung im Feld (Duty-Cycle, Paketverluste, Verhalten beim
   Überlauf der Sequenznummer bei 255).
