# `core/` in ein eigenes Git-Repository auslagern

Stand: 18.07.2026

## Kurze Antwort: Ja, das geht — `core/` ist bereits eigenständig.

Geprüft am hochgeladenen Stand (`personenzaehlung.zip`):

- **Kein einziger Import aus `basic_pipelines`.** `grep` über alle `.py` in
  `core/` findet keine Referenz auf `basic_pipelines`, kein `sys.path`-Basteln,
  keine relativen `../`-Pfade.
- **Das Hailo-Framework kommt aus einem installierten Paket, nicht aus dem
  Repo.** `core.py` importiert aus `hailo_apps.hailo_app_python...`; einen
  Ordner `hailo_apps` gibt es im Repository nicht — er wird durch `install.sh`
  bzw. die venv bereitgestellt. Das Auslagern von `core/` ändert daran nichts.
- **`core/setup_env.sh` ist schon dafür geschrieben.** Es setzt den PYTHONPATH
  auf den `core`-Ordner und hält im Kommentar ausdrücklich fest, dass das
  Elternverzeichnis nicht mehr gebraucht wird. Die venv wird in `core/`, im
  Elternverzeichnis und in `$HOME` gesucht — funktioniert also auch, wenn die
  vom Hailo-Setup angelegte venv woanders liegt.
- **Keine Verweise auf Dateien außerhalb.** Kein Zugriff auf `resources/`,
  keine `.hef`-Modelldateien, keine fest verdrahteten Videopfade.

Damit hängt `core/` nur noch an Dingen, die ohnehin systemweit installiert sind
(Hailo-Stack, GStreamer/`gi`) und an den eigenen `requirements.txt`.

## Erledigt: alles Wichtige ist bereits eingesammelt (18.07.)

Der Ordner ist inzwischen vollständig — es muss nichts mehr aus dem alten
Repository nachgeholt werden:

- **Alle Markdown-Dokumente** aus `basic_pipelines/Commando/` (Abschlussarbeit),
  `basic_pipelines/core/` (Projektdoku) und `basic_pipelines/lora_hardware_test/`
  liegen jetzt in `docs/`, thematisch sortiert. Wegweiser: `docs/README.md`.
- **Alle Test- und Diagnoseskripte** liegen in `tests/` (`kamera/`,
  `lora_hardware/`), inklusive des im TTN hinterlegten Payload-Decoders.
- Besonders wichtig war `LoRa_Nachrichtenformat_Spezifikation.md` — sie lag nur
  im alten Ordner und definiert die Byte-Belegung verbindlich. Jetzt unter
  `docs/lora/`.

Im alten Repository bleiben damit nur: der Hailo-Upstream-Code
(`basic_pipelines/`, `community_projects/`, `doc/`), die Testvideos und
Laufzeitdaten. Nichts davon wird gebraucht.

## Wie du es machst

### Variante A — sauberer Neuanfang (empfohlen)

Einfach, nachvollziehbar, aber ohne die alte Commit-Historie.

```bash
# 1. core-Ordner an einen neuen Ort kopieren
cp -r ~/personenzaehlung/core ~/besucherzaehlsensor
cd ~/besucherzaehlsensor

# 2. Laufzeitdaten entfernen, die nicht ins Repo gehören
rm -f zaehlung.csv ergebniss.csv auto_config_points.csv bewegungsbild_*.png camera_raw.png
rm -rf vorherige_laeufe __pycache__
# (die .gitignore fängt diese Dateien ohnehin ab — das Löschen hält den
#  neuen Ordner nur von Anfang an sauber)

# 3. Neues Repository anlegen
git init
# .gitattributes liegt bereits bei (Zeilenenden auf LF) — siehe unten
git add .
git commit -m "Besucherzählsensor: eigenständiges Repository aus core/"

# 4. Auf GitHub ein leeres Repo anlegen, dann:
git remote add origin https://github.com/<dein-name>/<neues-repo>.git
git branch -M main
git push -u origin main
```

Das alte Repository `personenzaehlung` bleibt bestehen — als Archiv der
Vorgeschichte. In der Arbeit lässt sich das gut begründen: erst Arbeit im Fork
der Hailo-Beispiele, dann Herauslösen der eigenen Anwendung, sobald sie keine
Abhängigkeit mehr zum Beispielcode hatte.

### Variante B — mit Historie

Wenn die Commit-Historie von `core/` erhalten bleiben soll (kann für die Arbeit
als Nachweis des Arbeitsverlaufs nützlich sein):

```bash
# git-filter-repo installieren (einmalig)
pip install git-filter-repo

git clone https://github.com/FriedrichSigel/personenzaehlung.git core-only
cd core-only
git filter-repo --subdirectory-filter core

git remote add origin https://github.com/<dein-name>/<neues-repo>.git
git push -u origin main
```

