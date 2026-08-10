# Video-Mitschnitt — nur für Benchmarkläufe, nie im Normalbetrieb

Stand: 19.07.2026

Dieses Dokument beschreibt die Mitschnitt-Funktion (`recording.py`) und zieht
die Grenze, die dabei entscheidend ist: **Der Mitschnitt ist ausschließlich ein
Werkzeug zur Validierung der Messgenauigkeit. Im normalen Zählbetrieb werden
keine Bilddaten gespeichert.**

---

## 1. Warum diese Trennung

Der Sensor ist nach *Privacy by Design* entworfen (DSGVO Art. 25). Der
tragende Gedanke der Architektur: Bilddaten werden auf dem Gerät verarbeitet
und **sofort verworfen**; das Gerät gibt nur aggregierte Zählwerte je Klasse
und Richtung ab. Weder Bilder noch Positionen noch Einzelereignisse verlassen
den Sensor.

Genau dieses Argument trägt in der Arbeit mehrere Kapitel — die Wahl von Edge
Computing und Hailo-8 statt Cloud-Inferenz wird damit begründet
(`../abschlussarbeit/Gliederung_DSRM_v2.md`, Abschnitte 2.a.iii, 3.e.iii und
6.d).

Ein dauerhaft mitlaufender Videomitschnitt würde diesen Kern aushebeln: Aus
einem datensparsamen Zählsensor würde eine Videoüberwachungsanlage mit
vollständig anderer Rechtsgrundlage, Zweckbindung und Dokumentationspflicht.

Für die **Bewertung der Messgenauigkeit** braucht es dennoch eine Referenz
(Ground Truth): Ohne Bildmaterial lässt sich nicht feststellen, ob eine
gezählte Person tatsächlich vorbeigegangen ist. Der Mitschnitt löst genau
dieses Problem — zeitlich befristet, unter kontrollierten Bedingungen und
außerhalb des Produktivbetriebs.

## 2. Die Trennung in einem Satz

| | Normalbetrieb (Feld) | Benchmarklauf (Labor) |
|---|---|---|
| Zweck | Besucher zählen | Zählgenauigkeit messen |
| Bilddaten | werden verworfen, nie gespeichert | werden befristet gespeichert |
| `RECORDING_ENABLED` | `false` (Standard) | `true`, bewusst gesetzt |
| Ausgabe | aggregierte Zählwerte per LoRa | zusätzlich Videosegmente lokal |
| Dauer | Dauerbetrieb | einzelne Läufe, typisch 30–60 min |
| Aufnahmeort | — | lokaler Datenträger, nicht im Feld |

## 3. Technische Absicherung

Die Voreinstellung ist **aus**, und sie ist an keiner Stelle implizit an:

- `config.py`: `RECORDING_ENABLED` ist standardmäßig `False`. Nur eine
  ausdrücklich gesetzte Umgebungsvariable `RECORDING_ENABLED=true` schaltet
  die Funktion ein.
- `app.py`, Tab 3: Die Checkbox „Video mitschneiden (Benchmark / Laborlauf)"
  ist beim Start immer abgewählt. Der Zustand wird **nicht** gespeichert — ein
  Neustart der App setzt ihn zurück. Das ist Absicht: Ein versehentlich
  aktivierter Mitschnitt soll sich nicht über Läufe hinweg fortsetzen.
- `core.py`: Ohne den Schalter wird der Aufnahmezweig gar nicht erst gebaut;
  die Pipeline verwirft die Frames wie zuvor.
- Der Mitschnitt ist bei der Auto-Konfigurations-Datensammlung (Tab 5)
  grundsätzlich deaktiviert.

## 4. Umgang mit dem aufgezeichneten Material

Für die Dauer, in der Aufnahmen existieren, gelten sie als personenbezogene
Daten. Deshalb:

- **Nur unter kontrollierten Bedingungen aufnehmen** — Testaufbau, informierte
  Beteiligte, kein Publikumsverkehr ohne Kenntnis.
- **Nicht im Feldeinsatz** an einem der 17 Eingänge der Biosphäre.
- **Zweckgebunden verwenden**: ausschließlich zum Abgleich mit `zaehlung.csv`.
- **Nach der Auswertung löschen.** In die Arbeit gehören die abgeleiteten
  Kennzahlen (Trefferquote, Fehlerarten), nicht das Bildmaterial.
- **Keine Einzelbilder mit erkennbaren Personen** in die Abschlussarbeit
  übernehmen. Für Abbildungen eignen sich Szenen ohne Personen oder
  unkenntlich gemachte Ausschnitte.

Die eingebrannte Uhrzeit (`clockoverlay`) dient allein dem Abgleich mit den
Zeitstempeln der Zählereignisse.

## 5. Wie es technisch funktioniert

Kurzfassung — Details stehen im Kopfkommentar von `recording.py`:

- Ein `tee` in der GStreamer-Pipeline vor `hailo_display` (`core.py`,
  `_attach_recording_tee`). Zweig 1 läuft weiter wie bisher, Zweig 2 in den
  Aufnahme-Bin. Ein zweiter Prozess mit eigenem Kamerazugriff wäre nicht
  möglich — die Kamera lässt sich nur einmal öffnen.
