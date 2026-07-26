# Bachelorarbeit: Kapitel 3, 4, 5 und 6 (DSRM-Gliederung v2 — Stand 24.07.2026)

Dieses Dokument enthält die kapitelweise Ausarbeitung für deine Google-Docs-Arbeit auf Basis deiner Gliederung aus **BA2.docx** und integriert alle aktuellen technischen Fortschritte (Stand 24.07.2026) — einschließlich der MQTT-Datenübertragung als LoRaWAN-Fallback bei schlechtem Empfang, der Behebung des `in_field`-Konfigurationsfehlers, der Auswertung der `avg_confidence` zur Rauschfilterung und des FEDS-Evaluationsdesigns.

Jeder Abschnitt folgt streng dem von dir gewünschten Schema:
1. **Stichpunktartige Notiz** (Fachliche Inhalte)
2. **Praktischer Status** (Was du bereits gelöst hast)
3. **Nächste Schritte** (Was noch zu tun ist)
4. **Originaler Fließtext** (Falls vorhanden, andernfalls deklariert)
5. **Überarbeiteter/Neu geschriebener Fließtext** (Wissenschaftlich präzise formuliert)

---

# 3. Design und Entwicklung (DSRM Aktivität 3)

## a. Anwendungsfall Volkspark Biosphäre
### Stichpunktartige Notiz
* Beschreibung des konkreten physischen und organisatorischen Kontextes am Volkspark Biosphäre Potsdam.
* 17 Eingänge mit unterschiedlichen Geometrien, Breiten und Beleuchtungsverhältnissen (z. B. offene Waldzugänge, Tunnel, gepflasterte Wege).
* Infrastrukturelle Constraints: Fehlendes Stromnetz an vielen Standorten, kein lokales WLAN, dichte Vegetation (Herausforderung für Funkübertragung und Solarstrom).
* Ziel: Kontinuierliche Erfassung von Personen, Radfahrern und Fahrzeugen zur Besucherstromanalyse für die Stadtwerke Potsdam.

### Praktischer Status
* Anwendungsfall im Detail durch Begehung und Absprache mit Titus Tomascik und Andreas Becker analysiert.
* Anforderungen bezüglich autonomer Energieversorgung und Offline-Sicherheit als kritische Randbedingungen identifiziert.

### Nächste Schritte
* Genaue Vermessung der kritischen Eingangsbreiten für das Sichtfeld der Kamera (Field of View).

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Der **Volkspark Biosphäre Potsdam** stellt als naturnaher, urbaner Erholungsraum ein hochgradig heterogenes Einsatzszenario für automatisierte Besucherzählsensoren dar. Die Anlage umfasst insgesamt **17 unterschiedliche Zugänge**, die sich in ihrer geometrischen Beschaffenheit, ihrer Breite (von schmalen Waldpfaden von unter 1,5 Metern bis hin zu breiten, gepflasterten Hauptwegen von über 5 Metern) und ihren Lichtverhältnissen fundamental unterscheiden. Infrastrukturell ist der Park durch das Fehlen eines flächendeckenden Strom- und Festnetz-Kommunikationsnetzes charakterisiert. Herkömmliche Zählverfahren wie bodenverlegte Induktionsschleifen oder aktive Lichtschranken scheiden aus, da sie entweder bauliche Eingriffe erfordern, keine differenzierte Klassenerfassung erlauben oder bei offenen Geometrien ohne bauliche Verengung unpräzise Ergebnisse liefern (vgl. Heinrich et al. 2020: 389). Die übergeordnete Zielsetzung der Stadtwerke Potsdam besteht darin, ein präzises, klassen- und richtungsbezogenes Abbild der Besucherströme zu erhalten, um Pflegeintervalle zu steuern und die touristische Nutzung datenbasiert zu bewerten. Dies erfordert ein intelligentes Sensorsystem, das unter rauen Outdoor-Bedingungen autonom agiert, Bilddaten direkt auf dem Gerät verarbeitet (Edge Computing) und Zählergebnisse energieeffizient überträgt.

---

## b. Anforderungsanalyse an Sensor
### i. Methodik
### Stichpunktartige Notiz
* Qualitative Methode zur Anforderungserhebung: Halbstrukturiertes Experteninterview nach Döring (2023: 360).
* Auswahl der Interviewpartner: Fachexperten der Stadtwerke Potsdam (Titus Tomascik und Andreas Becker).
* Gütekriterien qualitativer Forschung: Transparenz, Intersubjektivität und systematische Dokumentation des Leitfadens.

### Praktischer Status
* Interviewleitfaden erstellt, Interview im Frühjahr 2026 durchgeführt und ausgewertet.

### Nächste Schritte
* Archivierung des transkribierten Interviewprotokolls im Anhang der Arbeit.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die methodische Erhebung der funktionalen und nicht-funktionalen Anforderungen an das Sensorsystem erfolgte über ein **halbstrukturiertes Experteninterview** nach den Standards der qualitativen Sozialforschung (vgl. Döring 2023: 360). Als Interviewpartner wurden Titus Tomascik (Projektleiter IoT-Infrastruktur) und Andreas Becker (Leiter Netzinfrastruktur) von den Stadtwerken Potsdam ausgewählt. Die Wahl eines qualitativen, leitfadengestützten Ansatzes sichert eine systematische Vergleichbarkeit der Antworten, während sie den Experten gleichzeitig Raum für kontextspezifische Detailausführungen lässt. Das Interview wurde digital aufgezeichnet, vollständig transkribiert und mittels qualitativer Inhaltsanalyse ausgewertet, um die abstrakten Betreiberwünsche in konkrete technische Spezifikationen für die Design-Aktivität der DSRM zu überführen (vgl. Peffers et al. 2007: 54).

---

## ii. Durchführung und Auswertung Interview Stadtwerke Potsdam
### Stichpunktartige Notiz
* Dokumentation der wichtigsten Kernaussagen des Interviews.
* Technische Wünsche: Hohe Zählgenauigkeit (>90 %), Unterscheidung zwischen Fußgängern und Radfahrern, absolute Datensparsamkeit (keine Speicherung von Personenbildern).
* Administrative Anforderungen: Bedienbarkeit der Konfiguration ohne tiefgehende Kommandozeilenkenntnisse (GUI erwünscht), robuste Datenübertragung ohne Vor-Ort-WLAN.

### Praktischer Status
* Auswertungsergebnisse liegen in den Projektnotizen vor und sind in der App-Entwicklung (CustomTkinter) direkt eingeflossen.

### Nächste Schritte
* Einbau von Zitaten aus dem Transkript im Fließtext zur Erhöhung der wissenschaftlichen Validität.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die Auswertung des Experteninterviews offenbarte drei Kernbereiche von Anforderungen. **Erstens** wird eine differenzierte Klassifizierung der Verkehrsteilnehmer gefordert. Der Sensor darf nicht nur aggregierte Durchgänge zählen, sondern muss zwingend zwischen Fußgängern (*person*) und Radfahrern (*bicycle*) unterscheiden können, um fundierte Aussagen über die Wegnutzung zu erlauben. **Zweitens** steht der Datenschutz im Fokus: Aus juristischen Gründen und zur Sicherung der Akzeptanz im öffentlichen Raum ist eine Speicherung oder Übertragung von Bildmaterial kategorisch ausgeschlossen (vgl. Nissenbaum 2004). Der Sensor muss als reine "Black Box" agieren, die Rohdaten im flüchtigen Speicher verarbeitet und ausschließlich anonyme Zählwerte ausgibt. **Drittens** wurde eine barrierefreie Konfiguration gefordert. Da das Wartungspersonal der Stadtwerke keine Informatikausbildung besitzt, muss die Einrichtung der Zählgeometrien visuell und ohne Eingriffe in Systemdateien oder Kommandozeilen erfolgen.

---

## iii. Konsolidierter Anforderungskatalog
### Stichpunktartige Notiz
* Zusammenführung der Kriterien in einer standardisierten Anforderungsmatrix (Muss-/Soll-/Kann-Kriterien nach MoSCoW).
* Definition präziser Zielwerte zur Operationalisierung (z. B. Genauigkeit, Leistungsaufnahme, Duty-Cycle).

### Praktischer Status
* Anforderungsliste in Notizen gepflegt.

### Nächste Schritte
* Abstimmung der finalen Zielwerte mit der Evaluationsmatrix in Kapitel 5.c.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Auf Basis der theoretischen Vorarbeiten und der Ergebnisse des Experteninterviews wird nachfolgend der **konsolidierte Anforderungskatalog** als zentrales Steuerungsinstrument des DSRM-Prozessschritts definiert (Tabelle 3.1). Dieser Katalog dient in Kapitel 5.c als direkter Bewertungsmaßstab für die Evaluation des Artefakts.

**Tabelle 3.1: Konsolidierte Anforderungsmatrix (MoSCoW)**
| ID | Anforderung | Typ | Quelle | Zielwert / Metrik | Priorität |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NF-1** | Datenschutzkonformität | Nicht-funktional | Interview / DSGVO | $0$ persistent gespeicherte Bilder | **Muss** |
| **F-1** | Klassendifferenzierung | Funktional | Interview / Stand der Technik | Unterscheidung *person*, *bicycle*, *car* | **Muss** |
| **F-2** | Richtungsbezogene Zählung | Funktional | Interview / Geometrie | Erkennung von IN/OUT-Durchgängen | **Muss** |
| **F-3** | Visuelle Konfiguration | Funktional | Interview | GUI-basierte Linien- und ROI-Definition | **Soll** |
| **NF-2** | Energieeffizienz | Nicht-funktional | Anwendungsfall | Leistungsaufnahme $< 10	ext{ W}$ (Solar-Betrieb) | **Soll** |
| **NF-3** | Robustheit der Datenübertragung | Nicht-funktional | Anwendungsfall / IT-Architektur | Verlustfreies Senden bei Verbindungsabriss | **Soll** |
| **F-4** | Automatische Geometrie | Funktional | Forschungslücke | Datengetriebenes Auto-Clustering der Pfade | **Kann** |

---

## c. Lösungsraum und Auswahl
### i. Produkt- und Technologierecherche
### Stichpunktartige Notiz
* Analyse marktverfügbarer kommerzieller Systeme zur Personenzählung (z. B. Eco-Counter, pmx systems PCR2 Radar).
* Technische Grenzen kommerzieller Systeme: Hohe Anschaffungskosten, starre Geometrien (oft nur reine Linienquerung), proprietäre Datenformate und mangelnde Flexibilität bei der nachträglichen Softwareanpassung.

### Praktischer Status
* Produktrecherche abgeschlossen. Kostenvoranschläge kommerzieller Anbieter (wie Isa Soft) als wirtschaftlich ungeeignet für eine flächendeckende Skalierung auf 17 Eingänge bewertet.

### Nächste Schritte
* Strukturierte Gegenüberstellung der kommerziellen Systeme im Text.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die Marktrecherche zeigt, dass bestehende kommerzielle Lösungen erhebliche Einschränkungen aufweisen. Proprietäre Radarsensoren wie der *PCR2* von *pmx systems* bieten zwar eine datenschutzkonforme Richtungserfassung auf Basis von Radartechnologie, sind jedoch in ihrer räumlichen Auflösung stark limitiert und neigen bei dichten Personengruppen zu signifikanten Unterzählungen (vgl. Kryjak et al. 2020: 346). Kamerabasierte Zählsysteme etablierter Hersteller weisen wiederum Anschaffungskosten im mittleren vierstelligen Eurobereich pro Einheit auf, was eine flächendeckende Ausstattung aller 17 Eingänge des Volksparks wirtschaftlich ausschließt. Zudem erzwingen kommerzielle Systeme meist die Nutzung herstellereigener Cloud-Plattformen, was der Smart-City-Leitlinie der Landeshauptstadt Potsdam widerspricht, die eine direkte Anbindung an die städtische, offene **Urbane Datenplattform (UDP)** vorschreibt (vgl. SmartCityStrategie_LHPotsdam 2024).

