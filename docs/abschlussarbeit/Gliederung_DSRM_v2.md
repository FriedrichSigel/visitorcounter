# Gliederung — Entwicklung eines Computer-Vision-basierten Sensors zur automatisierten Besucherzählung

**Stand: 14.07.2026 · Version 2** — ersetzt `Gliederung_DSRM.md` (13.07.).
Basis: tatsächlicher Entwurf aus `BA.pdf`. Grobeinteilung 1.–6. sowie Kapitel 1 mit
allen Unterpunkten **unverändert übernommen**. Kapitel 2–6 neu strukturiert nach
DSRM (Peffers et al. 2007) und gängigen Standards der gestaltungsorientierten
Wirtschaftsinformatik.

> **Offener Punkt vor Abgabe:** Titel-Inkonsistenz zwischen „Personenzählung" (BA.pdf)
> und „Besucherzählung" (Anmeldung/Statusbericht, FF C). Vereinheitlichen — und die
> Unterscheidung in 1.b sauber definieren, sie trägt die gesamte Argumentation für
> die Bewegungsrichtungs-/Übergangserkennung.

---

## Zuordnung: Kapitel → DSRM-Aktivität → Forschungsfrage

| Kapitel | DSRM-Aktivität (Peffers et al. 2007) | Beantwortet |
|---|---|---|
| 1 Einleitung | Aktivität 1 — Problem Identification and Motivation | — (bereits geschrieben) |
| 2 Zielvorgabe und Leistungsdefinition | Aktivität 2 — Define the Objectives for a Solution (allgemein) | FF A, FF B |
| 3 Design und Entwicklung | Aktivität 2 (fallspezifisch) → Aktivität 3 — Design and Development | FF C |
| 4 Prototyping und Demonstration | Aktivität 3 (Umsetzung) + Aktivität 4 — Demonstration | FF D |
| 5 Evaluation und Kommunikation | Aktivität 5 — Evaluation + Aktivität 6 — Communication | — |
| 6 Zusammenfassung, Fazit und offene Fragen | Reflexion / Beitrag | FF A–D (Synthese) |

**Roter Faden:** Die allgemeinen Zielkriterien (2.d) werden in 3.b.iii zu einem
konkreten Anforderungskatalog verdichtet — und genau dieser Katalog ist in 5.c der
Maßstab der Evaluation. Diese drei Stellen müssen wörtlich aufeinander verweisen.

---

## 1. Einleitung *(unverändert)*

- a. Motivation
- b. (Begriffsklärung)
- c. Forschungsziel
- d. Forschungsmethode
- e. Gliederung der Arbeit

---

## 2. Zielvorgabe und Leistungsdefinition
*DSRM Aktivität 2 — allgemeiner, anwendungsfall-unabhängiger Teil. Beantwortet FF A und FF B.*

Peffers et al. (2007: 55) verlangen, die Ziele „rational aus der Problemspezifikation"
abzuleiten. Dieses Kapitel bleibt deshalb bewusst noch allgemein; die Zuspitzung auf
den Fall Stadtwerke Potsdam folgt erst in Kapitel 3.

### a. Grundlagen
- **i.** Computer Vision, Objekterkennung und Objekt-Tracking (Einordnung der YOLO-Modellfamilie)
- **ii.** Zählprinzipien: Linienzählung, ROI-basierte Zählung, Zonenübergangszählung
- **iii.** Edge Computing und Privacy by Design als Datenschutzarchitektur
- **iv.** LoRaWAN und die Urbane Datenplattform (UDP) Potsdam als Zielinfrastruktur

### b. Methodik der Literaturrecherche
- **i.** Vorgehensmodell der systematischen Recherche (vom Brocke et al. 2009; Webster & Watson 2002)
- **ii.** Suchstrategie: Datenbank ProQuest, Suchstrings, Erhebungszeitpunkte, Ein- und Ausschlusskriterien
- **iii.** Selektionsprozess und Trefferaufbereitung (Flussdiagramm; Konzeptmatrix)

> Deine drei Suchdurchläufe (u. a. `noft(computer vision) AND noft((people OR person) counting)`,
> 68 Treffer / 15 relevant / 5 sehr relevant, 28.10.2025; sowie
> `noft(computer vision) AND noft(yolo) AND noft(realtime)`, 92 Treffer, 28.01.2026)
> gehören **hier gebündelt** hin — nicht verstreut über drei Kapitel. Die zwei nicht
> zugänglichen Paper (DSORT-MCU, YOLO-Drone) als Einschränkung dokumentieren.

