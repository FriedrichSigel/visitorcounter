# Live-Bild-Spiegelung bei `--input usb` — Vorgehensweise & Lösungsansätze

**Stand 15.07.2026.** Mehrere Lösungswege, nach Aufwand/Erfolgswahrscheinlichkeit
geordnet. Zuerst die Diagnose (klärt, welcher Weg überhaupt nötig ist), dann fünf
Ansätze von „ein Wert ändern" bis „vorgeschaltete Pipeline".

## Was bereits bekannt ist (nicht nochmal untersuchen)

- **Ursache bestätigt:** Hailos GStreamer-Pipeline für `--input usb` enthält
  explizit `videoflip name=videoflip video-direction=horiz` — sie spiegelt aktiv.
  (Aus einem Fehlermeldungs-Screenshot des Pipeline-Strings.)
- **Warum `camera_raw.png` trotzdem korrekt ist:** Der Snapshot liest den Buffer
  über `get_numpy_from_buffer()` **vor** dem `videoflip`-Element. Referenzbild und
  Live-Anzeige durchlaufen also unterschiedlich viele Flip-Schritte.
- **Wichtig für die Bewertung:** Die **Zähllogik ist nie betroffen** — sie arbeitet
  auf den rohen Hailo-Erkennungsdaten, lange vor jeder Anzeige. Es geht rein um die
  *visuelle Übereinstimmung* zwischen Live-Fenster und Referenzbild/Realität. Das
  relativiert die Dringlichkeit: kosmetisch für die Kalibrierung, nicht
  ergebnisrelevant.

---

## Schritt 0 — Diagnose zuerst (5 Minuten, immer machen)

Bevor irgendein Fix: klären, welchen Zustand wir wirklich haben.

### 0.1 Steht der Schalter überhaupt auf True?
```bash
grep LIVE_PREVIEW_HORIZONTAL_FLIP config.py
```
In der zuletzt hochgeladenen Version steht **`= False`**. Wenn das noch so ist,
ist „das Bild ist immer noch gespiegelt" schlicht erwartbar — der Fix war nie
aktiv. Dann:
```python
LIVE_PREVIEW_HORIZONTAL_FLIP = True
```
setzen, App neu starten, Live-Fenster mit `camera_raw.png` vergleichen.

### 0.2 Wirkt der Flip, aber in die falsche Richtung / doppelt?
Falls `True` gesetzt ist und das Bild *trotzdem* gespiegelt bleibt, gibt es genau
zwei Möglichkeiten — die man unterscheiden muss:
- **(a)** Der Flip in `core.py` wird ausgeführt, aber Hailos `set_frame()`/Anzeige
  spiegelt **danach** nochmal → netto wieder gespiegelt.
- **(b)** Der Codepfad mit dem Flip wird gar nicht erreicht (z. B. `set_frame`
  zeigt einen anderen Frame als den, den wir spiegeln).

Unterscheiden mit einer **Wasserzeichen-Probe** — ein asymmetrisches Zeichen in
die Ecke malen, direkt vor `set_frame`:
```python
import cv2
cv2.putText(frame, "L", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,0,255), 3)
if LIVE_PREVIEW_HORIZONTAL_FLIP:
    frame = cv2.flip(frame, 1)
user_data.set_frame(frame)
```
- Erscheint das „L" **rechts** im Live-Fenster → unser Flip wirkt, Hailo spiegelt
  danach nochmal → Fall (a) → **Ansatz A greift nicht**, weiter zu B/C/D.
- Erscheint das „L" **links** und lesbar, aber die *Szene* ist gespiegelt → unser
  Flip wird nicht auf den angezeigten Frame angewandt → Fall (b).
- Erscheint gar kein „L" → `set_frame` zeigt einen anderen Frame → Fall (b),
  anderer Codepfad.

Diese eine Probe entscheidet, welcher der folgenden Ansätze der richtige ist —
ohne sie rät man.

---

