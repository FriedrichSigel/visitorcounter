# Statusbericht Bachelorarbeit

*Entwicklung eines Computer-Vision-basierten Sensors zur automatisierten Besucherzählung*

Vorbereitung für das Gespräch mit Betreuer und Projektpartner (Stadtwerke Potsdam) — Stand 02.07.2026

## 1. Aktueller Stand in Kürze

Die Arbeit folgt der Design Science Research Methodology (DSRM). Problemerkennung, Motivation, die systematische Literaturrecherche (drei Suchdurchläufe) und das Anforderungsinterview mit den Stadtwerken Potsdam sind abgeschlossen. Die Hardware- und Produktrecherche liegt vor (morphologisches Tableau, drei kalkulierte Lösungskonfigurationen). Der Software-Prototyp (YOLO-basierte Personenzählung auf Raspberry Pi 5 mit Hailo-8-Beschleuniger, inkl. Tracking- und Konfigurationslogik) läuft und wurde zuletzt im Juni weiterentwickelt. Offen sind: Sensorgehäuse, ggf. finale Hardware-Beschaffung, Labor-/Realtest, Evaluation sowie der komplette Schreibteil.

## 2. Vorläufige Gliederung

*Entwurf auf Basis der bisherigen Recherche und der DSRM-Struktur. Feedback vom Betreuer zu Umfang und Schwerpunkten ist ausdrücklich erwünscht.*

1. Einleitung
   1. Problemstellung und Motivation
   2. Zielsetzung und Forschungsfragen
   3. Aufbau der Arbeit
2. Grundlagen
   1. Computer Vision und Objekterkennung
   2. Personenzählung im technischen Kontext
   3. Design Science Research als methodischer Rahmen
3. Stand der Technik der Personenzählung
   1. Vorgehen der systematischen Literaturrecherche
   2. Theoretische und methodische Ansätze zur Personenzählung
   3. Aktueller technischer Standard von Personenzählsensoren
   4. Implikationen für die weitere Arbeit
4. Anforderungsanalyse
   1. Untersuchungsgegenstand und Anwendungsfall
   2. Methodik der Anforderungserhebung
   3. Ergebnisse der Experteninterviews
   4. Abgeleitete Leistungsanforderungen
5. Design und Entwicklung des Prototyps
   1. Produkt- und Technologierecherche
   2. Morphologisches Tableau und Lösungsauswahl
   3. Systemarchitektur
   4. Implementierung von Hardware und Software
6. Demonstration und Evaluation
   1. Testkonzept
   2. Labortest
   3. Realtest
   4. Bewertung anhand der Leistungsanforderungen
7. Zusammenfassung, Fazit und Ausblick
   1. Zusammenfassung der Ergebnisse
   2. Kritische Reflexion und Limitationen
   3. Ausblick

Literaturverzeichnis
Anhang
Ehrenwörtliche Erklärung

## 3. Status-Checkliste je Kapitel

**1 Einleitung**
- [x] Inhaltlich vorbereitet (Motivation, Anwendungsfall vorhanden)
- [ ] Text geschrieben

**2 Grundlagen**
- [ ] Inhaltlich vorbereitet (Begriffsklärung CV/YOLO aus Literatur zusammenstellen)
- [ ] Text geschrieben

**3 Stand der Technik (SLR)**
- [x] Inhaltlich vorbereitet (3 Suchdurchläufe abgeschlossen)
- [ ] Auswertung aus Notizen/Tabellen in Fließtext übertragen
- [ ] Text geschrieben

**4 Anforderungsanalyse**
- [x] Inhaltlich vorbereitet (Interview geführt und dokumentiert)
- [ ] Text geschrieben

**5 Design & Entwicklung**
- [x] Hardware-/Produktrecherche und morphologisches Tableau
- [x] Software-Prototyp läuft (Hailo/YOLO, Tracking-Pipeline)
- [ ] Gehäuse geklärt
- [ ] Finale Hardware-Beschaffung abgeschlossen
- [ ] Text geschrieben

**6 Demonstration & Evaluation**
- [x] Erste Performance-Tests vorhanden
- [ ] Labortest durchgeführt
- [ ] Realtest durchgeführt
- [ ] Text geschrieben

**7 Fazit & Ausblick**
- [ ] Inhaltlich vorbereitet (erst nach Abschluss der übrigen Kapitel möglich)
- [ ] Text geschrieben

## 4. Offene Fragen an den Betreuer

- [ ] Ist bei Zeitdruck eine Fokussierung auf den Labortest ausreichend, falls für einen Realtest im Volkspark kein Zeitfenster mehr vorhanden ist?
- [ ] Ist ein reduzierter Umfang beim Prototyping (z. B. eine statt mehrerer geplanter Iterationen) akzeptabel?
- [ ] Rückmeldung zur vorläufigen Gliederung – passt Schwerpunkt und Tiefe der Kapitel?
- [ ] Bestätigung des exakten Abgabetermins (Datum, Uhrzeit/Upload-Cutoff, Vorgaben zu Druck/Bindung)

## 5. Offene Punkte für den Projektpartner (Stadtwerke Potsdam)

- [ ] Stand der Hardware-Beschaffung/Anträge – wird die finale Hardware rechtzeitig verfügbar sein?
- [ ] Zeitfenster für einen Realtest im Volkspark Biosphäre in den nächsten zwei bis drei Wochen
- [ ] Anforderungen an das Sensorgehäuse (Wetterfestigkeit, Befestigung an den Eingängen)
- [ ] Feedback zu den vorgeschlagenen Lösungskonfigurationen (Preis/Hardware-Zusammenstellung)

## 6. Zeitplan bis zur Abgabe (Übersicht)

Detaillierter Wochenplan siehe separate Datei „Zeitplan_bis_Abgabe.xlsx". Annahme: Abgabetermin 31.07.2026 – bitte im Gespräch bestätigen.

**Diese Woche**
- [ ] Gliederung fertigstellen
- [ ] Checkliste fertigstellen
- [ ] Statusgespräch vorbereiten

**KW 28 (6.–12.7.)**
- [ ] Statusgespräch mit Betreuer und Stadtwerke
- [ ] Kapitel 1 schreiben
- [ ] Kapitel 2 schreiben
- [ ] Kapitel 3 schreiben

**KW 29 (13.–19.7.)**
- [ ] Kapitel 3 fertigstellen
- [ ] Kapitel 4 schreiben
- [ ] Gehäuse/Hardware klären
- [ ] Labortest durchführen

**KW 30 (20.–26.7.)**
- [ ] Kapitel 5 schreiben
- [ ] Kapitel 6 schreiben
- [ ] Realtest (falls möglich)

**KW 31 (27.–31.7.)**
- [ ] Kapitel 7 schreiben
- [ ] Literaturverzeichnis fertigstellen
- [ ] Formatierung prüfen
- [ ] Korrekturlesen
- [ ] Abgabe
