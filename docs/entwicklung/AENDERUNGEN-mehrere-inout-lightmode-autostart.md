# IN/OUT je Fläche, Light-Mode, Auto-Konfiguration ausgeblendet, Autostart

**Stand 03.08.2026.** Vier zusammenhängende Änderungen aus derselben Sitzung,
betreffen `app.py`, `roi_config_app.py`, `config.py`, `counting.py`,
`uebergangs_payload.py`, `lora_message.py`, `lora_send_loop.py`,
`konfig_payload.py`, `tests/vergleich_app.py`, `warmup.py`, `start_app.sh`.

## 1. IN/OUT je Fläche statt einem einzigen IN-Feld (`multi_roi`)

**Vorher:** Im Modus „Mehrere Flächen" gab es genau ein Dropdown „IN-Feld" —
nur eine Fläche konnte als IN-Bereich gelten, alle anderen waren automatisch
OUT. `roi_config.json` speicherte das als `"in_field": "Name"` (String).

**Jetzt:** In Tab 2 gibt es je Fläche eine Checkbox („angehakt = IN, sonst
OUT"). Es können mehrere Flächen gleichzeitig IN oder OUT sein.
**Standardwert:** die zuerst angelegte Fläche ist IN, alle weiteren OUT — lässt
sich danach frei umstellen.

**Datenformat:** `"in_field"` in `roi_config.json` ist jetzt eine **Liste**
von Flächennamen (`["Berlin"]` statt `"Berlin"`). Jede Fläche bekommt zusätzlich
ein `"direction": "in"|"out"`. Ältere Konfigurationen mit einem einzelnen
String werden beim Laden automatisch als Ein-Element-Liste interpretiert
(`normalize_in_fields()` in `lora_message.py`, analoge Helfer in
`uebergangs_payload.py` und `roi_config_app.py`) — kein manuelles Nachziehen
alter `roi_config.json`-Dateien nötig.

**Zähllogik (`uebergangs_payload.py`, `lora_message.py`):** ein Übergang zählt
als IN, wenn er aus einer Nicht-IN- in eine IN-Fläche geht, als OUT umgekehrt.
Übergänge zwischen zwei IN- oder zwei Nicht-IN-Flächen zählen nicht (analog zum
bisherigen Verhalten mit einem einzelnen IN-Feld).

**Validierung beim Speichern:** mindestens eine Fläche muss IN, mindestens eine
muss OUT sein — sonst Warnhinweis, kein Speichern.

→ Damit ist der ToDo-Punkt „Fehlendes IN-Feld sichtbarer machen" (aus
`projekt/ToDo.md`, LoRa-Abschnitt) in seiner ursprünglichen Form hinfällig: es
gibt kein einzelnes optionales Feld mehr, das vergessen werden kann — ohne
gültige IN/OUT-Aufteilung lässt sich gar nicht erst speichern.

## 2. Auto-Konfiguration ausgeblendet (nicht gelöscht)

Clustering/Randraster sind für den Produktivbetrieb noch nicht ausgereift
genug, sollen aber nicht verloren gehen. Neuer Schalter `SHOW_AUTO_CONFIG` in
`config.py` (Standard `False`):

- `app.py`: Tab 5 „Auto-Konfiguration" wird nur gebaut/angezeigt, wenn
  `SHOW_AUTO_CONFIG = True`.
- `roi_config_app.py`: die beiden Radiobuttons „Auto: Clustering (DBSCAN)" /
  „Auto: Randraster" erscheinen nur dann in Tab 2.

Der gesamte Code (Clustering, Randraster, Tab-5-UI, `AUTO_MODES`-Handling in
`save()`/`load_config()`) bleibt unverändert bestehen — nur die UI-Sichtbarkeit
ist geschaltet. Zum Reaktivieren: `SHOW_AUTO_CONFIG = True` setzen.

## 3. Light-Mode