## Ansatz A — Anzeige-Flip in `core.py` (bereits vorhanden)

**Aufwand:** minimal · **Erfolg:** hoch, WENN Fall (b) oder einfacher Doppel-Flip.

Der Schalter `LIVE_PREVIEW_HORIZONTAL_FLIP = True` spiegelt den Frame nach den
Overlays, vor `set_frame`. Ist der sauberste Fix, *falls* er greift.

- Wenn Schritt 0.2 Fall (a) zeigt (Hailo spiegelt nach uns): Ansatz A kann den
  Doppel-Flip nicht auflösen, weil unser Flip *vor* Hailos Flip liegt → weiter.
- Wenn Fall (b): den Flip an die Stelle rücken, die den tatsächlich angezeigten
  Frame trifft. Prüfen, ob `set_frame` intern eine Kopie/Referenz nutzt.

**Vorteil:** kein Systemeingriff, betrifft nur die Anzeige, Zähllogik unberührt.
**Grenze:** wirkt nur, wenn wir die Kontrolle über den angezeigten Frame haben.

---

## Ansatz B — Hailos `videoflip` an der Quelle neutralisieren

**Aufwand:** mittel · **Erfolg:** hoch · **sauberste Lösung, wenn erreichbar.**

Da das Problem ein konkretes GStreamer-Element ist (`videoflip
video-direction=horiz`), ist die direkteste Lösung, dieses Element zu entfernen
oder auf `identity`/`none` zu setzen, statt es nachträglich auszugleichen.

**Vorgehen:**
1. Den Pipeline-String finden, den hailo-apps für `--input usb` baut:
   ```bash
   grep -rn "videoflip\|video-direction\|GET_PIPELINE_STRING\|SOURCE_PIPELINE" \
     ~/hailo-rpi5-examples/ ~/venv_hailo_rpi_examples/lib/python*/site-packages/hailo_apps/ 2>/dev/null
   ```
2. Ist die Stelle in einer **eigenen/überschreibbaren** Datei (nicht im
   installierten Paket): `video-direction=horiz` → `video-direction=identity`
   ändern.
3. Ist sie im **installierten Paket**: nicht das Paket editieren (wird bei
   Updates überschrieben). Stattdessen prüfen, ob die Pipeline-Funktion Parameter
   akzeptiert, oder ob `MyDetectionApp` den Quell-Pipeline-Teil überschreiben kann
   (analog zu `on_eos()`, das ihr schon überschreibt).

**Vorteil:** behebt die Ursache, kein Doppel-Flip, Referenzbild und Live-Bild
werden konsistent. **Grenze:** hängt davon ab, wie tief der String im Paket sitzt.

---

## Ansatz C — V4L2-Treiber-Flip (Kamera spiegelt selbst)

**Aufwand:** gering · **Erfolg:** geräteabhängig (oft nicht verfügbar).

Manche USB-Kameras können horizontal spiegeln direkt im Treiber. Dann kommt das
Bild schon korrekt in die Pipeline, und Hailos `videoflip` würde es *einmal*
spiegeln — man müsste die Kamera-Spiegelung so setzen, dass sie Hailos Flip
vorwegnimmt.

**Vorgehen:**
1. Prüfen, ob die Kamera das kann:
   ```bash
   v4l2-ctl --list-ctrls -d /dev/video0
   ```
   Nach `horizontal_flip` / `hflip` suchen.
2. Falls vorhanden:
   ```bash
   v4l2-ctl -d /dev/video0 --set-ctrl horizontal_flip=1
   ```
   Muss **vor** dem Pipeline-Start gesetzt sein.
3. Wirkung mit Hailos `videoflip` zusammendenken: Kamera-Flip + Pipeline-Flip =
   zweimal = wieder original. Also entweder Kamera-Flip **oder** Pipeline-Flip,
   nicht beides. Praktisch: Ansatz C ersetzt Ansatz B nur, wenn man Hailos Flip
   *nicht* abschalten kann.