### c. Stand der Forschung und Technik
- **i.** Theoretische und methodische Ansätze zur Personenzählung *(→ FF A)* — Kategorisierung nach Zählprinzip, Genauigkeit, Einsatzkontext
- **ii.** Sensortechnologien im Vergleich *(→ FF B)* — Lichtschranke, Infrarot, Ultraschall, LIDAR, Radar, WLAN-/BLE-Tracking, Computer Vision
- **iii.** Forschungslücke: kein direkt vergleichbarer CV-Zählsensor für kommunale, naturnahe Freiflächen (variable Lichtverhältnisse, mehrere gleichzeitige Bewegungsrichtungen, keine bauliche Engstelle wie eine Ladentür)

### d. Leistungsdefinition
- **i.** Funktionale Zielkriterien (Erkennung, Richtungs-/Musterunterscheidung, Konfigurierbarkeit)
- **ii.** Nicht-funktionale Zielkriterien (Datenschutz durch Edge-Verarbeitung, Robustheit, Bedienbarkeit ohne Kommandozeile, Anbindbarkeit an die UDP, Kosten)
- **iii.** Operationalisierung zu messbaren Zielgrößen — methodisch gestützt auf den Ultralytics-Leitfaden zur Zieldefinition in CV-Projekten

> Der Ultralytics-Guide stand im Entwurf unter Kapitel 3. Er gehört methodisch hierher:
> Er beschreibt das **Setzen messbarer Ziele**, also DSRM-Aktivität 2 — nicht das Design.

---

## 3. Design und Entwicklung
*DSRM Aktivität 2 (fallspezifisch konkretisiert) → Aktivität 3. Beantwortet FF C.*

Peffers et al. (2007: 55) halten fest, dass identifizierte Probleme sich nicht
automatisch in Ziele übersetzen. Abschnitt a–b vollenden deshalb Aktivität 2 für den
konkreten Fall; ab c beginnt Aktivität 3.

### a. Anwendungsfall Volkspark Biosphäre
Untersuchungsgegenstand, 17 Eingänge unterschiedlicher Geometrie, bauliche und
infrastrukturelle Rahmenbedingungen (kein WLAN/Festnetz vor Ort), Stakeholder.

### b. Anforderungsanalyse
- **i.** Methodik: qualitatives Experteninterview, halbstrukturiertes Leitfadeninterview nach Döring (2023: 360), Gütekriterien qualitativer Forschung *(bereits ausformuliert)*
- **ii.** Durchführung und Auswertung: Interview Stadtwerke Potsdam
- **iii.** **Konsolidierter Anforderungskatalog** — Zusammenführung der allgemeinen Kriterien aus 2.d mit den Interviewergebnissen; Priorisierung (Muss/Soll/Kann) und Zielwerte

> 3.b.iii ist die **Angelpunkt-Tabelle der ganzen Arbeit**: Sie ist das Ergebnis von
> Aktivität 2 und gleichzeitig der Bewertungsmaßstab in 5.c. Spalten:
> `Anforderung | Quelle (2.d / Interview) | Priorität | Zielwert`.

### c. Lösungsraum und Auswahl
- **i.** Produkt- und Technologierecherche: marktverfügbare Zählsensoren, vergleichbare CV-Projekte in anderen Anwendungsdomänen
- **ii.** Morphologisches Tableau: Teilfunktionen × Lösungsalternativen
- **iii.** Begründete Auswahl der Lösungskonfiguration

| Teilproblem | Alternativen | Gewählt |
|---|---|---|
| Erkennungsmodell | YOLO-Varianten, weitere CV-Modelle | YOLO (Hailo-optimiert) |
| Recheneinheit | Cloud-Inferenz, CPU-only, Edge-TPU, Hailo-8 | Raspberry Pi 5 + Hailo-8 (Edge → Datenschutz) |
| Zählprinzip | nur Linie, nur ROI, nur Mehrere Flächen | alle drei, wählbar |
| Konfiguration | nur manuell, nur automatisch | beides (manuell + zwei automatische Verfahren) |
| Übertragungsweg | WLAN, Mobilfunk, LoRaWAN | LoRaWAN (kein Festnetz/WLAN vor Ort nötig) |

### d. Ableitung des Zählprinzips
- **i.** Vorstudie: Erkennungsgüte von YOLO auf Beispielmaterial (Machbarkeitsnachweis vor dem Architekturentwurf)
- **ii.** Herleitung der drei Zählmodi — Begründung, warum ein einzelnes Prinzip bei 17 unterschiedlich geformten Eingängen nicht trägt
- **iii.** Herleitung des Bedarfs an manueller **und** automatischer Konfiguration (direkt aus 3.b.ii)

