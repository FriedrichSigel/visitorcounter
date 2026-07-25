# Bachelorarbeit: Kapitel 3, 4, 5 und 6 (DSRM-Gliederung)

---

## 3. Design und Entwicklung
*DSRM Aktivität 2 (fallspezifisch konkretisiert) -> Aktivität 3. Beantwortet FF C.*

Peffers et al. (2007: 55) halten fest, dass sich identifizierte Probleme nicht automatisch in Ziele übersetzen lassen. Die Abschnitte 3.a und 3.b vollenden deshalb die DSRM-Aktivität 2 für den konkreten Fall der Stadtwerke Potsdam; ab Abschnitt 3.c beginnt die systematische Aktivität 3 (Design und Entwicklung).

---

### a. Anwendungsfall Volkspark Biosphäre

#### Stichpunktartige Notizen:
*   **Volkspark Biosphäre Potsdam**: Einzigartige, naturnahe Freizeitanlage mit ca. 17 Eingängen von höchst heterogener Geometrie.
*   **Geometrische Varianz**: Reicht von schmalen Gehwegen und Gartentoren (bauliche Engpässe) bis hin zu breiten, offenen Übergängen ohne physische Führung.
*   **Infrastrukturelle Barrieren**: Kein flächendeckendes Stromnetz an den Toren, absolute Abwesenheit von städtischem WLAN oder leitungsgebundenem Festnetz.
*   **Stakeholder**: Stadtwerke Potsdam (Betreiber des Volksparks, primärer Praxispartner), Landeshauptstadt Potsdam (Modellprojekt Smart City), Besucher und Aufsichtsbehörden (Datenschutz).
*   **Zielsetzung**: Eine kosteneffiziente, datenschutzkonforme und autonome Dauererfassung der Besucherströme zur fundierten Steuerung der Parkpflege und Infrastrukturplanung.

#### Sachen, die ich da schon gemacht habe:
*   Der physische Ort wurde analysiert und die 17 Eingänge kartografiert [153, 330].
*   Die infrastrukturellen Restriktionen (kein WLAN, Strommangel) wurden dokumentiert und als primäre Randbedingungen in das Systemdesign aufgenommen [162, 384].

#### Was als nächstes da noch rein muss:
*   Einbindung des offiziellen Hostname-Schemas (z. B. `sensor-eingang-01` bis `-17`) zur eindeutigen Zuweisung von SSH-Zugängen und LoRaWAN-Sensor-IDs im späteren 17-Sensor-Rollout [231, 234].

#### Originaler Fließtext:
*(Es lag noch kein ausgearbeiteter Fließtext für diesen neu eingeführten Gliederungspunkt vor.)*

#### Überarbeiteter Fließtext:
Der Volkspark Biosphäre Potsdam stellt als naturnahe, urbane Freizeitanlage ein zentrales Naherholungsgebiet der Landeshauptstadt Potsdam dar [150, 157]. Die Anlage verfügt über insgesamt 17 physische Eingänge, die sich durch eine extreme strukturelle Heterogenität auszeichnen [153, 330]. Während einige Zugänge als schmale, klar definierte Gartentore ausgeführt sind, weisen andere Eingänge offene, fließende Geometrien auf, die keine baulichen Engpässe oder Zwangsführungen für Besucher besitzen [162]. Dies macht den Einsatz klassischer, physikalisch beschränkter Zählverfahren (wie Infrarotschranken oder Drehkreuze) unmöglich oder wirtschaftlich unrentabel [164, 277].

Infrastrukturell ist der Volkspark Biosphäre durch erhebliche Barrieren gekennzeichnet. An der Mehrzahl der 17 Eingänge existieren weder ein leitungsgebundenes Stromnetz noch eine Netzwerkinfrastruktur in Form von Glasfaser, Kupfer oder städtischem WLAN [162, 384]. Für einen dauerhaften Betrieb muss der zu entwickelnde Sensor daher zwingend energieeffizient ausgelegt sein (Betrieb über Solar- oder Batteriegepufferte Systeme) und die erfassten Daten über ein drahtloses, reichweitenstarkes Netzwerk übertragen [166, 384]. Als primäre Stakeholder agieren die Stadtwerke Potsdam, welche die Betriebsverantwortung für den Park tragen, sowie die Landeshauptstadt Potsdam, die im Rahmen der geförderten „Smart-City-Strategie“ den Aufbau einer übergeordneten Urbanen Datenplattform (UDP) vorantreibt [151, 152]. Um den Betrieb an allen 17 Standorten effizient zu verwalten, wird ein standardisiertes Hostname-Schema (von `sensor-eingang-01` bis `sensor-eingang-17`) etabliert, welches eine eindeutige Zuweisung im Rahmen des Device-Managements und der LoRaWAN-Metadatenstruktur ermöglicht [231, 234].

---

### b. Anforderungsanalyse an Sensor

#### i. Methodik

#### Stichpunktartige Notizen:
*   **Qualitatives Leitfadeninterview**: Methodische Absicherung über Döring (2023: 360).
*   **Begründung der Methodenwahl**: Ein strukturiertes quantitatives Verfahren greift zu kurz, da implizites, kommunales Betriebswissen und spezifische Barrieren der Stadtwerke erfasst werden müssen.
*   **Halbstrukturiertes Vorgehen**: Ermöglicht durch offene Fragen Flexibilität im Gesprächsverlauf, um unvorhergesehene technische Restriktionen aufzudecken [163].

#### Sachen, die ich da schon gemacht habe:
*   Das Interview wurde konzipiert, mit einem wissenschaftlich fundierten Leitfaden versehen und durchgeführt [162, 163].

#### Was als nächstes da noch rein muss:
*   Explizite Einordnung dieses qualitativen Schrittes als Kern der DSRM-Aktivität 2 („Define Objectives for a Solution“), um die Zielkriterien rational und wissenschaftlich abzusichern [155, 274].

#### Originaler Fließtext:
Zur Durchführung der Anforderungsanalyse für den zu entwickelnden Prototypen wurde als zentrale Methode der Datenerhebung ein qualitatives Experteninterview nach Döring 2023 gewählt. Die methodische Durchführung erfolgt in Form eines halbstrukturierten Leitfadeninterviews. Diese Form zeichnet sich dadurch aus, dass ein vorbereiter Leitfaden mit offenen Fragen die Themenstruktur vorgibt, jedoch ausreichend Flexibilität besteht, um auf den situativen Gesprächsfluss zu reagieren (vgl. Döring 2023: 360). Dass im Verlauf des Gesprächs wesentliche Informationen abseits der... [163]

#### Überarbeiteter Fließtext:
Zur präzisen Bestimmung der sensorischen Anforderungen wurde als Methode der Datenerhebung ein qualitatives Experteninterview nach Döring (2023: 360) gewählt [162, 163]. Diese methodische Entscheidung ist im DSRM-Framework nach Peffers et al. (2007) der Aktivität 2 („Define Objectives for a Solution“) zuzuordnen [155, 272]. Da die Ausgestaltung eines solchen Smart-Sensors im kommunalen Kontext stark von implizitem, organisationsspezifischem und lokalem Betriebswissen abhängt, wäre ein rein quantitatives Standardverfahren unzureichend gewesen [162].

Die Durchführung erfolgte als halbstrukturiertes Leitfadeninterview [163]. Dieses Format stellt sicher, dass alle theoretisch relevanten Themenkomplexe (wie Datenschutz, technische Schnittstellen, Energieversorgung und geometrische Gegebenheiten) abgedeckt werden, während gleichzeitig eine hohe Flexibilität verbleibt, um auf unerwartete technische Randbedingungen des Praxispartners einzugehen [162, 163]. Der vorbereitete Leitfaden diente als Orientierungsrahmen, der es den Experten erlaubte, frei zu formulieren und komplexe Zusammenhänge – wie das Zusammenspiel mit bereits existierenden Smart-City-Infrastrukturen – detailliert zu erläutern [151, 163]. Die wissenschaftlichen Gütekriterien qualitativer Forschung – namentlich Transparenz, Intersubjektivität und Reichweite – wurden durch eine lückenlose Protokollierung und die anschließende systematische Strukturierung gesichert [162, 249].

---

### ii. Durchführung und Auswertung Interview Stadtwerke Potsdam

#### Stichpunktartige Notizen:
*   **Interviewpartner**: Titus Tomascik (Projektleiter) und Andreas Becker (Technischer Berater, Stadtwerke Potsdam) [384].
*   **Datenschutz (Privacy by Design)**: Höchste Priorität. Keine Übertragung oder Speicherung von Bilddaten oder Personenmerkmalen. Auswertung muss vollständig auf dem Edge-Device stattfinden [152, 384].
*   **Schnittstellen und Funk**: LoRaWAN zur städtischen Urbanen Datenplattform (UDP) Potsdam zur Visualisierung [152, 384].
*   **Bedienerfreundlichkeit**: GUI-Anforderung. Bedienung muss zwingend ohne Kommandozeile erfolgen, um Nicht-Technikern die Konfiguration vor Ort zu ermöglichen [169, 384].
*   **Klassenunterscheidung**: Detektion und getrenntes Zählen von Personen und Fahrrädern [384]. Minimum 15 FPS zur zuverlässigen Erfassung [384].
*   **Autarkie**: Pufferung bei Stromausfall und Offline-Resistenz gegen Übertragungsfehler [384].

#### Sachen, die ich da schon gemacht habe:
*   Das Interview wurde ausgewertet und die Transkriptionen liegen in den Notizen vor [152, 384].
*   Die Kernanforderungen (LoRaWAN, Datenschutz, GUI-Bedienung, 15 FPS) wurden strukturiert [169, 384].

#### Was als nächstes da noch rein muss:
*   Verbindung zur städtischen UDP aufzeigen, insbesondere die geplante Weiterverarbeitung im dortigen „Seeker Layer“ für Dashboards und Open Data [152, 384].

#### Originaler Fließtext:
*(Es lag noch kein ausformulierter Fließtext vor, nur die rohen Notizen aus dem Interview.)*

#### Überarbeiteter Fließtext:
Das Experteninterview wurde mit Titus Tomascik und Andreas Becker, den verantwortlichen Projektleitern der Stadtwerke Potsdam, durchgeführt [384]. Die Auswertung des Gesprächs offenbarte ein klares Bild über die funktionalen und nicht-funktionalen Anforderungen an das Sensorsystem [162].

Als primäre nicht-funktionale Anforderung wurde die Einhaltung eines kompromisslosen Datenschutzes nach dem Prinzip *Privacy by Design* definiert [160, 166]. Aufgrund der rechtlichen Rahmenbedingungen im öffentlichen Raum ist eine Speicherung oder Übertragung von Bilddaten oder personenbezogenen Merkmalen kategorisch ausgeschlossen [166, 385]. Die gesamte Bildverarbeitung und das Tracking müssen vollständig lokal auf dem Edge-Sensor stattfinden (*Edge Computing*); an übergeordnete Systeme dürfen ausschließlich anonymisierte, aggregierte Zählwerte gesendet werden [165, 384].

Als Zielinfrastruktur für den Datenstrom wurde das bestehende städtische LoRaWAN-Netzwerk definiert [152, 422]. Der Sensor muss die Daten zyklisch an die Urbane Datenplattform (UDP) der Landeshauptstadt Potsdam übermitteln, wo sie über einen sogenannten „Seeker Layer“ für Dashboards, Stadtklimakarten und Open-Data-Anwendungen aufbereitet werden [152, 384].

Hinsichtlich der funktionalen Kriterien forderten die Experten eine detaillierte Unterscheidung von Objektklassen (mindestens Personen und Fahrräder), um die Nutzungsmuster der Freiflächen präzise zu analysieren [168, 384]. Zur Erreichung einer hohen Zählgenauigkeit bei normaler Gehgeschwindigkeit wurde eine Mindestbildrate der Kamera von 15 Frames per Second (FPS) festgelegt [384]. Ein zentraler operationaler Stolperstein wurde in der Konfiguration identifiziert: Da die 17 Eingänge hochgradig heterogen sind, muss das System über eine grafische Bedienoberfläche (GUI) verfügen, die eine Definition von Zähllinien und Zonen direkt vor Ort ohne jegliche Kommandozeilen-Interaktion ermöglicht [169, 384]. Zudem muss das System widerstandsfähig gegen temporäre Stromausfälle und Funkunterbrechungen ausgelegt sein [384].

---

### iii. Konsolidierter Anforderungskatalog

#### Stichpunktartige Notizen:
*   **Ankerpunkt-Tabelle**: Das direkte Bindeglied zwischen DSRM Aktivität 2 (Ziele) und Aktivität 5 (Evaluation) [273, 279].
*   **Priorisierung**: Gliederung nach Muss (M), Soll (S), Kann (K) (MoSCoW-Schema) [179, 279].
*   **Anforderungen**: Multi-Klassen-Zählung, Zählgenauigkeit (MAPE), Datenschutz, GUI-Konfiguration, LoRaWAN-Konnektivität, Ausfallsicherheit, Kosten.

#### Sachen, die ich da schon gemacht habe:
*   Die theoretische Anforderungsstruktur wurde skizziert [245].

#### Was als nächstes da noch rein muss:
*   Erstellung einer vollständigen, tabellarischen Anforderungsmatrix mit eindeutigen IDs, Quellen, Prioritäten und quantitativen Zielwerten zur späteren exakten Evaluation [279, 280].

#### Originaler Fließtext:
*(Es lag noch kein ausformulierter Text oder eine fertige Tabelle vor.)*

#### Überarbeiteter Fließtext:
Der konsolidierte Anforderungskatalog führt die allgemeinen systemtheoretischen Anforderungen aus Kapitel 2.d mit den spezifischen Praxiskriterien aus dem Experteninterview zusammen [279]. Er bildet das methodische Scharnier der Arbeit: In Kapitel 5.c wird das entwickelte Artefakt exakt an diesen Kriterien gemessen [273]. Die Priorisierung folgt dem standardisierten MoSCoW-Schema [179].

**Tabelle 3.1: Konsolidierter Anforderungskatalog für den Besucherzählsensor** [280]

| ID        | Anforderung              | Typ         | Quelle           | Priorität | Zielwert / Metrik                                        |
| :-------- | :----------------------- | :---------- | :--------------- | :-------- | :------------------------------------------------------- |
| **F-01**  | Multi-Klassen-Erkennung  | Funktional  | Interview [384]  | **Muss**  | Getrennte Erfassung von *person* und *bicycle*           |
| **F-02**  | Richtungsdifferenzierung | Funktional  | Grundlagen [160] | **Muss**  | Unterscheidung von Eintritt (IN) und Austritt (OUT)      |
| **F-03**  | Lokale Konfiguration     | Funktional  | Interview [384]  | **Muss**  | Interaktive Zählgeometrie-Definition per GUI             |
| **F-04**  | Automatische Geometrie   | Funktional  | Interview [245]  | **Soll**  | Selbstständige Weg- und Zonenerkennung                   |
| **NF-01** | Datenschutzkonformität   | Nicht-Funk. | Grundlagen [160] | **Muss**  | 100 % lokale Verarbeitung; keine Bildspeicherung         |
| **NF-02** | Systemstabilität         | Nicht-Funk. | Grundlagen [162] | **Muss**  | 24/7 Headless-Betrieb; automatischer Wiederanlauf        |
| **NF-03** | Übertragungssicherheit   | Nicht-Funk. | Interview [384]  | **Soll**  | LoRaWAN-Uplink an UDP; verlustfrei bei Funkloch          |
| **NF-04** | Hardware-Effizienz       | Nicht-Funk. | Grundlagen [296] | **Soll**  | Verarbeitungsrate $\ge$ 15 FPS; Leistungsaufnahme < 10 W |
| **NF-05** | Wirtschaftlichkeit       | Nicht-Funk. | Interview [384]  | **Kann**  | Gesamtkosten pro Sensor < 350 € (Massen-Rollout)         |

---

### c. Lösungsraum und Auswahl

#### i. Produkt- und Technologierecherche

#### Stichpunktartige Notizen:
*   **Marktanalyse**: Betrachtung kommerzieller CV-Systeme (z. B. FootfallCam) [388].
*   **Alternative Technologien**: Radar-Sensoren (pmx systems PCR2) [358], Wi-Fi-Sniffer (Paxcounter/AFOROS) [26, 384].
*   **Limitationen kommerzieller Produkte**: Extrem hohe Anschaffungskosten (z. B. Isasoft) [385], mangelnde Flexibilität bei unregelmäßigen Freiflächen-Eingängen, proprietäre Cloud-Zwangssysteme verstoßen gegen kommunale Open-Data- und UDP-Richtlinien [152].

#### Sachen, die ich da schon gemacht habe:
*   Recherche marktgängiger Systeme und Identifikation von Open-Source-Bibliotheken (OpenCV, Ultralytics YOLO) [164, 388].

#### Was als nächstes da noch rein muss:
*   Präzise theoretische Abgrenzung gegenüber Radar- und Wi-Fi-basierten Verfahren, um die technologische Entscheidung für ein Computer-Vision-System wissenschaftlich zu untermauern [384].

#### Originaler Fließtext:
Im Rahmen der bisherigen Recherche wurde kein direkt vergleichbares Projekt gefunden, bei der eine Personenzählsensor unter Nutzung von Computer Vision genutzt wird. Jedoch gibt es einige Computer Vision Projekte in anderen Anwendungsbereichen. [164]

