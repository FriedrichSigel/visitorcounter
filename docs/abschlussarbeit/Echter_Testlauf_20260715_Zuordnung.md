# Echter Testlauf vom 15.07.2026, 10:36–10:38 — Artefakte im Datenfluss

**Ersetzt die fiktiven Beispieldaten. Alle Werte hier stammen aus den echten
Dateien deines Laufs (`camera_raw.png`, `roi_config.json`, `ergebniss.csv/.txt`,
`zaehlung.csv`, Bewegungsbilder). Für Kapitel 4.b.vii + Anhang.**

Szene: Kamerablick aus einem Fenster auf eine Straße (Berlin-Zehlendorf-artige
Wohnstraße). Zwei Zählflächen auf der Fahrbahn: **Potsdam** links,
**Berlin** rechts. Auflösung 1280×720. Klassen: person, bicycle, car, bus, truck
(bicycle-Klasse aktiv, im Gegensatz zum fiktiven Beispiel). 28 Tracks erfasst.

---

## Zuordnung zu den Stellen im Datenflussdiagramm (Abb. 2)

### Bahn KONFIGURATION

| Stelle im Diagramm | Echtes Artefakt | Inhalt in diesem Lauf |
|---|---|---|
| `core.py` (Snapshot) → **camera_raw.png** | ✅ vorhanden | 1280×720-Fensterblick auf die Straße; Grundlage der Flächendefinition |
| `roi_config_app.py` → **roi_config.json** | ✅ vorhanden | `mode: multi_roi`, zwei `regions` „Berlin" und „Potsdam", `snap_to_nearest: true`, 5 Klassen |
| `auto_config_points.csv` | — (in diesem Lauf nicht erzeugt; Flächen manuell gesetzt) | — |

**roi_config.json — die echten Flächen (Polygone, normalisiert):**

- **Potsdam** (linke Fläche): x ≈ 0.087–0.343, y ≈ 0.159–0.690
- **Berlin** (rechte Fläche): x ≈ 0.662–0.886, y ≈ 0.115–0.573

Dazwischen ein breiter Korridor (x ≈ 0.34–0.66) — die Fahrbahnmitte. `snap_to_nearest`
sorgt dafür, dass Fahrzeuge, deren Track erst in der Bildmitte erkannt wird,
trotzdem der nächstgelegenen Fläche zugeordnet werden. **Wichtig für die
Interpretation:** Die Flächen sitzen links und rechts auf *derselben Fahrbahn* —
„Potsdam→Berlin" heißt also Fahrtrichtung nach rechts (stadtauswärts), nicht
zwei getrennte Eingänge. Für die Arbeit ist das ein sauberes Beispiel für
Richtungszählung an einer Durchfahrt.

> Randnotiz: `bus` und `truck` fehlen in der `classes`-Liste der
> `roi_config.json`, tauchen aber in den Ergebnissen auf (`bus_ID_1` etc.).
> Das heißt: Die Klassenliste steuert offenbar (noch) nicht das Tracking/Zählen,
> sondern erfasst wird, was YOLO liefert. Kurz prüfen, ob das gewollt ist —
> falls die Liste filtern *soll*, ist das ein Bug; falls sie nur die
> Auto-Konfiguration betrifft, in der Arbeit sauber so benennen.

### Bahn BETRIEB

| Stelle im Diagramm | Echtes Artefakt | Inhalt in diesem Lauf |
|---|---|---|
| Hailo-Pipeline → `core.py`-Callback | (Laufzeit, nicht persistiert) | 28 Objekte über ~3 min erkannt und getrackt |
| `tracking.py` (Flush) → `logging_utils.py` → **ergebniss.csv** | ✅ 28 Zeilen | ein Track je Zeile, Pixelkoordinaten, alle `kind=FLUSH` |
| dieselben Daten menschenlesbar → **ergebniss.txt** | ✅ vorhanden | FLUSH-Blöcke mit `[FIRST]`/`[LAST]`, normalisierten Bounding-Boxen |
| `counting.py` → **zaehlung.csv** | ✅ 28 Zeilen | ein Zählereignis je Track, benannte Übergänge |
| `visualization.py` → **Bewegungsbilder** | ✅ 2 PNGs | Trajektorien aller Tracks |

---

## Was in diesem Lauf tatsächlich gezählt wurde

Ausgewertet aus `zaehlung.csv` (28 Ereignisse):