Umschalt-Knopf oben rechts in der Sidebar, neben dem App-Titel (`app.py`,
`_toggle_appearance_mode`). Größerer, gut sichtbarer Kreis-Knopf (40×40px) mit
festem Hintergrund statt transparent — schwarz im Light-Mode, weiß im
Dark-Mode (`fg_color=("black", "white")`), Symbol jeweils in der
Gegenfarbe. Symbole bewusst als **einfarbige** Textzeichen (☀ / ☾) statt
Vollfarb-Emoji (🌙) gewählt — Windows rendert Vollfarb-Emoji mit eigenem,
`text_color`-unabhängigem Hintergrund-Glyph, das sah auf dem farbigen Knopf
kaputt aus.

Die Wahl wird in **`ui_settings.json`** (Projektwurzel, `.gitignore`-t —
geräte-/nutzerspezifisch wie `roi_config.json`) gespeichert und beim nächsten
App-Start automatisch geladen (`_load_saved_appearance_mode()` /
`_save_appearance_mode()`), Standard beim allerersten Start: dunkel.

Alle bis dahin fest auf `"gray70"`/`"gray60"` (identischer Wert für beide
Modi) gesetzten Hinweistexte in `app.py`/`roi_config_app.py` wurden auf
Hell-/Dunkel-Farbpaare umgestellt (`("gray30", "gray70")` bzw.
`("gray25", "gray60")`) — vorher waren sie im Light-Mode kaum lesbar (helles
Grau auf hellem Hintergrund).

## 4. Autostart beim Hochfahren

Ziel: Pi bootet → Terminal öffnet sich automatisch → Pipeline läuft, ohne dass
jemand am Gerät etwas anklicken muss.

**Neu: `start_app.sh`** (Projektwurzel, ausführbar) — wird von einem
Desktop-Autostart-Eintrag (`~/.config/autostart/*.desktop`, XDG-Standard unter
Raspberry Pi OS Desktop) in einem frisch geöffneten Terminal ausgeführt:

1. In den Projektordner wechseln, `source setup_env.sh` (venv aktivieren).
2. `python warmup.py --input usb` — nutzt den bereits vorhandenen
   Aufwärmlauf-Mechanismus: startet `core.py --input usb --use-frame`, wartet
   bis das Vorschaufenster steht, beendet den Prozess dann sauber per SIGINT.
   Macht den allerersten echten Zähllauf-Start nach dem Booten schnell (siehe
   `warmup.py`-Kommentar: bis zu zwei Minuten beim ersten Mal, danach schnell).
3. `python app.py --autostart` — neues CLI-Flag in `app.py` (`argparse`).

**Neu in `app.py`:** `MainApp(autostart=...)` + `_maybe_autostart_pipeline()`.
Nach dem Öffnen der Oberfläche wird automatisch `_start_pipeline()`
aufgerufen (Standard-Input ist bereits „usb", siehe `input_mode_var`) —
mit einer kurzen Wartewiederholung, falls doch noch ein interner Aufwärmlauf
läuft (Normalfall: keiner mehr, weil `start_app.sh` ihn schon vorweg über
`warmup.py` erledigt hat).

**Einrichtung auf einem neuen Gerät** (Ergänzung zu
`einrichtung/GERAETE_EINRICHTUNG.md`):
```bash
chmod +x ~/visitorcounter/start_app.sh
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/visitorcounter.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Besucherzähler
Comment=Startet die Personenzähl-App automatisch beim Hochfahren
Exec=lxterminal --working-directory=/home/fritz/visitorcounter -e bash -c "./start_app.sh; exec bash"
X-GNOME-Autostart-enabled=true
EOF
```
`exec bash` am Ende hält das Terminal nach Absturz/Beenden offen, damit Fehler
sichtbar bleiben.

**Stolperstein beim Einrichten:** `start_app.sh` war im Git-Repository ohne
Ausführungsrecht (`100644`) abgelegt (unter Windows erzeugt, wo es kein
Unix-Dateirecht gibt) — `bash: ./start_app.sh: Permission denied` auf dem Pi.
Behoben mit `git update-index --chmod=+x start_app.sh` + Commit, damit das
Recht ab jetzt bei jedem `git pull` erhalten bleibt.