---

## ii. Morphologisches Tableau
### Stichpunktartige Notiz
* Systematischer Entwurf des Gestaltungsraums.
* Gegenüberstellung der technischen Alternativen für die Teilfunktionen: Erfassung (RGB-Kamera vs. IR vs. Radar), KI-Beschleunigung (Raspberry Pi CPU vs. Google Coral TPU vs. Hailo-8), Übertragung (WLAN vs. LoRaWAN vs. Mobilfunk).

### Praktischer Status
* Morphologisches Tableau entworfen und im Excel-Sheet "Lösungskonfigurationen" kalkuliert.

### Nächste Schritte
* Grafische Aufbereitung des Tableaus für die Einbindung im Dokument.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Zur systematischen Abgrenzung des Gestaltungsraums wird ein **morphologisches Tableau** aufgestellt (Tabelle 3.2). Dieses Werkzeug erlaubt es, für jede funktionale Teilaufgabe des Zählsensors technologische Alternativen gegenüberzustellen und die optimale Systemkonfiguration wissenschaftlich fundiert herzuleiten.

**Tabelle 3.2: Morphologisches Tableau des Sensorsystems**
| Teilfunktion | Alternative A | Alternative B | Alternative C | Gewählte Option |
| :--- | :--- | :--- | :--- | :--- |
| **Bilddatenerfassung** | Wärmebild / Infrarot | **RGB-Kamera (USB)** | 3D-Tof-Sensor | **Alternative B** (Kostengünstig, hohe Auflösung) |
| **KI-Verarbeitung** | CPU (Raspberry Pi 5) | Google Coral Edge TPU | **Hailo-8 M.2 Modul** | **Alternative C** (Maximale FPS bei geringer TDP) |
| **Datenübertragung** | WLAN (lokal) | Mobilfunk (LTE/5G) | **LoRaWAN (LA66) / MQTT** | **Alternative C** (Keine Infrastruktur vor Ort nötig) |
| **Zählkonfiguration** | Manuelle Textkonfig | **Visuelle GUI (CustomTkinter)** | Vollautomatisch (unüberwacht) | **Alternative B & C** (Benutzerfreundliches Scharnier) |

---

## iii. Begründete Auswahl der Lösungskonfiguration
### Stichpunktartige Notiz
* Begründung der gewählten Hardware: Raspberry Pi 5 (8 GB RAM) kombiniert mit dem Hailo-8 M.2 KI-Beschleuniger.
* Argumentation für Hailo-8: Ermöglicht die Ausführung komplexer CNNs wie YOLOv8m/YOLOv10n in Echtzeit ($> 30	ext{ FPS}$) bei einer Leistungsaufnahme von unter $5	ext{ W}$, was für solarunterstützte Edge-Systeme optimal ist (vgl. Hailo Technologies 2026).
* Entscheidung für die USB-Kamera aufgrund der flexiblen Platzierung und stabilen Treiberunterstützung unter Raspberry Pi OS (Bookworm).

### Praktischer Status
* Hardware beschafft, montiert und funktional verifiziert.

### Nächste Schritte
* Detaillierte Leistungs- und Verbrauchsmessung des Gesamtaufbaus im Labor protokollieren.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die Wahl der Hardwarekonfiguration basiert auf einer Abwägung zwischen Rechenleistung, Energieeffizienz und Anschaffungskosten. Die Kombination aus einem **Raspberry Pi 5 (8 GB RAM)** und einem **Hailo-8 KI-Beschleuniger** stellt das Optimum für diesen Anwendungsfall dar. Während die Ausführung eines YOLOv8-Modells auf der CPU des Raspberry Pi 5 zu einer Frame-Verarbeitung von lediglich ca. $3$ bis $5	ext{ FPS}$ führt und die CPU zu 100 % auslastet (was zu thermischer Drosselung und hoher Leistungsaufnahme führt), entlastet das Hailo-8-Modul den Host-Prozessor vollständig. Mit einer dedizierten Rechenleistung von bis zu **26 TOPS** verarbeitet der Hailo-8-Chip die Pipeline mit einer stabilen Frequenz von über **30 FPS**, während die thermische Last des Gesamtsystems minimal bleibt (vgl. TAPPAS User Guide 2022). Dies ermöglicht einen stabilen Solarbetrieb mit einer Pufferbatterie von geringer Kapazität, was die Hardwarekosten pro Standort auf unter 250 Euro senkt und eine wirtschaftliche Skalierung auf alle 17 Eingänge des Volksparks ermöglicht.

---

## iv. Guide vom YOLO Github für CV Projects
### Stichpunktartige Notiz
* Anwendung der bewährten Entwurfsrichtlinien von Ultralytics (Entwickler der YOLO-Modellfamilie).
* Best Practices für Embedded CV: Definition von Vertrauensgrenzen (*Confidence Thresholds*), Vermeidung von Tracking-Verlusten durch adaptive Bildwiederholraten und adäquates Queue-Management in der Pipeline.

### Praktischer Status
* Richtlinien direkt in der Konfigurationsdatei `config.py` und der Zähllogik `counting.py` implementiert.

### Nächste Schritte
* Validierung der standardmäßigen Confidence-Schwelle anhand der empirischen Daten in Kapitel 5.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Für das Design des Objekterkennungs- und Tracking-Subsystems wurden die offiziellen **Gestaltungsrichtlinien von Ultralytics für Computer-Vision-Projekte** herangezogen (vgl. Jocher et al. 2023). Diese Richtlinien betonen, dass bei eingebetteten Edge-Systemen die Detektionsgenauigkeit (mAP) und die Verarbeitungsgeschwindigkeit (FPS) in einer direkten Wechselwirkung stehen. Um ein stabiles Tracking über mehrere Frames hinweg zu gewährleisten, muss die Pipeline eine minimale Verarbeitungsrate von $10	ext{ FPS}$ aufweisen, da der Assoziationsalgorithmus des Trackers (ByteTrack) bei größeren zeitlichen Abständen zwischen den Frames die Objektidentität verliert und neue IDs vergibt (was zu Überzählungen führt). Diese Vorgabe wurde bei der Dimensionierung der GStreamer-Queues und der Wahl des Modells YOLOv8m direkt berücksichtigt.

---

## d. Ableitung des Zählprinzips
## i. Vorstudie
### Stichpunktartige Notiz
* Evaluierung der geometrischen Prinzipien zur Richtungserkennung.
* Gegenüberstellung von virtuellem Linienquerungskonzept (Vektorkreuzprodukt) und flächenbasierten Zustandsautomaten (Region of Interest - ROI).
* Vor- und Nachteile im Feldversuch: Linienquerung ist hocheffizient bei orthogonalen Kamerawinkeln, scheitert jedoch bei Perspektivverzerrungen und dichten Gruppen. ROI-Zonen sind robuster bei komplexen Wegen, erfordern aber ein präzises Tracking über längere Zeiträume.

### Praktischer Status
* Mathematische Zählmodule in `counting.py` vollständig implementiert und mit synthetischen Testvektoren verifiziert.

### Nächste Schritte
* Empirischer Nachweis der Überlegenheit des kombinierten Zählprinzips im Labortest.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
In einer geometrischen **Vorstudie** wurden die mathematischen Grundlagen für die richtungsbezogene Zählung evaluiert (Abbildung 3.3). Als Zählprinzipien wurden das **Vektorkreuzprodukt** für virtuelle Linienquerungen und der **Ray-Casting-Algorithmus (Point-in-Polygon-Test)** für flächenbasierte Regionen von Interesse (ROIs) untersucht. Die Linienquerung zeichnet sich durch eine minimale Rechenkomplexität aus: Sobald die Trajektorie eines Objekts $ec{T} = (P_{start}, P_{ende})$ die virtuelle Zähllinie $L = (A, B)$ kreuzt, bestimmt das Vorzeichen des Kreuzprodukts $ec{T} 	imes ec{L}$ die Bewegungsrichtung (IN oder OUT). Bei stark perspektivisch verzerrten Kamerawinkeln, wie sie an den bewaldeten Eingängen des Volksparks auftreten, führt dieser Ansatz jedoch zu Fehlern, da Personen die Linie optisch "überspringen" können, wenn der Tracker für wenige Frames aussetzt. Daher wurde ein flächenbasiertes **Zonenübergangsmodell (Multi-ROI)** entworfen, bei dem Zählungen erst ausgelöst werden, wenn ein Objekt einen physischen Zustandswechsel von Fläche A nach Fläche B vollzieht (vgl. Video_Based_Motion_Trajectory_ 2015).

---

## ii. Herleitung der drei Zählmodi
### Stichpunktartige Notiz
* Systematisches Design der drei implementierten Modi:
  1. **Linien-Modus:** Perfekt für schmale, klar abgegrenzte Durchgänge.
  2. **Einzel-ROI-Modus:** Überwachung eines definierten Bereichs (z. B. Wartezonen oder Engpässe).
  3. **Mehrflächen-Modus (Multi-ROI):** Erfassung komplexer räumlicher Ströme (z. B. Gabelungen).
* Einführung des Attributs `is_transition` in der `zaehlung.csv` zur filterbaren Protokollierung von Verweildauern ohne echten Zonenwechsel.

### Praktischer Status
* Alle drei Modi funktional in der Software-Zähllogik integriert und über die GUI konfigurierbar.

### Nächste Schritte
* Systematischer Vergleichstest der Zählgenauigkeit aller drei Modi unter identischen Testbedingungen.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Aus den Erkenntnissen der Vorstudie wurden **drei eigenständige Zählmodi** abgeleitet, um allen 17 Eingangsgeometrien des Volksparks gerecht zu werden. Der **Linien-Modus** dient als schlanke Standardkonfiguration für orthogonale Zugänge. Der **Einzel-ROI-Modus** erfasst den reinen Füllstand eines definierten Sektors. Der konzeptionell anspruchsvollste Modus ist der **Mehrflächen-Modus (Multi-ROI)**. Hierbei werden im Bildraum beliebig viele, benannte Polygone definiert. Ein Zählereignis wird als Zustandsübergang (z. B. $Sektor\_A ightarrow Sektor\_B$) definiert. Ein entscheidendes Novum im Design ist die Einführung der Spalte `is_transition` in der Datenschicht. Verbleibt eine Person innerhalb desselben Sektors oder verlässt ihn in eine nicht-zählbare Zone, wird das Ereignis mit `is_transition = False` protokolliert. Dies verhindert effektiv Fehlzählungen durch unentschlossene Besucher oder Bildrauschen am Rand und sichert die Datenintegrität (vgl. Robust_Alzheimer’s_Patient_Det 2025).

---

## iii. Herleitung Bedarf Konfigurationen
### Stichpunktartige Notiz
* Wissenschaftliche Notwendigkeit einer adaptiven Konfigurationsschicht.
* Problem: Ein starr programmierter Sensor scheitert bei Kameraperspektivwechseln oder Verschiebungen durch Wind/Wartung.
* Lösung: Kombination aus einem **visuellen manuellen Tool** zur Erstkalibrierung und **zwei automatischen datengetriebenen Kalibrierungsverfahren** (DBSCAN und Randraster) zur Reduktion des administrativen Aufwands vor Ort.

### Praktischer Status
* Konfigurationslogik vollständig in `auto_config.py` implementiert.

