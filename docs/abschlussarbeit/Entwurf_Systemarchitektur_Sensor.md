# Entwurf: Systemarchitektur des Zählsensors
## Für Kapitel 3.e (Konzept) und 4.b.i–ii (Umsetzung) — Stand 14.07.2026

Dieser Entwurf verbindet drei Ebenen: (A) das allgemeine Sensormodell aus der
Literatur, (B) die konkrete Hailo-Pipeline-Architektur, (C) den Datenfluss der
eigenen Software mit allen Zwischen- und Endergebnissen. A gehört konzeptionell
in Kapitel 3.e, B und C in 4.b.i–ii — die Trennung ist unten markiert.

---

## A. Der Zählsensor im allgemeinen Sensormodell *(→ Kapitel 3.e)*

### A.1 Einfaches Modell (Hering & Schönfelder 2018)

Nach Hering und Schönfelder (2018) besteht ein Sensor aus einem **Sensor-Element**,
das eine nicht-elektrische Eingangsgröße nach naturwissenschaftlichen Gesetzen in
ein elektrisches Rohsignal wandelt, und einer **Auswerte-Elektronik**, die daraus
per Schaltungselektronik *oder Software* ein nutzbares Sensor-Ausgangssignal
erzeugt und dabei Störgrößen berücksichtigt.

Übertragen auf den Zählsensor:

| Modellbaustein (Hering & Schönfelder 2018) | Umsetzung im Zählsensor |
|---|---|
| Eingangsgröße (nicht elektrisch) | Bewegung von Personen durch den Erfassungsbereich eines Eingangs |
| Sensor-Element | Bildsensor der USB-Kamera (photoelektrische Wandlung Licht → Digitalbild) |
| Störgrößen | wechselnde Lichtverhältnisse, Witterung, Verdeckungen, gleichzeitige Bewegungen mehrerer Personen |
| Auswerte-Elektronik | Raspberry Pi 5 mit Hailo-8: Objekterkennung, Tracking und Zähllogik in Software |
| Sensor-Ausgangssignal | aggregierte Zählwerte (Eintritte/Austritte je Zeitintervall) |

Zwei Punkte sind hier argumentativ wertvoll:

1. Hering und Schönfelder (2018) schließen **Softwareprogramme ausdrücklich als
   Teil der Auswerte-Elektronik ein** — die CV-Verarbeitung ist also keine
   Abweichung vom Sensorbegriff, sondern eine Ausprägung davon.
2. Die Definition verlangt die **Berücksichtigung von Störgrößen** in der
   Auswertung. Genau das leisten Tracking (Robustheit gegen kurzzeitige
   Erkennungsaussetzer, Flush nach 30 Frames) und die konfigurierbare
   Zählgeometrie (Ausblenden irrelevanter Bildbereiche). Damit lässt sich die
   eigene Softwarearchitektur direkt aus dem Sensormodell motivieren.

### A.2 Detailmodell und Smart-Sensor-Einordnung (Heinrich et al. 2020)

Heinrich et al. (2020) verfeinern den Aufbau zur Messkette
*Messfühler → Messverstärker → Auswerteelektronik → Wandler → Aus-/Übergabe →
Netzwerk-Schnittstelle* und unterscheiden drei Integrationsstufen:
**Elementarsensor** (nur Messfühler), **Messaufnehmer/integrierter Sensor**
(inkl. Signalaufbereitung) und **Smart-Sensor/intelligenter Sensor**
(zusätzlich Netzwerkanbindung und lokale Vorverarbeitung).

