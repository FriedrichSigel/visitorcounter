# Gliederung – Entwicklung eines Computer-Vision-basierten Sensors zur automatisierten Besucherzählung

**Stand: 13.07.2026 — überarbeitet, um explizit entlang der sechs DSRM-Aktivitäten nach Peffers et al. (2007) zu laufen.**
Ersetzt/aktualisiert die Gliederung aus `Statusbericht_Gliederung_Checkliste.md`.

## Das Grundprinzip dieser Überarbeitung

Peffers et al. (2007) definieren sechs Aktivitäten für Design-Science-Research (DSR):
(1) Problem Identification and Motivation, (2) Define the Objectives for a Solution,
(3) Design and Development, (4) Demonstration, (5) Evaluation, (6) Communication —
plus den Hinweis, dass der Prozess in der Praxis **iterativ** verläuft (Figure 1,
"Process Iteration"-Pfeil zurück zu Design & Development) und dass es **vier mögliche
Einstiegspunkte** gibt: Problem-Centered, Objective-Centered, Design-&-Development-Centered,
und Client-/Context-Initiated.

**Dieses Projekt ist ein Lehrbuchbeispiel für den vierten Fall.** Genau wie im Digia-
Fallbeispiel der Autoren (Peffers et al., 2007, S. 67f.: *"In fall 2000, Digia Chairman
Pekka Sivonen approached one of the authors with a request..."*) kam der Anstoß von
einem externen Praxispartner mit einem konkreten, bereits vorhandenen Bedarf
(Stadtwerke Potsdam, Besucherzählung Volkspark Biosphäre) — nicht aus einer
Literaturlücke oder einem abstrakten Forschungsinteresse heraus. Diese Einordnung
gehört explizit in Kapitel 2.4/4.2 und liefert einen direkten, zitierfähigen
Vergleichspunkt zur Methodik-Quelle selbst.

**Die zweite methodische Besonderheit, die die Arbeit ehrlich abbilden sollte:**
Der tatsächliche Entwicklungsprozess verlief **nicht linear**, sondern mit sehr vielen
Iterationsschleifen zurück von Demonstration/Evaluation zu Design & Development —
genau das im DSRM-Prozessmodell explizit vorgesehene *"Process Iteration"* (Peffers
et al., 2007, Figure 1). Konkrete Beispiele aus dem Projekt (Kamera-Auflösungs-
Diskrepanz, Hailo-Geräte-Sperre, Spiegelungs-Bug, Kaltstart-Timeout) eignen sich sehr
gut, um diese Prozess-Iteration nicht nur zu behaupten, sondern an echten,
dokumentierten Beispielen zu belegen (Quelle dafür: die laufende `HANDOFF.md`, in der
jede Iteration mit Ursache/Fix protokolliert ist).

## Kapitel-zu-DSRM-Aktivität-Zuordnung (Überblick)

| Kapitel | DSRM-Aktivität(en) | Kurzbeschreibung |
|---|---|---|
| 1 Einleitung | Aktivität 1 (Teil 1) | Problem benennen, Relevanz zeigen |
| 2 Grundlagen | — (Wissensbasis für alle Aktivitäten) | Theoretischer Unterbau |
| 3 Stand der Technik (SLR) | Aktivität 1 (Teil 2) | Bestehende Lösungen, Lücke aufzeigen |
| 4 Anforderungsanalyse | Aktivität 2 | Ziele der Lösung definieren |
| 5 Design & Entwicklung | Aktivität 3 | Artefakt bauen |
| 6 Demonstration & Evaluation | Aktivität 4 + 5 | Artefakt einsetzen, messen |
| 7 Fazit | Aktivität 6 (Teil 1) | — |
| *(Die Arbeit als Ganzes)* | Aktivität 6 (Teil 2) | Kommunikation des Ergebnisses an die Fachcommunity |

---

## 1 Einleitung — *DSRM Aktivität 1 (Problem Identification and Motivation)*

### 1.1 Problemstellung
Manuelle/stichprobenartige Besucherzählung an öffentlichen Standorten (Volkspark
Biosphäre, 17 Eingänge) ist aufwendig, fehleranfällig, nicht kontinuierlich. Peffers
et al. (2007, S. 50f.) verlangen für Aktivität 1 explizit, *"to atomize the problem
conceptually so that the solution can capture its complexity"* — d. h. hier schon
andeuten, dass das Problem mehrere Teilprobleme enthält (Erkennung, Zählung an
mehreren Punkten gleichzeitig, Übertragung ohne Festnetz/WLAN vor Ort, Datenschutz).

### 1.2 Zielsetzung und Forschungsfragen
Formulierung der Forschungsfrage(n) so, dass sie direkt auf Kapitel 4 (Anforderungen)
und Kapitel 6 (Evaluation) zurückführbar sind — Peffers verlangt Konsistenz zwischen
Problemdefinition, Lösungszielen und späterer Bewertung.

### 1.3 Aufbau der Arbeit
Kurzer Absatz, der die DSRM-Aktivitäten explizit den folgenden Kapiteln zuordnet
(siehe Tabelle oben) — macht dem Leser/Betreuer die Methodik-Treue sofort sichtbar.

---

## 2 Grundlagen — *Wissensbasis*

### 2.1 Sensorik: Begriff, Aufbau, Signalarten
**Neue Quelle nutzbar:** Vorlesungsfolien "Sensorik im Produktionskontext" (Gronau,
Lehrstuhl WI, Uni Potsdam) liefern direkt zitierfähigen Inhalt für diesen Abschnitt:
- Sensorbegriff nach DIN 1319-1 und Heinrich et al. (2020): Sensor = Sensor-Element
  (Umwandlung nicht-elektrischer Eingangsgröße in elektrisches Signal) + Auswerte-
  Elektronik (Signalaufbereitung)
- Drei Signalarten (analog/digital/binär) nach Heinrich et al. (2020) — direkt
  relevant, da die Kamera ein analoges optisches Signal liefert, das über das
  YOLO-Modell letztlich in binäre Zählereignisse überführt wird
- Sensoraufbau im Detail (Messfühler → Messverstärker → Auswerteelektronik →
  Wandler → Netzwerkschnittstelle) — eignet sich als Referenzmodell, um das eigene
  System in 2.2/5.3 einzuordnen (Kamera+Hailo-8 = Messfühler/Sensor-Element,
  Tracking-/Zähllogik = Auswerteelektronik, geplante LoRa-Übertragung =
  Netzwerkschnittstelle)
- Einordnung als Cyber-Physisches System (CPS) und in die Automatisierungspyramide
  (Control Level → SCADA → MES → ERP) — nützlich, um einzuordnen, wo der eigene
  Sensor in einer größeren städtischen IoT-Infrastruktur (Urbane Datenplattform
  Potsdam) sitzen würde

### 2.2 Computer Vision und Objekterkennung
YOLO-Architektur, Edge-AI-Beschleuniger (Hailo-8), Multi-Objekt-Tracking-Grundlagen
(Track-IDs, Re-Identifikation-Problematik) — hier auch die *tatsächlich* im Projekt
gelöste Herausforderung als Vorgriff nennen: klassengetrennte Zuordnung von
Tracker-IDs (`hailotracker class-id=-1`, siehe 5.4).

### 2.3 Automatisierte Personenzählung
Etablierte Ansätze: Linienzählung, ROI-basierte Zählung, LIDAR/Ultraschall/Infrarot-
basierte kommerzielle Zähler als Kontrastfolie zum CV-Ansatz.

### 2.4 Design Science Research Methodology (DSRM)
**Zentrale neue Quelle:** Peffers, Tuunanen, Rothenberger & Chatterjee (2007), *"A
Design Science Research Methodology for Information Systems Research"*.
- Die sechs Aktivitäten (S. 54–56) mit Definition
- Die vier Forschungseinstiegspunkte (Figure 1) — mit Begründung, warum dieses
  Projekt **Client-/Context-Initiated** ist (Parallele zum Digia-Fall, S. 67f.)
- Der explizite Hinweis auf iterative statt strikt lineare Durchführung (S. 56,
  "there is no expectation that researchers would always proceed in sequential
  order") — Grundlage für die spätere kritische Reflexion in 7.2
- Abgrenzung zu Action Research (S. 71f., Diskussion Cole et al./Järvinen) — falls
  im Kolloquium gefragt, warum nicht Action Research: das Projekt hat einen klar
  abgrenzbaren Artefakt-Fokus (der Sensor selbst), nicht primär den
  Organisationskontext als Erkenntnisgegenstand

---

## 3 Stand der Technik (SLR) — *DSRM Aktivität 1, Fortsetzung*

### 3.1 Vorgehen der Literaturrecherche
Systematisches Vorgehen (3 Suchdurchläufe bereits abgeschlossen) — hier auf Döring
(2023) als methodische Absicherung des SLR-Vorgehens verweisen (Gütekriterien für
systematische Literaturrecherchen in den Sozial-/Humanwissenschaften).

### 3.2 Bestehende Ansätze zur automatisierten Personenzählung
Ergebnisse der Recherche, kategorisiert (z. B. nach Sensortyp, nach Zählprinzip).

### 3.3 Vergleich/Standard
Herausarbeiten, wo ein CV-basierter, edge-verarbeiteter Ansatz mit Hailo-8 steht
im Vergleich zu Cloud-basierten oder klassischen Sensor-Ansätzen.

### 3.4 Implikationen für die eigene Arbeit
Explizit die Forschungslücke benennen, die Aktivität 2 (Anforderungen) motiviert —
schließt den Bogen zu Aktivität 1.

---

## 4 Anforderungsanalyse — *DSRM Aktivität 2 (Define the Objectives for a Solution)*

Peffers et al. (2007, S. 55) verlangen hier: *"infer the objectives of a solution from
the problem definition and knowledge of what is possible and feasible"* — sowohl
quantitativ als auch qualitativ.

### 4.1 Anwendungsfall Volkspark Biosphäre
17 Eingänge, städtischer Kontext, Anbindung an Urbane Datenplattform Potsdam als
Zielbild.

### 4.2 Methodik der Anforderungserhebung
**Neue Quelle nutzbar:** Döring (2023) zur methodischen Fundierung des geführten
Experteninterviews (mit Titus Tomascik/Andreas Becker, Stadtwerke Potsdam) — Gütekriterien
qualitativer Interviews, Auswertungsverfahren. Hier auch explizit machen: dieses
Interview *ist* die konkrete Umsetzung von DSRM-Aktivität 2 in diesem Projekt.

### 4.3 Ergebnisse des Anforderungsinterviews
Manuelle Konfiguration vs. Auto-Konfiguration als genannter Bedarf — direkte Brücke
zu 5.4 (beide Ansätze wurden tatsächlich gebaut: DBSCAN-Clustering UND Randraster).

### 4.4 Leistungsanforderungen (konsolidiert)
Tabelle: funktionale Anforderungen (Multi-Klassen-Erkennung, mehrere Zählmodi,
Selbstkonfiguration, Datenübertragung ohne Festnetz) und nicht-funktionale
Anforderungen (Datenschutz — nur aggregierte Werte verlassen das Edge-Gerät,
Wetterfestigkeit, Energieversorgung). Diese Tabelle ist der direkte Soll-Zustand,
gegen den in 6.4 der Ist-Zustand (Evaluation) gespiegelt wird.

---

## 5 Design & Entwicklung — *DSRM Aktivität 3 (Design and Development)*

Peffers et al. (2007, S. 55): *"determining the artifact's desired functionality and
its architecture and then creating the actual artifact"* — dieses Kapitel ist mit
Abstand das umfangreichste, da hier praktisch die gesamte technische Arbeit
dokumentiert wird. Empfehlung: als **Artefakt-Katalog** strukturieren (mehrere
Teilartefakte, die zusammen den Sensor bilden), das entspricht auch Hevner et al.'s
(in Peffers et al. zitierte) Definition, dass Artefakte "constructs, models, methods,
or instantiations" sein können — hier liegen alle vier Typen tatsächlich vor.

### 5.1 Produktrecherche und Technologieauswahl
Raspberry Pi 5 + Hailo-8 als Hardwareplattform, Begründung.

### 5.2 Morphologischer Kasten
Systematische Betrachtung der Lösungsalternativen (Zählprinzipien, Konfigurations-
ansätze, Übertragungswege) — Brücke zwischen 4.4 und 5.3.

### 5.3 Systemarchitektur
Gesamtüberblick der Softwarearchitektur (Modul-Diagramm empfohlen):
`core.py`/`tracking.py`/`counting.py`/`visualization.py`/`logging_utils.py`/
`csv_utils.py`/`config.py` als Pipeline-Kern, `app.py`/`roi_config_app.py` als
Bedienoberfläche, `auto_config.py`/`auto_config_clustering.py` als
Auto-Konfigurations-Subsystem.

### 5.4 Implementierung — Konstrukte, Modelle, Methoden, Instanziierungen
Empfohlene Unterstruktur (spiegelt den tatsächlichen Entwicklungsverlauf, jeweils
mit **Status** kennzeichnen: ✅ fertig / 🔧 vorbereitet, Hardware ausstehend):

- **5.4.1 Objekterkennung und Multi-Klassen-Tracking** ✅ — Hailo-8/YOLO-Pipeline,
  klassengetrennte Tracker-IDs, Race-Condition-Fix in `finalize()`
- **5.4.2 Zähllogik** ✅ — drei Modi (Linie, ROI, Mehrere-Flächen-Übergänge),
  `snap_to_nearest`, "Kein Wechsel"-Protokollierung (`is_transition`)
- **5.4.3 Manuelle Konfiguration** ✅ — `roi_config_app.py`, visuell, per Mausklick
- **5.4.4 Automatische Konfiguration** ✅ — **zwei eigenständige Verfahren**, das ist
  ein eigener, hervorhebenswerter Beitrag: DBSCAN-Clustering (datengetrieben) UND
  Randraster-Verfahren mit Mindestbewegungs-Filter (robuster gegenüber
  Tracking-Aussetzern — Design-Entscheidung mit Begründung aus der Praxis
  dokumentieren, das ist genau die Art von "grounded technological rule" (van Aken,
  in Peffers et al. zitiert), die DS-Forschung liefern soll)
- **5.4.5 Bedienoberfläche** ✅ — zentrale App (`app.py`, CustomTkinter,
  Sidebar-Navigation), bündelt den gesamten Arbeitsablauf ohne Kommandozeile
- **5.4.6 Datenhaltung und Schema-Sicherheit** ✅ — CSV-Exportformat, automatische
  Schema-Drift-Erkennung (`csv_utils.py`) als eigenständiger, robustheitsrelevanter
  Beitrag (mit dem *echten* gefundenen Datenfehler als Beleg, siehe 6.4/7.2)
  **Datenschutz-Design**: nur aggregierte Zählwerte werden für die Übertragung
  vorgesehen (siehe 5.4.7), keine Bilder/Positionen verlassen das Edge-Gerät
- **5.4.7 Datenübertragung (LoRaWAN)** 🔧 — Nachrichtenformat und
  Software-Architektur entworfen und getestet (kompaktes Binärformat, passend zu
  LoRaWAN-Nutzlastgrenzen), Hardware-Beschaffung zum Zeitpunkt der Abgabe ggf. noch
  nicht abgeschlossen — **wichtig: als bewusste Grenze des Artefakts zum
  Abgabezeitpunkt dokumentieren, nicht verschweigen** (siehe 7.2)

---

## 6 Demonstration & Evaluation — *DSRM Aktivität 4 + 5*

Peffers et al. (2007, S. 55f.) trennen bewusst Demonstration (*"use of the artifact
to solve one or more instances of the problem"*) von Evaluation (*"observe and
measure how well the artifact supports a solution"*) — beide Aktivitäten sollten
auch in der Arbeit als klar getrennte Abschnitte erscheinen, nicht vermischt werden.

### 6.1 Testkonzept
**Neue Quelle nutzbar:** Döring (2023) zur methodischen Fundierung des
Evaluationsdesigns (Gütekriterien: Validität, Reliabilität, Objektivität — auf die
Zählgenauigkeit als Messgröße übertragen).

### 6.2 Labortest (Demonstration, kontrollierte Bedingungen)
Testvideo-basierte Verifikation — hier gehört die (laut letztem Stand noch
ausstehende) systematische Verifikation der Kreuzungserkennung mit bekannter
Ground Truth hinein (siehe `ToDo.md`, aktuell höchste Priorität).

### 6.3 Realtest (Demonstration, reale Bedingungen)
Geplanter Testtermin an der Uni Potsdam (Vorschlag an Betreuer bereits kommuniziert)
als Zwischenschritt vor dem eigentlichen Einsatzort Volkspark Biosphäre — beide als
zwei separate Demonstrationsinstanzen dokumentieren, falls zeitlich beide
stattfinden.

### 6.4 Bewertung (Evaluation)
Abgleich der Ergebnisse aus 6.2/6.3 gegen die Leistungsanforderungen aus 4.4 —
tabellarische Gegenüberstellung empfohlen (Anforderung | Zielwert | gemessener
Wert | erfüllt?). Hier auch qualitative Evaluationsergebnisse einordnen, die schon
vorliegen: die *gelösten* technischen Probleme (Kamera-Auflösungs-Bug,
CSV-Schema-Drift, Hailo-Geräte-Sperre) sind selbst verwertbare Evaluationsbefunde
im Sinne von Peffers' *"any appropriate empirical evidence"* (S. 56) — sie zeigen,
dass das iterative Test-Fix-Vorgehen (Prozess-Iteration, siehe Einleitung dieser
Gliederung) tatsächlich funktioniert hat.

---

## 7 Zusammenfassung, Fazit, Ausblick — *DSRM Aktivität 6, Teil 1*

### 7.1 Zusammenfassung
Kurzer Rückblick über alle sechs DSRM-Aktivitäten, mit expliziter Nennung, welche
zum Abgabezeitpunkt vollständig durchlaufen wurden und welche (z. B. Aktivität 5 für
den LoRaWAN-Teilartefakt) noch offen sind.

### 7.2 Limitationen und kritische Reflexion
Hierhin gehören konkret:
- Die bewusst noch offene LoRaWAN-Hardware-Frage (Sonel-Sackgasse als
  dokumentiertes, methodisch interessantes Negativergebnis — proprietäre
  USB-Geräteklasse ohne öffentliche Dokumentation, guter Beleg für die reale
  Schwierigkeit der Anforderung "einfache Beschaffbarkeit")
- Bekannte technische Grenzen (Kreuzungserkennung noch nicht mit Ground-Truth-Daten
  verifiziert, `track_id`-Fallback-Kollisionsrisiko, fehlendes Verhalten bei
  Tag/Nacht-Wechsel)
- Methodische Reflexion: War der Client-/Context-initiierte Einstieg (siehe 2.4)
  im Rückblick der richtige Weg? Wie hat sich die Prozess-Iteration (viele
  Fix-Zyklen) auf den Zeitplan ausgewirkt?

### 7.3 Ausblick
LoRaWAN-Hardware-Integration nach Beschaffung, Skalierung auf alle 17 Eingänge,
Langzeitbetrieb/Wartungskonzept.

---

## Hinweis zur Aktivität 6 (Communication) insgesamt

Peffers et al. (2007, S. 56) verstehen "Communication" nicht als eigenes Kapitel,
sondern als Eigenschaft der **gesamten Arbeit**: *"researchers might use the
structure of this process to structure the paper"* — genau das leistet diese
überarbeitete Gliederung bereits durch die durchgängige DSRM-Zuordnung. Für das
Kolloquium/die Verteidigung empfiehlt sich, die Tabelle vom Anfang dieses Dokuments
als eine der ersten Folien zu verwenden — sie macht die Methodik-Treue der Arbeit
sofort sichtbar, ohne dass man sie erst mühsam erklären muss.