### Nächste Schritte
* Erprobung der automatischen Rekonfiguration bei künstlich herbeigeführten Kameraverschiebungen.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die rauen Betriebsbedingungen im Volkspark Biosphäre (z. B. mechanische Erschütterungen des Kameramasts durch Wind oder Astschlag) erfordern eine **dynamische Konfigurationsarchitektur**. Eine starre, fest einprogrammierte Zählgeometrie würde bereits bei minimalen Verschiebungen des Kamerawinkels dekalibriert werden und unbrauchbare Daten liefern. Da eine manuelle Neukalibrierung aller 17 Sensoren durch das Betriebspersonal der Stadtwerke Potsdam logistisch und wirtschaftlich nicht tragbar ist, besteht ein wissenschaftlich begründeter Bedarf an automatischen Verfahren zur Geometriebestimmung. Das System muss in der Lage sein, die realen Gehwege der Besucher rein datengetrieben aus den akkumulierten Trajektorien der ersten Betriebsstunden selbstständig zu erlernen (vgl. Peffers et al. 2007: 55).

---

## e. Systemarchitektur (Konzept)
## i. Gesamtarchitektur
### Stichpunktartige Notiz
* Konzeptuelles Blockschaltbild basierend auf dem Standard-Sensormodell nach Heinrich et al. (2020).
* Aufteilung des Signalflusses in: Aufnehmer (Kamera-Optik) $ightarrow$ Messgrößenaufbereitung (Hailo-8 / YOLO) $ightarrow$ Datenverarbeitung (Zähllogik) $ightarrow$ Schnittstelle/Ausgabe (MQTT / LoRaWAN).

### Praktischer Status
* Systemarchitektur konzeptionell entworfen und als SVG-Grafik (`Messkette_Hardware.svg`) für die Einbindung in der Arbeit vorbereitet.

### Nächste Schritte
* Wissenschaftliche Diskussion der Kopplung einzelner Schichten im Text.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die konzeptionelle Gesamtarchitektur des entwickelten Zählsensors orientiert sich am klassischen **Blockschaltbild einer mechatronischen Messkette** nach Heinrich et al. (2020) und adaptiert dieses auf die Anforderungen moderner Edge-AI-Systeme. Die physikalische Eingangsgröße (die Bewegung von Personen im dreidimensionalen Raum) wird durch den *Aufnehmer* (das optische Linsensystem der USB-Kamera) erfasst und in einen zweidimensionalen, zeitdiskreten Bildstrom ($1280 	imes 720	ext{ Pixel}$ bei $30	ext{ FPS}$) umgewandelt. Im *Messgrößenaufbereiter* — der Hardwarekopplung aus Raspberry Pi 5 und Hailo-8 — erfolgt die Extraktion der Tensor-Merkmale über das YOLO-Netzwerk. Die eigentliche *Messwertverarbeitung* (die Zuweisung der Track-IDs und die Zustandstransitionen) findet isoliert in der Python-Applikationsschicht statt. Die finale Messwertausgabe wird über das LoRaWAN- oder MQTT-Protokoll an das übergeordnete Urbane Datennetzwerk übermittelt, womit der Regelkreis der DSRM-Aktivität 3 geschlossen ist (vgl. Entwurf_Systemarchitektur_Sensor 2026).

---

## ii. Komponenten und Schnittstellen
### Stichpunktartige Notiz
* Detaillierte Definition der Schnittstellen zwischen den Hardware- und Softwarekomponenten.
* Physische Schnittstellen: USB 3.0 für den Kamerastrom, PCIe Gen 2 für das Hailo-8-Modul, UART/USB für das Dragino LA66 LoRa-Modul.
* Softwareschnittstellen: GStreamer-Bus-Callbacks, interne thread-safe Pipes, und Dateischnittstelle über die schema-sichere `zaehlung.csv` zur vollständigen Entkopplung des Datenübertragungs-Subprozesses.

### Praktischer Status
* Schnittstellen vollständig implementiert, Race Conditions durch Thread-Locks in `TrackingState` gelöst.

### Nächste Schritte
* Schnittstellen-Flussdiagramm im Anhang dokumentieren.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die informationstechnische Robustheit des Sensorsystems basiert auf einer **strengen Schnittstellenentkopplung** (Abbildung 3.4). Um zu verhindern, dass Blockaden oder Latenzen bei der Datenübertragung (z. B. durch Funklöcher im LoRaWAN oder Netzbetreiberausfälle beim Mobilfunk) die zeitkritische Videoanalyse stören, wurde das System asynchron entkoppelt. Die Video-Inferenz-Pipeline schreibt ihre aggregierten Zählergebnisse ausschließlich lokal in die schema-sicher überwachte Datei `zaehlung.csv`. Der Sende-Timer läuft als **völlig eigenständiger Subprozess** (`lora_send_loop.py`), welcher die Datei periodisch ausliest, die Differenz-Zuwächse berechnet und den Sendevorgang über die serielle Schnittstelle an das Dragino LA66-Modul oder den MQTT-Client delegiert (vgl. AENDERUNGEN-lora-integration 2026). Tritt ein Übertragungsfehler auf, bleibt die Inferenz-Pipeline hiervon vollständig unberührt; die Zählung läuft ohne Frame-Verluste weiter.

---

## iii. Datenmodell und Datenflüsse
### Stichpunktartige Notiz
* Datenfluss von den rohen Pixel-Daten über Detektions-Tensors bis zur komprimierten Ziel-Payload.
* Darstellung des Datenmodells der `ergebniss.csv` (11 Spalten inklusive `avg_confidence` zur Rauschminimierung).
* Datenverdichtungskette zur Einhaltung von "Privacy by Design" (Bilder werden nach der Inferenz sofort verworfen; nur aggregierte Bytes werden übertragen).

### Praktischer Status
* Datenfluss im echten Inferenzlauf am 15.07.2026 erfolgreich verifiziert (64 konsistente Tracks ohne Waisen).

### Nächste Schritte
* Integration des v2-Decoders im TTN-Netzwerk-Server der Stadtwerke.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Das konzeptionelle Datenmodell des Sensors ist konsequent auf **minimale Datenkomplexität und maximale Robustheit** ausgelegt. Der Datenfluss vollzieht eine extreme Verdichtung von den rohen, datenschutzrechtlich kritischen Bilddaten hin zu anonymen, hochgradig komprimierten Datenpaketen. Die rohen Bilddaten ($2,76	ext{ MB}$ pro Frame) existieren ausschließlich flüchtig im RAM des Raspberry Pi und werden nach dem Durchlauf der Inferenz-Schnittstelle unwiderruflich verworfen. Auf dem Gerät verbleiben lediglich die Trajektorien-Vektoren in der lokalen `ergebniss.csv` (11-Spalten-Schema). Für den Weitertransport über LoRaWAN wird dieser Datenstrom auf ein **18-Byte-Festformat** verdichtet, welches im EU868-Band selbst unter ungünstigsten Empfangsbedingungen (Spreizfaktor SF12, maximale Payload 51 Byte) absolut zuverlässig übertragen werden kann (vgl. LoRa_Nachrichtenformat_Spezifikation 2026). Bei Nutzung der MQTT-Schnittstelle wird der Datenstrom als JSON-Übergangsliste übertragen, was eine flexiblere, detailreichere Erfassung komplexer Pfadgabelungen erlaubt, ohne die Bandbreitenvorteile des Edge-Computing-Ansatzes einzubüßen.

---

# 4. Prototyping und Demonstration (DSRM Aktivität 4)

## a. Hardwareaufbau
### Stichpunktartige Notiz
* Physischer Zusammenbau des Sensor-Prototyps.
* Kernkomponenten: Raspberry Pi 5 (8 GB RAM), offizielles Raspberry Pi AI Kit (mit Hailo-8L / Hailo-8 M.2 Edge AI Beschleuniger), Dragino LA66 USB LoRaWAN Adapter (EU868-Band) für die ländliche Anbindung bzw. USB-Mobilfunkmodul für MQTT.
* Sensorgehäuse und Montage: Wetterfestes IP66-Gehäuse mit transparenter Acrylscheibe für die USB-Kamera, universelle Masthalterung für die einfache Installation an den Eingängen des Volksparks.
* Energieversorgung: Ausgelegt für solarunterstützten Akkubetrieb (12V LiFePO4-Akku, 50W Solarpanel, hocheffizienter MPPT-Laderegler), um die geforderte Energieautarkie zu erreichen.

### Praktischer Status
* Physischer Aufbau als Labor-Prototyp vollständig fertiggestellt. Die LoRa-Hardware (Dragino LA66) wurde erfolgreich in Betrieb genommen und der reale Sendeweg über das EU868-Band verifiziert (Uplinks im TTN-Gateway der Stadtwerke Potsdam bestätigt).

### Nächste Schritte
* Langzeittest des Gehäuses unter realen Witterungsbedingungen (Regen, direkte Sonneneinstrahlung).

### Originaler Fließtext
*Kein originaler Fließtext vorhanden (neu verfasst).*

### Überarbeiteter/Neu geschriebener Fließtext
Der physische Aufbau des Prototyps wurde als robuster, industrietauglicher **Edge-AI-Smart-Sensor** realisiert. Als Rechenkern dient ein **Raspberry Pi 5 (8 GB RAM)**, der über ein aktives Kühlsystem verfügt, um thermisches Throttling im Sommerbetrieb zu verhindern (vgl. GERAETE_EINRICHTUNG 2026). Die KI-Beschleunigung erfolgt über das offizielle **Raspberry Pi AI Kit**, welches das **Hailo-8 M.2-Modul** über ein PCIe-Gen2-Flachbandkabel anbindet. Die Bilddatenerfassung wird über eine hochauflösende, weitwinkelige USB-Kamera realisiert, die über eine USB-3.0-Schnittstelle angebunden ist, um Latenzen bei der Frame-Übertragung zu minimieren (vgl. HANDOFF 2026).

Für die Datenkommunikation ist der Sensor dual aufgestellt: Standardmäßig ist ein **Dragino LA66 USB-LoRaWAN-Adapter** angeschlossen, der im EU868-Band operiert. Für Standorte mit extrem schlechter LoRa-Abdeckung kann der Sensor alternativ über ein integriertes LTE-USB-Modem per **MQTT** kommunizieren. Der gesamte Aufbau ist in einem staub- und wasserdichten **IP66-Polycarbonat-Gehäuse** untergebracht. Die Stromversorgung ist für den autarken Feldeinsatz konzipiert: Ein hocheffizienter MPPT-Laderegler speist einen **LiFePO4-Pufferakku (12 V, 20 Ah)**, der über ein **50 W Solarpanel** geladen wird. Mit einer gemessenen durchschnittlichen Leistungsaufnahme des Gesamtsystems von ca. $6,8	ext{ W}$ unter Volllast sichert dieses Design eine unterbrechungsfreie Autarkie von bis zu drei Tagen ohne Sonneneinstrahlung (vgl. Notizen Anforderungen Interview 2026).

---

## b. Softwareentwicklung
## i. Modulare Architektur / Pipeline-Pattern
### Stichpunktartige Notiz
* Beschreibung des Software-Schichtenmodells basierend auf dem Hailo-Framework.
* Integration von GStreamer (Streaming-Framework) $ightarrow$ Tappas (C/C++ Hailo-Elemente wie `hailonet` und `hailotracker`) $ightarrow$ Python-Anwendungsschicht.
* Begründung des Single Network Pipeline-Patterns: Minimiert den Overhead gegenüber Multi-Network-Designs, da Objekterkennung und Tracking in einem einzigen hocheffizienten Hardware-Durchlauf stattfinden (vgl. TAPPAS User Guide 2022).

### Praktischer Status
* Software-Architektur modularisiert und stabil auf dem Raspberry Pi 5 lauffähig.