| Messkettenglied (Heinrich et al. 2020) | Umsetzung im Zählsensor | Signalcharakter |
|---|---|---|
| Messgröße | Personenbewegung am Eingang | nicht elektrisch |
| Messfühler (Elementarsensor) | Bildsensor der Kamera | analoges → digitalisiertes Bildsignal |
| „Messverstärker" (Signalanpassung) | Videokonvertierung/-skalierung der GStreamer-Pipeline (Format- und Auflösungsanpassung auf die Netzeingangsgröße) | digitales Signal |
| Auswerteelektronik | YOLO-Inferenz auf dem Hailo-8 (`hailonet`), Nachverarbeitung (`hailofilter`), Objektverfolgung (`hailotracker`) | digitale Erkennungs-/Trackingdaten |
| Wandler | Zähllogik: kontinuierliche Trajektorien → **diskrete Zählereignisse** (Linienquerung, ROI-Ein-/Austritt, Zonenübergang) | quasi-binäre Ereignisse (vgl. Signalarten bei Heinrich et al. 2020) |
| Aus-/Übergabe | Persistierung als CSV/TXT, Live-Visualisierung | strukturierte Daten |
| Netzwerk-Schnittstelle | LoRaWAN-Uplink (25-Byte-Binärformat) an die Urbane Datenplattform | Bussignal-Analogon |

**Einordnung:** Da das System Signalaufbereitung, lokale Vorverarbeitung *und*
eine Netzwerkschnittstelle vereint, erfüllt es die Definition des
**Smart-Sensors** nach Heinrich et al. (2020). Diese Einordnung rechtfertigt
den Begriff „Sensor" im Titel der Arbeit literaturgestützt — es handelt sich
nicht um „eine Kamera mit Software", sondern um einen intelligenten Sensor im
Sinne der Automatisierungstechnik.

**Brücke zum Datenschutz:** Die lokale Vorverarbeitung ist bei Heinrich et al.
(2020) ein Merkmal des Smart-Sensors zur Komplexitätsreduktion; im Zählsensor
erfüllt sie zusätzlich die Datenschutzanforderung: Bilddaten verlassen das
Gerät nie, ausgegeben wird ausschließlich das hochaggregierte Zählsignal.
Dieselbe Architektureigenschaft löst also zwei Anforderungen zugleich
(Bandbreite der LoRa-Übertragung und Privacy by Design) — ein Satz, der in
3.e.iii gut sitzt.

> **Abbildungsempfehlung 1 (für 3.e):** Das Blockschaltbild von Heinrich et al.
> (2020) nachzeichnen und jedes Glied mit der eigenen Komponente beschriften
> (zweizeilige Kästen: oben Modellbegriff, unten Umsetzung). Eine Abbildung,
> zwei Aussagen: Literaturanschluss + Gesamtarchitektur.

---

## B. Pipeline-Architektur nach dem Hailo-Framework *(→ Kapitel 4.b.i)*

### B.1 Schichtenmodell

Das Hailo-Applikationsframework ist dreischichtig aufgebaut (Hailo Technologies
2026): (1) **GStreamer** als Streaming-Grundgerüst mit Plugin-Architektur,
(2) **Tappas** — Hailos C/C++-GStreamer-Elemente als Brücke zur
Beschleuniger-Hardware (u. a. `hailonet`, `hailofilter`, `hailotracker`,
`hailooverlay`), (3) die **Python-Schicht** mit `GStreamerApp`-Klasse
(Pipeline-Lebenszyklus, Bus-Nachrichten wie End-of-Stream) und
Callback-Mechanismus.

Die eigene Software dockt an Schicht 3 an: Sie folgt dem von Hailo als
„Development Path 1" beschriebenen **Callback-basierten Ansatz** — die
Pipeline übernimmt Dekodierung, Inferenz und Rendering; die eigene Logik wird
pro Frame über eine Callback-Funktion aufgerufen, die Videoframe und
KI-Metadaten erhält. Die Vorgabe, dass der Callback nicht blockieren darf,
prägt die eigene Architektur an zwei Stellen: Die CSV-Persistierung erfolgt
gepuffert, und der LoRa-Uplink läuft in einem separaten Thread mit Queue.

### B.2 Pipeline-Pattern: erweiterte Single Network Pipeline

Von den fünf im Entwicklerguide beschriebenen Architektur-Patterns (Single
Network, Wrapped Inference, Cascaded Networks, Parallel Networks, Tiled
Inference) verwendet der Zählsensor die **Single Network Pipeline** — ein
einzelnes Erkennungsmodell auf einem Videostrom:

