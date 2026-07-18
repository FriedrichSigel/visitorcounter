# Datenartefakte des Zählsensors — durchgängiges Beispiel
## Zwei-Flächen-Konfiguration „Potsdam" / „Berlin" (Modus: Mehrere Flächen)

**Für Kapitel 4.b.vii (Datenhaltung), Beispieldaten auch als Anhang geeignet.
Stand 14.07.2026.**

Dieses Dokument arbeitet den Datenfluss (vgl. Abb. 2) artefaktweise ab. Alle
Beispiele beschreiben **denselben fiktiven Testlauf**, sodass sich jeder
Datensatz über die `display_id` durch alle Dateien verfolgen lässt.

> ⚠️ **Vor Übernahme in die Arbeit:** Die Spaltennamen und Semantik stammen aus
> der Projektdokumentation (HANDOFF) und sind verlässlich. Zwei Details sind
> **Annahmen** und müssen einmal gegen echte Dateien vom Pi geprüft werden:
> (1) das exakte Zeitstempel-Format, (2) ob `ergebniss.csv` Pixel- oder
> normalisierte Koordinaten schreibt (hier: Pixel bei 1280×720 angenommen).
> Am schnellsten: `head -5 *.csv` auf dem Pi und die Beispielwerte hier ersetzen.

---

## Das Beispielszenario

Kamera blickt auf einen Durchgang; links wurde die Fläche **Potsdam**, rechts
die Fläche **Berlin** eingezeichnet. Videoauflösung 1280×720. Vier Tracks
treten auf:

| Track (display_id) | Verhalten | Erwartetes Zählergebnis |
|---|---|---|
| `person_ID_1` | betritt links, verlässt rechts | **Potsdam→Berlin** (gezählt) |
| `person_ID_2` | läuft links im Kreis, bleibt in Potsdam | „kein Wechsel" (protokolliert, **nicht** gezählt) |
| `car_ID_1` | fährt von rechts nach links | **Berlin→Potsdam** (gezählt) |
| `person_ID_3` | wird nach 30 Frames ohne Sichtung geflusht, Endpunkt lag (per `snap_to_nearest`) näher an Berlin | **Potsdam→Berlin** (gezählt) |

---

## Artefakt 1: `roi_config.json` — die Konfiguration (Ausgangspunkt)

Geschrieben von `roi_config_app.py` (manuell) oder
`auto_config_clustering.py --save` (automatisch); gelesen von `config.py` beim
Start. **Alle Koordinaten normalisiert 0.0–1.0** — dadurch ist die
Konfiguration unabhängig von der Auflösung wiederverwendbar (Referenzbild und
Live-Pipeline können identisch interpretiert werden).

```json
{
  "mode": "multi_roi",
  "regions": [
    {
      "name": "Potsdam",
      "points": [
        [0.05, 0.15],
        [0.42, 0.15],
        [0.42, 0.90],
        [0.05, 0.90]
      ]
    },
    {
      "name": "Berlin",
      "points": [
        [0.58, 0.15],
        [0.95, 0.15],
        [0.95, 0.90],
        [0.58, 0.90]
      ]
    }
  ],
  "classes": ["person", "bicycle", "car", "motorcycle", "bus", "truck"],
  "reverse_direction": false,
  "snap_to_nearest": true
}
```

**Lesehilfe:** Zwei benannte Rechtecke mit einem Korridor dazwischen
(x 0.42–0.58 gehört keiner Fläche an). `snap_to_nearest: true` bedeutet:
Track-Start-/Endpunkte im Korridor werden der **nächstgelegenen** Fläche
zugeordnet — ohne diese Option würden Tracks, die im Niemandsland beginnen
oder enden (typisch bei spätem Erkennen/frühem Flush), keiner Zählung
zugeordnet. Im Modus `line` enthielte die Datei stattdessen `points` mit
2 Punkten, im Modus `roi` ein einzelnes Polygon; `regions` existiert nur bei
`multi_roi`.

---

## Artefakt 2: `camera_raw.png` — der Referenzframe