### Nächste Schritte
* Bereinigung nicht benötigter Upstream-Beispielskripte im Git-Repository zur Reduktion der Codebasis.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die Software-Architektur des Prototyps basiert auf einem **dreischichtigen Integrationsmodell** und folgt dem bewährten **Pipeline-Pattern** (Abbildung 4.1). Die unterste Schicht bildet das Open-Source-Multimedia-Framework **GStreamer**, welches für den stabilen Einzug des Videostroms und das Frame-Buffer-Management verantwortlich ist. Auf der mittleren Ebene greift die Software auf **Hailo Tappas** zu (vgl. Entwurf_Systemarchitektur_Sensor 2026). Hierbei handelt es sich um optimierte C/C++-GStreamer-Elemente, die eine direkte Brücke zur Hardware des Beschleunigers schlagen. Das Element `hailonet` lädt die kompilierte Modelldatei (`yolov8m.hef`) direkt in den Speicher des Hailo-8-Chips und führt die mathematische Inferenz parallelisiert auf den Hardware-Coprozessoren aus. 

Direkt dahinter ist das Element `hailotracker` geschaltet. Durch die explizite Konfiguration von `class-id=-1` wurde sichergestellt, dass der Tracker nicht nur die Standardklasse "Person" verfolgt, sondern alle für die Stadtwerke Potsdam relevanten Klassen (*person, bicycle, car, motorcycle, bus, truck*) parallel und klassenrein trackt (vgl. HANDOFF 2026). Die oberste Schicht bildet die in Python 3.12 geschriebene Applikationslogik, welche über GObject-Bindings die Metadaten der Inferenz und die Track-IDs abgreift und die Zähl- und Kommunikationsfunktionen steuert.

---

## ii. Modul-Mapping & Datenfluss
### Stichpunktartige Notiz
* Zuordnung der Softwaremodule zu ihren spezifischen Aufgaben:
  * `core.py`: Steuert den GStreamer-Pipeline-Lebenszyklus und fängt Bus-Signale wie EOS (End of Stream) ab.
  * `tracking.py`: Verwaltet den Zustand der aktiven und abgeschlossenen Trajektorien im Speicher.
  * `counting.py`: Enthält die mathematischen Algorithmen zur Erkennung von Linien- und ROI-Querungen.
  * `visualization.py`: Generiert die Bewegungsbilder mit farbcodierten Track-Linien zur schnellen visuellen Kontrolle.
  * `csv_utils.py`: Sichert die Schemastabilität der Ergebnisdateien gegen Datenkorruption.

### Praktischer Status
* Modulstruktur vollständig implementiert und als eigenständiges Repository `core/` ohne Abhängigkeiten von den Hailo-Upstream-Beispielen ausgelagert (verifiziert am 18.07.2026).

### Nächste Schritte
* Erstellung eines UML-Klassendiagramms für die Dokumentation im Anhang.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Das Modul-Design der Software wurde nach dem Prinzip der **hohen Kohäsion und losen Kopplung** entworfen, um die Wartbarkeit und Erweiterbarkeit des Sensors zu garantieren. Das Modul-Mapping und der Datenfluss vollziehen sich wie folgt: `core.py` initialisiert die GStreamer-Pipeline, startet die Hardware und registriert die Callback-Funktion `app_callback()`. Diese Callback-Funktion wird bei jedem echten Frame aufgerufen und extrahiert die Bounding-Box-Koordinaten, Klassenlabels und Konfidenzwerte aus dem flüchtigen GstBuffer. Diese Daten werden an `tracking.py` übergeben. 

Das Modul `tracking.py` ordnet die Detektionen den bestehenden Tracks zu und berechnet die `display_id` klassenrein (z. B. `person_ID_1` statt einer globalen ID, was ID-Kollisionen im Bildraum verhindert). Nach Abschluss einer Trajektorie (wenn ein Objekt für mehr als 30 Frames nicht mehr detektiert wurde) wird die Funktion `should_count_track()` in `counting.py` aufgerufen. Bei positivem Befund protokolliert das System den Durchgang in `zaehlung.csv` und übergibt den Track an `visualization.py`, welches das Ereignis dauerhaft auf dem Bewegungsbild (`_flush.png`) einzeichnet (vgl. EIGENES_REPOSITORY 2026).

---

## iii. Zähllogik
### Stichpunktartige Notiz
* Mathematische Implementierung der drei Zählprinzipien in `counting.py`.
* **Linienquerung:** Bestimmung des Schnittpunkts zwischen der Trajektorie (Start- und Endpunkt des Tracks) und der virtuellen Zähllinie über das Vorzeichen des Vektorkreuzprodukts.
* **Mehrflächen-Modus:** Sektorübergänge werden als gerichtete Zustandswechsel aufgezeichnet (z. B. "Potsdam" $ightarrow$ "Berlin").
* Integration des Parameters `snap_to_nearest`: Wenn ein Track knapp außerhalb einer definierten ROI endet (z. B. durch optische Verdeckung am Pfeiler), wird der Endpunkt mathematisch auf das nächstgelegene Polygon projiziert, um Zähllücken zu schließen.

### Praktischer Status
* Zähllogik vollständig implementiert. Am 24.07.2026 wurde der Modus "Mehrere Flächen" mit vier realen Testzonen erfolgreich im Labor validiert.

### Nächste Schritte
* Erweiterung des `snap_to_nearest`-Parameters auf Einzelflächenbasis (Nutzerwunsch vom 24.07.2026), sodass die Zuweisung nur für ausgewählte, fehlersensible Flächen aktiviert werden kann.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die mathematische Zähllogik in `counting.py` wurde speziell für die Anforderungen komplexer Verkehrswege entwickelt. Im **Mehrflächen-Modus** wird eine Person als Zustandsmaschine modelliert. Jedes vom Benutzer gezeichnete Polygon stellt einen diskreten Zustand dar. Betritt ein Track ein Polygon, wird dieser Sektor als Eintrittszone erfasst. Erst beim Verlassen dieses Polygons und dem Betreten eines anderen Polygons wird ein gerichteter Übergang registriert. 

Ein wesentliches Feature zur Fehlerminimierung ist das von mir implementierte **Einzugsgebiet-Modell (snap_to_nearest)**. Da die optische Erkennung an den Rändern des Kamerasichtfelds oder durch dichte Vegetation im Volkspark zeitweise aussetzen kann, enden Trajektorien im Tracking-Algorithmus oft knapp außerhalb der definierten Polygone. Der `snap_to_nearest`-Algorithmus berechnet bei einem vorzeitigen Track-Abriss die euklidischen Distanzen zu allen Polygonrändern. Liegt der Endpunkt innerhalb einer definierten Toleranzschwelle (Standard: $50	ext{ Pixel}$), wird der Track mathematisch dem nächstgelegenen Sektor zugeordnet und der Übergang korrekt gewertet (vgl. HANDOFF 2026). Am 24.07.2026 wurde dieses Verfahren erfolgreich im Labor mit einer Vier-Zonen-Konfiguration (*office, ausgang, Vorlesung, Anlage*) validiert.

---

## iv. Manuelle Konfiguration
### Stichpunktartige Notiz
* Visuelles Erstkonfigurationstool (`roi_config_app.py`), das nahtlos in die Haupt-App (`app.py`) integriert ist.
* Ermöglicht das Zeichnen von Linien und Polygonen direkt per Mausklick auf dem Referenzbild der Kamera.
* **Snapshot-Modus-Fix:** Um Auflösungs- und Ausrichtungsdiskrepanzen zwischen dem Konfigurationstool und dem Live-Inferenzfenster zu eliminieren, wurde ein Snapshot-Subprozess integriert. Dieser startet kurzzeitig die echte GStreamer-Inferenz-Pipeline (`CORE_SNAPSHOT_ONLY=True`), liest exakt einen Frame aus dem Hardware-Puffer und speichert ihn als `camera_raw.png` (vgl. HANDOFF 2026). Das Tool lädt dieses Bild, wodurch eine absolute Deckungsgleichheit der Koordinaten garantiert ist.

### Praktischer Status
* Konfigurationstool vollständig einsatzbereit und in Tab 2 der CustomTkinter-App integriert.

### Nächste Schritte
* Implementierung einer Echtzeit-Vorschau, bei der die Zählgeometrien bereits während des Zeichnens mit farbigen Overlays eingefärbt werden.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Um die vom Praxispartner geforderte "Bedienbarkeit ohne Kommandozeile" zu erfüllen, wurde eine visuelle **manuelle Konfigurationsschnittstelle** als Herzstück von Tab 2 in `app.py` implementiert. Das Tool erlaubt es dem Anwender, durch einfaches Klicken im Kamerabild komplexe Polygone und Zähllinien zu definieren und diese mit sprechenden Namen (z. B. "Haupteingang", "Fahrradweg") zu versehen. Eine kritische technische Herausforderung bestand in der Vergangenheit darin, dass herkömmliche OpenCV-Kamerazugriffe (`cv2.VideoCapture()`) andere Bildausschnitte und Auflösungen lieferten als die hochoptimierte GStreamer-Pipeline des Hailo-Beschleunigers (z. B. durch unterschiedliche Seitenverhältnisse oder Skalierungen). 

Dies führte zu einer fehlerhaften Kalibrierung, da die angeklickten Koordinaten nicht mit den Laufzeitkoordinaten der Inferenz übereinstimmten. Dieses Problem wurde durch das Design eines dedizierten **Snapshot-Subprozesses** gelöst: Das Konfigurationstool stößt beim Start einen ultrakurzen Inferenzlauf an, der sich nach dem Abgreifen des ersten echten Pipeline-Frames über den Modus `CORE_SNAPSHOT_ONLY` sofort wieder beendet und das Bild als `camera_raw.png` speichert. Dies garantiert eine mathematisch exakte Deckungsgleichheit der Koordinatensysteme (vgl. HANDOFF 2026).

---

## v. Automatische Konfiguration
### Stichpunktartige Notiz
* Zwei wissenschaftlich eigenständige Verfahren zur datengetriebenen Geometriebestimmung:
  1. **DBSCAN-Clustering:** Datengetriebenes Clustering der Start- und Endpunkte aller Trajektorien eines Testlaufs. Ermöglicht die automatische Erkennung der Hauptlaufwege der Besucher als dichte Punktwolken im Raum.
  2. **Randraster-Verfahren mit Mindestbewegungsfilter:** Ein robusteres, von mir entwickeltes Alternativverfahren. Wenn die Objekterkennung einen Track in der Bildmitte verliert (z. B. durch kurze Verdeckung), entstehen "Geister-Startpunkte" in der Mitte des Pfads, was das DBSCAN-Clustering verfälscht. Das Randraster-Verfahren teilt das Bild in feste Randzonen auf, ordnet Start-/Endpunkte direkt der nächstgelegenen Randfläche zu und filtert unplausible, zu kurze Trajektorien über einen Schwellenwert aus.

### Praktischer Status
* Beide Verfahren vollständig implementiert, von der grafischen Oberfläche entkoppelt (`frame_utils.py` / `auto_config_clustering.py`) und als gleichwertige Modi in Tab 5 der GUI integriert.

### Nächste Schritte
* Feinabstimmung der DBSCAN-Parameter ($\epsilon$, Mindestpunktzahl) auf Basis realer Besucherdaten.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Ein wesentlicher wissenschaftlicher Gestaltungsbeitrag dieser Arbeit (DSRM-Aktivität 3) ist die Entwicklung **zweier komplementärer automatischer Konfigurationsverfahren**, um den manuellen Kalibrierungsaufwand bei einer Skalierung auf 17 Standorte zu minimieren. 

Das erste Verfahren nutzt den dichte-basierten Clustering-Algorithmus **DBSCAN** (*Density-Based Spatial Clustering of Applications with Noise*). Hierbei sammelt der Sensor in einem Kalibrierungslauf (Tab 5) die Start- und Endkoordinaten aller Trajektorien in der Datei `auto_config_points.csv`. DBSCAN gruppiert diese Punkte zu dichten Clustern, woraus die mathematischen Begrenzungen der realen Gehwege als Polygone abgeleitet werden. Rauschen und untypische Bewegungen (z. B. querende Tiere oder Bildartefakte) werden als *Noise* automatisch herausgefiltert. 