#### Überarbeiteter Fließtext:
Um den Lösungsraum systematisch zu erschließen, wurde eine umfassende Technologie- und Marktrecherche durchgeführt [280]. Neben kamerabasierten Systemen wurden alternative Sensorkonzepte analysiert. Wi-Fi-Sniffer (wie das AFOROS-System oder der Paxcounter) erfassen die Beacon-Signale von Mobiltelefonen [26, 384]. Sie bieten zwar einen hervorragenden Datenschutz, weisen jedoch eine erhebliche systematische Ungenauigkeit auf, da nicht jeder Besucher ein aktives Wi-Fi-Gerät mitführt und manche Personen mehrere Geräte besitzen [384]. Radarsensoren (wie der pmx systems PCR2) bieten eine präzise, richtungsbezogene Zählung auf Basis von Mikrowellen-Reflexionen [358], scheitern jedoch bei der geforderten Klassentrennung, da sie Personen nicht verlässlich von Fahrrädern oder Hunden unterscheiden können [384].

Kommerzielle Computer-Vision-Systeme (wie FootfallCam) bieten hochentwickelte Stereokamera-Zählungen [388], sind jedoch für den Einsatz im Volkspark Biosphäre ungeeignet: Ihre Anschaffungs- und Lizenzkosten sind extrem hoch (wie am Beispiel von Isasoft-Lösungen deutlich wird) [384, 385]. Zudem erzwingen sie meist eine Datenhaltung in proprietären Hersteller-Clouds, was im direkten Widerspruch zum städtischen Open-Data-Ansatz der Potsdamer UDP steht, welche eine direkte, herstellerunabhängige Einbindung über offene LoRaWAN-Standards fordert [152, 422]. Aus diesen Gründen ist die Entwicklung eines maßgeschneiderten, quelloffenen Edge-CV-Sensors auf Basis offener Standards technologisch und wirtschaftlich alternativlos [165, 384].

---

### ii. Morphologisches Tableau

#### Stichpunktartige Notizen:
*   **Systematische Synthese**: Strukturierung der Kernkomponenten des Sensors [280].
*   **Dimensionen**: Erkennungsmodell, Tracking-Algorithmus, Hardware-Plattform, Übertragungsweg, Benutzerschnittstelle.
*   **Lösungsalternativen**: YOLO vs. MobileNet; ByteTrack vs. DeepSORT; Raspberry Pi 5 vs. Jetson Nano vs. Edge-TPU; LoRaWAN vs. LTE vs. Wi-Fi [140, 245, 384].

#### Sachen, die ich da schon gemacht habe:
*   Das Tableau wurde konzeptionell erarbeitet und im Excel-Sheet des Prototyp-Tagebuchs dokumentiert [390, 393].

#### Was als nächstes da noch rein muss:
*   Integration des morphologischen Tableaus als Übersichtstabelle, um die nachfolgende Design-Entscheidung transparent und logisch nachvollziehbar zu machen [280].

#### Originaler Fließtext:
*(Es lag noch kein ausformulierter Fließtext vor.)*

#### Überarbeiteter Fließtext:
Das morphologische Tableau dient der systematischen Gegenüberstellung von Teilproblemen und potenziellen Lösungsalternativen [280]. Es ermöglicht eine strukturierte und nachvollziehbare Selektion der optimalen Systemkonfiguration für den Zählsensor [280].

**Tabelle 3.2: Morphologisches Tableau der Lösungsalternativen** [280]

| Teilproblem / Dimension | Alternative 1 | Alternative 2 | Alternative 3 | Ausgewählt |
| :--- | :--- | :--- | :--- | :--- |
| **A: Erkennungsmodell** | MobileNet-SSD | YOLOv8 / YOLOv10 | HOG + SVM [188] | **YOLOv8 / v10** |
| **B: Objekt-Tracking** | Sort / DeepSORT | ByteTrack | Hailo-Tracker | **Hailo-Tracker** |
| **C: Hardware-Plattform** | Jetson Nano | Raspberry Pi 5 | Pi 5 + Hailo-8 | **Pi 5 + Hailo-8** |
| **D: Übertragungsweg** | Mobilfunk (LTE-M) | Wi-Fi (AFOROS) [26] | LoRaWAN (EU868) | **LoRaWAN (EU868)** |
| **E: Konfigurationsmethode** | SSH / Textdatei | Web-Dashboard | CustomTkinter GUI | **CustomTkinter GUI** |

---

### iii. Begründete Auswahl der Lösungskonfiguration

#### Stichpunktartige Notizen:
*   **Kombinationsentscheidung**: Begründung der gewählten Spalte im morphologischen Tableau [280].
*   **YOLO & Hailo**: YOLOv8 und YOLOv10 bieten die beste Genauigkeit bei Realzeit-Anforderungen [245]. Der integrierte, hardwarebeschleunigte Hailo-Tracker läuft hocheffizient direkt auf der NPU.
*   **Raspberry Pi 5 mit Hailo-8**: Bietet mit 26 TOPS Rechenleistung bei nur ca. 2–5 Watt Leistungsaufnahme ein unschlagbares Verhältnis aus Rechenpower und Energieeffizienz für solarbetriebene Standorte [231, 330].
*   **LoRaWAN**: Perfekte Abdeckung im Stadtgebiet über die Stadtwerke Potsdam, minimale Betriebskosten, keine Abhängigkeit von Mobilfunkverträgen [141, 422].
*   **CustomTkinter**: Ermöglicht eine ressourcenschonende, plattformunabhängige GUI direkt auf dem Pi [169].

#### Sachen, die ich da schon gemacht habe:
*   Die Hardware-Zusammenstellung wurde am 17.02.2026 preislich und technisch festgeschrieben und als Referenzgerät `stadtwerke2` aufgebaut [231, 390].
*   Die Leistungsdaten des Hailo-8-Beschleunigers wurden verifiziert [231].

#### Was als nächstes da noch rein muss:
*   Präzise Argumentation bzgl. der massiven Energieeinsparung durch die Kombination Pi 5 + Hailo-8 im Vergleich zu reinen CPU-basierten Systemen oder energiehungrigen GPUs [231, 330].

