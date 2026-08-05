#!/bin/bash
#
# start_app.sh — Autostart-Einstiegspunkt für die App.
#
# Wird von einem Desktop-Autostart-Eintrag (siehe README/Setup) in einem
# frisch geöffneten Terminal ausgeführt:
#   1. in diesen Ordner wechseln, venv über setup_env.sh aktivieren
#   2. einmalig aufwärmen: core.py NACHEINANDER mit der USB-Kamera UND dem
#      zuletzt in der App gewählten Input starten (siehe warmup.py:
#      run_warmup_all() - USB immer, plus current_input() aus
#      app_settings.json, falls abweichend), je Lauf warten bis das
#      Vorschaufenster steht, dann wieder sauber beenden - macht den
#      allerersten Zähllauf-Start nach dem Booten schnell, für beide Wege.
#   3. app.py mit --autostart öffnen - die Oberfläche startet dann selbst
#      automatisch die Zähl-Pipeline mit demselben Input, sobald sie steht
#
# Manuell testen:
#   bash start_app.sh

# In den Ordner wechseln, in dem dieses Skript liegt (funktioniert unabhängig
# davon, von wo aus es aufgerufen wird).
cd "$(dirname "$0")" || exit 1

source setup_env.sh || exit 1

python warmup.py

python app.py --autostart