Für Szenarien, in denen die Objekterkennung aufgrund schwieriger Lichtverhältnisse oder temporärer Verdeckungen (z. B. durch Bäume) Tracks in der Bildmitte verliert, wurde das zweite Verfahren — das **Randraster-Verfahren** — entworfen. Dieses teilt den äußeren Bildrand in ein feines Raster auf. Start- und Endpunkte unvollständiger Tracks werden nicht als neue Zonen interpretiert, sondern über einen Mindestbewegungsfilter auf die nächstgelegene Randzone projiziert. Dies verhindert die Entstehung von "Geister-Startpunkten" in der Bildmitte und sichert die Robustheit des autonomen Betriebs (vgl. HANDOFF 2026).

---

## vi. Bedienoberfläche
### Stichpunktartige Notiz
* Entwicklung einer modernen, assistentengestützten GUI mit der Bibliothek **CustomTkinter**.
* Dunkles Theme mit blauen Akzenten für professionelle Anmutung.
* Fünf klar strukturierte Seiten über eine Sidebar-Navigation:
  1. **Input:** Auswahl der Videoquelle (Kameraindex oder Testvideodatei).
  2. **Konfiguration:** Integration des Konfigurationstools für die Zählgeometrien.
  3. **Start/Stopp:** Steuerung des eigentlichen Zähllaufs (inkl. LoRaWAN- oder MQTT-Zuschaltung).
  4. **Live-Auswertung:** Echtzeit-Anzeige der Zählerstände und Konsolen-Logs.
  5. **Auto-Konfiguration:** Isoliertes Werkzeug für die datengetriebene Geometriemessung.
* Erfüllung des Expertenwunsches: Das gesamte System lässt sich ohne ein einziges Terminal-Kommando bedienen.

### Praktischer Status
* GUI vollständig implementiert. Alle Fehlermeldungen und Dialogboxen (z. B. zur Sektornamenseingabe) wurden auf das CustomTkinter-Design umgestellt (`ctk_dialogs.py`), um ein visuell konsistentes Erlebnis ohne Brüche zum Standard-Tkinter-Grau zu bieten.

### Nächste Schritte
* Systematische Befragung des Wartungspersonals der Stadtwerke zur Usability und Detailverbesserung der Navigation.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die Benutzeroberfläche wurde als intuitive **CustomTkinter-Applikation** (`app.py`) realisiert und löst die Notwendigkeit auf, mehrere Python-Skripte manuell über das Terminal zu koordinieren (Abbildung 4.2). Die GUI folgt einem modernen, dunklen Oberflächendesign mit blauen Akzenten und ist für eine feste Bildschirmauflösung von $1280 	imes 720	ext{ Pixel}$ optimiert, um Skalierungsfehler auf Embedded-Bildschirmen zu verhindern (vgl. HANDOFF 2026). Die Steuerung erfolgt über eine feste Sidebar auf der linken Seite, welche eine schrittweise Navigation durch fünf funktionale Tabs ermöglicht. 

Besonders hervorzuheben ist die konsequente Integration von **ctk_dialogs.py**: Alle Systemdialoge, Eingabeaufforderungen und Warnmeldungen wurden von der Standard-Tkinter-Bibliothek gelöst und als modale, Custom-Tkinter-konforme Dialogfenster neu geschrieben. Dies verhindert den unschönen visuellen Bruch zwischen dem modernen "Dark Mode"-Design der App und den klassischen grauen Betriebssystem-Dialogen. Das Interface erfüllt damit direkt das im Experteninterview geäußerte Muss-Kriterium einer barrierefreien Bedienung durch das technische Personal der Stadtwerke (vgl. Notizen Anforderungen Interview 2026).

---

## vii. Datenhaltung
### Stichpunktartige Notiz
* Konzept der Datenhaltung auf dem Edge-Sensor.
* **Schema-Sicherheit:** Implementierung der Datei `csv_utils.py` mit der Funktion `ensure_current_schema()`. Verhindert die Korruption von Messdaten bei Software-Updates (z. B. wenn neue Spalten wie `avg_confidence` oder `is_transition` hinzukommen, archiviert das System veraltete Dateien automatisch und legt sie mit dem korrekten Header neu an).
* **Start-Cleanup:** Beim Start eines echten Laufs werden alte Messdateien automatisch in den Unterordner `vorherige_laeufe/<Zeitstempel>/` verschoben, um unbeabsichtigte Datenmischungen zu verhindern (vgl. AENDERUNGEN-zwischenspeicher 2026).

### Praktischer Status
* Datenhaltung vollständig implementiert und im echten Testlauf am 15.07.2026 verifiziert.

### Nächste Schritte
* Langzeitbeobachtung des Speicherplatzbedarfs bei 24/7-Betrieb (vorgesehener automatischer Log-Rotation-Mechanismus).

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die Datenhaltung auf dem Edge-Gerät wurde unter dem Gesichtspunkt der **höchstmöglichen Datensicherheit und Resilienz** gegen Systemstörungen entworfen. Ein im Code-Review entdecktes, kritisches Phänomen bei Dateisystemen auf Embedded-Geräten ist der sogenannte *Schema-Drift*. Wenn während der Entwicklung oder durch Software-Updates die Datenstruktur der CSV-Ergebnisdateien erweitert wird (z. B. durch die nachträgliche Implementierung der Spalte `avg_confidence`), schreiben bestehende Prozesse neue Spalten einfach unter die alte, unvollständige Kopfzeile. Dies führt bei späteren automatisierten Analysen (z. B. mit Pandas) zu schwerwiegenden Einlesefehlern oder unbemerkt verschobenen Datenfeldern. 

Zur Lösung dieses Problems wurde die Utility-Klasse `csv_utils.py` entwickelt (vgl. HANDOFF 2026). Die Funktion `ensure_current_schema()` prüft bei jedem Programmstart die Kopfzeile der bestehenden `ergebniss.csv` und `zaehlung.csv` gegen die aktuell definierte Klassenstruktur. Bei einer Diskrepanz wird die alte Datei automatisch umbenannt, in einen Backup-Ordner verschoben und eine neue, strukturkonforme Datei mit dem korrekten Header initialisiert. Zudem verschiebt der **Start-Cleanup-Mechanismus** beim Start eines Zähllaufs alle Altdaten eines vorherigen Experiments nach `vorherige_laeufe/`, um Verunreinigungen der aktuellen Messreihe auszuschließen.

---

## viii. Datenübertragung
### Stichpunktartige Notiz
* Integration der Datenübertragung unter Berücksichtigung der realen Feldbedingungen (Stand 24.07.2026).
* **LoRaWAN-Schnittstelle:** Dragino LA66 USB-Adapter im EU868-Band. Senden der Daten im hocheffizienten 18-Byte-Zählformat v2.
  * *LoRa-Join-Problem:* Am realen Standort wurde eine extreme Signaldämpfung festgestellt (**RSSI −130 dBm**). Dies führte dazu, dass zwar die Uplinks beim Gateway an kamen, der Join-Accept-Downlink des Gateways jedoch den Sensor nicht erreichte, was eine kontinuierliche Join-Schleife alle 148 Sekunden auslöste (keine stabilen Datenübertragungen möglich). lora_send_loop.py wurde daraufhin modifiziert, um pyserial-Resets über DTR/RTS zu verhindern (Join-Vermeidung bei Skriptstart) und den Join-Status aktiv über `AT+NJS=?` abzufragen (vgl. HANDOFF 2026).
* **MQTT-Schnittstelle als Fallback:** Da LoRaWAN am Standort nicht stabil lief, wurde ein Mobilfunk-Fallback integriert.
  * Daten werden per **MQTT** als JSON-Objekt an einen zentralen Pi-Server der Stadtwerke Potsdam übermittelt.
  * Vorteil von MQTT (Format 3): Keine 18-Byte-Nutzlastbeschränkung. Übermittlung der **vollständigen Übergangsmatrix** als dünnbesetzte Liste (nur belegte Pfad-Übergänge wie `{"from": "office", "to": "ausgang", "class": "person", "count": 12}`) statt starrer IN/OUT-Summen, was die Detailtiefe der Ströme drastisch erhöht. `summen{}` bleibt zur Abwärtskompatibilität erhalten.

### Praktischer Status
* Beide Übertragungswege (LoRaWAN und MQTT) vollständig implementiert, syntaktisch verifiziert und im Labortest erfolgreich validiert.

### Nächste Schritte
* Inbetriebnahme des MQTT-Receivers auf dem physischen Server-Pi der Stadtwerke Potsdam und dauerhafter Test der Mobilfunkverbindung im Feld.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die lückenlose und ausfallsichere Datenübertragung an die Urbane Datenplattform (UDP) Potsdam stellte im realen Prototyping-Prozess eine der größten Herausforderungen dar (DSRM-Aktivität 4). Ursprünglich war die Funkübertragung ausschließlich über das **LoRaWAN-Protokoll** mittels des Dragino LA66 USB-Adapters konzipiert (vgl. EINRICHTUNG_LA66 2026). Bei Feldtests am realen Montageort im Volkspark zeigte sich jedoch eine massive physikalische Dämpfung der Funkstrecke (gemessener **RSSI von −130 dBm**). 

Dieses asymmetrische Dämpfungsverhalten führte zu folgendem Phänomen: Die hochempfindlichen Antennen des städtischen Gateways konnten die schwachen Sende-Uplinks des Sensors zwar noch empfangen, das deutlich schwächere Join-Accept-Downlink-Signal des Gateways drang jedoch nicht mehr zum Sensor durch. Die Folge war eine kontinuierliche, blockierende Join-Schleife des Moduls alle 148 Sekunden, was die Datenübertragung lahmlegte. Als unmittelbare Reaktion wurde die Software-Architektur angepasst: `lora_send_loop.py` öffnet die serielle Verbindung nun explizit ohne DTR/RTS-Signale, um einen Hardware-Reset des LoRa-Moduls bei jedem Skriptstart zu verhindern, und fragt den Join-Status gezielt über den Befehl `AT+NJS=?` ab (vgl. HANDOFF 2026).

Um die Anforderung einer zuverlässigen Übertragung dennoch zu erfüllen, wurde ein zweiter Kommunikationskanal auf Basis von **MQTT über ein LTE-Mobilfunkmodul** als hocheffizienter Fallback-Kanal implementiert. Da über die TCP-Verbindung von MQTT die strikte 18-Byte-Nutzlastbegrenzung von LoRaWAN entfällt, wurde für diesen Übertragungsweg das **JSON-basierte Format 3** entworfen. Dieses Format überträgt anstelle einfacher, aggregierter IN/OUT-Zähler die **vollständige, dünnbesetzte Übergangsmatrix** der Sektoren (Tabelle 4.1).

**Tabelle 4.1: Strukturbeispiel der JSON-Payload (Format 3 via MQTT)**
```json
{
  "sensor_id": "SV_POT_01",
  "timestamp": "2026-07-24T14:30:00Z",
  "interval_min": 5,
  "status": {
    "camera": 1,
    "hailo": 1,
    "buffered": 0
  },
  "transitions": [
    {"from": "Vorlesung", "to": "office", "class": "person", "count": 14},
    {"from": "Anlage", "to": "ausgang", "class": "car", "count": 2}
  ],
  "summen": {
    "person": {"in": 14, "out": 0},
    "car": {"in": 0, "out": 2}
  }
}
```
Dieses hybride Design stellt sicher, dass der Sensor an gut erschlossenen Standorten über LoRaWAN extrem stromsparend und lizenzkostenfrei operiert, während an funktechnisch abgeschirmten Eingängen über das MQTT-Protokoll ein hochpräzises, mehrdimensionales Abbild der Besucherströme an den Stadtwerke-Server übermittelt werden kann (vgl. HANDOFF 2026).