Kein Datensatz, sondern das Bild, **auf dem** die Flächen aus Artefakt 1
eingezeichnet wurden. Entscheidend ist seine Herkunft: Es wird im
Snapshot-Modus (`CORE_SNAPSHOT_ONLY`) aus **exakt derselben Hailo-Pipeline**
aufgenommen wie der spätere Live-Betrieb — gleiche Auflösung, gleicher
Bildausschnitt. Nur dadurch stimmen die normalisierten Koordinaten aus
`roi_config.json` im Betrieb pixelgenau. Wird bei jeder Aufnahme überschrieben.

---

## Artefakt 3: `auto_config_points.csv` — Rohdaten der Auto-Konfiguration

Nur bei aktivierter Datensammlung (`AUTO_CONFIG_COLLECTION_ENABLED = True`).
Pro Track **zwei Zeilen**: Start- und Endpunkt. Das ist die Eingabe für
DBSCAN-Clustering bzw. Randraster-Verfahren — hätte man die Flächen
Potsdam/Berlin automatisch bestimmen lassen, wären sie aus genau solchen
Punktwolken entstanden.

```csv
timestamp,display_id,label,point_type,x,y
2026-07-14 18:02:41.120,person_ID_1,person,start,0.11,0.52
2026-07-14 18:02:44.960,person_ID_1,person,end,0.83,0.49
2026-07-14 18:02:47.400,person_ID_2,person,start,0.19,0.63
2026-07-14 18:02:52.240,person_ID_2,person,end,0.27,0.58
2026-07-14 18:02:55.080,car_ID_1,car,start,0.91,0.71
2026-07-14 18:02:58.520,car_ID_1,car,end,0.08,0.69
2026-07-14 18:03:01.360,person_ID_3,person,start,0.14,0.44
2026-07-14 18:03:05.800,person_ID_3,person,end,0.55,0.47
```

**Lesehilfe:** Koordinaten normalisiert (konsistent zu `roi_config.json`).
Die letzte Zeile zeigt den `snap_to_nearest`-Fall: `x=0.55` liegt im Korridor
(0.42–0.58), näher an Berlin (Grenze 0.58) — wird bei der Zählung Berlin
zugeschlagen.

---

## Artefakt 4: `zaehlung.csv` — ein Eintrag pro Zählereignis (im Betrieb, sofort)

Geschrieben von `logging_utils.py` **im Moment des Ereignisses** (nicht am
Laufende) — bei Absturz sind alle bisherigen Ereignisse bereits persistent.
Schema: 5 Spalten, abgesichert durch `csv_utils.ensure_current_schema()`.

```csv
timestamp,display_id,label,direction,is_transition
2026-07-14 18:02:44.960,person_ID_1,person,Potsdam->Berlin,True
2026-07-14 18:02:52.240,person_ID_2,person,Potsdam (kein Wechsel),False
2026-07-14 18:02:58.520,car_ID_1,car,Berlin->Potsdam,True
2026-07-14 18:03:05.800,person_ID_3,person,Potsdam->Berlin,True
```