### e. Systemarchitektur (Konzept)
- **i.** Gesamtarchitektur: Single Network Pipeline auf Edge-Hardware *(Architekturdiagramm)*
- **ii.** Komponenten und Schnittstellen
- **iii.** Datenmodell und Datenflüsse — Nachweis Privacy by Design: keine Bilder, keine Positionsdaten verlassen das Gerät, nur aggregierte Zählwerte

---

## 4. Prototyping und Demonstration
*DSRM Aktivität 3 (Umsetzung) + Aktivität 4 (Demonstration). Beantwortet FF D.*

Design/Development und Demonstration sind hier bewusst in einem Kapitel zusammengefasst,
weil der reale Entwicklungsprozess iterativ zwischen beiden verlief — siehe 4.d.

### a. Hardwareaufbau
- **i.** Komponenten und Aufbau (Pi 5 8 GB, Hailo-8, Kamera, LoRa-Modul)
- **ii.** Sensorgehäuse, Montage, Energieversorgung *(Stand zum Abgabezeitpunkt ehrlich benennen)*

### b. Softwareentwicklung
- **i.** Modulare Umsetzung der Architektur aus 3.e
- **ii.** Einbindung des KI-Beschleunigers (Installation; gelöste Kernprobleme, u. a. klassengetrennte Tracker-IDs)
- **iii.** Implementierung der Zähllogik (drei Zählmodi)
- **iv.** Manuelle Konfiguration (visuelles Werkzeug für die Zählgeometrie)
- **v.** **Automatische Konfiguration** — datengetriebenes Clustering (DBSCAN) und Randraster-Verfahren mit Mindestbewegungsfilter
- **vi.** Bedienoberfläche (Bedienung ohne Kommandozeile — direkte Erfüllung einer Interview-Anforderung)
- **vii.** Datenhaltung: Exportformat und Schemastabilität als Robustheitsmaßnahme
- **viii.** Datenübertragung: Nachrichtenformat und Anbindungsarchitektur an die UDP

> 4.b.v ist dein **stärkster eigener Beitrag**: zwei alternative Verfahren, wobei das
> Randraster-Verfahren erst entstand, nachdem sich Clustering bei Tracking-Aussetzern
> als weniger robust erwies. Das ist eine belegbare, aus der Praxis abgeleitete
> Gestaltungsregel — entsprechend prominent schreiben, nicht als Fußnote.

### c. Testung
- **i.** Testung von Optimierungsparametern (Clustering-Radius, Rastersegmentierung, Bewegungsschwelle, Tracking-/Flush-Timing)
- **ii.** Funktionalitätstest der Einzelkomponenten
- **iii.** Labortest (kontrollierte Bedingungen, Testvideomaterial)
- **iv.** Realtest (Uni Potsdam als Zwischenschritt, anschließend Volkspark Biosphäre)

### d. Iterationen im Entwicklungsprozess
Dokumentierte Rücksprünge von Demonstration/Test zurück zu Design & Development
(Peffers et al. 2007: 56 betonen ausdrücklich die Nicht-Linearität des Prozesses).
Belegbare Beispiele: Diskrepanz zwischen Konfigurationsbild und Live-Betrieb;
Gerätekonflikt der Beschleuniger-Hardware durch Prozess-Timeout; Sackgasse bei der
LoRa-Hardware wegen proprietärer Schnittstelle.

> Dieser Abschnitt macht Methodentreue **sichtbar** statt die Iterationen zu verschweigen.
> Er ist billig zu schreiben (du hast alles dokumentiert) und wertet die Arbeit
> methodisch deutlich auf.

---

## 5. Evaluation und Kommunikation
*DSRM Aktivität 5 + 6.*

### a. Evaluationsdesign
- **i.** Einordnung nach FEDS (Venable, Pries-Heje & Baskerville 2016): Strategie *Technical Risk & Efficacy*; Verlauf von formativ/artificial (Labortest) zu summativ/naturalistic (Realtest)
- **ii.** Gütekriterien (Validität, Reliabilität, Objektivität nach Döring 2023), übertragen auf die Messgröße Zählgenauigkeit; Ground-Truth-Verfahren (manuelle Referenzzählung)
- **iii.** Metriken: absolute und relative Zählabweichung (MAE/MAPE), Genauigkeit der Übergangserkennung (Precision/Recall), Verarbeitungsrate (FPS), Laufzeitstabilität