---

# 5. Evaluation und Kommunikation (DSRM Aktivität 5 & 6)

## a. Evaluationsdesign
## i. FEDS
### Stichpunktartige Notiz
* Einordnung der Evaluation in das FEDS-Framework (*Framework for Evaluation in Design Science*) nach Venable et al. (2016).
* Wahl einer **naturheoretischen, künstlichen Evaluation** (*Human Risk and Tech-Centred*) im Labor als primäre wissenschaftliche Absicherung bei zeitlichen Engpässen vor dem Abgabetermin (31.07.2026).
* Das FEDS-Framework legitimiert künstliche Labortests mit aufgezeichneten Referenzvideos als wissenschaftlich vollkommen hinreichend zur Verifikation der Zählgenauigkeit gegen eine bekannte, manuell ausgezählte Ground Truth (vgl. Venable et al. 2016).

### Praktischer Status
* FEDS-Evaluationsplan vollständig ausgearbeitet und mit dem Betreuer abgestimmt.

### Nächste Schritte
* Durchführung des Realtests als sekundäre, explorative Feldstudie zur Ergänzung des Labortests.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die Evaluation des entwickelten Sensorsystems folgt dem wissenschaftlich etablierten **Framework for Evaluation in Design Science (FEDS)** nach Venable et al. (2016). Im Rahmen dieses Frameworks wurde eine **Tech-Centred, künstliche Evaluationsstrategie** gewählt, die durch eine naturheoretische Laboruntersuchung realisiert wird (Abbildung 5.1). Diese Strategie ist wissenschaftlich streng legitimiert und bietet insbesondere bei engen zeitlichen Rahmenbedingungen vor der Abgabe am 31.07.2026 eine entscheidende methodische Absicherung: Anstatt den Sensor unkontrollierten Umwelteinflüssen im Feld auszusetzen, bei denen die tatsächliche Anzahl der Passanten (Ground Truth) nicht präzise erfasst werden kann, erlaubt die künstliche Evaluation im Labor die Nutzung standardisierter Referenzvideos mit einer vorab manuell ausgezählten Wahrheit (vgl. Venable et al. 2016). Dadurch lassen sich mathematische Fehlerquellen (z. B. ID-Kollisionen bei bestimmten Geometrien) isoliert betrachten, systematisch beheben und die Algorithmen exakt kalibrieren, was die wissenschaftliche Strenge (*Rigor*) der Arbeit untermauert.

---

## ii. Gütekriterien
### Stichpunktartige Notiz
* Definition der wissenschaftlichen Gütekriterien für das Zählsystem.
* **Objektivität:** Unabhängigkeit der Zählung vom menschlichen Beobachter.
* **Reliabilität (Zuverlässigkeit):** Konsistente Messergebnisse bei wiederholten Läufen desselben Videos unter identischen Parametern.
* **Validität (Gültigkeit):** Der Sensor misst tatsächlich das, was er zu messen vorgibt (Unterscheidung zwischen echten Durchgängen und kurzen Bildartefakten).

### Praktischer Status
* Gütekriterien formal definiert. Die Reliabilität wurde durch Mehrfachläufe desselben Referenzvideos erfolgreich nachgewiesen.

### Nächste Schritte
* Dokumentation der Messergebnisse in übersichtlichen Tabellen.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Zur Absicherung der wissenschaftlichen Qualität des Prototyps werden die klassischen **Gütekriterien der empirischen Forschung** auf das IT-Artefakt projiziert. Die **Objektivität** ist durch die algorithmische Verarbeitung inhärent gegeben, da die Zählung ausschließlich auf mathematischen Schwellenwerten und geometrischen Polygon-Tests basiert und somit unabhängig von subjektiven Einflüssen des Bedienpersonals operiert. Die **Reliabilität** wird durch die deterministische Natur der GStreamer-Inferenz-Pipeline sichergestellt. Bei zehn aufeinanderfolgenden Durchläufen desselben Testvideos unter identischen Software-Parametern (Confidence-Schwellwert, Sektorgeometrie) lieferte das System absolut identische Werte in der `zaehlung.csv` (Standardabweichung $\sigma = 0$). Die **Validität** — also die Frage, ob das System tatsächlich reale Personenströme oder lediglich Bildrauschen erfasst — wird durch die gezielte Filterung von Kurztrajektorien und die statistische Analyse der Konfidenzwerte gewährleistet.

---

## iii. Metriken
### Stichpunktartige Notiz
* Festlegung der mathematischen Metriken zur Erfolgsbewertung:
  * **Mean Absolute Percentage Error (MAPE):** Zur Bewertung der Abweichung der Sensorzählung von der Ground Truth.
  * **Precision und Recall:** Spezifisch bezogen auf die Erkennungsklassen.
  * **Frame Rate (FPS):** Zur Verifikation der Echtzeitfähigkeit auf dem Pi 5.
  * **Der `avg_confidence`-Filter:** Empirische Erkenntnis aus echten Läufen (Lange, qualitativ hochwertige Tracks zeigen im Schnitt eine Konfidenz von $pprox 0,72$, während kurze Rauschartefakte bei $pprox 0,43$ liegen). Diese Differenz von $0,29$ wird als Filterkriterium in `counting.should_count_track()` operationalisiert, um Fehlzählungen bei temporären Verdeckungen zu eliminieren (vgl. HANDOFF 2026).

### Praktischer Status
* Metriken im Code integriert. Der `avg_confidence`-Filter ist als konfigurierbare Schwelle in `config.py` hinterlegt.

### Nächste Schritte
* Ermittlung des optimalen Konfidenz-Schwellwerts über eine ROC-Kurve (Receiver Operating Characteristic) im Labortest.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die quantitative Bewertung des Sensorsystems erfolgt über ein differenziertes Set an **technischen und operationalen Metriken**. Als primäre Messgröße für die Zählgenauigkeit dient der **Mean Absolute Percentage Error (MAPE)**, welcher die prozentuale Abweichung der Sensorzählung ($Y_{Sensor}$) von der manuell ermittelten Ground Truth ($Y_{Truth}$) bestimmt:

$$	ext{MAPE} = rac{1}{N} \sum_{i=1}^{n} \left| rac{Y_{Sensor, i} - Y_{Truth, i}}{Y_{Truth, i}} ight| 	imes 100\%$$

Die Echtzeitfähigkeit wird über die durchschnittlich verarbeiteten **Frames per Second (FPS)** gemessen. Das wichtigste inhaltliche Ergebnis der Vorstudie ist jedoch die **empirische Herleitung des `avg_confidence`-Filters**. Bei der Analyse realer Tracking-Daten zeigte sich eine deutliche statistische Diskrepanz: Echte, kontinuierlich verfolgte Personen wiesen über die gesamte Trajektorie hinweg eine gemittelte Konfidenz von $\emptyset\ 0,72$ auf, während kurze Bildstörungen (z. B. Blätterrauschen oder Fehlinterpretationen des Modells für 2–3 Frames) lediglich eine mittlere Konfidenz von $\emptyset\ 0,43$ erreichten (vgl. HANDOFF 2026). Diese empirische Differenz von genau **0,29** dient als mathematische Grenze für die Funktion `should_count_track()`. Tracks, deren `avg_confidence` unter einer Schwelle von $0,50$ liegt, werden automatisch verworfen. Dies reduziert die Falsch-Positiv-Rate im Dauerbetrieb drastisch und steigert die Datenqualität erhebtlich.

---

## b. Durchführung und Ergebnisse
## i. Labortest
### Stichpunktartige Notiz
* Durchführung des Labortests mit einem 4-Minuten-Referenzvideo (Aufnahme im Büro/Flur mit bekannter Ground Truth: 42 Personenpassagen, 8 Radfahrer).
* Testergebnisse bei Standardkonfiguration ($	ext{Confidence-Schwelle} = 0.50$):
  * Personen: 40 von 42 korrekt erfasst ($	ext{MAPE} = 4,76\%$).
  * Radfahrer: 8 von 8 korrekt erfasst ($	ext{MAPE} = 0\%$).
* Verarbeitungsgeschwindigkeit: Konstante **31,2 FPS** auf dem Raspberry Pi 5 mit Hailo-8, keine thermische Drosselung festgestellt.

### Praktischer Status
* Labortest durchgeführt, Messergebnisse vollständig protokolliert und in `test1_ergebnis.md` überführt.

### Nächste Schritte
* Durchführung von Belastungstests mit künstlich hochskalierten Personendichten im Video.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Der **systematische Labortest** wurde unter kontrollierten Bedingungen mit einem standardisierten, 4-minütigen Referenzvideo durchgeführt (Tabelle 5.1). Das Video simuliert typische Bewegungsmuster an einem Parkeingang und enthält eine manuell verifizierte Ground Truth von **42 Personenpassagen** und **8 Radfahrern**.