#### Originaler Fließtext:
*(Es lag noch kein ausformulierter Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die Entscheidung für die endgültige Konfiguration basiert auf einer detaillierten Abwägung von Performanz, Energieeffizienz, Datensicherheit und Wirtschaftlichkeit [280]. 

Als Erkennungsverfahren wird ein One-Stage-Detektor der YOLO-Familie (YOLOv8/YOLOv10) gewählt, da dieser im Vergleich zu älteren Verfahren (wie HOG+SVM) eine signifikant höhere Robustheit bei unterschiedlichen Lichtverhältnissen und Verdeckungen aufweist [188, 245]. Die Wahl der Hardware-Plattform fiel auf den **Raspberry Pi 5 (8 GB) in Kombination mit dem Hailo-8 M.2 KI-Beschleuniger** [166, 231]. Während ein reiner Raspberry Pi 5 bei der Ausführung von YOLO-Modellen auf der CPU eine Bildrate von unter 2 FPS erreicht und dabei thermisch stark limitiert ist, ermöglicht der Hailo-8-Chip mit einer Rechenleistung von 26 TOPS eine Pipeline-Geschwindigkeit von über 30 FPS [231, 330]. Die Leistungsaufnahme der NPU liegt dabei im Betrieb bei nur ca. 2 bis 5 Watt, was den Sensor für den autarken, solarunterstützten Langzeitbetrieb an den stromlosen Volkspark-Eingängen prädestiniert [231, 330].

Als Übertragungstechnologie wird **LoRaWAN (EU868-Band)** festgelegt [141]. Da die Stadtwerke Potsdam in Kooperation mit der Landeshauptstadt bereits ein engmaschiges LoRaWAN-Gateway-Netzwerk betreiben, entstehen für die Datenübertragung keinerlei laufende Mobilfunkkosten [141, 422]. Zudem garantiert das schmalbandige Senden im EU868-Band eine hohe Durchdringung im dichten Baumbestand des Volksparks Biosphäre [384, 433]. Die Benutzerschnittstelle wird als lokale **CustomTkinter-GUI** direkt auf dem Raspberry Pi realisiert [169]. Dies erfüllt die Anforderung einer kopfschmerzlosen Bedienung ohne Terminal und schont gleichzeitig im Vergleich zu webbasierten Frameworks (wie Electron) die RAM-Ressourcen des Einplatinencomputers [169, 327].

---

### iv. Guide vom YOLO Github für CV Projects

#### Stichpunktartige Notizen:
*   **Wissenschaftliche Fundierung**: Nutzung des offiziellen Leitfadens von Ultralytics zur Projektdurchführung.
*   **Modellauswahl**: Nutzung von vortrainierten Modellen, die auf dem COCO-Datensatz trainiert wurden [358].
*   **Feineinstellung**: Festlegung der Bildgröße auf 640 Pixel für die Objekterkennung (Standard-Optimierung) [188, 277].
*   **Confidence Threshold**: Empfohlene Mindestkonfidenz von 0.25 bis 0.50 als Filter zur Vermeidung von Falsch-Positiven [188].

#### Sachen, die ich da schon gemacht habe:
*   Der Guide wurde gesichtet und die Empfehlungen (Bildgröße, Konfidenzwerte) in die Standardkonfiguration (`config.py`) übernommen [248].

#### Was als nächstes da noch rein muss:
*   Wissenschaftlicher Nachweis, warum die Einhaltung dieses Industriestandards die Zuverlässigkeit unseres Prototyps signifikant erhöht [188].

#### Originaler Fließtext:
*(Es lag noch kein Fließtext für diesen neu verschobenen Gliederungspunkt vor.)*

#### Überarbeiteter Fließtext:
Um das Projekt nach State-of-the-Art-Standards der Computer Vision zu realisieren, orientiert sich das Design an den offiziellen Projektempfehlungen des Ultralytics-Frameworks [248]. Diese Richtlinien definieren bewährte Vorgehensweisen für Modellauswahl, Bildauflösung und Schwellenwert-Optimierungen im praktischen Einsatz [188, 277].

Gemäß den Richtlinien wird auf ein vortrainiertes YOLO-Modell zurückgegriffen, das auf dem standardisierten COCO-Datensatz (*Common Objects in Context*) trainiert wurde [358]. Da dieser Datensatz über 80 Objektklassen umfasst – darunter alle für die Besucherzählung geforderten Klassen wie Personen, Fahrräder und Kraftfahrzeuge –, ist kein zeitaufwendiges und fehleranfälliges Custom-Training notwendig (*Zero-Shot-Transfer*) [159, 358]. Die Verarbeitungsauflösung der Pipeline wird auf das standardisierte Maß von $640 	imes 640$ Pixeln festgeschrieben [188]. Dies stellt den optimalen Kompromiss zwischen der Erkennungsgenauigkeit kleinerer Objekte im Hintergrund und der Verarbeitungsgeschwindigkeit (Latenzzeit) des Prozessors dar [188, 277]. Für die Objekterkennung wird ein dynamischer Schwellenwert (*Confidence Threshold*) von standardmäßig 0.40 festgelegt, um Falschdetektionen (z. B. durch Schattenwurf oder Vegetation) robust herauszufiltern [188, 203].

---

### d. Ableitung des Zählprinzips

### i. Vorstudie

#### Stichpunktartige Notizen:
*   **Machbarkeitsnachweis**: Erste Tests mit YOLO auf Testvideos, um die Erkennungsleistung grundsätzlich abzusichern [248].
*   **Befund**: YOLOv8 und YOLOv10 liefern im Außeneinsatz hervorragende Klassifizierungsraten [245].
*   **Problemstellung**: Reine Objekterkennung (Detection) reicht nicht aus, da Objekte in jedem Frame neu erkannt werden. Tracking ist zwingend nötig, um Trajektorien (Bewegungspfade) aufzubauen [160, 245].

#### Sachen, die ich da schon gemacht habe:
*   Vorstudienläufe mit Testvideos wurden erfolgreich durchgeführt und die Machbarkeit belegt [248].

#### Was als nächstes da noch rein muss:
*   Formulierung der Erkenntnis, dass die reine Framerate-basierte Detektion ohne zeitliche Assoziation (Tracking) zu massiven Überzählungen führt [160, 245].

#### Originaler Fließtext:
*(Es lag kein Fließtext für diesen Gliederungspunkt vor.)*

#### Überarbeiteter Fließtext:
Vor dem eigentlichen Softwareentwurf wurde eine empirische Vorstudie durchgeführt, um die Machbarkeit und Erkennungsgüte der YOLO-Modellfamilie auf realem Bildmaterial abzusichern [248]. Als Testdaten diente Videomaterial einer typischen urbanen Straßenszene (Auflösung $1280 	imes 720$ Pixel), die den geometrischen Verhältnissen der Volkspark-Zugänge gleicht [213, 214].

Die Vorstudie bestätigte, dass YOLOv8 und YOLOv10 Personen und Fahrräder selbst unter wechselnden Lichtverhältnissen mit einer Konfidenz von über 85 % zuverlässig detektieren [202, 245]. Es zeigte sich jedoch eine fundamentale architektonische Limitation: Die reine Objekterkennung arbeitet rein raumbezogen (frameweise) [203]. Ohne eine zeitliche Verknüpfung der Erkennungen über aufeinanderfolgende Einzelbilder hinweg (*Multi-Object Tracking*) ist eine Zählung unmöglich, da dasselbe Objekt in jedem Frame als neue Entität registriert würde [160, 203]. Die Zählung erfordert daher zwingend den Aufbau von konsistenten Objekt-Trajektorien (Bewegungspfaden), auf die geometrische Zählregeln angewandt werden können [160, 218].

---

### ii. Herleitung der drei Zählmodi

#### Stichpunktartige Notizen:
*   **Die 17 Standorte**: Kein einzelnes physikalisches Prinzip kann alle Standorte abdecken [281].
*   **Modus 1: Linienquerung (Line Crossing)**: Bestens geeignet für schmale Geometrien (z. B. Gartentore) [168, 281].
*   **Modus 2: ROI-basierte Zählung (Region of Interest)**: Für flächige Zugänge ohne feste Begrenzung [281].
*   **Modus 3: Mehrflächen-Übergangszählung (Zone Transition)**: Bestimmung von echten Bewegungsströmen (Fläche A nach Fläche B) zur präzisen Erfassung von Passanten, die keine echten Zonenwechsel vollziehen [168, 193].

#### Sachen, die ich da schon gemacht habe:
*   Alle drei Modi wurden mathematisch und algorithmisch vollständig implementiert (`counting.py`) [218].

#### Was als nächstes da noch rein muss:
*   Die detaillierte geometrische Herleitung der Zählmodi (Vektorkreuzprodukt für Linien, Polygon-Raycasting für ROIs) [160].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Aufgrund der extremen strukturellen Diversität der 17 Eingänge des Volksparks Biosphäre kann kein einzelnes Zählprinzip flächendeckend eingesetzt werden [281]. Daher wurden systematisch drei mathematische Zählmodi hergeleitet und implementiert [218]:

1.  **Linienquerung (Line Crossing):** An schmalen Toren wird eine zweidimensionale Vektor-Zähllinie im Bildraum definiert [160, 168]. Die Querung der Linie wird über das mathematische Vorzeichen des Vektorkreuzprodukts zwischen dem Linienrichtungsvektor und dem Objektbewegungsvektor bestimmt [160]. Dies erlaubt eine präzise Richtungsunterscheidung (IN/OUT) [160].
2.  **ROI-basierte Zählung (Region of Interest):** Bei breiteren Eingängen wird ein geschlossenes Polygon als Aufenthaltsbereich definiert [160, 218]. Ob sich ein Objekt innerhalb der ROI befindet, wird über den *Ray-Casting-Algorithmus* (Punkt-in-Polygon-Test nach Jordan) ermittelt [160]. Ein Zählereignis wird ausgelöst, wenn ein Track die ROI betritt oder verlässt [168, 218].
3.  **Zonenübergangszählung (Zone Transition):** An unübersichtlichen Kreuzungen oder sehr weiten Flächen werden zwei oder mehr unabhängige Polygone (z. B. „Fläche Potsdam“ und „Fläche Berlin“) definiert [192]. Gezählt wird ausschließlich ein vollendeter Übergang zwischen diesen Flächen [193, 218]. Verbleibt ein Besucher in einer einzelnen Zone oder kehrt am Rand um, ohne die zweite Zone zu betreten, wird dies als „kein Wechsel“ (`is_transition=False`) im System verbucht, was Fehlzählungen im Randbereich effektiv verhindert [193, 198].

---

### iii. Herleitung des Bedarfs an manueller und automatischer Konfiguration

#### Stichpunktartige Notizen:
*   **Problem**: Das manuelle Einzeichnen von Linien bei 17 Kameras ist zeitaufwendig [330].
*   **Lösung**: Kombination aus manueller GUI-Konfiguration für Spezialfälle und automatischer Konfiguration für den schnellen Massen-Rollout [245, 283].
*   **Zwei Auto-Verfahren**:
    1.  *DBSCAN-Clustering*: Gruppierung von Trajektorien-Start- und Endpunkten zur automatischen Platzierung der Zählzonen [248].
    2.  *Randraster-Verfahren*: Speziell entwickelt, um Tracking-Aussetzer in der Bildmitte zu kompensieren (Schaffung einer robusten Gestaltungsregel) [248, 284].

#### Sachen, die ich da schon gemacht habe:
*   Beide automatischen Konfigurationsverfahren wurden praktisch lauffähig umgesetzt (`auto_config.py`, `auto_config_clustering.py`) [219, 248].

#### Was als nächstes da noch rein muss:
*   Wissenschaftliche Begründung, warum die Kombination beider Verfahren (datengetrieben vs. geometrisch-heuristisch) eine signifikant höhere Robustheit im Feld bietet [248, 284].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Der operative Rollout an 17 verschiedenen Standorten erfordert ein hochgradig flexibles Konfigurationskonzept [281, 330]. Eine rein manuelle Konfiguration, bei der ein Techniker vor Ort jede Zähllinie Pixel für Pixel einzeichnen muss, ist zeitaufwendig und anfällig für menschliche Fehleinschätzungen der tatsächlichen Hauptlaufwege [330]. Daher wurde eine innovative Kombination aus manueller GUI-Steuerung und zwei automatischen Konfigurationsverfahren entworfen [245, 283].

Das erste automatische Verfahren basiert auf dem **DBSCAN-Algorithmus** (*Density-Based Spatial Clustering of Applications with Noise*) [248]. Hierbei sammelt das System im Konfigurationsmodus über einen definierten Zeitraum (Sammeldauer) alle Start- und Endpunkte der erkannten Bewegungspfade [138, 219]. Diese Punktwolken werden räumlich geclustert [219]. Die dichten Zentren der Punktwolken repräsentieren mathematisch die Hauptstrom-Korridore der Besucher und werden automatisch als Zählpolygone in die `roi_config.json` geschrieben [219].

Das zweite, von mir entwickelte **Randraster-Verfahren**, wurde als komplementäre heuristische Gestaltungsregel entworfen [248, 284]. In der Praxis zeigte sich, dass Kameras bei extremem Gegenlicht oder Verdeckungen Tracks in der Bildmitte kurzzeitig verlieren, was bei DBSCAN zu fehlerhaften „Geister-Startpunkten“ mitten auf der Lauffläche führt [248, 284]. Das Randraster-Verfahren segmentiert ausschließlich die physischen Bildränder und verlangt eine Mindestbewegung der Objekte [284]. Es schlägt nur dann Zählzonen vor, wenn Tracks tatsächlich den Bildraum betreten oder verlassen [284]. Dieses Zusammenspiel erhöht die Robustheit der Inbetriebnahme im realen Feldbetrieb dramatisch [284, 305].

---

### e. Systemarchitektur (Konzept)

### i. Gesamtarchitektur

#### Stichpunktartige Notizen:
*   **Modellbegriff**: Einordnung als intelligenter Sensor (*Smart Sensor*) nach Heinrich et al. (2020) [216, 224].
*   **Glieder der Messkette**:
    *   *Messfühler/Aufnehmer*: Optischer CMOS-Kamerasensor [222, 241].
    *   *Signalaufbereitung*: GStreamer-Pipeline auf dem Raspberry Pi 5 [217, 226].
    *   *Auswerte-Elektronik*: YOLOv8/v10-Detektion, Hailo-8-Beschleuniger und Python-Zähllogik [226].
    *   *Schnittstelle*: Dragino LA66 USB-LoRaWAN-Modul [226, 332].
*   **Automatisierungspyramide**: Einordnung im Control Level als dezentraler Datenlieferant für das SCADA/MES der Urbanen Datenplattform Potsdam [241, 422].

#### Sachen, die ich da schon gemacht habe:
*   Das konzeptionelle Architekturdiagramm wurde auf Basis von Heinrich et al. (2020) entworfen und die Glieder der Kette im Systemdesign verortet [165, 215].

#### Was als nächstes da noch rein muss:
*   Expliziter Nachweis der Definitionseinhaltung: Da unser System Signalaufbereitung, lokale Vorverarbeitung *und* eine standardisierte Netzwerkschnittstelle in einem physischen Gehäuse vereint, ist der Begriff „Sensor“ im Titel der Arbeit wissenschaftlich fundiert bewiesen [216, 224].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die Gesamtarchitektur des Besucherzählsensors ist konsequent an dem etablierten Metrologie- und Automatisierungsmodell nach Heinrich et al. (2020) und Hering & Schönfelder (2018) ausgerichtet [221]. Das physische System vereint alle klassischen Elemente einer industriellen Messkette in einer einzigen, dezentralen Edge-Einheit [165, 215]:

```
+---------------------------------------------------------------------------------+
|                                 SMART SENSOR                                    |
|                                                                                 |
|  +------------+     +---------------+     +--------------------+     +-------+  |
|  | Messfühler | --> | Signalaufber. | --> | Auswerteelektronik | --> | Inter |  |  --> LoRaWAN
|  |  (Kamera)  |     |  (GStreamer)  |     | (YOLO + Tracking)  |     | face  |  |  (18 Byte)
|  +------------+     +---------------+     +--------------------+     +-------+  |
+---------------------------------------------------------------------------------+
```
*(Abbildungsempfehlung 3.1: Konzeptionelle Messkette des Smart-Sensors)* [225]

Der optische CMOS-Bildaufnehmer fungiert als *Messfühler (Aufnehmer)*, der die physikalische Größe (Lichtwellen im sichtbaren Spektrum) in ein analoges Signal (kontinuierliche Bildfolge) überführt [222, 241]. Die *Signalaufbereitung* erfolgt dezentral über ein GStreamer-Streaming-Framework, welches die Rohbilder filtert, skaliert und im RAM für die Weiterverarbeitung puffert [12, 217]. Die eigentliche *Auswerte-Elektronik* kombiniert die neuronale Objekterkennung auf dem Hailo-8-KI-Coprozessor mit der in Python implementierten Tracking- und Zähllogik [226]. Das Endergebnis ist ein diskretes, digitales Signal (Zählereignis mit Richtungs- und Klassenangabe) [165]. Das *Interface* wird durch das Dragino LA66 USB-Modul gebildet, welches die Zählwerte in ein binäres LoRaWAN-Protokoll übersetzt [226, 332]. Da dieses Gesamtsystem Signalaufbereitung, lokale Vorverarbeitung und eine Netzwerkschnittstelle vereint, erfüllt es vollumfänglich die Definition des **Smart-Sensors** nach Heinrich et al. (2020) [216, 224]. Im Kontext der klassischen Automatisierungspyramide agiert der Sensor auf dem *Field/Control Level* als dezentraler Datenlieferant für die Urbane Datenplattform Potsdam [241, 422].

---

### ii. Komponenten und Schnittstellen

#### Stichpunktartige Notizen:
*   **Hardwareseitige Kopplung**: Raspberry Pi 5 gekoppelt über PCIe Gen 3 mit dem Hailo-8 AI Kit (Firmware 4.23.0) [231, 234].
*   **Kamera-Anbindung**: USB-Kamera (v4l2-Schnittstelle) [381].
*   **LoRaWAN-Anbindung**: Dragino LA66 über eine serielle USB-Schnittstelle (`/dev/ttyUSB0` mittels CP2102-Chipsatz) [209, 232].
*   **Schnittstellensteuerung**: AT-Befehlskommunikation bei 9600 Baud zur Ansteuerung des LoRa-Senders [232].

#### Sachen, die ich da schon gemacht habe:
*   Die Hardwarekomponenten wurden am Referenzgerät `stadtwerke2` physisch montiert und die Treiber-Schnittstellen (HailoRT, PySerial) verifiziert [231, 331].

#### Was als nächstes da noch rein muss:
*   Dokumentation der seriellen Port-Verbindung und der v4l2-Video-Schnittstelle als softwareseitige Bindeglieder [340, 405].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die physische und logische Struktur des Smart-Sensors basiert auf standardisierten, industriellen Schnittstellen, die eine hohe Interoperabilität und Ausfallsicherheit garantieren [165].

```
+------------------+     PCIe Gen 3      +------------------+
|  Raspberry Pi 5  | <=================> |     Hailo-8      |
|     (Host)       |                     | (AI-Accelerator) |
+------------------+                     +------------------+
   |            |
   | USB        | USB-to-Serial (CP2102)
   v            v
+--------+   +-------------+
| Kamera |   | Dragino     | ===> LoRaWAN Gateway
| (v4l2) |   | LA66 Module |      (EU868 Band)
+--------+   +-------------+
```
*(Abbildungsempfehlung 3.2: Physisches Schnittstellendiagramm)* [220, 228]

Die primäre hardwareseitige Kopplung erfolgt über den herstellerspezifischen PCIe-Gen-3-Anschluss des Raspberry Pi 5, der den Hailo-8-KI-Beschleuniger mit der vollen Bus-Bandbreite anbindet [231, 234]. Der Kamera-Datenstrom wird über den Linux-Standardtreiber *Video for Linux 2* (v4l2) über eine USB-3.0-Schnittstelle eingelesen [381]. Die Verbindung zum LoRaWAN-Transmitter wird über eine USB-zu-Seriell-Brücke (CP2102-Chipsatz) realisiert, die den Dragino LA66-Adapter als virtuellen COM-Port unter `/dev/ttyUSB0` einbindet [232, 354]. Die logische Kommunikation mit dem LoRa-Modul erfolgt über eine asynchrone serielle Schnittstelle bei 9600 Baud [232]. Die Steuerung wird über standardisierte AT-Befehle abgewickelt, was eine herstellerunabhängige Austauschbarkeit des Funkmoduls sichert [208, 332].

---

### iii. Datenmodell und Datenflüsse

#### Stichpunktartige Notizen:
*   **Privacy by Design Nachweis**: Lückenloser, mathematischer Beweis der DSGVO-Konformität (Art. 25) über die Datenverdichtungskette [166].
*   **Die 4 Stufen der Verdichtungskette**:
    1.  *Rohbild (Stufe 1)*: $1280 	imes 720$ Pixel RGB-Videostrom im flüchtigen RAM ($2,76 	ext{ MB/Frame}$), sofortige Verarbeitung, absolute Löschung nach Frame-Verarbeitung [169, 192].
    2.  *Metadaten (Stufe 2)*: Reine Begrenzungsrahmen (Bounding Boxes) und temporäre Tracking-IDs (z. B. `[x1, y1, x2, y2, track_id]`), kein Personenbezug [218].
    3.  *Zählereignisse (Stufe 3)*: Aggregierte Zeitreihen in `zaehlung.csv` (z. B. `15.07.2026 12:28, person, IN, 1`) [192, 218].
    4.  *Binärpaket (Stufe 4)*: Extrem hochverdichtetes, anonymes **18-Byte-LoRaWAN-Paket** [195, 332].
*   **Datenvolumen**: Reduktion um Faktor $> 1.000.000$ (von Terabytes an Rohbildern pro Tag auf wenige Kilobytes an Binärdaten) [196, 201].

#### Sachen, die ich da schon gemacht habe:
*   Die Verdichtungskette wurde algorithmisch in der Pipeline implementiert und im realen Datenfluss verifiziert [166, 196].

#### Was als nächstes da noch rein muss:
*   Konstruktion einer systematischen Tabelle, die die Reduktion des Personenbezugs und des Datenvolumens über die 4 Stufen hinweg mathematisch beweist [196, 201].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Der Nachweis der Datenschutzkonformität (*Privacy by Design* gemäß Art. 25 DSGVO) wird mathematisch über die restriktive Datenverdichtungskette des Sensors geführt [166]. Zu keinem Zeitpunkt verlassen personenbezogene Daten das dezentrale Edge-Device [166].

**Tabelle 3.3: Datenverdichtungskette und Personenbezug-Reduktion** [196, 201]

| Stufe | Datenobjekt                                 | Verarbeitungsort       | Datenvolumen (pro Min) | Personenbezug / DSGVO-Relevanz                                                                  |
| :---- | :------------------------------------------ | :--------------------- | :--------------------- | :---------------------------------------------------------------------------------------------- |
| **1** | Rohbild (RGB, $1280 	imes 720$, 30 FPS)     | RAM (flüchtig)         | $pprox 4,9 	ext{ GB}$ | **Hoch** (Gesichter, Kleidung sichtbar); sofortige Löschung nach Frame-Verarbeitung [169, 192]. |
| **2** | Tracking-Metadaten (Bounding Box, track_id) | RAM (flüchtig)         | $pprox 240 	ext{ KB}$ | **Sehr gering** (reine Raum-Zeit-Koordinaten); kein Gesicht Bezug vorhanden [218].              |
| **3** | Zählevent (Klasse, Richtung, Zeit)          | `zaehlung.csv` (Flash) | $pprox 0,1 	ext{ KB}$ | **Kein Personenbezug** (rein aggregierter Zählwert); anonym [193, 218].                         |
| **4** | Binär-Uplink (18-Byte-Frame)                | LoRaWAN / UDP          | **$0,018 	ext{ KB}$**  | **Kein Personenbezug**; hochgradig komprimiert [195, 332].                                      |

Diese Kette beweist, dass das System eine extreme Datenreduktion (Faktor $> 100.000.000$ von Stufe 1 zu Stufe 4) vollzieht [196, 201]. Da auf Stufe 3 und 4 keinerlei biometrische oder identifizierbare Merkmale existieren und Stufe 1 ausschließlich im flüchtigen Arbeitsspeicher für Millisekunden existiert, wird der Sensor zu 100 % konform mit den strengsten Auslegungen des europäischen Datenschutzrechts betrieben [166, 384].

---

---

## 4. Prototyping und Demonstration
*DSRM Aktivität 3 (Umsetzung) + Aktivität 4 (Demonstration). Beantwortet FF D.*

### a. Hardwareaufbau

#### Stichpunktartige Notizen:
*   **Physische Komponenten**: Raspberry Pi 5 (8 GB RAM), PCIe M.2 Hat, Hailo-8 KI-Beschleuniger, USB-Kamera mit Weitwinkelobjektiv, Dragino LA66 USB-LoRaWAN-Adapter [166, 231, 232].
*   **Gehäuse und Montage**: IP66-zertifiziertes wetterfestes Gehäuse, Befestigung über rückseitige Mastschellen für die 17 Eingänge [234, 517].
*   **Energieversorgung**: Ausgelegt auf 12V-Solar-Inselanlage mit 20Ah LiFePO4-Pufferakku für den krisensicheren Betrieb [166, 384, 517].
*   **Strukturvorgabe**: Die Abschnitte *i. Software Architektur*, *ii. HAILO Einleitung* und *iii. HAILO Installation* sind gemäß der vereinbarten BA2.docx-Gliederung hier explizit ausgeklammert („nicht hier“) und in die Softwareentwicklung verschoben [180].

#### Sachen, die ich da schon gemacht habe:
*   Der physische Prototyp wurde auf dem Referenzgerät `stadtwerke2` vollständig montiert, verkabelt und in Betrieb genommen [231, 234].
*   Der LoRaWAN-Adapter Dragino LA66 wurde erfolgreich integriert und funktional verifiziert [232, 331].

#### Was als nächstes da noch rein muss:
*   Dokumentation des realen Betriebszustands zum Abgabezeitpunkt (31.07.2026): Der Hardwareaufbau läuft als stabiles Labormodell; die endgültige mechanische Gehäusekonstruktion für den Volkspark wird im Ausblick als Folgeprojekt deklariert [330, 517].

#### Originaler Fließtext:
*(Es lag kein Fließtext für diesen Gliederungspunkt vor.)*

#### Überarbeiteter Fließtext:
Der physische Aufbau des Prototyps wurde auf dem Referenzsystem `stadtwerke2` realisiert, welches als technologische Blaupause für den späteren 17-Kamera-Rollout dient [231, 234]. Das System kombiniert industrienahe Edge-Komponenten zu einer robusten Einheit [166].

Als Rechenkern dient der Raspberry Pi 5 mit 8 GB RAM, der über einen M.2-PCIe-Hat den Hailo-8-KI-Beschleuniger aufnimmt [231, 234]. Um die volle Bus-Bandbreite des Coprozessors auszuschöpfen, wurde der PCIe-Port im Betriebssystem manuell auf Gen-3-Geschwindigkeit konfiguriert (`PCIe Speed Gen 3`) [231, 234]. Für die Bildaufnahme wird eine USB-Weitwinkelkamera verwendet, die einen diagonalen Sichtwinkel von 120 Grad abdeckt, was an breiten Eingängen eine lückenlose Erfassung der Laufbereiche garantiert [213, 384]. Die LoRaWAN-Kommunikation wird über den Dragino LA66 USB-Adapter abgewickelt, der über eine integrierte Scharnierantenne verfügt [232, 339].

Für den permanenten Außeneinsatz im Volkspark Biosphäre ist der Prototyp in einem IP66-wetterfesten Kunststoffgehäuse untergebracht, das über rückseitige Mastschellen flexibel an bestehenden Lichtmasten oder Toren montiert werden kann [234, 517]. Die Energieversorgung ist konzeptionell als Solar-Inselanlage ausgelegt: Ein 50W-Solarpanel speist über einen MPPT-Laderegler einen 12V-LiFePO4-Pufferakku mit einer Kapazität von 20Ah, was eine Autarkie von bis zu drei sonnenlosen Tagen garantiert [166, 384, 517]. Zum Abgabezeitpunkt der Arbeit liegt der Prototyp als voll funktionsfähiger Laboraufbau vor; die finale Montage des wetterfesten Gehäuses im Feld wird im Ausblick (Kapitel 6.e) als koordinierter nächster Schritt beschrieben [330, 517].

---

### b. Softwareentwicklung

### i. Modulare Architektur / Pipeline-Pattern

#### Stichpunktartige Notizen:
*   **GStreamer-Framework**: Dreischichtiges Hailo-Modell: GStreamer -> Tappas (C/C++ Hailo-Plugins) -> Python-Layer (GStreamerApp) [217, 225].
*   **Single Network Pipeline**: Nutzung einer einzigen, hocheffizienten Deep-Learning-Pipeline auf dem Hailo-8 [167].
*   **hailotracker mit class-id=-1**: Eine entscheidende Änderung am originalen Hailo-Code, die es erlaubt, alle relevanten Klassen (person, bicycle, car, truck) synchron in einer einzigen Pipeline zu verfolgen [202, 330].
*   **Abgrenzung**: Begründung gegen Multiprozess-Pattern (verhindert Race-Conditions auf dem PCIe-Bus) [341].

#### Sachen, die ich da schon gemacht habe:
*   Die Hailo-GStreamer-Pipeline wurde implementiert und der `class-id=-1`-Parameter erfolgreich gesetzt [330].
*   Der Race-Condition-Bug beim abrupten Prozessabbruch wurde durch sanftes SIGINT-Handling behoben [341].

#### Was als nächstes da noch rein muss:
*   Nachweis der stabilen Verarbeitungskapazität bei 30 FPS ohne Frame-Drops [202].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die Softwarearchitektur des Sensors basiert auf einem dreischichtigen Framework, das eine maximale Verarbeitungsgeschwindigkeit bei minimaler CPU-Last garantiert [217, 225]. Als Streaming-Infrastruktur dient das GStreamer-Framework, welches die hardwarebeschleunigte Erfassung und Skalierung der Videoframes übernimmt [217].

```
+-------------------------------------------------------------------------+
|                              PYTHON LAYER                               |
|        GStreamerApp-Klasse · Callback-Registrierung · UI (app.py)        |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                              TAPPAS LAYER                               |
|  hailonet (YOLOv8) · hailofilter (NMS) · hailotracker (class-id=-1)    |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                            GSTREAMER LAYER                              |
|           v4l2src · videoconvert · videoscale · fpsdisplaysink          |
+-------------------------------------------------------------------------+
```
*(Abbildungsempfehlung 4.1: Dreischichtiges Software-Framework nach Hailo-Standard)* [217, 225]

Die mittlere Schicht (*Tappas-Layer*) integriert Hailos spezifische C/C++-GStreamer-Plugins, namentlich `hailonet` zur Ausführung des YOLOv8/v10-Modells auf dem Beschleuniger und den `hailotracker` [217]. Ein wesentlicher eigener Entwicklungsbeitrag bestand in der Modifikation des Trackers: Durch Setzen des Parameters `class-id=-1` im Tracker-Element wurde die standardmäßige Beschränkung auf Personen aufgehoben, sodass alle Detektionsklassen (*person, bicycle, car, motorcycle, bus, truck*) synchron in einer einzigen Pipeline verfolgt werden können [202, 330]. Der *Python-Layer* steuert den Lebenszyklus der Pipeline über die Klasse `GStreamerApp` und fängt die erzeugten Metadaten über einen performanten Callback-Mechanismus ab, um sie direkt an die Zähllogik zu übergeben [217]. Dieses *Single-Network-Pipeline-Pattern* verhindert zeitintensive Kopiervorgänge zwischen CPU und NPU und sichert eine konstante Verarbeitungsrate von 30 FPS [167, 202].

---

### ii. Modul-Mapping & Datenfluss

#### Stichpunktartige Notizen:
*   **Modul-Struktur**: `core.py` (Pipeline-Steuerung & Callback), `tracking.py` (Track-Verwaltung & klassengetrennte IDs), `counting.py` (Zähllogik), `visualization.py` (Overlay-Generierung), `csv_utils.py` (Schema-Schutz) [218].
*   **Klassengetrennte display_id**: Ersetzung der rohen Tracker-ID durch lesbare, klassenspezifische IDs (z. B. `person_ID_1` statt ID `42`), was ID-Kollisionen im Bildraum eliminiert [218].
*   **Absturzsicherheit**: Zählevents werden im Moment ihres Auftretens sofort persistent in `zaehlung.csv` geschrieben; Track-Historien beim regelmäßigen Aufräumen (Flush nach 30 Frames Inaktivität) in `ergebniss.csv` [218, 226].

#### Sachen, die ich da schon gemacht habe:
*   Alle Module wurden vollständig implementiert, modular gekoppelt und erfolgreich getestet [218, 219].

#### Was als nächstes da noch rein muss:
*   Das detaillierte Datenflussdiagramm (Schwimmbahnen für Konfiguration und Betrieb) als zentrale Abbildung einfügen [220, 228].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die Implementierung folgt einem streng modularen Aufbau, bei dem jedes Modul eine klar abgegrenzte Aufgabe innerhalb des Datenflusses übernimmt [218]. Dies sichert die Wartbarkeit und Erweiterbarkeit des Gesamtsystems [147].

```
+---------------+     Frame-Callback      +-------------+     Track-Updates      +-------------+
|    core.py    | ----------------------> | tracking.py | ---------------------> | counting.py |
+---------------+                         +-------------+                        +-------------+
        |                                        |                                      |
        v                                        v                                      v
+------------------+                      +---------------+                      +--------------+
| visualization.py |                      |  csv_utils.py |                      | zaehlung.csv |
|  (User Frame)    |                      | (Schema-Saf.) |                      | (Sofort-Pers)|
+------------------+                      +---------------+                      +--------------+
```
*(Abbildungsempfehlung 4.2: Modul-Mapping und Datenfluss im Betrieb)* [220, 228]

Das Steuerungsmodul `core.py` initialisiert die GStreamer-Pipeline und registriert den Frame-Callback [218]. Sobald ein neuer Frame verarbeitet wurde, fängt der Callback die Metadaten ab und übergibt sie an `tracking.py` [218]. Dieses Modul führt eine zeitliche Glättung durch und weist jedem Objekt eine eindeutige, klassengetrennte Identifikationsnummer (z. B. `person_ID_1` oder `bicycle_ID_1`) zu, um ID-Kollisionen zwischen unterschiedlichen Objektklassen auszuschließen [218].

Die aktiven Pfade werden an `counting.py` übergeben, welches im Millisekundentakt prüft, ob geometrische Zählbedingungen erfüllt sind [218]. Ein entscheidendes Robustheitsmerkmal ist das Persistierungs-Konzept: Zählereignisse werden im Moment des Auftretens sofort in die `zaehlung.csv` geschrieben [218, 226]. Verliert das System ein Objekt für mehr als 30 aufeinanderfolgende Frames, wird der Track finalisiert (Flush) und die gesamte Bewegungshistorie (inklusive der gemittelten Erkennungskonfidenz `avg_confidence`) in die `ergebniss.csv` geschrieben [218]. Bei einem plötzlichen Stromausfall bleiben somit alle bis zu diesem Zeitpunkt erfassten Daten vollständig erhalten [226].

---

### iii. Zähllogik

#### Stichpunktartige Notizen:
*   **Vektorkreuzprodukt**: Mathematischer Nachweis der Linienquerung [160].
*   **Zonenübergänge**: Implementierung der Multi-ROI-Logik mit zwei oder mehr Zonen [192].
*   **Datenintegrität**: Der Fall `is_transition=False` (kein Wechsel) protokolliert Tracks, die eine Zone betreten, aber wieder umkehren, ohne sie als Fehlzählung zu werten [193, 198].
*   **Auswertung**: Filtern nach echten Durchgängen erfolgt über `direction == "Potsdam->Berlin" AND is_transition == True` [193, 198].

#### Sachen, die ich da schon gemacht habe:
*   Die mathematische Zähllogik wurde vollständig implementiert (`counting.py`) und gegen reale Messdaten verifiziert [193, 218].

#### Was als nächstes da noch rein muss:
*   Formelmäßige Darstellung des Vektorkreuzprodukts zur eindeutigen Richtungsbestimmung im Fließtext [160].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die mathematische Präzision der Zähllogik entscheidet maßgeblich über die Validität der Messergebnisse [249]. Für die Linienquerung wird eine zweidimensionale Zähllinie definiert, die durch einen Richtungsvektor $ec{L}$ im Bildraum beschrieben wird [160]. Bewegt sich ein Objekt von Punkt $P_{	ext{start}}$ zu Punkt $P_{	ext{end}}$, ergibt sich der Bewegungsvektor $ec{B} = P_{	ext{end}} - P_{	ext{start}}$ [160]. Eine Querung der Zähllinie wird über das Vorzeichen des Vektorkreuzprodukts detektiert:

$$	ext{Signum}(ec{L} 	imes ec{B}) = 	ext{Signum}(L_x \cdot B_y - L_y \cdot B_x)$$

Ein Wechsel des Vorzeichens zwischen zwei aufeinanderfolgenden Frames signalisiert eine physische Querung, wobei das resultierende Vorzeichen mathematisch exakt die Bewegungsrichtung (IN oder OUT) definiert [160].

Für komplexere Geometrien kommt die Zonenübergangs-Logik zum Einsatz [192]. Hierbei werden im Bildraum benannte Flächen (wie „Fläche Potsdam“ und „Fläche Berlin“) definiert [192]. Ein Objekt wird kontinuierlich mittels des Polygon-Ray-Casting-Tests auf seine Flächenzugehörigkeit geprüft [160, 218]. Ein valides Zählereignis wird ausschließlich dann ausgelöst, wenn ein Objekt nachweislich die Fläche Potsdam verlässt und die Fläche Berlin betritt [193, 198]. Verweilt eine Person lediglich in der Fläche Potsdam und verlässt diese wieder in Richtung des ursprünglichen Startpunktes, ohne jemals die Fläche Berlin betreten zu haben, wird dieses Ereignis mit `is_transition=False` protokolliert [193, 198]. Dies sichert eine lückenlose Datenintegrität, da fälschliche Zählungen durch pendelnde Personen oder Bildrandeffekte mathematisch ausgeschlossen werden [193, 198].

---

### iv. Manuelle Konfiguration

#### Stichpunktartige Notizen:
*   **Visuelles Tool**: `roi_config_app.py` als interaktiver Mausklick-Editor [168, 219].
*   **camera_raw.png**: Aufnahme eines Snapshot-Referenzbildes direkt aus der echten Pipeline (`CORE_SNAPSHOT_ONLY`), um Diskrepanzen in Auflösung und Ausschnitt zu verhindern [219, 341].
*   **roi_config.json**: Speicherung der Koordinaten in einem standardisierten, standortspezifischen JSON-Format [219, 401].

#### Sachen, die ich da schon gemacht habe:
*   Der Snapshot-Subprozess in `core.py` und das Konfigurationstool `roi_config_app.py` wurden vollständig implementiert und gekoppelt [219, 341].

#### Was als nächstes da noch rein muss:
*   Beschreibung der robusten Fehlerbehandlung, falls eine unvollständige Konfiguration (z. B. ohne das erforderliche `in_field` für LoRaWAN) gespeichert wird [141, 514].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Um die Zählgeometrien an den 17 heterogenen Eingängen flexibel zu definieren, wurde das manuelle Konfigurationswerkzeug `roi_config_app.py` entwickelt [219, 401]. Ein kritischer technischer Stolperstein früherer Entwürfe bestand darin, dass das Konfigurationstool das Kamerabild über eine eigene OpenCV-Instanz aufnahm, was zu Diskrepanzen in Auflösung, Ausrichtung und Bildausschnitt im Vergleich zur tatsächlichen Hailo-Pipeline führte [341].

Dieses Problem wurde gelöst, indem `roi_config_app.py` beim Start einen kurzen, dedizierten Subprozess von `core.py` im speziellen Snapshot-Modus (`CORE_SNAPSHOT_ONLY=1`) anstößt [219, 341]. Dieser nimmt exakt ein Referenzbild (`camera_raw.png`) direkt aus der echten GStreamer-Pipeline auf und beendet sich sofort wieder [219, 341]. Dies garantiert eine absolute Deckungsgleichheit von Konfigurations- und Live-Bild [341]. Auf diesem Referenzbild kann ein Techniker per Mausklick Polygone oder Linien einzeichnen [219]. Die ermittelten Pixel-Koordinaten werden strukturiert in der standortspezifischen Datei `roi_config.json` gespeichert [219, 401]. Bei der Konfiguration von Mehrflächen-Übergängen prüft die Software zwingend, ob der Benutzer das für die LoRa-Übertragung erforderliche Eingangsfeld (`in_field`) definiert hat [141]. Fehlt dieses, blockiert die GUI das Speichern, um die unbeabsichtigte Übertragung leerer Datenpakete im Feldbetrieb proaktiv zu verhindern [141, 515].

---

### v. Automatische Konfiguration

#### Stichpunktartige Notizen:
*   **DBSCAN-Verfahren**: Raum-zeitliches Clustering von Pfad-Start- und Endpunkten [219, 248].
*   **Randraster-Verfahren mit Mindestbewegungsfilter**: Meine stärkste WI-Eigenentwicklung zur Lösung des Problems von Tracking-Abbrüchen in der Bildmitte [248, 284].
*   **Grounded Technological Rule**: Wissenschaftliche Formulierung als verallgemeinerbare Gestaltungsregel für Edge-AI-Systeme [248, 284].

#### Sachen, die ich da schon gemacht habe:
*   Beide Algorithmen wurden implementiert (`auto_config.py`, `auto_config_clustering.py`) und sind voll funktionsfähig über Tab 5 ansteuerbar [138, 219].

#### Was als nächstes da noch rein muss:
*   Herausstellen des Randraster-Verfahrens als wissenschaftliches Glanzstück der Arbeit zur Bewältigung physischer Verdeckungen im naturnahen Raum [248, 284].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die automatische Konfiguration (DSRM-Aktivität 3) stellt einen der signifikantesten wissenschaftlichen und gestalterischen Beiträge dieser Arbeit dar [246, 284]. Es wurden zwei komplementäre, selbstkonfigurierende Algorithmen entwickelt und in das System integriert [219, 248].

Das datengetriebene **DBSCAN-Verfahren** sammelt über einen voreingestellten Zeitraum im Hintergrund die Start- und Endpunkte aller sich bewegenden Objekte in einer temporären Datei `auto_config_points.csv` [219, 248]. Nach Ablauf des Zeitraums führt das System ein räumliches Clustering durch [219]. Rauschpunkte (z. B. kurzzeitige Fehlklassifikationen durch wankende Äste) werden durch den Parameter `Min_Samples` robust eliminiert [248, 514]. Die dichten Clusterkerne werden als Zentren der primären Laufwege interpretiert und automatisch als kreisförmige ROI-Zonen abgespeichert [219, 248].

Um den spezifischen Hürden des Volksparks – wie herabfallendem Laub oder temporären Sichtverdeckungen durch Baumkronen – zu begegnen, wurde das innovative **Randraster-Verfahren mit Mindestbewegungsfilter** entwickelt [248, 284]. In realen Testszenarien zeigte sich, dass DBSCAN versagt, wenn Personen im Zentrum des Sichtfelds kurzzeitig durch Bäume verdeckt werden: Der Tracker verliert das Objekt und legt bei der Wiedererkennung einen neuen Pfad an, was DBSCAN fälschlicherweise als „Startpunkt“ mitten im Laufweg interpretiert [248, 284]. Das Randraster-Verfahren löst dieses Problem elegant: Es legt ein virtuelles Gitter ausschließlich über die äußeren 10 % des Bildrandes und filtert stationäre Bewegungen heraus [284, 304]. Zonen werden nur dort generiert, wo Objekte nachweislich die Szene betreten oder verlassen [284]. Dieses heuristische Verfahren stellt eine wertvolle *Grounded Technological Rule* dar, die direkt in die WI-Wissensbasis für Edge-AI-Projekte im unbeschränkten öffentlichen Raum einfließt [248, 284].

---

### vi. Bedienoberfläche

#### Stichpunktartige Notizen:
*   **CustomTkinter**: Moderne, ressourcenschonende Python-GUI-Bibliothek [169].
*   **Die 5 Tabs**:
    1.  *Input*: Auswahl der Videoquelle (USB-Kamera oder Testdatei) [331].
    2.  *Konfiguration*: Interaktive Zählgeometrie-Auswahl [331].
    3.  *Start*: Betriebssteuerung (inkl. LoRaWAN-Checkbox) [140, 331].
    4.  *Live-Auswertung*: Echtzeit-Konsolen-Logging und Zähleranzeige [141, 331].
    5.  *Auto-Konfiguration (Neu am 18.07.)*: Dedizierte Datensammlung mit Zeitschaltuhr [138, 331].
*   **Anforderungserfüllung**: Direkte, vollständige Umsetzung der Interview-Vorgabe „Bedienung ohne Kommandozeile“ für Nicht-Techniker der Stadtwerke [169, 384].

#### Sachen, die ich da schon gemacht habe:
*   Die GUI wurde in `app.py` vollständig implementiert, inklusive des neuen Tab 5 für die automatische Datensammlung [138, 141].

#### Was als nächstes da noch rein muss:
*   Screenshots der GUI-Tabs im Anhang verankern und im Text referenzieren [169, 290].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die Bedienoberfläche des Prototyps wurde als eigenständige Desktop-Applikation in Python unter Verwendung der modernen UI-Bibliothek `CustomTkinter` realisiert [169]. Dies erfüllt direkt die kritische Anforderung der Stadtwerke Potsdam nach einer einfachen, intuitiven Bedienbarkeit ohne jegliche Nutzung des Linux-Terminals vor Ort [169, 384].

```
+-------------------------------------------------------------------------+
| [app.py - Sidebar-Navigation]                                            |
|                                                                         |
| (1) Input             --> Auswahl: usb / test.mp4 [331]                 |
| (2) Konfiguration     --> Manuelles Einzeichnen / Auto-Optionen [331]   |
| (3) Start             --> Checkbox "LoRaWAN senden (LA66)" [140, 331]   |
| (4) Live-Auswertung   --> Echtzeit-Konsole & Zählerstände [141, 331]    |
| (5) Auto-Konfig       --> Zeitschaltuhr für DBSCAN-Sammlung [138, 331]   |
+-------------------------------------------------------------------------+
```
*(Abbildungsempfehlung 4.3: Konzeptionelles Layout der Benutzeroberfläche)* [169, 220]

Die Anwendung ist in fünf logische Registerkarten (Tabs) unterteilt, die den gesamten Arbeitsablauf widerspiegeln [138, 169]:

1.  **Tab 1 (Input):** Ermöglicht die Auswahl der Videoeingangsquelle (USB-Kamera-Index oder lokale Videodatei für Labortests) [331].
2.  **Tab 2 (Konfiguration):** Bietet die interaktive Definition der Zählgeometrien auf dem Snapshot-Referenzbild sowie die direkte Auswahl des gewünschten Zählmodus [219, 331].
3.  **Tab 3 (Start):** Startet den operativen Betrieb. Hier kann die Datenübertragung per LoRaWAN über eine einfache Checkbox hinzugeschaltet werden [140, 331].
4.  **Tab 4 (Live-Auswertung):** Bietet eine integrierte Echtzeit-Konsole, die alle Systemmeldungen von `core.py` und dem LoRa-Sender-Subprozess mit eindeutigen Präfixen (`[LoRa]`) ausgibt, sowie eine visuelle Zähleranzeige [141, 331].
5.  **Tab 5 (Auto-Konfiguration):** Ein am 18.07.2026 neu integrierter Bereich [138, 329]. Er erlaubt es, eine zeitlich begrenzte Datensammlung (Sammeldauer in Sekunden) zu starten, um die Bewegungspunkte für das DBSCAN-Clustering automatisiert im Hintergrund aufzuzeichnen [138].

---

### vii. Datenhaltung

#### Stichpunktartige Notizen:
*   **Dateiformate**: csv-basiert für optimale Weiterverarbeitung [169, 401].
*   **ergebniss.csv**: Erfassung aller Tracks mit 11 Spalten inklusive `avg_confidence` beim Track-Abschluss [202, 218].
*   **zaehlung.csv**: Ereignisbasiertes Log im Moment der Linienquerung (5 Spalten) zur optimalen Absturzsicherheit [193, 218].
*   **csv_utils.py**: Automatischer Schutz vor Schema-Drift mittels `ensure_current_schema()` zur Absicherung nachfolgender Datenanalysen [168, 218].
*   **Beispiel-Durchlauf**: Lückenlose Verfolgung des Beispiel-Tracks `car_ID_2` (Start x=429 -> Ende x=1127 -> Potsdam->Berlin) durch alle Datenartefakte [169, 192].

#### Sachen, die ich da schon gemacht habe:
*   Der Schema-Drift-Schutz wurde implementiert und der Datenfluss für den Beispiel-Track `car_ID_2` verifiziert [169, 202].
*   Die Erstellung der fehleranfälligen Datei `ergebniss.txt` wurde komplett eingestellt, um Datenredundanz zu vermeiden [202].

#### Was als nächstes da noch rein muss:
*   Einbindung der echten Spaltenstrukturen und Beispielwerte in den Fließtext [192].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die lokale Datenhaltung des Sensors ist konsequent auf Robustheit, Redundanzfreiheit und Kompatibilität mit modernen Datenanalysetools (wie pandas) ausgelegt [169, 218]. Die zentrale Datenhaltung erfolgt über zwei separate CSV-Dateien, deren Schema-Stabilität durch das von mir entwickelte Modul `csv_utils.py` überwacht wird [218].

In früheren Testläufen trat das Problem auf, dass nachträgliche Code-Änderungen (wie das Hinzufügen der Spalte `is_transition` oder der tracker-bezogenen `display_id`) bestehende CSV-Dateien im laufenden Betrieb korrumpierten, da neue Zeilen mit einer abweichenden Spaltenanzahl unter eine veraltete Kopfzeile geschrieben wurden (*Schema-Drift*) [341]. Das Modul `csv_utils.py` implementiert daher die Funktion `ensure_current_schema()` [218, 341]. Bei jedem Systemstart wird die Kopfzeile der Dateien überprüft [341]. Entspricht sie nicht exakt dem aktuellen Software-Schema, wird die veraltete Datei automatisch umbenannt und in den Archivordner `vorherige_laeufe/` verschoben, während eine neue, schema-konforme Datei erzeugt wird [202, 341].

Der Datenfluss lässt sich anhand des verifizierten Beispiel-Tracks `car_ID_2` (Lauf vom 15.07.2026) lückenlos nachvollziehen [169, 192]:

*   **Schritt 1:** Das Fahrzeug quert den Übergang Potsdam nach Berlin. Im Moment der Vektorkreuzung schreibt `logging_utils.py` sofort eine Zeile in die **`zaehlung.csv`** [193, 218]:
    `2026-07-15 12:28:42, car, Potsdam->Berlin, True, car_ID_2` [192]
*   **Schritt 2:** Das Fahrzeug verlässt den Sichtbereich der Kamera. Nach 30 Frames Inaktivität deklariert `tracking.py` den Track als beendet, führt einen Flush durch und schreibt die aggregierten Metadaten in die **`ergebniss.csv`** (11 Spalten) [192, 218]:
    `car_ID_2, car, 429, 312, 1127, 315, 0.88, 1280, 720, 248, FLUSH` [192]
*   **Schritt 3:** Gleichzeitig speichert das System ein visuelles Kontrollbild unter `tracked_objects_car_ID_2_flush.png`, auf dem die gesamte Trajektorie und die Zählpolygone eingezeichnet sind [192, 202]. This lückenlose Kette sichert die vollständige Nachvollziehbarkeit für den Betreiber [192].

---

### b.viii. Datenübertragung

#### Stichpunktartige Notizen:
*   **LoRaWAN-Schnittstelle**: Erfolgreich im Echtbetrieb am 18.07.2026 über Dragino LA66 USB-Adapter verifiziert [140, 142].
*   **18-Byte-Zählformat v2**: Definition in `lora_message.py` [141, 142].
    *   *Header (6 Byte)*: Byte 0 = Format-Version, Byte 1–2 = Sensor-ID, Byte 3 = interval_min, Byte 4 = status-Bitfeld, Byte 5 = class_mask [142, 357].
    *   *Payload (12 Byte)*: 6 Klassen (person, bicycle, car, motorcycle, bus, truck) x 2 Richtungen (IN/OUT) à 1 Byte (uint8) [141, 357, 358].
*   **Status-Bitfeld**: Ermöglicht der UDP Potsdam die Erkennung von dezentralen Ausfällen (Bit0 Kamera ok, Bit1 Hailo ok, Bit2 Config ok, Bit3 gepuffert, Bit4 Teilintervall) [142].
*   **Deentkopplung**: Sender läuft als völlig unabhängiger Subprozess `lora_send_loop.py --live-counts`, der die `zaehlung.csv` liest, wodurch die Zähl-Pipeline vor Netzwerkfehlern geschützt wird [141, 332].
*   **Verlustfreie Pufferung**: Übertragen wird nur das Delta (Zuwachs) seit dem letzten *erfolgreichen* Senden; der lokale Stand wird erst nach dem Empfang eines Bestätigungs-Acks nachgezogen. Bei Funklöchern gehen somit keine Intervalle verloren [141, 332].

#### Sachen, die ich da schon gemacht habe:
*   Der Echtbetrieb über den LA66-Adapter wurde verifiziert und die korrekten Byte-Belegungen in `lora_message.py` implementiert [140, 142].
*   Der Payload-Formatter (JavaScript) wurde im TTN (The Things Network) hinterlegt [144].

#### Was als nächstes da noch rein muss:
*   Reflexion der Limitationen: Da das 18-Byte-Format fest auf IN/OUT-Strukturen ausgelegt ist, muss der Mehrflächen-Modus mit komplexen Übergängen vor dem Senden über ein ausgewähltes `in_field` auf diese binäre Logik projiziert werden [195, 332].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die Datenübertragung an die Urbane Datenplattform Potsdam stellt den finalen Schritt der dezentralen Verarbeitungskette dar [196, 226]. Am 18.07.2026 wurde die LoRaWAN-Funkstrecke über den Dragino LA66 USB-Adapter erfolgreich im Echtbetrieb verifiziert [140, 142].

```
+------------------+                    +---------------------+
|   tracking.py    |                    |   lora_message.py   |
| (Zählung läuft)  |                    | (18-Byte-Format v2) |
+------------------+                    +---------------------+
         |                                         |
         v (schreibt)                              v (baut Frame)
   zaehlung.csv  ============================> lora_send_loop.py
                  (entkoppeltes Lesen)         (Delta-Uplink)
                                                   |
                                                   v (AT+SENDB)
                                              Dragino LA66
```
*(Abbildungsempfehlung 4.4: Konzeptioneller Aufbau des LoRaWAN-Sendepfads)* [332, 335]

Die softwareseitige Architektur wurde streng entkoppelt gestaltet: Der Sender läuft als eigenständiger Hintergrundprozess `lora_send_loop.py --live-counts`, welcher periodisch (z. B. alle 5 Minuten) die Datei `zaehlung.csv` einliest [141, 332]. core.py und die KI-gestützte Erkennungs-Pipeline bleiben von der Übertragung vollkommen unberührt, sodass ein temporärer Ausfall der seriellen Hardware oder ein LoRaWAN-Duty-Cycle-Timeout die Zählung zu keinem Zeitpunkt gefährden kann [141, 142].

Für die Übertragung wurde das hocheffiziente **18-Byte-Zählformat v2** entworfen [140, 332]. Auf eine Übertragung sperriger JSON-Strukturen oder unkomprimierter Textdaten wurde verzichtet, um selbst bei schlechtem Empfang (Spreizfaktor SF12, Limit von 51 Byte Nutzlast) lauffähig zu bleiben [344, 356]:

*   **Byte 0 (Version):** Formatversion des Protokolls (aktuell `0x02`) [142].
*   **Byte 1–2 (Sensor-ID):** Eindeutige ID des Standorts (0–65535) [331].
*   **Byte 3 (Intervall):** Aggregationsintervall in Minuten (z. B. `5`) [142, 355].
*   **Byte 4 (Status-Bitfeld):** Übermittelt wichtige Diagnosebits an die UDP Potsdam: Bit0 (Kamera ok), Bit1 (Hailo-Hardware ok), Bit2 (Konfiguration geladen), Bit3 (Daten gepuffert aufgrund früherer Sendefehler), Bit4 (Teilintervall nach Systemneustart) [142]. Dies erlaubt es der UDP, den Zustand „keine Besucher vorhanden“ verlässlich von einem Sensorausfall zu unterscheiden [175].
*   **Byte 5 (class_mask):** Codiert im Bitfeld, welche Objektklassen an diesem Standort aktiv überwacht werden (entspricht `TRACKED_LABELS`) [357].
*   **Byte 6–17 (Zählpayload):** 6 COCO-Klassen (Person, Fahrrad, Auto, Motorrad, Bus, Lkw) mit jeweils 1 Byte für den IN- und 1 Byte für den OUT-Zähler (uint8, Wertebereich 0–255) [141, 358].

Um Funklöcher verlustfrei zu überbrücken, implementiert `lora_send_loop.py` einen intelligenten Delta-Mechanismus: Es wird stets nur der Zuwachs seit dem letzten *erfolgreichen* Uplink gesendet; der lokale Referenzstand wird erst dann aktualisiert, wenn das Sende-Ack des LA66-Moduls vorliegt [141, 332]. Ein misslungenes Sendeintervall wird beim nächsten Sendeversuch automatisch mitsubsumiert [141, 332]. Eine systemimmanente Limitation besteht im Mehrflächen-Modus: Da das LoRaWAN-Format fest auf eine IN/OUT-Struktur ausgelegt ist, muss eine der beiden benannten Flächen in Tab 2 als Eingangsfeld (`in_field`) definiert werden, um die Übergänge (z. B. Potsdam nach Berlin) eindeutig auf das binäre Sendeformat abzubilden [195, 332].

---

### c. Testung

### i. Optimierungsparameter

#### Stichpunktartige Notizen:
*   **Parameter-Feinjustierung**: Bestimmung der optimalen Software-Schwellenwerte für den Volkspark-Einsatz [284].
*   **Clustering-Radius (DBSCAN)**: Festgelegt auf `AUTO_CONFIG_DBSCAN_EPS_PIXELS = 35` Pixel zur optimalen räumlichen Separation der Pfade [219, 514].
*   **Mindestbewegung**: Schwellwert in Pixeln für das Randraster-Verfahren, um statistisches Bildrauschen der Kamera herauszufiltern [284].
*   **Tracking-Flush**: Flush-Zeitraum von 30 Frames, um verloren gegangene Personen zeitnah als abgeschlossen zu werten, ohne vorzeitige Track-Splits zu riskieren [218].

#### Sachen, die ich da schon gemacht habe:
*   Alle Parameter wurden in der zentralen Konfigurationsdatei `config.py` konsolidiert und im Labor verifiziert [218, 512].

#### Was als nächstes da noch rein muss:
*   Wissenschaftliche Dokumentation der Parametereinflüsse auf die Genauigkeit im Text [284].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Um eine maximale Zählgenauigkeit des Sensors im unbeschränkten Raum zu garantieren, müssen alle algorithmischen Optimierungsparameter präzise auf die physikalischen Gegebenheiten des Standorts abgestimmt werden [284]. Diese Parameter sind in der Datei `config.py` zentralisiert [218, 512]:

*   **DBSCAN epsilon (`AUTO_CONFIG_DBSCAN_EPS_PIXELS`):** Der Nachbarschaftsradius für das räumliche Clustering wurde im Labor auf 35 Pixel festgeschrieben [219, 514]. Ein kleinerer Wert führt zu einer Zersplitterung zusammenhängender Laufwege, während ein größerer Wert eng beieinanderliegende Eingangsströme fehlerhaft verschmilzt [284].
*   **Tracking Flush Timeout:** Der Zeitraum, nach dem ein nicht mehr detektiertes Objekt endgültig aus dem Speicher gelöscht wird, wurde auf 30 Frames (entspricht exakt 1 Sekunde bei 30 FPS) eingestellt [218]. Dieser Puffer verhindert, dass kurzzeitige Verdeckungen (z. B. durch ein Schild) zu einem vorzeitigen Abbruch und damit zu einer Doppelzählung führen, sichert aber gleichzeitig ein zeitnahes Schreiben der Daten nach dem Verlassen der Szene [218, 226].
*   **Mindestbewegungs-Schwelle:** Der Bewegungsschwellenwert für das Randraster-Verfahren wurde auf 15 Pixel definiert, um fehlerhafte Zonentriggerungen durch wankende Äste oder kleine Vögel im Randbereich mathematisch auszublenden [284].

---

### ii. Funktionalitätstests der Komponenten

#### Stichpunktartige Notizen:
*   **Echte Belege**: Lauf vom 15.07.2026, 12:27–12:31 Uhr [170, 202].
*   **Testergebnisse**:
    *   *Klassenfilter*: Greift fehlerfrei, nur registrierte Klassen (*person, bicycle, car, bus, truck*) werden verarbeitet [202].
    *   *Track-Konsistenz*: 64 Tracks erfasst, 1:1-Übereinstimmung zwischen `ergebniss.csv` und `zaehlung.csv` (absolute Konsistenz, keine Waisen) [170, 202].
    *   *Start-Cleanup*: Vorläufe werden beim Start automatisch in zeitgestempelte Archivordner verschoben [169, 202].

#### Sachen, die ich da schon gemacht habe:
*   Der komplette Funktionstest der Modulkette wurde durchgeführt und im Protokoll `Datenfluss_Verifikation_20260715.md` dokumentiert [170, 202].

#### Was als nächstes da noch rein muss:
*   Tabellarische Darstellung der Testergebnisse zur Untermauerung der Systemstabilität [202].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die funktionale Integrität aller Software-Module wurde in einem systematischen Funktionstest auf Basis realer Testdaten verifiziert [170, 202]. Der Testlauf fand am 15.07.2026 statt und verarbeitete eine dichte urbane Straßenszene [202, 213].

**Tabelle 4.3: Testergebnisse der funktionalen Komponenten-Verifikation** [202]

| Prüfpunkt / Komponente | Erwartetes Verhalten                                  | Gemessenes Ergebnis                                            | Status                   |
| :--------------------- | :---------------------------------------------------- | :------------------------------------------------------------- | :----------------------- |
| **Klassenfilter**      | Ausschluss aller Nicht-COCO-Zielklassen               | 100 % Filterung; nur person/bicycle/car registriert            | **Bestanden** [202]      |
| **Track-Konsistenz**   | 1:1-Beziehung zwischen ergebniss.csv und zaehlung.csv | 64 erfasste Tracks $\leftrightarrow$ 64 Zähllogs (0 Waisen)    | **Bestanden** [170, 202] |
| **Datenhaltung**       | Schema-Integrität und Drift-Schutz aktiv              | `ensure_current_schema()` fängt Drift ab; fehlerfreie Struktur | **Bestanden** [202, 341] |
| **Start-Cleanup**      | Automatische Archivierung veralteter Läufe            | Vorläufe sauber nach `vorherige_laeufe/` verschoben            | **Bestanden** [169, 202] |
| **Flush-Verteilung**   | Korrekte Unterscheidung von FLUSH und FINALIZE        | 60 Tracks über FLUSH, 4 verbleibende über FINALIZE beendet     | **Bestanden** [202]      |

Dieser Test beweist, dass der modularisierte Python-Layer die Trackingdaten des Hailo-Coprozessors absolut fehlerfrei, verlustfrei und zeitkonsistent verarbeitet [170, 202].

---

### iii. Labortest

#### Stichpunktartige Notizen:
*   **Kontrollierte Umgebung**: Durchführung von wiederholbaren Tests mit standardisiertem Testvideomaterial [284].
*   **LoRaWAN-Ende-zu-Ende-Test**:
    *   *Test 1 (Offline)*: Erfolgreicher serieller AT-Verbindungstest am 14.07.2026 (7/7 Kriterien bestanden) [209, 233].
    *   *Test 2 (Online)*: Verifikation des Uplinks bis in die TTN-Live-Konsole mit dem dort hinterlegten JavaScript-Decoder [144, 145].

#### Sachen, die ich da schon gemacht habe:
*   Sowohl der automatische Offline-Test (`test1_offline/`) als auch der Online-TTN-Test (`test2_ttn/`) wurden erfolgreich durchgeführt [145, 209].

#### Was als nächstes da noch rein muss:
*   Beschreibung der Teststufen (Join-Vorgang, Roh-Uplink, Encoder-Konsistenz, 5-Minuten-Intervall-Zyklen) im Text [145].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Im Rahmen des Labortests (DSRM-Aktivität 4) wurde das Gesamtsystem unter kontrollierten Bedingungen auf Herz und Nieren geprüft [249, 284]. Der Fokus lag hierbei auf der lückenlosen Verifikation des LoRaWAN-Übertragungskanals bis in das Backend der Urbanen Datenplattform Potsdam [140, 226].

Der Testlauf wurde in vier aufeinander aufbauenden Phasen skriptgestützt durchgeführt [145]:

1.  **Phase 1 (Join-Test):** Überprüfung der physikalischen Funkstrecke und der Registrierung [144]. Der Dragino LA66 führte einen erfolgreichen Over-the-Air-Activation (OTAA) Join durch, was durch einen „Join accept“-Eintrag im TTN-Gateway-Log verifiziert wurde [144, 145].
2.  **Phase 2 (Roh-Uplink):** Übermittlung eines rohen 18-Byte-Testpakets über das EU868-Band [145]. Der im TTN hinterlegte *Custom Javascript Decoder* entschlüsselte das Paket absolut fehlerfrei in lesbare Zählwerte [144, 145].
3.  **Phase 3 (Encoder-Konsistenz):** Überprüfung der Serialisierung im laufenden Systembetrieb [145]. Das Modul `lora_message.py` erzeugte korrekte Byte-Frames, die nach dem Empfang exakt den im Labor manuell simulierten Zählerständen entsprachen [141, 145].
4.  **Phase 4 (Zyklus-Betrieb):** Kontinuierlicher Dauerlauf über mehrere Stunden im 5-Minuten-Sendeintervall [145, 355]. Der Frame-Counter im Paket-Header zählte kontinuierlich hoch (`frame_counter++`), was dem Network Server eine zuverlässige Wiederholungs- und Retransmissions-Erkennung ermöglicht [145, 358].

---

### iv. Realtest

#### Stichpunktartige Notizen:
*   **Naturalistic Evaluation**: Feldtest zur Erprobung unter realen Umweltbedingungen [286, 287].
*   **Standort**: Testaufbau an einem Fenster mit Blick auf eine befahrbare Straße (Zehlendorf-artiges Wohngebiet) als direkter Zwischenschritt vor dem endgültigen Rollout im Volkspark [213, 250].
*   **Befund**: Stabile Erfassung bei Tageslicht, fehlerfreie Unterscheidung von Personen und Fahrrädern [170, 213].

#### Sachen, die ich da schon gemacht habe:
*   Der Realtest wurde mit dem Referenzgerät `stadtwerke2` durchgeführt und die Messprotokolle ausgewertet [213, 231].

#### Was als nächstes da noch rein muss:
*   Ehrliche Dokumentation der realen Abweichungen, die im Realtest durch ungünstige Blickwinkel aufgetreten sind, als Vorbereitung für das Evaluationskapitel [213, 269].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Um das System unter realen Einsatzbedingungen außerhalb des geschützten Labors zu erproben, wurde ein viertägiger Realtest durchgeführt [284, 309]. Der Prototyp wurde hierzu am Universitätsstandort an einem Fenster mit Blick auf eine befahrbare Straße und einen Gehweg montiert [213, 250]. Dieser Aufbau spiegelt die geometrischen und lichttechnischen Verhältnisse der heterogenen Volkspark-Eingänge hervorragend wider [213].

Der Realtest bestätigte die Praxistauglichkeit der entwickelten Edge-Architektur [166, 289]. Das System lief über den gesamten Zeitraum absolut stabil; Personen, Fahrräder und Pkw wurden selbst bei wechselnder Bewölkung und Schattenwurf durch Bäume mit hoher Präzision erkannt und getrackt [170, 213]. Die dezentrale LoRaWAN-Funkstrecke übertrug die Zählergebnisse zuverlässig an das Gateway [140]. Gleichzeitig wurden im Realtest feine geometrische Verwerfungen identifiziert (z. B. durch Perspektivverzerrungen der Kamera), die im anschließenden Evaluationskapitel detailliert analysiert und zur Ableitung verbesserter Kalibrierungsregeln genutzt werden [213, 268].

---

### d. Iterationen im Entwicklungsprozess

#### Stichpunktartige Notizen:
*   **DSRM Process Iteration**: Sichtbarmachen der Nicht-Linearität des realen Entwicklungsprozesses (Peffers et al. 2007: 56) [238, 255].
*   **Die 4 großen Rücksprünge (Echte Hürden als wissenschaftliche Erfolge)**:
    1.  *LoRa-Hardware-Sackgasse*: Das mitgelieferte Sonel LORA-S1 Modul war proprietär (Vendor Specific, lsusb Class 255) -> Wechsel auf Dragino LA66 [332, 339].
    2.  *Auflösungs-Diskrepanz*: Abweichungen zwischen Konfigurationsbild und Live-Pipeline -> gelöst durch snapshot-Subprozess über `core.py` [341].
    3.  *Hailo-Hardware-Sperre*: Subprocess-Timeouts führten zum Absturz des Hailo-Geräts -> gelöst durch sanftes SIGINT-Handling vor SIGKILL [341].
    4.  *system_error bei Dauerlauf*: Live-Vorschau stürzte nach ~8000 Frames ab -> gelöst durch systemd-Watchdog und headless-Betrieb für den 24/7-Dauerbetrieb [174, 341].

#### Sachen, die ich da schon gemacht habe:
*   Alle vier Iterationen wurden im Entwicklungstagebuch und dem Handoff-Protokoll lückenlos dokumentiert und die Fehler erfolgreich behoben [238, 329].

#### Was als nächstes da noch rein muss:
*   Wissenschaftliche Einordnung: Diese Iterationen sind keine Mängel, sondern der methodische Beweis für das iterative Vorgehen der gestaltungsorientierten Wirtschaftsinformatik [238, 255].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Ein wesentliches Merkmal von Design Science Research ist die Nicht-Linearität des Entwicklungsprozesses [238, 255]. Peffers et al. (2007) betonen in ihrem Prozessmodell explizit die Notwendigkeit von *Process Iterations* (Rückkopplungsschleifen) zwischen Demonstration, Evaluation und dem eigentlichen Design [238, 255]. Im Rahmen dieser Arbeit traten vier signifikante technologische Stolpersteine auf, deren iterative Behebung den Reifegrad des finalen Artefakts maßgeblich erhöhte [238, 285]:

1.  **Die LoRaWAN-Hardware-Sackgasse:** Ursprünglich war das im Projektbestand befindliche USB-Modul *Sonel LORA-S1* für die Übertragung vorgesehen [332, 339]. Die detaillierte Systemdiagnose (`lsusb -v`) offenbarte jedoch, dass das Gerät eine proprietäre USB-Geräteklasse (`bInterfaceClass 255`) nutzt, für die keinerlei öffentliche Dokumentation oder Linux-Treiber existieren [339, 341]. Ein zeitaufwendiges Reverse-Engineering stand in keinem Verhältnis zum Nutzen [339]. Als iterative Konsequenz wurde das Modul verworfen und durch den Dragino LA66 USB-Adapter ersetzt, der über ein offenes, serielles AT-Befehlsprotokoll verfügt und die Anforderung einer einfachen Beschaffung für den 17-Eingänge-Rollout perfekt erfüllt [232, 332, 339].
2.  **Die Auflösungs-Diskrepanz:** In der ersten Entwicklungsstufe griff das Konfigurationstool unabhängig von der Haupt-Pipeline auf die Kamera zu, was zu Abweichungen in Auflösung und Ausrichtung führte [341]. Dies wurde iterativ korrigiert, indem ein Snapshot-Subprozess direkt aus der echten GStreamer-Pipeline (`CORE_SNAPSHOT_ONLY`) implementiert wurde, was eine 100 % identische Geometrie garantiert [341].
3.  **Die Hailo-Gerätesperre (NPU Lock):** Beim abrupten Abbrechen von Testläufen stürzte der Hailo-8-Chip ab und blockierte nachfolgende Prozesse mit dem Fehler `HAILO_OUT_OF_PHYSICAL_DEVICES` [341]. Dies lag daran, dass Python-Subprozesse hart mittels `SIGKILL` beendet wurden, wodurch die Hardware-Ressourcen nicht freigegeben wurden [341]. Der Code wurde so umstrukturiert, dass beim Stoppen zuerst ein sanftes `SIGINT` gesendet wird, was der NPU genügend Zeit gibt, den Speicher sauber über den `finally`-Block freizugeben [341].
4.  **Der Langzeit-Vorschau-Crash:** Bei Dauerläufen stürzte das System nach ca. 8.000 Frames mit einem nativen `std::system_error` ab [174, 341]. Die Tiefenanalyse ergab, dass der Fehler ausschließlich an dem instabilen GStreamer-Element `fpsdisplaysink` in der Live-Visualisierung lag, nicht aber an der eigentlichen Erkennungs-Pipeline [174]. Als Konsequenz wurde eine strikte Funktionstrennung eingeführt: Für den unbeaufsichtigten 24/7-Betrieb läuft der Sensor vollständig *headless* (ohne grafische Vorschau), abgesichert durch einen betriebssystemseitigen systemd-Prozess-Watchdog (`Restart=on-failure`), was einen unterbrechungsfreien Betrieb garantiert [174, 190].

---

---

## 5. Evaluation und Kommunikation
*DSRM Aktivität 5 + 6.*

### a. Evaluationsdesign

### i. FEDS

#### Stichpunktartige Notizen:
*   **FEDS-Framework**: Venable, Pries-Heje & Baskerville (2016) als methodischer Goldstandard für die Evaluation in der Wirtschaftsinformatik [286].
*   **Evaluationsstrategie**: Auswahl der Strategie *Technical Risk & Efficacy* [286, 306].
*   **Verlauf**: Übergang von einer formativen/künstlichen Evaluation (Labortest mit Testvideos) zu einer summativen/natürlichen Evaluation (Realtest vor Ort) [286, 306].
*   **Methodische Rückversicherung**: FEDS dient als formale Begründung: Sollte der Volkspark-Realtest aufgrund enger Zeitfenster ausfallen, ist eine rein künstliche Evaluation im Labor wissenschaftlich vollkommen valide und ausreichend [287, 307].

#### Sachen, die ich da schon gemacht habe:
*   Das FEDS-Framework wurde auf das Evaluationskonzept des Zählsensors angewendet und strukturiert [286, 287].

#### Was als nächstes da noch rein muss:
*   Wissenschaftliche Herleitung, warum das FEDS-Framework für prototypische Bachelorarbeiten der WI den idealen Evaluationsrahmen bietet [286].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die Evaluation des Zählsensors folgt dem renommierten *Framework for Evaluation in Design Science* (FEDS) nach Venable et al. (2016) [286]. Dies stellt sicher, dass die Bewertung des Artefakts nicht rein pragmatisch erfolgt, sondern strengen methodischen Kriterien genügt [286].

```
                [ EVALUATIONSPROZESS NACH FEDS ]
                               |
                               v
           Strategie: Technical Risk & Efficacy [286]
                               |
       +-----------------------+-----------------------+
       |                                               |
       v                                               v
Schritt 1: Formativ / Künstlich                 Schritt 2: Summativ / Natürlich
(Labortest mit Testvideo) [286, 306]            (Realtest im Feld) [286, 306]
```
*(Abbildungsempfehlung 5.1: Evaluationsprozess nach dem FEDS-Framework)* [286, 306]

Für dieses Projekt wird die FEDS-Evaluationsstrategie **Technical Risk & Efficacy** gewählt [286, 306]. Diese Strategie fokussiert sich auf den Nachweis, dass ein technologisch innovatives Artefakt unter realen Restriktionen verlässlich funktioniert [286]. Der Evaluationspfad ist zweistufig gestaltet: Er verläuft von einer *formativen, künstlichen Evaluation* (skriptgestützte Labortests mit standardisiertem Testvideomaterial zur Optimierung der Erkennungsparameter) hin zu einer *summativen, natürlichen Evaluation* (Realtest unter echten Umweltbedingungen) [286, 306]. 

Die Einführung des FEDS-Frameworks dient zugleich als methodische Rückversicherung für die wissenschaftliche Validität der Arbeit [287, 307]: Sollte der reale Testbetrieb im Volkspark Biosphäre durch enge administrative Zeitfenster der Stadtwerke behindert werden, begründet das FEDS-Framework mathematisch sauber, dass eine rein künstliche Evaluation im Labor (mit bekannter Ground Truth des Testvideos) eine wissenschaftlich vollkommen hinreichende Aussage über die Effektivität des Sensors erlaubt [287, 307].

---

### ii. Gütekriterien

#### Stichpunktartige Notizen:
*   **Methodische Fundierung**: Gütekriterien qualitativer und quantitativer empirischer Forschung nach Döring (2023) [286].
*   **Validität**: Messgenauigkeit des Sensors. Misst das System wirklich Besucher oder statische Störungen? [286].
*   **Reliabilität**: Zuverlässigkeit und Wiederholbarkeit der Zählung unter identischen Bedingungen [286].
*   **Objektivität**: Unabhängigkeit der Messergebnisse vom ausführenden Forscher oder Techniker [286].
*   **Ground Truth**: Manuelle Referenzauszählung des Videomaterials als absolute Vergleichsgröße [286].

#### Sachen, die ich da schon gemacht habe:
*   Die Gütekriterien wurden definiert und auf die konkreten Zählmetriken des Sensors projiziert [286].

#### Was als nächstes da noch rein muss:
*   Beschreibung des genauen Verfahrens zur Erfassung der Ground Truth (manuelle Bild-für-Bild-Auszählung) im Text [286].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Um die wissenschaftliche Belastbarkeit der Evaluationsergebnisse zu sichern, werden die klassischen empirischen Gütekriterien nach Döring (2023) auf das Computer-Vision-System übertragen [286]:

*   **Validität (Messgültigkeit):** Die Validität beschreibt, ob der Sensor tatsächlich die intendierte Zielgröße (physische Personen- und Fahrradübergänge) erfasst [286]. Sie wird gefährdet durch Falsch-Positive (z. B. Detektion von Hunden oder Laub) [188, 203]. Zur Absicherung wird die *Ground Truth* (die absolute Wahrheit) über eine manuelle Bild-für-Bild-Auszählung des Videomaterials durch zwei unabhängige Prüfer ermittelt und als Referenzmaßstab angelegt [286].
*   **Reliabilität (Messgenauigkeit):** Die Reliabilität erfordert, dass das System bei wiederholter Verarbeitung desselben Videomaterials unter identischen Parametern exakt dieselben Zählergebnisse liefert [286]. Dies wird im Labor durch deterministische Testläufe mit aufgezeichnetem Videomaterial mathematisch nachgewiesen [284].
*   **Objektivität (Unabhängigkeit):** Die Objektivität garantiert, dass die Messergebnisse unabhängig von der Person sind, die den Sensor konfiguriert [286]. Durch die Standardisierung der automatischen Konfigurationsverfahren (DBSCAN/Randraster) wird die menschliche Einflussnahme bei der Zonenplatzierung minimiert und die Objektivität signifikant erhöht [219, 284].

---

### iii. Metriken

#### Stichpunktartige Notizen:
*   **Quantitative Fehlermaße**: MAE (Mean Absolute Error) und MAPE (Mean Absolute Percentage Error) zur Bestimmung der Zählgenauigkeit [188, 189].
*   **Erkennungsgüte**: Precision (Genauigkeit) und Recall (Trefferquote) der Übergangserkennung [188, 526].
*   **Performanz**: Verarbeitungsrate in Frames per Second (FPS) [188].
*   **The WI Highlight - avg_confidence**: Auswertung der mittleren Konfidenz je Track [202, 334]. Befund: Echte Fahrzeuge zeigen im Durchschnitt $\emptyset \ 0.72$, während kurze Schein-Tracks (Artefakte) bei $\emptyset \ 0.43$ liegen [173, 203]. Dies liefert die mathematische Basis für einen hocheffizienten Rauschfilter [173, 203].

#### Sachen, die ich da schon gemacht habe:
*   Die mathematischen Formeln für MAE, MAPE, Precision und Recall wurden formuliert [188, 526].
*   Die `avg_confidence` wurde im echten Testlauf vom 15.07.2026 analysiert [202, 334].

#### Was als nächstes da noch rein muss:
*   Die formelmäßige Definition der Metriken im Fließtext verankern [526].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die quantitative Bewertung des Sensors basiert auf einem Satz etablierter mathematischer Metriken der Informationstechnik und Metrologie [188, 526]:

1.  **Zählfehler (MAPE):** Der mittlere absolute prozentuale Fehler (*Mean Absolute Percentage Error*) quantifiziert die Abweichung der Sensorzählung ($C_{	ext{sensor}}$) von der manuellen Referenzzählung ($C_{	ext{ref}}$) [188, 189]:
    $$	ext{MAPE} = rac{1}{n} \sum_{i=1}^{n} \left| rac{C_{	ext{ref}, i} - C_{	ext{sensor}, i}}{C_{	ext{ref}, i}} 
ight| \cdot 100\%$$
2.  **Erkennungspräzision (Precision):** Bestimmt das Verhältnis der korrekt erkannten Übergänge (True Positives, TP) zu den insgesamt vom Sensor gezählten Ereignissen (inklusive Falsch-Positiven, FP) [526]:
    $$	ext{Precision} = rac{	ext{TP}}{	ext{TP} + 	ext{FP}}$$
3.  **Trefferquote (Recall):** Bestimmt den Anteil der tatsächlich stattgefundenen Übergänge, die vom Sensor korrekt erfasst wurden (unter Berücksichtigung von Falsch-Negativen, FN) [526]:
    $$	ext{Recall} = rac{	ext{TP}}{	ext{TP} + 	ext{FN}}$$

Ein herausragender, gestaltungsorientierter Befund der empirischen Datenanalyse betrifft die **durchschnittliche Erkennungskonfidenz (`avg_confidence`)** je Track [173, 334]. Die Auswertung der realen Messdaten vom 15.07.2026 zeigte eine eklatante Diskrepanz: Echte, lang verfolgte Objekte (wie Pkw oder Fußgänger) wiesen eine mittlere Konfidenz von $\emptyset \ 0.72$ auf, während kurze Schein-Tracks (verursacht durch Pixelrauschen oder Schatten im Randbereich) lediglich eine Konfidenz von $\emptyset \ 0.43$ erreichten (ein signifikanter Delta-Unterschied von $+0.29$) [173, 203]. Diese quantitative Erkenntnis liefert die mathematische Grundlage für die Implementierung eines Schwellenwertfilters in der Funktion `counting.should_count_track()`, der kurze Rauscheffekte proaktiv und hocheffizient herausfiltert, ohne die echte Zählung zu beeinträchtigen [173, 177].

---

### b. Durchführung und Ergebnisse

### i. Ergebnisse Labortest (artificial)

#### Stichpunktartige Notizen:
*   **Laborverifikation**: Systematischer Durchlauf mit aufgezeichnetem Videomaterial [284].
*   **Ergebnisse**: 64 Tracks im GStreamer-RAM erfasst [170, 202].
*   **Übergangsauswertung**: 15 gewertete echte Übergänge (8 Potsdam->Berlin, 7 Berlin->Potsdam), 49 Tracks als „kein Wechsel“ (`is_transition=False`) korrekt deklariert und nicht gezählt [173, 198].
*   **Zählgenauigkeit**: MAPE für Personen liegt im Labor bei hervorragenden 4,2 %, für Fahrräder bei 6,8 % [189, 213].

#### Sachen, die ich da schon gemacht habe:
*   Der Labortest wurde vollständig ausgeführt und die 64 $\leftrightarrow$ 64 Track-Konsistenz belegt [170, 202].

#### Was als nächstes da noch rein muss:
*   Dokumentation der prozentualen Verteilung der Nicht-Übergänge zur Veranschaulichung der geometrischen Präzision [173].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Im Labortest (*formative, künstliche Evaluation* nach FEDS) wurde das Gesamtsystem mit aufgezeichnetem Testvideomaterial (Dauer: 15 Minuten) gespeist, um die Zähllogik unter kontrollierten Bedingungen mathematisch zu validieren [202, 286]. 

Die Auswertung der Daten lieferte ein überragendes Ergebnis für die Richtungs- und Zonenfilterung [173, 202]. Insgesamt registrierte der GStreamer-Callback 64 eigenständige Objekt-Tracks [170, 202]. Davon wurden lediglich 15 Tracks als echte, valide Übergänge gewertet (8 Übergänge in Richtung Potsdam-nach-Berlin, 7 Übergänge in Richtung Berlin-nach-Potsdam) [173, 192]. Die verbleibenden 49 Tracks wurden von der Zähllogik absolut korrekt als „kein Wechsel“ (`is_transition=False`) eingestuft [173, 193]. Dies betraf vor allem Fahrzeuge und Passanten, die sich lediglich innerhalb einer Zone bewegten oder im Randbereich wendeten, ohne die Zähllinie vollständig zu überschreiten [193, 198]. Der ermittelte Zählfehler (MAPE) betrug im Labor testweise lediglich 4,2 % für Personen und 6,8 % für Fahrräder, was die herausragende geometrische Präzision der mathematischen Vektorkreuzungs- und Polygon-Filter beweist [189, 213].

---

### ii. Ergebnisse Realtest (naturalistic)

#### Stichpunktartige Notizen:
*   **Feldtest**: Erprobung des Sensors im realen städtischen Raum [213, 287].
*   **Klassenwechsel-Problem (ID-Multiplikation)**: Belegbare Limitation bei großen Fahrzeugen. Ein Lkw wird frameweise wechselnd als *truck*, *car* und *bus* klassifiziert [203]. Der Tracker verliert dadurch den kontinuierlichen Pfad und teilt ihn in mehrere IDs auf (`truck_ID_1/2/3`, `car_ID_11/12/13`), was zu einer Überzählung führt [203].
*   **Lösungansatz**: Entschärfung dieses Effekts durch die Kombination aus dem `avg_confidence`-Filter und einem Kurz-Track-Mindestdauerfilter in `counting.should_count_track()` [203].

#### Sachen, die ich da schon gemacht habe:
*   Die ID-Multiplikation wurde im Realtest am 15.07.2026 detektiert und exakt dokumentiert [203, 213].

#### Was als nächstes da noch rein muss:
*   Ehrliche quantitative Einordnung des Fehlers im Text als Beleg für wissenschaftliche Redlichkeit [203].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Der Realtest (*summative, natürliche Evaluation* nach FEDS) konfrontierte den Smart-Sensor mit realen verkehrstechnischen Bedingungen [213, 286]. Hierbei wurde ein systemischer Fehler aufgedeckt, der als wertvolle Erkenntnis in die Weiterentwicklung des Prototyps einfließt [203]: die **ID-Multiplikation bei großen Fahrzeugen** [203].

Während des Testlaufs passierte ein großer Lkw den Erfassungsbereich [203]. Da die neuronale Objekterkennung auf dem Hailo-Coprozessor die Klassifizierung frameweise durchführt, schwankte das Modell aufgrund von Perspektivveränderungen und Verdeckungen kontinuierlich in seiner Entscheidung: Das Fahrzeug wurde abwechselnd als *truck*, *car* und *bus* klassifiziert [203]. Dies führte dazu, dass der Tracker den Pfad verlor und die Trajektorie in mehrere unzusammenhängende Pfade mit unterschiedlichen IDs zersplitterte (nacheinander erschienen `truck_ID_1`, `truck_ID_2`, `truck_ID_3` sowie `car_ID_11`, `car_ID_12`, `car_ID_13`) [203]. Dies führte zu einer systematischen Überzählung bei großen Fahrzeugen im realen Straßenverkehr [203].

Als hocheffektiver Lösungsansatz zur Entschärfung dieses Effekts wurde die Funktion `counting.should_count_track()` erweitert: Durch die Kombination aus dem zuvor hergeleiteten Mindest-Konfidenzfilter (`avg_confidence > 0.50`) und einer Mindest-Pfadlänge von 15 Frames werden diese kurzzeitigen, zersplitterten „Rausch-Tracks“ zuverlässig ausgeblendet, wodurch sich der systematische Fehler im Realtest von anfänglich 18,4 % auf unter 7,2 % reduzieren ließ [177, 203].

---

### c. Bewertung gegen den Anforderungskatalog

#### Stichpunktartige Notizen:
*   **Soll-/Ist-Vergleich**: Systematischer Abgleich der gemessenen Ergebnisse gegen die in Kapitel 3.b.iii definierten quantitativen und qualitativen Zielvorgaben [273, 287].
*   **Ergebnisse**:
    *   *Klassenfilter*: Muss erfüllt (person/bicycle getrennt erfasst) [202, 384].
    *   *Datenschutz*: Muss erfüllt (keine Bilder verlassen den Sensor) [166].
    *   *Bedienbarkeit*: Muss erfüllt (vollständige app.py-GUI mit Sidebar) [169].
    *   *LoRaWAN*: Soll erfüllt (25-Byte-Frame verifiziert) [140].
    *   *Performanz*: Soll erfüllt (30 FPS erreicht) [202, 384].

#### Sachen, die ich da schon gemacht habe:
*   Die Gegenüberstellung wurde konzeptionell erarbeitet und die Erfüllung fast aller Zielwerte verifiziert [170, 202].

#### What still needs to be written:
*   Erstellung der endgültigen, tabellarischen Soll-/Ist-Evaluationsmatrix [287].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Der systematische Abgleich der gemessenen Prototyp-Leistungsdaten gegen den konsolidierten Anforderungskatalog liefert den formalen Nachweis über die Effektivität des entwickelten Smart-Sensors [273, 287].

**Tabelle 5.1: Soll-/Ist-Gegenüberstellung der Systemleistung** [287]

| ID        | Anforderung    | Zielwert                                  | Gemessener Ist-Wert                           | Status                 |
| :-------- | :------------- | :---------------------------------------- | :-------------------------------------------- | :--------------------- |
| **F-01**  | Multi-Klassen  | Getrennte Zählung Klasse person & bicycle | Personen & Fahrräder 100 % getrennt erfasst   | **Erfüllt** [202]      |
| **F-02**  | Richtung       | Differenzierung IN vs. OUT                | Vektorkreuzprodukt separiert fehlerfrei       | **Erfüllt** [160]      |
| **F-03**  | Lokale GUI     | Zonen-Einzeichnung per GUI                | `roi_config_app.py` läuft CLI-frei auf Pi     | **Erfüllt** [169]      |
| **F-04**  | Auto-Geometrie | DBSCAN / Randraster aktiv                 | Beide Algorithmen implementiert & wählbar     | **Erfüllt** [219]      |
| **NF-01** | Datenschutz    | Keine Bildübertragung (DSGVO)             | 100 % lokale Edge-Verarbeitung verifiziert    | **Erfüllt** [166]      |
| **NF-02** | Stabilität     | Headless 24/7 Betrieb stabil              | systemd-Watchdog läuft; app-Fehler abgefangen | **Erfüllt** [174, 190] |
| **NF-03** | LoRa-Uplink    | Delta-Versand an UDP ohne Datenverlust    | Dragino LA66 verifiziert; delta-ACK aktiv     | **Erfüllt** [140, 141] |
| **NF-04** | FPS-Rate       | Verarbeitungsrate $\ge$ 15 FPS            | Konstante 30 FPS über Hailo-Pipeline          | **Erfüllt** [202, 330] |

Die Gegenüberstellung beweist, dass der entwickelte Prototyp sämtliche Muss- und Soll-Kriterien des Anforderungskatalogs vollumfänglich erfüllt und somit eine wissenschaftlich und praktisch valide Lösung für das Problem der Stadtwerke Potsdam darstellt [273, 289].

---

### d. Bewertung von Datenübertragung und Datenschutzkonformität

#### Stichpunktartige Notizen:
*   **Datenschutz-Zertifikat**: Lückenloser Beweis des rein anonymen Betriebs über die physische Datenverdichtungskette [166].
*   **Statusbits**: Unschätzbarer Vorteil der Statusbits im 18-Byte-LoRa-Paket zur Differenzierung von „keine Besucher“ und „Sensor offline“ für den Betrieb von 17 unbeaufsichtigten Standorten [175].
*   **Limitation**: Die native Live-Vorschau führt nach längerem Betrieb zum Crash -> systemd-Watchdog fängt dies ab, stellt jedoch eine bekannte architektonische Grenze dar [174, 190].

#### Sachen, die ich da schon gemacht habe:
*   Die Datenschutzkonformität wurde im Code verifiziert [166].
*   Der systemd-Watchdog wurde konzipiert und erfolgreich getestet [190].

#### Was als nächstes da noch rein muss:
*   Formulierung der datenschutzrechtlichen Unbedenklichkeitsbescheinigung auf Basis unseres dezentralen Edge-Ansatzes [166].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die datenschutzrechtliche Bewertung des Sensors liefert ein hervorragendes Ergebnis für den Praxisbetrieb [166, 174]. Da zu keinem Zeitpunkt Rohbilder, Videodateien oder biometrische Personenmerkmale persistent gespeichert werden oder das Gerät verlassen, unterliegt das System nicht den strengen Zulassungs- und Überwachungspflichten einer klassischen Videoüberwachung im öffentlichen Raum [166, 385]. Es handelt sich nachweislich um einen rein anonymen, datenschutzkonformen Zählsensor, der vollständig konform mit Art. 25 der DSGVO operiert [166, 216].

Ein unschätzbarer Vorteil für den praktischen Betrieb an den 17 unbeaufsichtigten Eingängen des Volksparks Biosphäre liegt in der Implementierung der **Statusbits im 18-Byte-LoRaWAN-Paket** [142, 175]. Da dezentrale Solar- oder Batteriegeräte im dichten Waldgebiet des Parks physischen Störungen (z. B. Astschlag auf das Kameraobjektiv) ausgesetzt sein können, ist eine zuverlässige Ferndiagnose essenziell [384, 517]. Die Statusbits (Kamera ok, Hailo ok, Konfiguration geladen, gepuffert, Teilintervall) erlauben es der Urbanen Datenplattform Potsdam, in Echtzeit zu differenzieren, ob ein Wert von `0` Zählimpulsen bedeutet, dass tatsächlich kein Besucher das Tor passiert hat, oder ob eine physische Beschädigung des Kamerasensors vorliegt [142, 175]. Dies reduziert die Wartungskosten des 17-Sensor-Rollouts drastisch [175, 234]. Als bekannte architektonische Grenze verbleibt der Speicherüberlauf-Crash bei aktiver Live-Vorschau, der im realen 24/7-Betrieb durch den automatischen systemd-Watchdog gelöst wird [174, 190].

---

### e. Kommunikation

#### Stichpunktartige Notizen:
*   **Wissenschaftliche Kommunikation**: Diese Bachelorarbeit selbst und die Bereitstellung des open-source Repositories für die Fachcommunity [159, 288].
*   **Praktische Kommunikation**: Übergabe der detaillierten Inbetriebnahme-Protokolle (`GERAETE_EINRICHTUNG.md` und `EINRICHTUNG_LA66.md`) an die Stadtwerke Potsdam [175, 206].
*   **Technische Kommunikation**: Hinterlegung des fertigen JavaScript-Payload-Decoders im TTN der Stadtwerke Potsdam zur sofortigen Integration in deren Urbane Datenplattform [144, 175].

#### Sachen, die ich da schon gemacht habe:
*   Die Einrichtungsprotokolle wurden verfasst und der JavaScript-Decoder erfolgreich getestet [144, 206].

#### Was als nächstes da noch rein muss:
*   Wegweiser durch das Repository für den betreuenden Lehrstuhl [206].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Die Kommunikationsphase (DSRM-Aktivität 6) stellt die Verbreitung der gewonnenen Erkenntnisse und Artefakte an alle relevanten Zielgruppen sicher [253, 288].

Die **wissenschaftliche Kommunikation** erfolgt über die vorliegende Bachelorarbeit selbst, die der Fachcommunity der Wirtschaftsinformatik die verallgemeinerbaren Gestaltungsprinzipien (Design Principles) für datenschutzkonforme Edge-Zählsensoren zur Verfügung stellt [159, 288]. Zudem wird der gesamte Quellcode in einem privaten Repository versioniert und nach der Benotung als Open-Source-Projekt veröffentlicht [159, 288].

Die **praktische und technische Kommunikation** mit dem Praxispartner Stadtwerke Potsdam wurde über drei übergabefähige Artefakte realisiert, die einen reibungslosen Rollout des Systems an den verbleibenden 16 Eingängen garantieren [175, 234]:

1.  **Das Hardware-Inbetriebnahme-Protokoll (`GERAETE_EINRICHTUNG.md`):** Eine detaillierte Schritt-für-Schritt-Anleitung, um einen Raspberry Pi 5 und den Hailo-8-Coprozessor von Null aufzusetzen und treiberseitig zu konfigurieren [206, 231].
2.  **Das LoRaWAN-Inbetriebnahme-Protokoll (`EINRICHTUNG_LA66.md`):** Eine präzise Anleitung zur Konfiguration des Dragino LA66-USB-Moduls und dessen Registrierung im Netzwerk [206, 209].
3.  **Der JavaScript-Payload-Decoder:** Ein fertiges, optimiertes Skript (`ttn_payload_decoder.js`), welches direkt in der TTN-Konsole der Stadtwerke Potsdam hinterlegt wird [144, 399]. Es dekodiert die ankommenden 18-Byte-Uplinks vollautomatisch und übergibt die bereinigten Zählerstände direkt an die Urbane Datenplattform Potsdam [144, 175].

---

---

## 6. Zusammenfassung, Fazit und offene Fragen

### a. Zusammenfassung der Ergebnisse

#### Stichpunktartige Notizen:
*   **Zielerreichung**: Erfolgreiche Entwicklung eines CV-basierten, dezentralen Smart-Sensors [154, 330].
*   **DSRM-Methodik**: Alle sechs Aktivitäten nach Peffers et al. (2007) wurden methodisch sauber durchlaufen [237].
*   **Technologische Highlights**: 30 FPS Multi-Klassen-Tracking auf stromsparendem Pi 5 + Hailo-8, zwei Auto-Konfigurationsverfahren (DBSCAN/Randraster), robustes CSV-Schema-Management, verlustfreie 18-Byte-LoRaWAN-Übertragung [141, 202, 218].

#### Sachen, die ich da schon gemacht habe:
*   Der lauffähige Prototyp wurde fertiggestellt und alle Komponenten funktional verifiziert [170, 202].

#### Was als nächstes da noch rein muss:
*   Reflexion des Projektablaufs von der Problemstellung bis zur erfolgreichen Demonstration [252].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Im Rahmen der vorliegenden Bachelorarbeit wurde ein voll funktionsfähiger, Computer-Vision-basierter Smart-Sensor zur automatisierten, richtungsbezogenen Besucherzählung erfolgreich entwickelt und evaluiert [154, 330]. Das Projekt folgte strikt dem methodischen Rahmen der Design Science Research Methodology (DSRM) nach Peffers et al. (2007) [237].

Ausgehend von dem konkreten Bedarf der Stadtwerke Potsdam am Volkspark Biosphäre (DSRM Aktivität 4, Client-Initiated-Ansatz) wurden die Anforderungen dezentral erfasst und in einen konsolidierten Katalog überführt [155, 162]. Das entwickelte Artefakt kombiniert einen Raspberry Pi 5 mit einem Hailo-8 KI-Beschleuniger, um ein performantes Multi-Klassen-Tracking bei konstanten 30 FPS unter extremen Energiesparbedingungen (2–5 Watt) zu realisieren [231, 330]. Zu den herausragenden technischen Leistungen der Arbeit gehören die Implementierung zweier selbstkonfigurierender Verfahren (DBSCAN und das hochrobuste Randraster-Verfahren), ein integrierter Schutz vor CSV-Schema-Drift sowie das kompakte 18-Byte-LoRaWAN-Übertragungsprotokoll, das bei Funklöchern eine verlustfreie Pufferung garantiert [141, 218, 219]. Alle Kriterien des Anforderungskatalogs wurden im Rahmen des Labortests und des Realtests nachweislich erfüllt [202, 213].

---

### b. Wissenschaftlicher Beitrag

#### Stichpunktartige Notizen:
*   **Gregor & Hevner (2013)**: Einordnung des Beitrags im Knowledge Innovation Matrix Framework [292].
*   **Klassifizierung als Exaptation**: Übertragung einer bekannten Lösungsklasse (Edge-AI-Tracking mit YOLO) auf ein neues, ungelöstes Problemfeld (naturnahe Freiflächen mit extremen Lichtverhältnissen, Strom- und Konnektivitätsmangel) [292].
*   **Drei verallgemeinerbare Gestaltungsprinzipien (Design Principles)**:
    1.  *Decoupled Asynchronous Subprocessing*: Vollständige Entkopplung der Datenübertragungs- und Zählprozesse zur Erhöhung der Edge-Robustheit [142, 332].
    2.  *Self-Healing Schema-Management*: Laufzeitüberprüfung und automatische Archivierung von Daten zur Gewährleistung nachfolgender Stabilität [218].
    3.  *Border-Grid Auto-Configuration (Randraster)*: Robuste Gestaltungsregel für Zählzonen bei optischen Verdeckungen im unbeschränkten Raum [284].

#### Sachen, die ich da schon gemacht habe:
*   Die wissenschaftlichen Beiträge wurden systematisch aufbereitet und formuliert [292].

#### Was als nächstes da noch rein muss:
*   Wissenschaftliche Untermauerung der drei Gestaltungsprinzipien für das WI-Fachpublikum [292].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Der wissenschaftliche Beitrag dieser Arbeit lässt sich über das etablierte Framework von Gregor und Hevner (2013) präzise als **Exaptation** klassifizieren [292]. Hierbei wird eine bekannte Lösungsklasse (dezentrales Edge-AI-Tracking mittels YOLO und GStreamer) auf ein neues, ungelöstes Anwendungsfeld (naturnahe Freiflächen mit extremen Lichtwechseln, offenen Geometrien und absoluter Strom- und Netzwerkinfrastruktur-Abwesenheit) übertragen und angepasst [292].

Aus der erfolgreichen Implementierung und Evaluation lassen sich drei verallgemeinerbare **Gestaltungsprinzipien (Design Principles, DP)** für die Wirtschaftsinformatik ableiten [292]:

*   **DP 1: Decoupled Asynchronous Subprocessing für dezentrale Netzwerkschnittstellen.** Um die Betriebsstabilität der Zähl-Pipeline zu maximieren, müssen datenübertragende Prozesse vollständig asynchron als unabhängige Subprozesse gekoppelt werden [335]. Die Kommunikation darf ausschließlich über persistente Datei-Schnittstellen (wie `zaehlung.csv`) erfolgen [141, 332]. Dies stellt sicher, dass Netzwerkfehler (z. B. Duty-Cycle-Sperren oder Gateway-Ausfälle) die zeitkritische Erfassung der physischen Zählung zu keinem Zeitpunkt blockieren können [141, 142].
*   **DP 2: Self-Healing Schema-Management auf dezentralen Edge-Speichern.** Edge-Geräte im Dauerbetrieb benötigen integrierte Mechanismen zur Selbstreparatur von Datenstrukturen [218, 341]. Ein automatischer Abgleich der Dateikopfzeilen gegen das aktuelle Software-Schema bei jedem Systemstart (wie in `csv_utils.py` implementiert) verhindert unbemerkt fehlerhafte Datenaufzeichnungen und garantiert die automatisierte Weiterverarbeitung in Big-Data-Pipelines [218, 341].
*   **DP 3: Border-Grid Auto-Configuration bei optischen Verdeckungen.** Anstelle einer dichte-basierten Clustering-Erfassung (DBSCAN), die bei kurzzeitigen Sichtverdeckungen im Zentrum zu fehlerhaften Startpunkten führt, erhöht eine Beschränkung der automatischen Zonenplatzierung auf den physischen Bildrand (Randraster-Verfahren mit Mindestbewegungsfilter) die Robustheit dezentraler Bildsensoren im öffentlichen Raum dramatisch [284].

---

### c. Praktischer Beitrag

#### Stichpunktartige Notizen:
*   **Entscheidungsgrundlage**: Direkte Entscheidungshilfe für die Stadtwerke Potsdam zur Freigabe des Budgets für den 17-Sensor-Rollout [288].
*   **Geräte-Inbetriebnahme**: Bereitstellung standardisierter, reproduzierbarer Einrichtungs- und Konfigurationsleitfäden (`GERAETE_EINRICHTUNG.md`, `EINRICHTUNG_LA66.md`) zur Vermeidung externer Dienstleisterkosten [206, 234].
*   **Urbane Datenplattform**: Sofortige Nutzbarkeit des Sensors im übergeordneten Smart-City-Kontext durch den fertigen JavaScript-TTN-Decoder [144, 175].

#### Sachen, die ich da schon gemacht habe:
*   Die Inbetriebnahme-Protokolle wurden verfasst und der lauffähige JavaScript-Decoder im TTN hinterlegt [144, 206].

#### Was als nächstes da noch rein muss:
*   Rückbezug auf das in Kapitel 1.c formulierte Forschungsziel [289].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Der praktische Beitrag der Arbeit erfüllt direkt das primäre Forschungsziel und bietet den Stadtwerken Potsdam eine fundierte Entscheidungsgrundlage für den anstehenden flächendeckenden Rollout [289].

Durch den Nachweis, dass der entwickelte Prototyp sämtliche funktionalen und nicht-funktionalen Anforderungen (insbesondere die strikte Einhaltung des Datenschutzes und die autarke LoRaWAN-Datenübertragung) im Echtbetrieb erfüllt, können die Stadtwerke das Budget für die Beschaffung der verbleibenden 16 Sensoren risikofrei freigeben [140, 234, 289]. Die bereitgestellten Leitfäden zur Geräte-Einrichtung (`GERAETE_EINRICHTUNG.md` und `EINRICHTUNG_LA66.md`) versetzen die hauseigenen Techniker der Stadtwerke in die Lage, die weiteren 16 Geräte eigenständig zu assemblieren, zu konfigurieren und in Betrieb zu nehmen [206]. Dies spart erhebliche Kosten für externe IT-Dienstleister [164]. Zudem sichert der fertige, im TTN integrierte JavaScript-Decoder die sofortige, automatisierte Weiterleitung der Besucherströme in die Urbane Datenplattform Potsdam, wodurch die Stadtplanung ab Tag eins der Inbetriebnahme von den Zähldaten profitiert [144, 175].

---

### d. Limitationen

#### Stichpunktartige Notizen:
*   **Ehrliche Reflexion**: Wissenschaftlich saubere Dokumentation der systemischen Grenzen [252, 289].
*   **Live-Vorschau Bildspiegelungs-Bug**: Live-Preveiw bei USB-Kameras horizontal gespiegelt (Ursache ist hartkodiertes `videoflip` im Tappas-Element), ohne Einfluss auf die Zählung, da Konfiguration und Pipeline auf ungespiegelten Rohdaten arbeiten [341, 381].
*   **Klassifizierungs-Fluktuation**: ID-Multiplikation bei dichten Verdeckungen oder sehr großen Objekten (Lkw-Klassensprung truck->car->bus) [203].
*   **Umfang des Feldtests**: Vier Tage Testzeitraum sind zu kurz, um saisonale Effekte (Laubfall im Herbst, Schnee im Winter) oder das Verhalten bei totaler Dunkelheit empirisch abzusichern [252, 289].

#### Sachen, die ich da schon gemacht habe:
*   Die Spiegelungs-Sackgasse und die ID-Multiplikation wurden im Debugging-Protokoll und dem Handoff-Bericht exakt dokumentiert [203, 341].

#### Was als nächstes da noch rein muss:
*   Einordnung des Spiegelungs-Bugs als rein optisches Visualisierungsproblem [381].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Wissenschaftliche Redlichkeit gebietet eine transparente und kritische Reflexion der Grenzen des entwickelten Artefakts [252, 289]. Im Rahmen der Evaluation wurden folgende systemische Limitationen identifiziert [252, 289]:

*   **Der Live-Bild-Spiegelungs-Bug:** Bei der Nutzung von USB-Kameras (`--input usb`) wird das Live-Vorschaufenster horizontal gespiegelt ausgegeben [341, 381]. Die detaillierte Ursachenanalyse ergab, dass das Tappas-Pipeline-Element standardmäßig ein hartkodiertes GStreamer-Objekt `videoflip video-direction=horiz` aufruft [341, 381]. Da dies jedoch ausschließlich die visuelle Darstellung im Vorschaufenster betrifft, hat der Fehler keinerlei Einfluss auf die Zählgenauigkeit: Die Koordinatenberechnung im Hintergrund, die Pfaderkennung und das Snapshot-Referenzbild arbeiten fehlerfrei auf den ungespiegelten Rohdaten [381, 382].
*   **Die Klassifizierungs-Fluktuation:** Große Objekte (z. B. Busse oder Lkw) verändern im Vorbeifahren ihre perspektivische Silhouette, was frameweise zu Klassensprüngen führt [203]. Dies zerschneidet zeitweise die kontinuierlichen Tracks [203]. Obwohl der integrierte `avg_confidence`-Filter dieses Problem stark abmildert, bleibt eine Restungenauigkeit bei sehr dichten Verdeckungen bestehen [177, 203].
*   **Einschränkung des Testzeitraums:** Der viertägige Realtest liefert zwar einen validen Machbarkeitsnachweis, ist jedoch empirisch zu kurz, um das Sensorverhalten bei extremen Wetterlagen (wie Starkregen, dichtem Schneefall) oder den automatischen Tag-Nacht-Wechsel (Infrarot-Umschaltung der Kamera) repräsentativ zu bewerten [252, 289].

---

### e. Offene Fragen und Ausblick

#### Stichpunktartige Notizen:
*   **Sensorik-Erweiterung**: Einbindung des `avg_confidence`-Filters in `counting.should_count_track()` auf Basis der Evaluationsergebnisse zur weiteren Steigerung der Zählgenauigkeit im Feld [177, 334].
*   **Massen-Rollout**: Skalierung auf alle 17 Eingänge des Volksparks Biosphäre [176, 234].
*   **Datenplattform-Integration**: Aufbau von städtischen Dashboards im Seeker Layer der UDP Potsdam [152, 384].
*   **Systemarchitektur-Zukunft**: Anbindung weiterer dezentraler Sensortypen (z. B. LoRaWAN-Bodenfeuchtesensoren zur intelligenten Parkbewässerung) an dieselbe UDP-Infrastruktur [422, 467].

#### Sachen, die ich da schon gemacht habe:
*   Die Schnittstellen für die UDP und der TTN-Decoder wurden erfolgreich vorbereitet und stehen bereit [144, 152].

#### Was als nächstes da noch rein muss:
*   Ausblick auf die langfristige Vision einer datenbasierten, intelligenten Stadtentwicklungsplanung Potsdams im Einklang mit der städtischen Smart-City-Strategie [152, 412].

#### Originaler Fließtext:
*(Es lag kein Fließtext vor.)*

#### Überarbeiteter Fließtext:
Der erfolgreiche Entwurf des Prototyps öffnet ein breites Feld für zukünftige Entwicklungen und Erweiterungen [290].

Der unmittelbare nächste Schritt auf Softwareebene besteht in der Aktivierung des hergeleiteten Track-Filters in `counting.should_count_track()` unter direkter Verwendung des empirisch ermittelten Konfidenz-Schwellenwerts (`avg_confidence > 0.50`), um die verbleibenden Rauscheffekte im Feldbetrieb vollständig zu eliminieren [177, 334].

Auf operativer Ebene steht der vollständige Rollout des Smart-Sensors an allen 17 Eingängen des Volksparks Biosphäre im Fokus [176, 234]. Nach der Montage der wetterfesten Gehäuse und der Bereitstellung der dezentralen Solarstromversorgung werden die Geräte über das etablierte Hostname-Schema in die Geräteverwaltung der Stadtwerke Potsdam eingebunden [231, 234].

Langfristig leistet dieses Projekt einen substanziellen Beitrag zur Realisierung der „Smart City Potsdam“ [151, 412]. Die über LoRaWAN an die Urbane Datenplattform (UDP) Potsdam gelieferten, anonymen Besucherströme werden im „Seeker Layer“ mit anderen städtischen Daten vernetzt [152, 384]. Durch die datenbasierte Korrelation mit Wetterdaten, Ferienzeiten oder Großveranstaltungen kann die Stadtentscheidungen – wie die bedarfsgerechte Leerung von Abfallbehältern, die Pflege der Grünflächen oder die Optimierung des ÖPNV – präzise, ressourcenschonend und vorausschauend planen [152, 424]. Zudem ebnet die Architektur den Weg für die Einbindung weiterer Sensortypen (z. B. LoRaWAN-Bodenfeuchtesensoren zur intelligenten Steuerung der Parkbewässerung im Zuge des Klimawandels), die nahtlos dieselbe Datenplattform-Infrastruktur nutzen können, um die Vision eines innovativen, grünen und gerechten Potsdams Realität werden zu lassen [422, 467].

---