```
Source → Videokonvertierung → hailonet → hailofilter → hailooverlay → Display
```

Der Zählsensor erweitert dieses Grundpattern an zwei Stellen:

1. **`hailotracker`** zwischen Nachverarbeitung und Anzeige — mit `class-id=-1`,
   damit alle sechs Klassen (person, bicycle, car, motorcycle, bus, truck)
   getrackt werden, nicht nur die Standardklasse.
2. **Callback-Abgriff** der Metadaten für die eigene Verarbeitungskette
   (Abschnitt C).

Damit lautet die konkrete Pipeline:

```
Source (Video/USB/RPi-Kamera)
  → Videokonvertierung
  → hailonet     (YOLO-Inferenz auf Hailo-8)
  → hailofilter  (Rohtensoren → Erkennungsobjekte)
  → hailotracker (frameübergreifende IDs, class-id=-1)
  → [Callback: eigene Zähl-Software, siehe C]
  → hailooverlay → Display
```

**Begründung der Pattern-Wahl (für das morphologische Tableau in 3.c):**
Kaskadierte oder parallele Netze sind nicht erforderlich, da eine einzige
Erkennungsaufgabe vorliegt; Tiled Inference adressiert hochauflösende
Weitwinkelszenen mit sehr kleinen Objekten und würde die Verarbeitungsrate
senken. Die Single Network Pipeline ist die ressourcenschonendste Variante —
relevant für Dauerbetrieb auf Edge-Hardware.

---

## C. Eigene Software: Module, Aufgaben, Zwischenergebnisse *(→ Kapitel 4.b.ii)*

### C.1 Verarbeitungskette im Betrieb (pro Frame)

| # | Schritt | Modul | Eingabe | Ergebnis (flüchtig) | Persistiertes (Zwischen-)Ergebnis |
|---|---|---|---|---|---|
| 1 | Pipeline-Steuerung, Frame-Callback | `core.py` | GStreamer-Buffer | Frame + Erkennungs-/Tracking-Metadaten | — |
| 2 | Track-Verwaltung: anlegen, aktualisieren, flushen (30 Frames ohne Sichtung), klassengetrennte lesbare IDs (`person_ID_1`) | `tracking.py` | Metadaten aus 1 | aktueller Track-Zustand (Trajektorien) | — |
| 3 | Zählentscheidung: Linienquerung / ROI-Ein-Austritt / Zonenübergang (`A->B`), inkl. „kein Wechsel"-Fall | `counting.py` | abgeschlossene/aktive Tracks | diskrete Zählereignisse mit Richtung | **`zaehlung.csv`** (ereignisweise, mit `is_transition`-Spalte) |
| 4 | Track-Finalisierung bei Flush/Ende | `tracking.py` → `logging_utils.py` | Track-Historie | — | **`ergebniss.csv`**, **`ergebniss.txt`** (ein Datensatz je Track), **Bewegungsbilder** (Pillow, echte Videoauflösung) |
| 5 | Live-Overlay: Zählgeometrie, Boxen, Zählerstände | `visualization.py` | Frame + Zustand aus 2/3 | „User Frame"-Anzeigefenster | — |
| 6 | Schema-Sicherung aller CSV-Schreiber | `csv_utils.py` (`ensure_current_schema()`) | bestehende Dateien | — | Archivkopie veralteter Dateien (umbenannt, nie gelöscht) |
| 7 | (Anbindung vorbereitet) Intervall-Aggregation → Uplink | `lora_transmitter.py` | Zählerstände aus 3 | — | **25-Byte-LoRaWAN-Nachricht** an die UDP |

Die Endergebnisse (`ergebniss.csv`, `zaehlung.csv`) entstehen also **nicht erst
am Ende des Programmlaufs**, sondern fortlaufend: Zählereignisse werden im
Moment ihres Auftretens geschrieben (Schritt 3), Track-Zusammenfassungen beim
Flush des jeweiligen Tracks (Schritt 4). Das ist eine bewusste
Robustheitsentscheidung — bei Absturz oder Stromausfall sind alle bis dahin
erfassten Ereignisse bereits persistiert.