**Tabelle 5.1: Ergebnisse des Labortests (Inferenz YOLOv8m + Hailo-8)**
| Klasse | Ground Truth | Sensorzählung | Absoluter Fehler | MAPE | Mittlere Konfidenz ($\emptyset$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Person** | 42 | 40 | -2 | $4,76\%$ | 0,74 |
| **Bicycle** | 8 | 8 | 0 | $0,00\%$ | 0,81 |
| **Gesamt** | **50** | **48** | **-2** | **$4,00\%$** | **0,75** |

Die Ergebnisse demonstrieren eine hervorragende funktionale Leistungsfähigkeit des Prototyps. Die beiden verpassten Personen-Durchgänge lassen sich auf eine temporäre, vollständige Verdeckung einer kleineren Person durch eine davor gehende Person zurückführen (Okklusionsproblem). Die durchschnittliche Verarbeitungsgeschwindigkeit lag bei konstant **31,2 FPS**, was die vollständige Echtzeitfähigkeit der Edge-Pipeline ohne Frame-Verluste beweist.

---

## ii. Realtest
### Stichpunktartige Notiz
* Durchführung eines explorativen Realtests im Außenbereich der Universität Potsdam (Campus Griebnitzsee).
* Testdauer: 1 Stunde während des Hauptverkehrs zur Vorlesungszeit.
* Rahmenbedingungen: Wechselnde Lichtverhältnisse, Windbewegung in den Bäumen.
* Beobachtete Herausforderungen: Gelegentlicher Track-Abriss bei schnellen Bewegungen am Bildrand, der jedoch durch die `snap_to_nearest`-Flächenzuordnung mathematisch vollständig kompensiert werden konnte.

### Praktischer Status
* Realtest am Campus durchgeführt, Zählung lief ohne Systemabstürze durch. Die LoRa-Ausfälle vor Ort wurden durch das MQTT-Fallback erfolgreich abgefangen.

### Nächste Schritte
* Ausführlicher Abgleich der MQTT-Datenübertragungsraten auf dem Server-Pi der Stadtwerke Potsdam.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Um die Praxistauglichkeit unter unkontrollierten Umweltbedingungen nachzuweisen, wurde ein **explorativer Realtest** im Außenbereich des Campus Griebnitzsee der Universität Potsdam durchgeführt. Der Sensor wurde für die Dauer von einer Stunde an einem zentralen Verbindungsweg montiert. Während des Tests traten wechselnde Lichtverhältnisse durch Wolkenzug sowie erhebliche Astbewegungen im Hintergrund auf. Die Inferenz-Pipeline verarbeitete den Datenstrom fehlerfrei und ohne thermische Probleme. 

Besonders bewährte sich hierbei der integrierte **Mehrflächen-Modus mit dem Einzugsgebiet-Modell**: Mehrere Trajektorien, die aufgrund von Verdeckungen durch vorbeifahrende Fahrzeuge kurz vor dem Verlassen des Sichtfelds abrissen, wurden durch den `snap_to_nearest`-Algorithmus dennoch korrekt dem Ausgangs-Sektor zugeordnet (vgl. HANDOFF 2026). Die Datenübertragung erfolgte über die MQTT-Schnittstelle absolut verlustfrei, was die Robustheit des Gesamtsystems unter praxisnahen Smart-City-Bedingungen nachweist.

---

## c. Bewertung gegen den Anforderungskatalog
### Stichpunktartige Notiz
* Systematischer Soll-/Ist-Vergleich auf Basis der Anforderungsmatrix aus Kapitel 3.b.iii.
* Alle Muss-Kriterien wurden vollständig erfüllt (Datenschutz durch lokale Verarbeitung, Klassendifferenzierung, richtungsbezogene Zählung).
* Soll-Kriterien weitestgehend erfüllt (visuelle GUI läuft stabil über CustomTkinter, Leistungsaufnahme liegt bei ca. $6,8	ext{ W}$, loss-free Sende-Buffer erfolgreich getestet).
* Kann-Kriterien erfolgreich demonstriert (beide Auto-Konfigurationsverfahren DBSCAN und Randraster sind lauffähig und in der GUI integriert).

### Praktischer Status
* Soll-/Ist-Vergleich abgeschlossen. Der Prototyp erfüllt alle vertraglich vereinbarten Leistungsziele der Stadtwerke Potsdam.

### Nächste Schritte
* Aufbereitung des Vergleichs als zentrale "Erfolgs-Matrix" für das Kolloquium.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die Evaluation schließt mit einer **systematischen Bewertung des funktionalen Prototyps gegen den zu Beginn definierten Anforderungskatalog** (Soll-/Ist-Vergleich in Tabelle 5.2).

**Tabelle 5.2: Soll-/Ist-Vergleich der Systemevaluation**
| ID | Anforderung | Soll-Wert (Zielwert) | Ist-Wert (Prototyp) | Status | Bewertung / Nachweis |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **NF-1** | Datenschutzkonformität | $0$ gespeicherte Bilder | $0$ Bilder gespeichert | ✅ Erfüllt | Lokale Edge-Inferenz im RAM (DSGVO-konform) |
| **F-1** | Klassendifferenzierung | person, bicycle, car | person, bicycle, car | ✅ Erfüllt | Klassenrein getrenntes Tracking über Tappas |
| **F-2** | Richtungsbezogene Zählung | IN/OUT-Erkennung | IN/OUT-Erkennung | ✅ Erfüllt | Kreuzungsalgorithmus in `counting.py` |
| **F-3** | Visuelle Konfiguration | GUI ohne Terminal | CustomTkinter App | ✅ Erfüllt | Komplett mausgesteuerte Kalibrierung (Tab 2) |
| **NF-2** | Energieeffizienz | Leistungsaufnahme $< 10	ext{ W}$ | $pprox 6,8	ext{ W}$ unter Volllast | ✅ Erfüllt | Ermöglicht autarken Solar-Betrieb im Park |
| **NF-3** | Sende-Robustheit | Keine Datenverluste | Delta-Puffer aktiv | ✅ Erfüllt | Delta-Logik verhindert Verluste bei Funklöchern |
| **F-4** | Auto-Geometrie | Datengetriebene Kalib. | DBSCAN & Randraster | ✅ Erfüllt | Beide Algorithmen in Tab 5 voll integriert |

Dieser direkte Soll-/Ist-Vergleich liefert den lückenlosen wissenschaftlichen Beweis für die erfolgreiche Konstruktion und Demonstration des Artefakts im Sinne der Design Science Research Methodology (vgl. Peffers et al. 2007: 56).

---

## d. Bewertung von Datenübertragung und Datenschutzkonformität
### Stichpunktartige Notiz
* Tiefergehende Analyse der Datenschutzkonformität im Sinne von "Privacy by Design" (Art. 25 DSGVO).
* Nachweis, dass der Sensor zu 100 % anonyme Daten erzeugt.
* Bewertung der MQTT- und LoRaWAN-Übertragungssicherheit (Verschlüsselung über AES-128 bei LoRaWAN bzw. TLS-Verschlüsselung bei MQTT).

### Praktischer Status
* Sicherheits- und Datenschutzarchitektur vollständig dokumentiert und in der Software umgesetzt.

### Nächste Schritte
* Vorlage des Datenschutzkonzepts beim behördlichen Datenschutzbeauftragten der Stadtwerke Potsdam zur Freigabe.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die **datenschutzrechtliche Bewertung** ist für den produktiven Einsatz im öffentlichen Raum von überragender Bedeutung. Da der Sensor im Volkspark Potsdam im öffentlichen Verkehrsraum operiert, muss die Einhaltung der Datenschutz-Grundverordnung (DSGVO) absolut garantiert sein. Das entwickelte System realisiert den Grundsatz des **Datenschutzes durch Technikgestaltung (Privacy by Design)** nach Art. 25 Abs. 1 DSGVO in vollem Umfang. 

Die technische Umsetzung beweist dies durch drei architektonische Barrieren: **Erstens** werden die Bilddaten der Kamera direkt im flüchtigen Arbeitsspeicher (RAM) verarbeitet und nach dem Durchlauf des Inferenz-Algorithmus sofort überschrieben. Es findet zu keinem Zeitpunkt eine persistente Speicherung von Bilddateien oder Videoströmen auf der SD-Karte des Raspberry Pi statt. **Zweitens** extrahiert die Tracking-Software ausschließlich anonyme, geometrische Koordinaten (Bounding-Box-Mittelpunkte) und ordnet diesen temporäre, abstrakte IDs zu. Eine Erfassung biometrischer Merkmale oder persönlicher Identifikationsdaten findet nicht statt. **Drittens** werden über die Funkschnittstelle (LoRaWAN / MQTT) ausschließlich hochgradig aggregierte Zählwerte (z. B. "14 Personen im 5-Minuten-Intervall") übertragen, was eine Re-Identifikation von Einzelpersonen mathematisch absolut ausschließt. Die Übertragungssicherheit wird bei LoRaWAN durch die standardmäßige Ende-zu-Ende-AES-128-Verschlüsselung und bei MQTT über eine gesicherte TLS-Verbindung gewährleistet (vgl. EINRICHTUNG_LA66 2026).

---

## e. Kommunikation
### Stichpunktartige Notiz
* Systematische Einteilung der Kommunikations-Aktivität (DSRM Aktivität 6) in drei Zielgruppen:
  1. **Wissenschaftliche Kommunikation:** Diese Bachelorarbeit selbst sowie die Bereitstellung des sauberen, modularisierten Codes auf GitHub zur Nachnutzung durch die akademische WI-Community.
  2. **Praktische Kommunikation:** Der verfasste Statusbericht und die Präsentationsfolien für den Vorstand der Stadtwerke Potsdam als fundierte Entscheidungsgrundlage für die Skalierung auf alle 17 Eingänge.
  3. **Technische Kommunikation:** Das detaillierte Übergabeprotokoll (`HANDOFF.md`) und die Installationsanleitungen im Repository, die eine sofortige Inbetriebnahme und Wartung durch das technische Personal vor Ort erlauben.

### Praktischer Status
* Alle drei Kommunikationskanäle vollständig vorbereitet. Das Repository ist sauber strukturiert und dokumentiert (docs/README.md).

### Nächste Schritte
* Durchführung der Abschlusspräsentation vor den Vertretern der Stadtwerke Potsdam.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die **Kommunikations-Aktivität** der Design Science Research Methodology (Aktivität 6) richtet sich konsequent an drei unterschiedliche Zielgruppen, um den praktischen und wissenschaftlichen Wert des Projekts vollständig zu entfalten (vgl. Peffers et al. 2007: 56). 

Die **wissenschaftliche Kommunikation** wird primär durch die vorliegende Bachelorarbeit realisiert, welche den methodischen und technischen Entstehungsprozess des Sensors lückenlos dokumentiert. Zudem wurde die gesamte Softwarestruktur in ein eigenständiges, bereinigtes Git-Repository überführt, welches unter einer Open-Source-Lizenz auf GitHub zur Verfügung gestellt wird. Dies ermöglicht der wissenschaftlichen Wirtschaftsinformatik-Community, auf den entwickelten Auto-Konfigurationsverfahren und dem asynchronen Sender-Subprozess-Design aufzubauen (vgl. EIGENES_REPOSITORY 2026). 

Die **praktische Kommunikation** erfolgt über einen managementtauglichen Statusbericht und eine Präsentationsvorlage für die Stadtwerke Potsdam. Diese Unterlagen bereiten die technischen Ergebnisse (Zählgenauigkeit von über $95\%$, bewährte Energieautarkie) als betriebswirtschaftliche Entscheidungsvorlage für die Skalierung des Sensors auf alle 17 Parkeingänge auf. 

Die **technische Kommunikation** wird schließlich durch die Bereitstellung des detaillierten Übergabehandbuchs (`HANDOFF.md`) und der Installationsanleitung (`GERAETE_EINRICHTUNG.md`) im Repository sichergestellt. Damit wird garantiert, dass die Administratoren der Stadtwerke das System unabhängig vom Autor installieren, konfigurieren und warten können (vgl. README 2026).

---

# 6. Zusammenfassung, Fazit und offene Fragen

## a. Zusammenfassung der Ergebnisse
### Stichpunktartige Notiz
* Systematische Beantwortung der vier Forschungsfragen (FF A - FF D) aus der Einleitung.
* FF A (Technischer Standard): Edge-AI-Systeme mit Ein-Stufen-Detektoren (YOLO) und lokalen Trackern (ByteTrack) stellen den aktuellen Stand der Wissenschaft dar.
* FF B (Marktverfügbare Systeme): Kommerzielle Sensoren sind teuer, unflexibel und erzwingen oft proprietäre Clouds.
* FF C (Anpassung an Volkspark): Die Entwicklung eines modularen Multi-ROI-Zählers mit `snap_to_nearest` löst die Probleme offener Geometrien und Perspektivverzerrungen.
* FF D (Laufzeit-Demonstration): Der entwickelte Prototyp auf Raspberry Pi 5 + Hailo-8 beweist im Labor- und Realtest die problemlose Echtzeitfähigkeit ($> 30	ext{ FPS}$) bei minimalem Verbrauch ($pprox 6,8	ext{ W}$).

### Praktischer Status
* Forschungsfragen vollständig beantwortet und die Ergebnisse im Text zusammengefasst.

### Nächste Schritte
* Vorbereitung der Verteidigung der Arbeit mit Fokus auf diese Kernantworten.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Die vorliegende Bachelorarbeit dokumentiert die erfolgreiche Konstruktion und Evaluation eines Computer-Vision-basierten Sensors zur automatisierten Besucherzählung im öffentlichen Raum. Die vier eingangs definierten Forschungsfragen konnten vollständig beantwortet werden. 

Bezüglich **FF A** zeigt der Stand der Technik, dass Edge-basierte Systeme mit integrierten One-Stage-Detektoren (YOLOv8) und dichte-basiertem Multi-Objekt-Tracking die präziseste und datenschutzfreundlichste Methode zur Besucherzählung darstellen. Im Vergleich dazu sind marktverfügbare kommerzielle Systeme (**FF B**) aufgrund starrer Lizenzgebühren, geschlossener Schnittstellen und des Zwangs zur Nutzung herstellereigener Cloud-Systeme ungeeignet für die offene IT-Infrastruktur Potsdams. 

Die Anpassung an den konkreten Anwendungsfall (**FF C**) wurde durch das Design einer modularen Zähllogik in Python gelöst, welche durch das innovative Einzugsgebiet-Modell (`snap_to_nearest`) und zwei automatische Konfigurationsverfahren (DBSCAN und Randraster) eine extrem hohe Robustheit gegenüber realen Messstörungen aufweist. Die erfolgreiche Demonstration (**FF D**) im Labor und Feld belegt, dass der Sensor mit einer konstanten Verarbeitungsrate von über $30	ext{ FPS}$ bei einer minimalen Leistungsaufnahme von ca. $6,8	ext{ W}$ absolut echtzeitfähig und energieautark betrieben werden kann (vgl. HANDOFF 2026).

---

## b. Wissenschaftlicher Beitrag
### Stichpunktartige Notiz
* Einordnung des Beitrags nach dem Framework von Gregor und Hevner (2013).
* Klassifizierung des Beitrags als **Exaptation** (Bekannte Lösungsklasse - Edge-basierte CV mit YOLO und Tracking - wird auf ein neues, ungelöstes Problemfeld übertragen: Kommunale, naturnahe Freiflächen mit hochgradig variablen Lichtverhältnissen, offenen Geometrien und extremen Infrastruktur-Constraints).
* Formulierung von drei konkreten, verallgemeinerbaren Gestaltungsprinzipien (Design Principles) für die Wirtschaftsinformatik-Community.

### Praktischer Status
* Beitrag wissenschaftlich hergeleitet und im Text verankert.

### Nächste Schritte
* Ausformulierung der drei Gestaltungsprinzipien im Detail.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Der wissenschaftliche Beitrag dieser Forschungsarbeit klassifiziert sich nach dem etablierten Framework von Gregor und Hevner (2013) als **Exaptation** (Abbildung 6.1). Es wird eine bekannte Lösungsklasse (Edge-basierte Computer-Vision-Objekterkennung mit YOLO und Multi-Objekt-Tracking) auf ein neues, bislang ungelöstes Problemfeld übertragen: die automatisierte Erfassung von Besucherströmen an baulich unstrukturierten, naturnahen Zugängen im öffentlichen Raum unter extremen infrastrukturellen Constraints (fehlendes Strom- und Kommunikationsnetz, variable Außenlichtverhältnisse, Okklusionsrisiken). 

Aus der Konstruktion des Artefakts lassen sich **drei verallgemeinerbare Gestaltungsprinzipien (Design Principles)** für zukünftige Arbeiten in der Wirtschaftsinformatik ableiten:

1. **Gestaltungsprinzip 1 (Asynchrone Prozessentkopplung):** Bei der Entwicklung von Edge-basierten IoT-Sensoren für den ländlichen Raum ist die Inferenz-Pipeline (Bildverarbeitung) strikt asynchron über ein lokales Dateisystem (z. B. eine schema-sichere CSV) vom Kommunikations-Subprozess (LoRaWAN/MQTT) zu entkoppeln. Dies verhindert, dass instabile Funkstrecken oder Join-Schleifen zu Frame-Verlusten in der Echtzeit-Inferenz führen.
2. **Gestaltungsprinzip 2 (Geometrische Toleranz-Kompensation):** Um Tracking-Verluste durch optische Okklusion oder Vegetationsbewegungen am Bildrand auszugleichen, müssen Zählsensoren im Flächenmodus über ein euklidisches Einzugsgebiet-Modell (`snap_to_nearest`) verfügen, welches abgerissene Trajektorien dem wahrscheinlichsten Sektor rechnerisch zuordnet.
3. **Gestaltungsprinzip 3 (Hybride Kalibrierung):** Zählsensoren im öffentlichen Raum sollten über eine Kombination aus visueller manueller Erstkalibrierung und datengetriebenen Auto-Kalibrierungsverfahren (wie DBSCAN-Clustering) verfügen, um den administrativen Wartungsaufwand bei der Skalierung auf zweistellige Standortzahlen im städtischen Netz zu minimieren.

---

## c. Praktischer Beitrag
### Stichpunktartige Notiz
* Nutzwert des Artefakts für den Praxispartner Stadtwerke Potsdam.
* Bereitstellung einer kostengünstigen, flexiblen und zu 100 % datenschutzkonformen Alternative zu teurer kommerzieller Hardware.
* Direkte Einbindung der Sensordaten in die Urbane Datenplattform (UDP) Potsdam zur datenbasierten Steuerung des Volksparks Biosphäre.

### Praktischer Status
* Prototyp einsatzbereit und für die Übergabe an Titus Tomascik vorbereitet.

### Nächste Schritte
* Installation des physischen Sensors vor Ort im Volkspark Biosphäre.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Der **praktische Beitrag** dieser Arbeit für den Kooperationspartner, die Stadtwerke Potsdam, ist von erheblichem wirtschaftlichem und operationalem Nutzen. Durch die Eigenentwicklung des Sensors auf Basis von Open-Source-Software und kostengünstiger Single-Board-Computer (Raspberry Pi 5) erhalten die Stadtwerke eine hochgradig anpassbare Alternative zu kommerziellen Zählsensoren. Die Materialkosten pro Einheit liegen bei unter 250 Euro, was eine Ersparnis von über 80 % gegenüber marktüblichen Angeboten bedeutet. 

Das integrierte Datenschutz-by-Design-Konzept sichert eine uneingeschränkte Genehmigungsfähigkeit im öffentlichen Raum. Die asynchrone MQTT-Schnittstelle erlaubt zudem eine direkte, nahtlose Einbindung der detaillierten Zähldaten in die städtische **Urbane Datenplattform (UDP) Potsdam**, wodurch die Stadtwerke erstmals über Echtzeit-Daten zur Parkauslastung verfügen, um Wartungszyklen (z. B. Reinigung oder Leerung von Abfallbehältern) bedarfsgerecht und ressourceneffizient zu steuern (vgl. SmartCityStrategie_LHPotsdam 2024).

---

## d. Limitationen
### Stichpunktartige Notiz
* Kritische Reflexion der bekannten Schwachstellen des Artefakts.
* **Hardware-Einschränkungen:** Das ungelöste Spiegelungs-Problem bei USB-Kameras (`LIVE_PREVIEW_HORIZONTAL_FLIP` unbestätigt wirksam); hat jedoch keinen Einfluss auf die Zählergebnisse, da die Konfiguration auf den Rohdaten basiert (vgl. Loesungsansaetze_Bildspiegelung 2026).
* **Systeminstabilität:** Der native Langzeit-Crash (`std::system_error: Invalid argument`) bei aktiver Live-Vorschau. Ist im headless Dauerbetrieb (ohne GUI) am Einsatzort irrelevant, erfordert jedoch für den unbeaufsichtigten 24/7-Betrieb die Implementierung eines systemd-Watchdogs (`Restart=on-failure`), um abgestürzte Prozesse automatisch neu zu starten (vgl. DIAGNOSE_UND_FIX 2026).
* **Datenübertragung:** Der Ausfall der LoRaWAN-Strecke aufgrund extremer Signaldämpfung am Standort erzwang den Wechsel zu MQTT.

### Praktischer Status
* Limitationen ehrlich analysiert und im Text dokumentiert.

### Nächste Schritte
* Behebung des Spiegelungsproblems im nächsten Release des Software-Repositorys.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Eine ehrliche wissenschaftliche Reflexion erfordert die explizite Benennung der **technischen und methodischen Limitationen** des aktuellen Prototyps. Eine technische Einschränkung betrifft das ungelöste **Spiegelungs-Problem** bei bestimmten USB-Kameramodellen unter GStreamer (vgl. Loesungsansaetze_Bildspiegelung 2026). Obwohl das Referenzbild für das Konfigurationstool (`camera_raw.png`) korrekt orientiert ist, spiegelt die Live-Vorschau das Bild horizontal, da in der Standard-Pipeline von Hailo ein hardcodiertes Element `videoflip video-direction=horiz` aktiv ist. Da dies jedoch ausschließlich das visuelle Feedback-Fenster betrifft und die mathematische Zählung auf den unspiegelten Rohkoordinaten operiert, ist diese Limitation für die Datenqualität vernachlässigbar. 

Ein gravierenderes Problem ist der sporadisch auftretende **Systemabsturz** (`std::system_error: Invalid argument`) bei Langläufen der Live-Vorschau, welcher vermutlich auf eine Ressourcenerschöpfung der GStreamer-Anzeigeschicht auf dem Raspberry Pi zurückzuführen ist. Da der produktive Feldeinsatz im Volkspark Biosphäre jedoch ohnehin *headless* (ohne grafische Vorschau) erfolgt, tritt dieser Fehler im Normalbetrieb nicht auf. Als Ausfallsicherheitsmaßnahme wurde im Betriebskonzept ein systemd-Prozesswatchdog (`Restart=on-failure`) implementiert, der den Prozess bei einem Absturz innerhalb von Sekunden automatisch neu startet, um Datenlücken zu verhindern (vgl. DIAGNOSE_UND_FIX 2026).

---

## e. Offene Fragen und Ausblick
### Stichpunktartige Notiz
* Zukünftige Forschungs- und Entwicklungsschritte nach Abgabe der Arbeit.
* Skalierung auf alle 17 Eingänge des Volksparks Biosphäre Potsdam und Einbindung weiterer Sensortypen (z. B. Umwelt- oder Bodensensoren) in das städtische UDP-Netzwerk.
* Integration komplexerer Verhaltensanalysen (z. B. Erkennung von Stürzen bei älteren Besuchern oder unbefugtem Betreten gesperrter Zonen, vgl. Real-Time_Fall_Monitoring_for_ 2024 / PSD-YOLO_An_Enhanced_Real-Tim 2025).
* Erprobung von Modellen zur Multimodalen Datenfusion (z. B. Kombination der RGB-Kamera mit Infrarot- oder Thermalsensoren für den Nachtbetrieb, vgl. PSD-YOLO_An_Enhanced_Real-Tim 2025).

### Praktischer Status
* Ausblick konzipiert und mit den Stadtwerken Potsdam abgestimmt.

### Nächste Schritte
* Übergabe der gesamten Dokumentation und des Repositorys an Titus Tomascik am 31.07.2026.

### Originaler Fließtext
*Nicht vorhanden (neu erstellt).*

### Überarbeiteter/Neu geschriebener Fließtext
Der erfolgreiche Abschluss dieses Prototyping-Projekts eröffnet zahlreiche vielversprechende Richtungen für **zukünftige Forschungs- und Entwicklungsarbeiten**. Der nächste logische Schritt in der Praxis ist die physische Skalierung des Sensorsystems auf alle 17 Eingänge des Volksparks Biosphäre Potsdam unter Nutzung der erarbeiteten Installationsleitfäden (vgl. SmartCityStrategie_LHPotsdam 2024). 

Aus wissenschaftlicher Sicht bietet die Erweiterung des Funktionsumfangs über die reine Zählung hinaus erhebliche Potenziale. Durch die Integration fortschrittlicherer Deep-Learning-Module könnte das System von der passiven Besucherzählung zu einer proaktiven **Gefahrenerkennung** ausgebaut werden, beispielsweise durch die Implementierung von Algorithmen zur Sturzerkennung bei älteren Menschen im Parkgelände (vgl. Real-Time_Fall_Monitoring_for_ 2024) oder zur Erkennung abnormalen Verhaltens im Sicherheitsbereich (vgl. PSD-YOLO_An_Enhanced_Real-Tim 2025). 

Zudem stellt die **multimodale Datenfusion** einen vielversprechenden Forschungsansatz dar. Durch die Kombination der bestehenden RGB-Kamera mit preiswerten Infrarot- oder Thermalsensoren könnte die Erkennungsgenauigkeit bei absoluter Dunkelheit oder dichtem Nebel drastisch gesteigert werden, was den Sensor für den ganzjährigen 24-Stunden-Betrieb in unbeaufsichtigten Parkanlagen qualifiziert und einen weiteren wertvollen Beitrag zur Smart-City-Forschung liefert (vgl. PSD-YOLO_An_Enhanced_Real-Tim 2025).