**Lesehilfe:**
- `direction` trägt im Mehrflächen-Modus den **benannten Übergang** — die
  Flächennamen aus `roi_config.json` tauchen hier wörtlich wieder auf. Das ist
  der Grund, warum sprechende Namen (statt „Zone1/Zone2") die Auswertung
  selbsterklärend machen; am Volkspark stünden hier z. B. `Eingang_Nord->Park`.
- `is_transition=False` (Zeile 2) ist der dokumentierte „kein Wechsel"-Fall:
  protokolliert, aber **nicht** gezählt. Designentscheidung: Verwerfen wäre
  Informationsverlust — so bleibt z. B. auswertbar, wie viele Personen sich
  *innerhalb* eines Bereichs aufhalten, ohne die Übergangszählung zu verfälschen.
- Auswertung „gezählte Eintritte nach Berlin": Filter
  `direction == "Potsdam->Berlin" AND is_transition == True` → 2.

---

## Artefakt 5: `ergebniss.csv` — ein Datensatz pro Track (beim Flush/Finalize)

Geschrieben, wenn ein Track abgeschlossen wird — entweder durch **FLUSH**
(30 Frames ohne Sichtung) oder **FINALIZE** (Laufende). Feste Feature-Zeilen
für maschinelle Auswertung; genau diese Start-/Endpunkte sind auch die
Datengrundlage des Clustering-Ansatzes.

```csv
display_id,kind,track_id,label,start_x,start_y,end_x,end_y,first_timestamp,last_timestamp
person_ID_1,FLUSH,7,person,141,374,1062,353,2026-07-14 18:02:41.120,2026-07-14 18:02:44.960
person_ID_2,FLUSH,9,person,243,454,346,418,2026-07-14 18:02:47.400,2026-07-14 18:02:52.240
car_ID_1,FLUSH,12,car,1165,511,102,497,2026-07-14 18:02:55.080,2026-07-14 18:02:58.520
person_ID_3,FINALIZE,15,person,179,317,704,338,2026-07-14 18:03:01.360,2026-07-14 18:03:05.800
```

**Lesehilfe:**
- `display_id` vs. `track_id`: Die rohe Hailo-Tracker-ID (`track_id`) zählt
  klassenübergreifend hoch und ist nicht sprechend; `display_id` ist die
  eigene, **pro Klasse** hochzählende lesbare ID (`person_ID_1`, `car_ID_1`) —
  der Fremdschlüssel, über den sich dieser Track in `zaehlung.csv`,
  `ergebniss.txt` und im Bewegungsbild wiederfindet.
- `kind`: FLUSH = Track wegen Inaktivität abgeschlossen; FINALIZE = beim
  regulären Laufende noch aktiv gewesen (hier: `person_ID_3` war beim
  Video-Ende noch im Bild).
- Koordinaten hier in **Pixeln** der Videoauflösung (1280×720) —
  `end_x=704` von `person_ID_3` entspricht dem normalisierten 0.55 aus
  Artefakt 3 (704/1280 = 0.55). *(Annahme, s. o. — einmal gegen echte Datei prüfen.)*
- Bekannte Limitation für die Arbeit: Liefert der Tracker keine ID, fällt
  `track_id` auf 0 zurück; durch die Klassentrennung der `display_id`
  kollidieren verschiedene Klassen nicht mehr, zwei gleichzeitig ungetrackte
  Objekte *derselben* Klasse aber potenziell schon.

---

## Artefakt 6: `ergebniss.txt` — dieselben Ereignisse für Menschen

Fließtext-Log, gleicher Inhalt wie Artefakt 5, aber als lesbare Blöcke —
gedacht für schnelle Sichtkontrolle ohne Tabellenwerkzeug:

```
=== FLUSH ===
[ID]    person_ID_1 (Tracker-ID 7, Klasse person)
Start:  (141, 374)   um 18:02:41.120
Ende:   (1062, 353)  um 18:02:44.960
Zählung: Potsdam->Berlin

=== FLUSH ===
[ID]    person_ID_2 (Tracker-ID 9, Klasse person)
Start:  (243, 454)   um 18:02:47.400
Ende:   (346, 418)   um 18:02:52.240
Zählung: Potsdam (kein Wechsel) — nicht gezählt

...

=== FINALIZE (Laufende) ===
[ID]    person_ID_3 (Tracker-ID 15, Klasse person)
Start:  (179, 317)   um 18:03:01.360
Ende:   (704, 338)   um 18:03:05.800
Zählung: Potsdam->Berlin (Endpunkt per snap_to_nearest Berlin zugeordnet)
```

*(Blockaufbau illustrativ nach dokumentiertem Muster — exakten Wortlaut einmal
gegen eine echte Datei abgleichen.)*

---

## Artefakt 7: Bewegungsbilder (`tracked_objects_*.png` / `*_ENDE.png`)

Pro Lauf erzeugte Grafik in **echter Videoauflösung**: alle Trajektorien mit
ihren `display_id`-Labels über dem Szenenbild. Für das Beispiel: vier Pfade —
zwei lange von links nach rechts (person_ID_1, person_ID_3), einer von rechts
nach links (car_ID_1), ein kurzer Kringel links (person_ID_2). Funktion in der
Arbeit: **visuelle Plausibilitätsprüfung** der Zahlen aus Artefakt 4/5 — und
als Abbildung im Evaluationskapitel Gold wert, weil ein einziges Bild zeigt,
ob Tracking und Zuordnung stimmen.

Verwandte Kontrollbilder der Auto-Konfiguration (jeweils überschrieben):
`auto_config_clusters.png` (Punkte farblich je Cluster, grau = Ausreißer) und
`auto_config_border.png` (Randraster: grün = gewertete Überquerung, grau =
aussortiert).

---

## Artefakt 8 (vorbereitet): LoRaWAN-Nachricht — die Verdichtungsstufe

Am Ende der Kette wird **nicht** der Inhalt der CSVs übertragen, sondern eine
Aggregation: 25 Byte pro Intervall (vgl. `lora_transmitter.py`). Für das
Beispielintervall (18:00–18:05, Sensor-ID 3) etwa:

```
Feld               Wert            Herkunft
version            1               Formatkonstante
sensor_id          3               Gerätekonfiguration
timestamp          1784224800      Intervallende (Unix UTC)
count_in           2               zaehlung.csv: Potsdam->Berlin, is_transition=True
count_out          1               zaehlung.csv: Berlin->Potsdam, is_transition=True
count_total_in     2               kumuliert seit Start
count_total_out    1               kumuliert seit Start
interval_s         300             Konfiguration
zone_count         2               roi_config.json: len(regions)
mode               2               multi_roi
status             0b00000111      Kamera ok, Hailo ok, Konfig geladen
frames_processed   7482            Plausibilitätszähler
```

**Ehrlicher Hinweis für die Arbeit (dokumentierte offene Aufgabe):** Das
25-Byte-Format kennt bisher nur die Richtungen „in/out" — es bildet Linien-
und ROI-Modus direkt ab. Der Mehrflächen-Modus mit *benannten* Übergängen
(`Potsdam->Berlin`) müsste dafür auf in/out **abgebildet** werden (z. B.
eine Fläche als „innen" deklarieren) oder einen eigenen Nachrichtentyp
erhalten. Für einen einzelnen Eingang mit zwei Flächen ist die Abbildung
trivial (Übergang zur Innenfläche = in); für komplexere Geometrien ist das
eine benannte Grenze des aktuellen Formats → Limitationen/Ausblick.

---

## Die Verdichtungskette auf einen Blick (Kernaussage für 4.b.vii)

```
Rohsignal            ~25 Bilder/s à ~2,7 MB          (verlässt das Gerät nie)
  → Metadaten        Erkennungen + Track-IDs pro Frame   (flüchtig)
  → ergebniss.csv    1 Zeile pro Track                   (lokal persistent)
  → zaehlung.csv     1 Zeile pro Zählereignis            (lokal persistent)
  → LoRa-Uplink      25 Byte pro Intervall               (einziges, was das Gerät verlässt)
```

Jede Stufe reduziert Datenvolumen **und** Personenbezug: Vom Bild über die
Trajektorie zum anonymen Zählwert. Diese Tabelle ist gleichzeitig das
Privacy-by-Design-Argument (2.a.iii / 3.e.iii) und die Begründung, warum
LoRaWAN trotz 25-Byte-Nutzlast als Übertragungsweg ausreicht.

---

## Prüf-Checkliste vor Übernahme in die Arbeit

```
[ ] head -5 zaehlung.csv ergebniss.csv auto_config_points.csv   # echtes Format
[ ] Zeitstempel-Format aus echter Datei übernehmen
[ ] ergebniss.csv: Pixel- oder normalisierte Koordinaten? Beispielwerte anpassen
[ ] Wortlaut eines echten FLUSH-Blocks aus ergebniss.txt übernehmen
[ ] Ein echtes Bewegungsbild + auto_config_clusters.png als Abbildungen sichern
[ ] Optional: genau dieses Zwei-Flächen-Szenario einmal real durchspielen
    (Testvideo, Flächen "Potsdam"/"Berlin") und die echten Dateien als
    Anhang verwenden statt der fiktiven — stärkster Beleg
```
