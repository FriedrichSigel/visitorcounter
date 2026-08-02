#!/bin/bash
#
# start_app.sh — Autostart-Einstiegspunkt für die App.
#
# Wird von einem Desktop-Autostart-Eintrag (siehe README/Setup) in einem
# frisch geöffneten Terminal ausgeführt: wechselt in diesen Ordner, aktiviert
# die venv über setup_env.sh und startet die grafische Oberfläche.
#
# Manuell testen:
#   bash start_app.sh

# In den Ordner wechseln, in dem dieses Skript liegt (funktioniert unabhängig
# davon, von wo aus es aufgerufen wird).
cd "$(dirname "$0")" || exit 1

source setup_env.sh || exit 1

python app.py