**Vorteil:** kein Codeeingriff, sehr sauber, wenn die Kamera es unterstützt.
**Grenze:** laut HANDOFF auf diesem Gerät vermutlich nicht vorhanden — Schritt 1
klärt es in 30 Sekunden. Muss beim Boot/Start reproduzierbar gesetzt werden
(sonst nach Neustart weg → ins `GERAETE_EINRICHTUNG.md`-Setup aufnehmen).

---

## Ansatz D — `v4l2loopback` mit vorgeschalteter spiegelnder Pipeline

**Aufwand:** hoch · **Erfolg:** sehr hoch (funktioniert sicher) · **letzte Wahl.**

Ein virtuelles Kameragerät erzeugen, in das eine eigene GStreamer-Pipeline das
bereits gespiegelte Bild schreibt; Hailo liest dann aus diesem virtuellen Gerät.

**Vorgehen (Skizze):**
1. `sudo apt install v4l2loopback-dkms v4l2loopback-utils`
2. Loopback-Gerät anlegen:
   ```bash
   sudo modprobe v4l2loopback video_nr=10 card_label="mirrored" exclusive_caps=1
   ```
3. Spiegelnde Pipeline von echter Kamera → Loopback:
   ```bash
   gst-launch-1.0 v4l2src device=/dev/video0 ! videoflip video-direction=horiz \
     ! videoconvert ! v4l2sink device=/dev/video10
   ```
4. Hailo mit `--input /dev/video10` (bzw. dem passenden usb-Alias) starten.

**Vorteil:** entkoppelt vollständig von Hailos interner Pipeline, garantiert
kontrollierbar. **Grenze:** zusätzlicher Prozess + Kernelmodul, mehr
Latenz/CPU, komplexeres Setup und Autostart. Für 17 unbeaufsichtigte Sensoren
Wartungsaufwand → nur wenn A–C alle scheitern.

---

## Ansatz E — Bewusst nichts tun (dokumentierte Nicht-Lösung)

**Aufwand:** null · immer als Fallback legitim.

Da die **Zähllogik nicht betroffen** ist, ist die Spiegelung rein kosmetisch für
die Live-Vorschau. Für den Produktivbetrieb (headless, ohne `--use-frame`) spielt
sie **gar keine Rolle**. Der einzige echte Nachteil: Beim manuellen Kalibrieren
über das Live-Fenster ist links/rechts vertauscht — aber die **Konfiguration
läuft ohnehin über `camera_raw.png`**, das korrekt ist.

→ Wenn A–D zu aufwendig sind: in den Limitationen benennen („Live-Vorschau bei
USB horizontal gespiegelt; ohne Einfluss auf Zählung, da Konfiguration und
Auswertung auf dem unspiegelten Referenzbild bzw. den Rohdaten basieren") und
weitermachen. Ehrlich und für eine Bachelorarbeit völlig vertretbar.

---

## Empfohlene Reihenfolge

1. **Schritt 0** (Diagnose) — klärt, ob überhaupt ein Fix nötig ist und welcher.
   Oft ist hier schon Schluss (Schalter stand auf False).
2. **Ansatz A** — wenn Schalter greift, fertig.
3. **Ansatz C** — 30-Sekunden-Check (`v4l2-ctl --list-ctrls`); wenn Kamera es
   kann, elegant.
4. **Ansatz B** — die sauberste Ursachenbehebung, wenn der Pipeline-String
   erreichbar ist.
5. **Ansatz D** — nur wenn alles andere scheitert.
6. **Ansatz E** — jederzeit legitimer Abschluss, weil nicht ergebnisrelevant.

## Entscheidungshilfe in einem Satz
Wenn dich die Zeit drückt (Abgabe 31.07.) und A nicht sofort greift: **Ansatz E**
wählen, in den Limitationen sauber benennen, und die Zeit in Realtest/Schreiben
stecken — die Spiegelung ist der am wenigsten wichtige offene Punkt, weil sie
weder Daten noch Zählung berührt.
