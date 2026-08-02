#!/bin/bash
#
# start_app.sh — Autostart-Einstiegspunkt für die App.
#
# Wird von einem Desktop-Autostart-Eintrag (siehe README/Setup) in einem
# frisch geöffneten Terminal ausgeführt:
#   1. in diesen Ordner wechseln, venv über setup_env.sh aktivieren
#   2. einmalig aufwärmen: core.py mit USB-Eingang starten, warten bis das
#      Vorschaufenster steht, dann wieder sauber beenden (siehe warmup.py -
#      macht den allerersten Zähllauf-Start nach dem Booten schnell)
#   3. app.py mit --autostart öffnen - die Oberfläche startet dann selbst
#      automatisch die Zähl-Pipeline (Input: USB), sobald sie steht
#
# Manuell testen:
#   bash start_app.sh

# In den Ordner wechseln, in dem dieses Skript liegt (funktioniert unabhängig
# davon, von wo aus es aufgerufen wird).
cd "$(dirname "$0")" || exit 1

source setup_env.sh || exit 1

python warmup.py --input usb

python app.py --autostart
