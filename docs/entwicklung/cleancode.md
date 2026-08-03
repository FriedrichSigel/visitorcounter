# Clean-Code-Refactoring: app.py aufgeteilt

**Stand 03.08.2026.** Anlass: `app.py` war auf 1393 Zeilen angewachsen — eine
einzige Klasse (`MainApp`) baute alle fünf Seiten der App, verwaltete drei
Subprozess-Typen (core.py, LoRa-Sender, MQTT-Sender) und den kompletten
Fensteraufbau. Das widerspricht den in der Vorlesung *„10: Implementierung“*
(Lamprecht, Software Engineering I, Universität Potsdam) genannten
Prinzipien für die Implementierung der Programmlogik — insbesondere:

- **Modularisierung / Information Hiding / schmale Schnittstellen /
  Separation of Concerns** ("Empfehlenswert" laut Foliensatz, Folie
  *Codierungsrichtlinien*)
- **Festlegung einer Modul-/Codearchitektur**, die festlegt, *wie sich die
  Module der Implementierung aufeinander abstützen* (Folie
  *Implementierung der Programmlogik*)
- **Einfachheit, Klarheit, Lesbarkeit, Änderbarkeit** als oberste Gebote
  guten Programmierstils (Folie *Codierungsrichtlinien*)
- **"Lassen": raffinierter, undurchsichtiger Code** — eine 1400-Zeilen-Datei
  mit einer einzigen Klasse ist in diesem Sinn "undurchsichtig", auch ohne
  einen einzelnen kryptischen Ausdruck: die Übersicht geht verloren, nicht
  die Lesbarkeit einzelner Zeilen.

Dieses Dokument beschreibt die angewendete Lösung und begründet die
Entscheidungen.

## Diagnose

`app.py` hatte vor dem Refactoring:

```
1393 Zeilen, EINE Klasse (MainApp), 39 Methoden
```

Die Methoden gehörten klar erkennbar zu **fünf unabhängigen Zuständigkeiten**,
die aber alle im selben Namensraum lagen:

| Zuständigkeit | Methoden (Auszug) | Zeilen (ca.) |
|---|---|---|
| Fenster/Sidebar/Navigation/Autostart | `__init__`, `_show_page`, `_redraw_tree`, `_maybe_run_warmup` | 250 |
| Seite 1: Input | `_build_input_tab`, `_on_input_mode_change`, `_choose_file` | 45 |
| Seite 2: Konfiguration | `_build_config_tab`, `_load_config_frame`, `_load_existing_config` | 70 |
| Seite 3: Start (Mitschnitt) | `_build_start_tab`-Anteil, `_on_recording_toggle`, `_validate_recording_settings`, … | 180 |
| Seite 3: Start (LoRa) | `_on_lora_toggle`, `_refresh_lora_hint`, `_start_lora_sender`, … | 190 |
| Seite 3: Start (MQTT) | `_on_mqtt_toggle`, `_validate_mqtt_settings`, `_start_mqtt_sender`, … | 155 |
| Seite 3: Pipeline-Prozess | `_start_pipeline`, `_stop_pipeline`, `_escalate_stop`, `_on_process_ended` | 190 |
| Seite 4: Live-Auswertung | `_build_output_tab`, `_poll_output`, `_refresh_counts` | 60 |
| Seite 5: Auto-Konfiguration | `_build_autoconfig_tab` | 50 |

Neun Zuständigkeiten in einer Datei bedeuten: um zu verstehen oder zu ändern,
wie z. B. der MQTT-Versand funktioniert, musste man durch eine Datei
scrollen, die genauso gut beschreibt, wie das Sidebar-Layout berechnet wird —
Themen, die inhaltlich nichts miteinander zu tun haben.

## Lösung: ein Modul je Zuständigkeit, als Mixin eingemischt

Neues Paket `tabs/`, ein Modul je Zuständigkeit:

```
tabs/
├── __init__.py            Begründung des Mixin-Ansatzes (Docstring)
├── constants.py           gemeinsame Konstanten (Pfade, Layout-Maße)
├── input_tab.py           InputTabMixin       — Seite 1
├── config_tab.py          ConfigTabMixin      — Seite 2
├── recording_controls.py  RecordingControlsMixin — Mitschnitt-Abschnitt (Seite 3)
├── lora_controls.py       LoraControlsMixin      — LoRa-Abschnitt (Seite 3)
├── mqtt_controls.py       MqttControlsMixin      — MQTT-Abschnitt (Seite 3)
├── pipeline_control.py    PipelineControlMixin   — Start/Stopp core.py (Seite 3 + 5)
├── start_tab.py           StartTabMixin       — Seite 3, fügt die drei Abschnitte oben zusammen
├── output_tab.py          OutputTabMixin      — Seite 4
└── autoconfig_tab.py      AutoConfigTabMixin  — Seite 5
```

`app.py` bleibt die **Klammer**: Fensteraufbau, Sidebar, Seitenwechsel,
Autostart/Aufwärmlauf, Design-Umschaltung. `MainApp` erbt von allen
Tab-Mixins:

```python
class MainApp(
    InputTabMixin, ConfigTabMixin,
    RecordingControlsMixin, LoraControlsMixin, MqttControlsMixin,
    PipelineControlMixin, StartTabMixin,
    OutputTabMixin, AutoConfigTabMixin,
):
    ...
```

### Warum Mixins statt eigener Objekte je Seite?

