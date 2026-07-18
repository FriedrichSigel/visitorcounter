# Dokumentation — Übersicht

Stand: 18.07.2026

Alle Dokumente zum Besucherzählsensor, thematisch sortiert. Zusammengeführt aus
den früheren Ablageorten (`basic_pipelines/Commando/`, `basic_pipelines/core/`,
`basic_pipelines/lora_hardware_test/`), damit nichts mehr verstreut liegt.

## Wo fange ich an?

| Ich will … | Datei |
|---|---|
| das Projekt verstehen (Einstieg) | [`projekt/HANDOFF.md`](projekt/HANDOFF.md) |
| wissen, was als Nächstes zu tun ist | [`projekt/ToDo.md`](projekt/ToDo.md) |
| an der Abschlussarbeit schreiben | [`abschlussarbeit/Gliederung_DSRM_v2.md`](abschlussarbeit/Gliederung_DSRM_v2.md) |
| ein Gerät neu aufsetzen | [`einrichtung/GERAETE_EINRICHTUNG.md`](einrichtung/GERAETE_EINRICHTUNG.md) |
| das LoRa-Nachrichtenformat nachschlagen | [`lora/LoRa_Nachrichtenformat_Spezifikation.md`](lora/LoRa_Nachrichtenformat_Spezifikation.md) |

## `projekt/` — laufender Stand

Die zwei zentralen, ständig gepflegten Dateien.

- **`HANDOFF.md`** — Einstieg ins Projekt: worum geht's, wo liegt was, was
  funktioniert, was ist als Nächstes dran. Enthält auch den Bezug zur
  Bachelorarbeit (Kapitelzuordnung).
- **`ToDo.md`** — Implementierungsstand, offene Punkte, Priorisierung.

Beide bei inhaltlichen Änderungen mit aktualisieren (Datum oben mitziehen).

## `abschlussarbeit/` — Dokumente zur Arbeit

- **`Gliederung_DSRM_v2.md`** — aktuelle Gliederung nach DSRM (7 Kapitel).
  `Gliederung_DSRM_v1.md` ist die Vorfassung, zur Nachvollziehbarkeit behalten.
- **`Gliederung_DSRM_v2-print.PDF`** — Druckfassung derselben Gliederung.
- **`Statusbericht_Gliederung_Checkliste.md`** (+ `.docx`) — Kapitel-für-Kapitel
  Status, offene Fragen an Betreuer und Stadtwerke.
- **`Zeitplan_bis_Abgabe.xlsx`** — Detailzeitplan.
- **`Entwurf_Systemarchitektur_Sensor.md`** — Architekturentwurf, Grundlage für
  Kapitel 5.3.
- **`Datenartefakte_Beispiel_Potsdam_Berlin.md`** — Beispiel-Datenartefakte
  (Mehrere-Flächen-Modus) für die Ergebnisdarstellung.
- **`Echter_Testlauf_20260715_Zuordnung.md`** — Auswertung eines realen Laufs,
  Zuordnung der Artefakte.
- **`abbildungen/`** — SVG-Abbildungen (Messkette, Datenfluss) für die Arbeit.

## `einrichtung/` — Aufbau und Betrieb

- **`GERAETE_EINRICHTUNG.md`** — Raspberry Pi 5 + Hailo-8 von Null aufsetzen.
- **`EINRICHTUNG_LA66.md`** — LoRa-Adapter einrichten und mit TTN verbinden.
- **`EIGENES_REPOSITORY.md`** — `core/` als eigenständiges Git-Repository
  auslagern (Abhängigkeitsprüfung + Vorgehen).

## `lora/` — Funkübertragung

- **`LoRa_Nachrichtenformat_Spezifikation.md`** — **verbindliche Definition des
  18-Byte-Formats.** Bei allen Fragen zur Byte-Belegung gilt dieses Dokument.
  Die Umsetzung liegt in `../lora_message.py`.
- **`AENDERUNGEN-lora-integration.md`** — was bei der Integration in die App
  gebaut wurde, inklusive der Korrektur der Header-Bytes 3/4.
- **`LoRa_Recherche.md`** — Vorarbeit: Vergleich der Übertragungswege und
  Hardware-Kandidaten. Hintergrund für die Entscheidung pro LoRaWAN/LA66.

Der TTN-Decoder liegt bewusst **nicht** hier, sondern bei den Tests:
`../tests/lora_hardware/test2_ttn/ttn_payload_decoder.js` — eine Datei, ein Ort,
damit keine zwei Fassungen auseinanderlaufen.

## `entwicklung/` — Änderungshistorie und gelöste Probleme

Nachvollziehbarkeit des Entwicklungsverlaufs; für Kapitel 6.4 / 7.2 (Reflexion,
Limitationen) verwertbar.

- `AENDERUNGEN-UI.md`, `AENDERUNGEN-autoconfig.md`,
  `AENDERUNGEN-autoconfig Tabs.md`, `AENDERUNGEN-zwischenspeicher.md`
- `DIAGNOSE_UND_FIX.md` — diagnostizierte und behobene Fehler
- `Datenfluss_Verifikation_20260715.md` — Nachweis, dass die Daten korrekt
  durch die Kette laufen
- `Loesungsansaetze_Bildspiegelung.md` — Lösungswege zur Bildspiegelung
  (weiterhin offener Punkt, siehe `projekt/ToDo.md`)
- `ANALYSE_basic_pipelines.md` — Analyse der ursprünglichen Hailo-Beispiele,
  aus denen das Projekt hervorgegangen ist

## Bewusst nicht übernommen

- **Dokumentation des Hailo-Upstream-Projekts** (`doc/`, `community_projects/`,
  Wurzel-`README.md` des Forks) — fremder Code, online verfügbar, nicht Teil
  dieser Arbeit.
- **`basic_pipelines/Commando/ToDo.md`** (Stand 04.07.) — inhaltlich vollständig
  von `projekt/ToDo.md` abgelöst. Eine zweite, veraltete ToDo-Datei stiftet mehr
  Verwirrung als sie nützt.
- **`LoRa1.zip` / `LoRa2.zip`** — alte Code-Stände vom 07.07., durch den
  aktuellen Code überholt. Der darin enthaltene Unit-Test wurde gerettet:
  `../tests/lora_hardware/test_lora_transmitter.py`.
- **Doppelte Altfassungen** von `HANDOFF.md` und `ToDo.md`, die parallel im
  Wurzelverzeichnis und in `docs/` lagen — es gilt jeweils nur noch die Fassung
  in `projekt/`.