- Kette: `queue(leaky)` → `videoconvert` → `videorate` → `capsfilter` →
  `clockoverlay` → `videoconvert` → Encoder → Parser → `splitmuxsink`.
- Beide tee-Zweige haben eine eigene `queue` mit `leaky=downstream`. **Kommt
  der Encoder nicht mit, werden Frames im Mitschnitt verworfen — nie in der
  Zählung.** Ein Benchmark, der das Messobjekt verlangsamt, misst sich selbst.
- Container standardmäßig Matroska: MP4 schreibt sein Inhaltsverzeichnis erst
  beim Schließen und ist nach einem Abbruch unlesbar.
- Encoder wird zur Laufzeit gewählt (`pick_encoder`): `x264enc`, sonst
  `openh264enc`, sonst `avenc_mpeg4`. Der Pi 5 hat keinen
  Hardware-H.264-Encoder mehr, das Encoding läuft auf der CPU.

### Leistungs-Kennzahlen (`benchmark.py`, seit 10.08.)

Läuft der Mitschnitt tatsächlich (Tee erfolgreich in die Pipeline
eingehängt, nicht nur `RECORDING_ENABLED` gesetzt), legt `core.py` am
Lauf-Ende zusätzlich zum Video einen Benchmark-Bericht ins selbe Verzeichnis:
`<name>_<zeitstempel>_benchmark.json` (maschinenlesbar) und `...benchmark.txt`
(kurze Zusammenfassung). Enthalten:

- **Frame-Verarbeitungszeit** (min/max/Durchschnitt in ms) und die daraus
  berechnete effektive Bildrate über den gesamten Lauf — gemessen als
  Abstand zwischen zwei Aufrufen von `app_callback()`, deckt also die
  gesamte Pipeline ab (Hailo-Inferenz + eigener Code), nicht nur eigenen
  Code.
- **Leere Puffer** und **mögliche Aussetzer** (Frames, die > 3× länger als
  der bisherige Durchschnitt brauchten) — eine Heuristik aus Sicht des
  eigenen Callbacks, **kein vollständiger GStreamer-Drop-Zähler**: ein vor
  dem Callback verworfener Frame taucht darin nicht auf.
- **CPU-Auslastung, SoC-Temperatur, Leistungsaufnahme** des Raspberry Pi —
  im Hintergrund-Thread abgetastet (`/proc/stat` bzw. `vcgencmd`), jede
  Sekunde. Ohne diese Werkzeuge (z. B. kein Raspberry Pi) steht dort
  "nicht verfügbar" statt eines falschen Werts.
- **Hailo-Beschleuniger-Auslastung** — **experimentell**, best-effort über
  HailoRT's `HAILO_MONITOR`-Umgebungsvariable. **Nicht an echter Hardware
  verifiziert.** Liefert im Zweifel "nicht verfügbar" statt eines geratenen
  Werts — vor Verwendung in der Arbeit am realen Gerät gegenprüfen.

### Einstellungen (`config.py`, alle per Umgebungsvariable)

| Variable | Standard | Bedeutung |
|---|---|---|
| `RECORDING_ENABLED` | `false` | Hauptschalter |
| `RECORDING_DIR` | `auto` | Zielordner; `auto` sucht einen USB-Datenträger |
| `RECORDING_BITRATE_KBPS` | `2000` | ≈ 0,9 GB pro Stunde bei 720p |
| `RECORDING_SEGMENT_SECONDS` | `600` | Segmentlänge |
| `RECORDING_FPS` | `15` | reicht zur Beurteilung von Übertritten |
| `RECORDING_CONTAINER` | `mkv` | `mkv` oder `mp4` |

## 6. Für die Abschlussarbeit

Der Mitschnitt gehört methodisch in das Kapitel zur **Evaluation**, nicht in
die Systembeschreibung. Sinnvolle Formulierung des Unterschieds:

> Zur Bestimmung der Zählgenauigkeit wurde das System um eine optionale,
> im Normalbetrieb deaktivierte Mitschnittfunktion ergänzt. Sie diente
> ausschließlich der Erhebung einer Referenz unter Laborbedingungen. Im
> produktiven Zählbetrieb werden keine Bilddaten gespeichert; das
> Privacy-by-Design-Prinzip der Architektur bleibt davon unberührt.

Damit ist die Funktion kein Widerspruch zum Datenschutzkonzept, sondern ein
methodisch begründeter, zeitlich befristeter Sonderfall — und genau so sollte
sie in Kapitel 6.d gegenüber der Datenschutzbewertung dargestellt werden.

## 7. Verwandte Dokumente

- `../abschlussarbeit/Gliederung_DSRM_v2.md` — Privacy by Design als
  Zielkriterium und Bewertungsmaßstab
- `../lora/LoRa_Recherche.md` — Datensparsamkeit der Übertragung
- `../projekt/ToDo.md` — offene Punkte zur Genauigkeitsuntersuchung