| Richtung | Anzahl | gezählt? |
|---|---|---|
| Potsdam→Berlin | 3 | ✅ (`is_transition=True`) |
| Berlin→Potsdam | 6 | ✅ (`is_transition=True`) |
| Berlin (kein Wechsel) | 15 | ❌ protokolliert, nicht gezählt |
| Potsdam (kein Wechsel) | 4 | ❌ protokolliert, nicht gezählt |
| **Summe** | **28** | **9 gezählte Übergänge** |

**Aussage für die Arbeit:** Von 28 erfassten Objekten führten nur 9 zu einer
gewerteten Durchfahrt; 19 blieben „ohne Wechsel". Das ist **kein Fehler**,
sondern genau die Leistung der Übergangslogik: Objekte, die nur am Rand einer
Fläche auftauchen und wieder verschwinden (kurze Tracks, Erkennung erst spät),
werden dokumentiert, aber nicht fälschlich als Durchfahrt gezählt. Der hohe
Anteil „Berlin (kein Wechsel)" (15) passt zur Szene: Auf der rechten Bildseite
(Berlin-Fläche, näher an der Kamera) werden Objekte groß und oft erst spät oder
nur kurz erkannt.

---

## Ein Track durch alle Artefakte — `car_ID_2` (echte Durchfahrt)

Das durchgängige Beispiel, diesmal mit echten Zahlen:

**1. ergebniss.txt** (menschenlesbar, normalisierte Box):
```
FLUSH
[ID]    car_ID_2
[FIRST] 2026-07-15 10:36:46.853 | Label: car | ID: 7 | xcentre: 429.0 ...
[LAST]  2026-07-15 10:36:49.723 | Label: car | ID: 7 | xcentre: 1127.0 ...
```

**2. ergebniss.csv** (maschinenlesbar, Pixel):
```
car_ID_2,FLUSH,7,car,429,301,1127,275,2026-07-15 10:36:46.853,2026-07-15 10:36:49.723
```

**3. zaehlung.csv** (Zählereignis):
```
2026-07-15 10:36:49.723,car_ID_2,car,Potsdam->Berlin,True
```

**Verkettung:** `display_id=car_ID_2` ist der gemeinsame Schlüssel. Startpunkt
x=429 (norm. 0.335, rechter Rand der Potsdam-Fläche), Endpunkt x=1127
(norm. 0.881, in der Berlin-Fläche) → Bewegung nach rechts → Übergang
`Potsdam->Berlin`, gezählt. Der Zeitstempel des Zählereignisses (10:36:49.723)
ist identisch mit `last_timestamp` — gezählt wird beim Track-Abschluss.
Die rohe Tracker-ID (7) unterscheidet sich von der lesbaren `display_id` —
genau die Trennung, die klassenübergreifende ID-Kollisionen verhindert.

---
## Korrektur an der Diagramm-Zuordnung

Im echten Lauf sind **alle** Tracks `kind=FLUSH` (kein `FINALIZE`) — das Video
lief durch, ohne dass beim Ende noch aktive Tracks offen waren, ODER der Lauf
wurde nicht regulär beendet. Im Datenflussdiagramm ist der FINALIZE-Pfad damit
in diesem Beispiel ungenutzt; er bleibt aber Teil der Architektur (tritt auf,
wenn beim Stopp noch Objekte im Bild sind). Für die Bildunterschrift des
Bewegungsbilds also „alle Tracks per FLUSH abgeschlossen" vermerken.

---

## Prüfpunkte (erledigt / offen)

```
[x] zaehlung.csv-Schema bestätigt: timestamp,display_id,label,direction,is_transition
[x] ergebniss.csv-Schema bestätigt: 10 Spalten, Koordinaten in PIXELN (1280×720)
[x] Zeitstempelformat bestätigt: YYYY-MM-DD HH:MM:SS.mmm
[x] Konsistenz: 28 Tracks in beiden Dateien, keine Waisen
[x] Koordinaten-Umrechnung Pixel↔normalisiert stimmt (247/1280=0.193)
[ ] KLÄREN: bus/truck erscheinen trotz Fehlen in roi_config.json "classes" — Filter-Bug oder gewollt?
[ ] Für Anhang: dieses Bewegungsbild + camera_raw.png mit eingezeichneten Flächen als Abbildung aufbereiten
```