> FEDS ist deine **Rückversicherung gegen den Zeitplan**: Wenn der Volkspark-Test
> ausfällt, ist eine rein artificial/formative Evaluation methodisch begründbar —
> aber nur, wenn du das Framework vorher eingeführt hast, nicht als nachträgliche
> Ausrede.

### b. Durchführung und Ergebnisse
- **i.** Ergebnisse Labortest (artificial)
- **ii.** Ergebnisse Realtest (naturalistic)

### c. Bewertung gegen den Anforderungskatalog
Soll-/Ist-Gegenüberstellung zu 3.b.iii: `Anforderung | Zielwert | gemessener Wert | erfüllt?`

### d. Bewertung von Datenübertragung und Datenschutzkonformität
Robustheit der UDP-Anbindung bzw. deren Stand zum Abgabezeitpunkt; Nachweis der
Einhaltung des Edge-/Privacy-by-Design-Ansatzes.

### e. Kommunikation
Wissenschaftlich (diese Arbeit selbst — Peffers et al. 2007: 56); praktisch
(Rückmeldung an Stadtwerke Potsdam und Betreuung als Entscheidungsgrundlage für
weitere Installationen); technisch (Repository und Dokumentation als übergabefähiges Artefakt).

---

## 6. Zusammenfassung, Fazit und offene Fragen

### a. Zusammenfassung der Ergebnisse
Geordnete Beantwortung von FF A–D.

### b. Wissenschaftlicher Beitrag
Einordnung nach Gregor & Hevner (2013): Die Arbeit ist eine **Exaptation** — eine
bekannte Lösungsklasse (Edge-basierte CV-Objekterkennung mit YOLO) wird auf eine
Problemdomäne übertragen, für die sie bislang nicht ausgearbeitet ist (kommunale,
naturnahe Freiflächen mit heterogenen, baulich offenen Zugängen). Ableitbare
Gestaltungsprinzipien: (1) mehrere parallel wählbare Zählprinzipien statt eines
universellen; (2) Kombination aus manueller und automatischer Geometriekonfiguration
zur Skalierung über viele Standorte; (3) Priorität offener über proprietäre
Übertragungsschnittstellen.

### c. Praktischer Beitrag
Entscheidungsgrundlage für die Stadtwerke Potsdam zur Installation weiterer Sensoren
(Rückbezug auf das Forschungsziel in 1.c).

### d. Limitationen
Stand der LoRaWAN-Hardwareanbindung zum Abgabezeitpunkt; Umfang und Dauer des
Realtests; nicht getestetes Verhalten bei Tag-/Nacht- und Wetterwechsel;
Verallgemeinerbarkeit von einem Standort auf 17.

### e. Offene Fragen und Ausblick
Skalierung auf alle 17 Eingänge; Langzeitbetrieb und Wartung; Anbindung weiterer
Sensortypen an dieselbe UDP-Infrastruktur.

---

## Anhänge
Literaturverzeichnis · Anhang (Interviewleitfaden, Konzeptmatrix der SLR,
Anforderungskatalog, Messprotokolle, Quellcode-Übersicht) · Ehrenwörtliche Erklärung

---

## Was sich gegenüber Version 1 (13.07.) geändert hat

1. **Grundlagenteil ergänzt** (2.a) — fehlte komplett; für eine WI-Bachelorarbeit nicht verzichtbar.
2. **Literaturrecherche konsolidiert** — war über 2.a, 3.b und 3.c verstreut; jetzt eine systematische Recherche mit Vorgehensmodell (vom Brocke et al. 2009; Webster & Watson 2002), Ein-/Ausschlusskriterien und Konzeptmatrix.
3. **Ultralytics-Guide verschoben** von Kapitel 3 nach 2.d.iii — er dient der Definition messbarer Ziele (Aktivität 2), nicht dem Design.
4. **Evaluations-Framework eingeführt** (5.a.i, FEDS) — statt eines reinen Ground-Truth-Vergleichs; liefert zugleich die methodische Absicherung, falls der Realtest zeitlich nicht mehr passt.
5. **Anwendungsfall als eigener Abschnitt** (3.a) — war vorher implizit.
6. **Hardwareaufbau als eigener Abschnitt** (4.a) — Gehäuse/Montage/Energie hatten bisher keinen Ort.
7. **Iterationskapitel eigenständig** (4.d) — vorher nur als Randbemerkung.
8. **Wissenschaftlicher Beitrag explizit benannt** (6.b, Gregor & Hevner 2013: Exaptation, plus drei Gestaltungsprinzipien) — fehlte; ohne diesen Abschnitt bleibt der Forschungsanspruch unbelegt.