`--subdirectory-filter core` zieht `core/` an die Wurzel und wirft alles andere
weg. **Achtung:** Die Historie zeigt dann nur Commits, die `core/` betrafen —
die frühe Arbeit direkt in `basic_pipelines/` fällt weg. Vorher an einer Kopie
testen, nie am Original.

## Vorher: zwei Stolpersteine, die am 18.07. real aufgetreten sind

### 1. Zeilenenden (CRLF) — sonst ein unbrauchbar verrauschter erster Commit

Die Dateien auf dem Gerät haben Windows-Zeilenenden. Git meldet deshalb
Dutzende Dateien als geändert, die nie bearbeitet wurden — `LICENSE`,
`depth.py`, `VideoApp.py` und weitere. Bei `LICENSE` sind das 21 „geänderte"
Zeilen, die inhaltlich identisch sind.

Im neuen Repository **vor dem ersten `git add`** eine `.gitattributes` anlegen:

```
* text=auto eol=lf
```

Damit normalisiert Git die Zeilenenden im Repository auf LF, unabhängig davon,
von welchem Betriebssystem aus committet wird. Ohne das ist später kaum
erkennbar, welche Änderung inhaltlich war und welche nur Formatierung.

### 2. Alte Ordnerkopien — die häufigste Fehlerquelle beim Umzug

Beim Aufräumen sind mehrere Kopien desselben Projekts an verschiedenen Stellen
aufgetaucht, unter anderem ein Stand vom **16.07.** (vor der LoRa-Arbeit:
`app.py` mit 26 KB statt 36 KB, ohne `lora_message.py` und `lora_send_loop.py`).
Solche Doppelgänger sehen im Dateimanager identisch aus.

Vor dem Umzug einmal prüfen, welcher Ordner wirklich der aktuelle ist:

```bash
ls -la app.py lora_message.py lora_send_loop.py
```

Der aktuelle Stand hat **alle drei** Dateien, `app.py` ist ~36 KB groß. Fehlen
`lora_message.py`/`lora_send_loop.py`, ist es eine Kopie von vor dem 17.07.

Alte Kopien erst löschen, wenn das neue Repository steht **und** einen
Testlauf bestanden hat.

## Nach dem Umzug prüfen

```bash
cd ~/besucherzaehlsensor
source setup_env.sh          # muss gesourced werden, nicht ausgeführt
python app.py                # App muss normal starten
```

**Die Gerätekonfiguration mitnehmen** — sie ist per `.gitignore` ausgeschlossen
und kommt daher nicht automatisch mit:

```bash
cp <alter-ordner>/roi_config.json .
```

Und danach kontrollieren, dass das IN-Feld gesetzt ist (im `multi_roi`-Modus
sendet LoRa sonst stillschweigend Nullwerte):

```bash
python3 -c "import json; c=json.load(open('roi_config.json')); \
print('mode:', c.get('mode'), '| in_field:', repr(c.get('in_field')))"
```

Steht dort `in_field: None` oder `''`, in Tab 2 ein IN-Feld auswählen und
speichern.

Wenn `setup_env.sh` die venv nicht findet: sie liegt beim Hailo-Setup meist in
`$HOME/venv_hailo_rpi_examples` — das Skript sucht dort bereits. Sonst mit
`VENV_NAME=... source setup_env.sh` überschreiben.

Ein guter Test ist ein Lauf mit einer Videodatei. Die Testvideos
(`cars.mp4`, `test-video*.mp4`) liegen in `basic_pipelines/` und sind je
5–9 MB — **nicht** ins neue Repo committen, sondern außerhalb ablegen und über
`--input` referenzieren. Die `.gitignore` in `core/` deckt das ab, bitte
trotzdem einmal mit `git status` gegenprüfen, bevor du pushst.

## Zur `.gitignore`

`core/.gitignore` ist bereits sehr vollständig: Python-Artefakte, venvs, alle
Laufzeit-Ausgaben (`zaehlung.csv`, `ergebniss.csv`, `bewegungsbild_*.png`,
`vorherige_laeufe/` …) und sogar `roi_config.json` (geräte-/standortspezifisch)
sind ausgeschlossen. Nach dem Umzug funktioniert sie unverändert weiter.

Zwei Ergänzungen wären sinnvoll:

```
# Testvideos nicht ins Repo (liegen bei je 5-9 MB)
*.mp4
```

Und weil `roi_config.json` ignoriert wird: eine Beispielkonfiguration als
`roi_config.example.json` einchecken (der Kommentar in der `.gitignore` schlägt
das selbst vor). Sonst steht jemand, der das Repo frisch klont, ohne
funktionierende Konfiguration da — auch der Prüfer.
