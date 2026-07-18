# Datenfluss-Verifikation — echter Lauf 15.07.2026, 12:27–12:31

**Test der implementierten Änderungen gegen die tatsächlichen Ausgabedateien
eines echten Pipeline-Laufs (nicht simuliert). Bestätigt, dass der komplette
Datenfluss funktioniert.**

## Prüfungen entlang des Datenflusses

| # | Prüfpunkt | Ergebnis |
|---|---|---|
| 1 | `ergebniss.csv` Schema (11 Spalten inkl. `avg_confidence`) | ✅ korrekt |
| 2 | `ergebniss.txt` wird nicht mehr erstellt | ✅ existiert nicht |
| 3 | Track-Konsistenz `ergebniss.csv` ↔ `zaehlung.csv` | ✅ 64 ↔ 64, keine Waisen |
| 4 | `kind`-Verteilung (FLUSH während Lauf, FINALIZE am Ende) | ✅ 60 FLUSH, 4 FINALIZE |
| 5 | Zwei Bewegungsbilder mit neuer Benennung | ✅ `_flush.png` + `_finalize.png` |
| 6 | Start-Cleanup nach `vorherige_laeufe/` | ✅ zwei Archivordner vorhanden |
| 7 | Klassenfilter (nur `TRACKED_LABELS`) | ✅ nur person/bicycle/car/bus/truck |

## avg_confidence — funktioniert und ist aussagekräftig

Wertebereich über 64 Tracks: min 0.314, max 0.844, Mittel 0.494.

Die Confidence korreliert klar mit der Track-Qualität:

| Track-Typ | Anzahl | Ø avg_confidence |
|---|---|---|
| lange Durchfahrten (>400px Bewegung) | 11 | **0.717** |
| kurze Artefakt-Tracks (<20px Bewegung) | 26 | **0.429** |
| Differenz | | **+0.288** |

**Bedeutung für die Arbeit:** `avg_confidence` ist damit ein direkt nutzbarer
Filter, um kurze Fehldetektionen von echten Durchfahrten zu trennen — genau der
Hebel für den noch offenen `should_count_track()`-Filter. Beispiele aus dem
echten Lauf: `car_ID_6` (echte Durchfahrt, 127→1142px) hat 0.844; `car_ID_2`
(Ein-Frame-Artefakt) hat 0.314.

## Zählergebnis dieses Laufs

Aus `zaehlung.csv`, nur `is_transition=True`:

| Richtung | Anzahl |
|---|---|
| Potsdam→Berlin | 8 |
| Berlin→Potsdam | 7 |
| **gezählte Übergänge gesamt** | **15** (von 64 Ereignissen) |

Die übrigen 49 sind „kein Wechsel" — Objekte, die nur am Rand einer Fläche
auftauchten. Konsistent mit dem Verhalten, das schon der frühere Lauf zeigte.

## Nebenbefund: bus/truck-Rätsel geklärt

Die aktuelle `roi_config.json` listet `person, bicycle, car, bus, truck` — der
Klassenfilter greift korrekt, alle fünf erscheinen erwartungsgemäß. Das frühere
„Rätsel" (bus/truck trotz Fehlen in `classes`) war eine veraltete Config, kein
Bug. In HANDOFF.md 4a als geklärt vermerkt.

## Beobachtung für die Evaluation (Kapitel 5/6)

Der Lauf zeigt erneut die ID-Multiplikation bei großen Fahrzeugen: Um
12:30:53–55 erscheinen `truck_ID_1/2/3`, `car_ID_11/12/13`, `bus_ID_1` mit teils
identischen rohen `track_id`s (36, 37, 38) — dasselbe große Fahrzeug wird über
die Zeit als truck/car/bus klassifiziert. Bekannte, belegbare Limitation der
frameweisen Klassifikation; `avg_confidence` und der Kurz-Track-Filter können
das teilweise entschärfen.