Die naheliegende Alternative wäre, jede Seite als eigenständiges Objekt zu
bauen (z. B. `InputTab(parent, on_change=...)`), das `MainApp` nur noch hält.
Dagegen spricht hier konkret: alle Seiten teilen sich denselben
Tk-Zustand (Prozess-Handles wie `self.process`, die Ausgabe-Queue) und rufen
sich gegenseitig auf — Seite 5 startet z. B. dieselbe Pipeline-Logik wie
Seite 3 (`_start_pipeline(collection=True)`), Seite 3 zeigt Fehler an, die
aus dem LoRa-/MQTT-Abschnitt kommen. Eigenständige Objekte bräuchten dafür
eine breite Rückschnittstelle zu `MainApp` (Callbacks für praktisch jede
Statusänderung) — das verlagert die Kopplung nur, statt sie zu verringern.

Ein Mixin pro Datei erreicht dieselbe **Trennung der Zuständigkeiten** ohne
diesen Umweg: jede Datei ist für sich lesbar und verständlich (eine Methode
weiß nur von Attributen, die zu ihrem eigenen Thema gehören, z. B. kennt
`lora_controls.py` `self.lora_*`, aber nicht `self.mqtt_*`), während der
gemeinsame Tk-Zustand ganz normal über `self` erreichbar bleibt.

### Information Hiding / schmale Schnittstellen

`start_tab.py` baut Seite 3 zusammen, kennt aber die **Details** der drei
Abschnitte nicht — es ruft nur `self._build_recording_section(frame)`,
`self._build_lora_section(frame)`, `self._build_mqtt_section(frame)` auf.
Wie ein Abschnitt intern aufgebaut ist (welche Felder, welche Validierung),
ist reines Implementierungsdetail des jeweiligen Moduls. Das ist genau das
Prinzip *Information Hiding* aus der Vorlesung: ein Modul zeigt nach außen
nur, WAS es tut, nicht WIE.

### Zirkelimport vermieden: `tabs/constants.py`

Die Tab-Module werden von `app.py` eingemischt, dürften also nicht
ihrerseits aus `app.py` importieren (Zirkelimport). Gemeinsam genutzte
Konstanten (`ZAEHLUNG_CSV`, `ROI_CONFIG_PATH`, Layout-Maße,
`LORA_HINT_HEIGHT_*`) liegen deshalb in einer eigenen, abhängigkeitsfreien
Datei `tabs/constants.py`, die beide Seiten importieren können.

## Ergebnis

```
vorher:  app.py              1393 Zeilen, 1 Datei, 1 Klasse
nachher: app.py                368 Zeilen  (Fenster/Sidebar/Navigation/Autostart)
         tabs/__init__.py       16 Zeilen  (Begründung)
         tabs/constants.py      30 Zeilen
         tabs/input_tab.py      66 Zeilen
         tabs/config_tab.py     84 Zeilen
         tabs/output_tab.py     90 Zeilen
         tabs/start_tab.py      91 Zeilen
         tabs/autoconfig_tab.py 66 Zeilen
         tabs/mqtt_controls.py 174 Zeilen
         tabs/recording_controls.py 196 Zeilen
         tabs/lora_controls.py 215 Zeilen
         tabs/pipeline_control.py 219 Zeilen
```

Keine Datei mehr über 220 Zeilen; jede Datei ist einem einzigen, benennbaren
Thema gewidmet (Namensgebung nach Konvention *Substantiv beschreibt die
Zuständigkeit*, siehe Vorlesungsfolie *Beispiel: Benennungsregeln*).

**Verhalten unverändert:** reine Verschiebung von Code, keine Logikänderung.
Geprüft durch:
1. `python -m py_compile` über alle betroffenen Dateien.
2. Statischer Abgleich: jeder `self._methode(...)`-Aufruf in `app.py` und
   `tabs/*.py` löst gegen eine `def _methode(...)` irgendwo im
   Mixin-Verbund auf (kein Tippfehler beim Verschieben).
3. `MainApp` tatsächlich instanziiert (mit den Pi-only-GStreamer-Bindings
   `gi` gestubbt, da dieses Repo nur auf dem Raspberry Pi lauffähig ist) —
   Fenster baut auf, alle Seiten wechselbar, `roi_config_widget` und
   `start_button` etc. vorhanden.

## Nacharbeit / bewusst nicht angefasst

- **`CONFIG_PANEL_WIDTH`** (ehemals in `app.py`) war eine definierte, aber
  nirgends gelesene Konstante (toter Code) — beim Verschieben nach
  `tabs/constants.py` weggelassen statt mitgeschleppt.
- Innerhalb der neuen Dateien wurden **keine** weiteren Verhaltensänderungen
  vorgenommen (z. B. keine zusätzliche Fehlerbehandlung, keine
  Umbenennungen bestehender Methoden) — das Ziel dieser Runde war
  ausschließlich die Zerlegung nach Zuständigkeit, nicht ein umfassendes
  Redesign. Weitere Politur (z. B. `_build_*_section()`-Methoden
  konsistent überall dort einführen, wo noch Inline-Aufbau steckt) kann in
  einer eigenen, kleineren Änderung folgen.
- `roi_config_app.py` (1300+ Zeilen) hat dieselbe Diagnose verdient, war
  aber nicht Teil dieser Anfrage — als möglicher nächster Schritt in
  `projekt/ToDo.md` vermerkenswert, falls gewünscht.