### C.2 Konfigurationskette (vor dem Betrieb)

| # | Schritt | Modul | Persistiertes Ergebnis |
|---|---|---|---|
| K1 | Referenzframe aus der **echten Pipeline** aufnehmen (`CORE_SNAPSHOT_ONLY`) — garantiert identische Auflösung wie im Live-Betrieb | `core.py` (Snapshot-Modus), angestoßen aus `roi_config_app.py` | **`camera_raw.png`** |
| K2 | Manuelle Zählgeometrie per Mausklick ODER | `roi_config_app.py` | **`roi_config.json`** |
| K3 | Auto-Konfiguration Datensammlung: Start-/Endpunkte von Tracks protokollieren | `auto_config.py` | **`auto_config_points.csv`** |
| K4 | Auto-Konfiguration Auswertung: DBSCAN-Clustering ODER Randraster mit Mindestbewegungsfilter → Zonenvorschlag | `auto_config_clustering.py` | **`roi_config.json`** (via `--save`) |
| K5 | Laden der Konfiguration beim Start | `config.py` | — |

`app.py` bündelt K1–K5 und die Betriebssteuerung in vier Seiten
(Input → Konfiguration → Start → Live-Auswertung) — die Umsetzung der
Interview-Anforderung „Bedienung ohne Kommandozeile".

> **Abbildungsempfehlung 2 (für 4.b.i):** Datenflussdiagramm mit zwei
> Schwimmbahnen („Konfiguration" oben, „Betrieb" unten), Module als Kästen,
> persistierte Artefakte als Zylinder/Dokumentsymbole an den Übergabepunkten
> (`camera_raw.png`, `roi_config.json`, `auto_config_points.csv`,
> `zaehlung.csv`, `ergebniss.csv/.txt`, Bewegungsbilder, LoRa-Nachricht).
> Diese eine Abbildung beantwortet „welches Modul macht was und was kommt
> dabei raus" vollständig.

---

## Quellen (Harvard, für diese Abschnitte)

- Hering, E. & Schönfelder, G. (2018) *Sensoren in Wissenschaft und Technik:
  Funktionsweise und Einsatzgebiete.* 2. Aufl. Wiesbaden: Springer Vieweg.
- Heinrich, B., Linke, P. & Glöckler, M. (2020) *Grundlagen Automatisierung:
  Erfassen – Steuern – Regeln.* 3. Aufl. Wiesbaden: Springer Vieweg.
- Hailo Technologies (2026) *Hailo Application Development Guide.* Verfügbar
  unter: https://github.com/hailo-ai/hailo-apps/blob/main/doc/developer_guide/app_development.md
  (Zugriff: 14.07.2026).

### Zitierhinweise

1. **Vorlesungsfolien nicht als Beleg zitieren** — die VL04 nennt selbst ihre
   Quellen (Hering & Schönfelder 2018; Heinrich et al. 2020; DIN 1319-1).
   Immer die Originalquelle zitieren; die Folien höchstens als Fundhinweis für
   dich selbst behandeln.
2. **hailo-apps vs. hailo-rpi5-examples:** Der Entwicklerguide liegt im Repo
   `hailo-apps`; dein Code baut auf `hailo-rpi5-examples` auf. Beide gehören
   zum selben Framework (Tappas + Python-Schicht), aber im Text sauber
   formulieren: Architekturbeschreibung nach dem offiziellen Entwicklerguide
   (Hailo Technologies 2026), Implementierung auf Basis des
   Raspberry-Pi-Beispielrepositorys. Beim Online-Zitat Zugriffsdatum angeben —
   das Repo ändert sich laufend.
3. Optional für A.2: **DIN 1319-1** für den Begriff „Aufnehmer" als erstes
   Element der Messkette — mit Normzitaten sparsam sein, Heinrich et al.
   (2020) trägt die Argumentation allein.
