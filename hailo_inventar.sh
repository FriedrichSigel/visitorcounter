#!/bin/bash
#
# hailo_inventar.sh — zeigt, welche Hailo-/CV-/GStreamer-Bestandteile auf
# diesem Raspberry Pi installiert sind, und hilft beim sauberen Entfernen.
#
# ANWENDUNG:
#   bash hailo_inventar.sh                  # nur anzeigen (Standard, ändert nichts)
#   bash hailo_inventar.sh --abzug          # anzeigen + in Datei schreiben (für Gerätevergleich)
#   bash hailo_inventar.sh --plan-entfernen # zeigt die Deinstallationsbefehle, führt sie NICHT aus
#   bash hailo_inventar.sh --entfernen      # führt die Deinstallation nach Rückfrage aus
#
# Ohne Schalter wird nichts verändert. `--entfernen` fragt vor jedem Schritt
# einzeln nach und lässt sich jederzeit mit "n" überspringen.

set -uo pipefail

VENV_NAME="${VENV_NAME:-venv_visitorcounter}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/${VENV_NAME}"

MODUS="anzeigen"
case "${1:-}" in
    --abzug)          MODUS="abzug" ;;
    --plan-entfernen) MODUS="plan" ;;
    --entfernen)      MODUS="entfernen" ;;
    --hilfe|-h)       sed -n '2,20p' "$0"; exit 0 ;;
    "")               ;;
    *)                echo "Unbekannter Schalter: $1 — siehe --hilfe"; exit 1 ;;
esac

trenner() { printf '\n== %s %s\n' "$1" "$(printf '=%.0s' $(seq 1 $((60 - ${#1}))))"; }

# =====================================================================
# TEIL 1 — Bestandsaufnahme
# =====================================================================
inventar() {

trenner "System"
head -3 /etc/os-release
echo "Kernel:   $(uname -r)  ($(uname -m))"
echo "Modell:   $(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo unbekannt)"
echo "System-Python: $(python3 -V 2>&1)"

trenner "Hailo — apt-Pakete"
# hailo-all ist ein Metapaket; die eigentliche Software steckt in den anderen.
if dpkg -l | grep -qi hailo; then
    dpkg-query -W -f='${Package}\t${Version}\t${Status}\n' \
        'hailo*' 'python3-hailo*' 2>/dev/null | grep -v 'not-installed' || true
else
    echo "(keine Hailo-apt-Pakete installiert)"
fi

trenner "Hailo — Gerät und Firmware"
if command -v hailortcli >/dev/null 2>&1; then
    hailortcli fw-control identify 2>&1 | grep -Ei 'firmware|architecture|serial' \
        || echo "(hailortcli vorhanden, aber Gerät antwortet nicht)"
else
    echo "(hailortcli nicht im PATH)"
fi
echo "PCIe-Treiber geladen: $(lsmod | grep -c hailo) Modul(e)"
lsmod | grep hailo || true
ls -l /dev/hailo* 2>/dev/null || echo "(kein /dev/hailo* vorhanden)"

trenner "GStreamer / PyGObject — apt-Pakete"
dpkg-query -W -f='${Package}\t${Version}\n' \
    'python3-gi' 'python3-gi-cairo' 'gir1.2-gst*' 'python3-gst*' \
    'gstreamer1.0-*' 'libgstreamer1.0-0' 2>/dev/null | sort || true

trenner "GStreamer — Hailo-Plugins"
# Wenn diese Elemente fehlen, kann die Pipeline nicht aufgebaut werden.
for EL in hailonet hailofilter hailotracker hailocropper hailoaggregator hailooverlay; do
    if gst-inspect-1.0 "$EL" >/dev/null 2>&1; then
        echo "  vorhanden   $EL"
    else
        echo "  FEHLT       $EL"
    fi
done

trenner "PyGObject — Struktur-API (bekannte Bruchstelle)"
# hailo_apps ruft Gst.Structure.get_value(); neuere PyGObject-Versionen
# liefern stattdessen einen StructureWrapper ohne diese Methode.
python3 - <<'PY' 2>&1 || echo "(Prüfung fehlgeschlagen)"
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
Gst.init(None)
print("  PyGObject:", gi.__version__)
print("  GStreamer:", ".".join(str(x) for x in Gst.version()[:3]))
s = Gst.Caps.from_string('video/x-raw,format=RGB,width=1280,height=720').get_structure(0)
print("  Structure-Typ:", type(s).__name__)
print("  hat get_value():", hasattr(s, 'get_value'))
print("  unterstuetzte Zugriffe:", [a for a in dir(s) if not a.startswith('_')][:20])
PY

trenner "Projekt-venv"
if [ -d "$VENV_DIR" ]; then
    echo "Pfad:  $VENV_DIR"
    echo "Groesse: $(du -sh "$VENV_DIR" 2>/dev/null | cut -f1)"
    # shellcheck disable=SC1091
    source "${VENV_DIR}/bin/activate"
    echo "Python: $(python -V 2>&1)"
    echo "system-site-packages: $(grep -i include-system-site "${VENV_DIR}/pyvenv.cfg" 2>/dev/null || echo '?')"
    echo
    echo "--- pip freeze ---"
    pip freeze 2>/dev/null | sort
    echo
    echo "--- veraltet gegenueber PyPI (braucht Internet) ---"
    pip list --outdated 2>/dev/null || echo "(nicht abrufbar)"
    echo
    echo "--- hailo_apps ---"
    python -c "import hailo_apps, os; print('Version:', getattr(hailo_apps,'__version__','unbekannt')); print('Pfad:   ', os.path.dirname(hailo_apps.__file__))" 2>&1
    deactivate 2>/dev/null || true
else
    echo "(keine venv unter $VENV_DIR)"
fi

trenner "Weitere Hailo-venvs auf dem System"
find "$HOME" -maxdepth 4 -type d -name 'site-packages' 2>/dev/null \
    | while read -r SP; do
        [ -d "$SP/hailo_apps" ] && echo "  hailo_apps in: $SP"
      done
[ -d "$HOME/hailo-rpi5-examples" ] && echo "  Ordner vorhanden: $HOME/hailo-rpi5-examples"
[ -d "/usr/local/hailo" ] && echo "  Ordner vorhanden: /usr/local/hailo ($(du -sh /usr/local/hailo 2>/dev/null | cut -f1))"

trenner "Kamera"
v4l2-ctl --list-devices 2>/dev/null | head -20 || echo "(v4l-utils nicht installiert)"

}

# =====================================================================
# TEIL 2 — Deinstallation
# =====================================================================
#
# Reihenfolge ist wichtig: erst die venv (rein projektlokal, harmlos),
# dann hailo_apps, zuletzt die apt-Pakete inkl. Kernel-Treiber.

zeige_plan() {
cat <<'PLAN'

Deinstallation — die einzelnen Stufen, von harmlos nach eingreifend:

  STUFE 1 — nur die Projekt-venv loeschen (betrifft nichts ausserhalb
            des Projektordners; danach `bash create_venv.sh` neu ausfuehren)

      rm -rf ./venv_visitorcounter

  STUFE 2 — nur hailo_apps aus der venv entfernen (System-Hailo bleibt)

      source venv_visitorcounter/bin/activate
      pip uninstall -y hailo-apps
      # Falls per .pth-Fallback eingebunden:
      rm -f venv_visitorcounter/lib/python*/site-packages/hailo_apps.pth

  STUFE 3 — alle pip-Pakete des Projekts entfernen (venv bleibt bestehen)

      source venv_visitorcounter/bin/activate
      pip uninstall -y -r requirements.txt

  STUFE 4 — Hailo-Systempakete entfernen (ENTFERNT TREIBER UND FIRMWARE-TOOLS;
            danach ist das Hailo-Modul bis zur Neuinstallation unbenutzbar)

      sudo apt remove --purge -y 'hailo*' 'python3-hailo*'
      sudo apt autoremove --purge -y
      # Reste, die apt nicht mitnimmt:
      sudo rm -rf /usr/local/hailo
      sudo reboot          # Kernel-Treiber wird erst nach Neustart entladen

  NEUINSTALLATION danach:

      sudo apt update && sudo apt install -y hailo-all
      hailortcli fw-control identify
      cd ~/visitorcounter && bash create_venv.sh && source setup_env.sh

PLAN
}

frage() {
    # frage "<Text>"  ->  0 wenn ja
    local antwort
    read -r -p "  >> $1 [j/N] " antwort
    case "$antwort" in [jJyY]) return 0 ;; *) echo "     uebersprungen."; return 1 ;; esac
}

fuehre_aus() {
    echo
    echo "ACHTUNG: Es werden jetzt Pakete entfernt. Jede Stufe wird einzeln"
    echo "abgefragt. Abbruch jederzeit mit Strg+C."
    zeige_plan

    if frage "STUFE 1: venv ${VENV_DIR} loeschen?"; then
        rm -rf "$VENV_DIR" && echo "     venv geloescht."
    fi

    if [ -d "$VENV_DIR" ]; then
        if frage "STUFE 2: hailo-apps aus der venv deinstallieren?"; then
            # shellcheck disable=SC1091
            source "${VENV_DIR}/bin/activate"
            pip uninstall -y hailo-apps
            rm -f "${VENV_DIR}"/lib/python*/site-packages/hailo_apps.pth
            deactivate 2>/dev/null || true
        fi
        if frage "STUFE 3: alle Pakete aus requirements.txt deinstallieren?"; then
            # shellcheck disable=SC1091
            source "${VENV_DIR}/bin/activate"
            pip uninstall -y -r "${SCRIPT_DIR}/requirements.txt"
            deactivate 2>/dev/null || true
        fi
    fi

    echo
    echo "  STUFE 4 entfernt Treiber und Firmware-Tools. Das Hailo-Modul ist"
    echo "  danach bis zur Neuinstallation nicht mehr nutzbar."
    if frage "STUFE 4: Hailo-Systempakete per apt entfernen?"; then
        sudo apt remove --purge -y 'hailo*' 'python3-hailo*'
        sudo apt autoremove --purge -y
        if frage "Auch /usr/local/hailo loeschen (Modelle, .so-Dateien)?"; then
            sudo rm -rf /usr/local/hailo
        fi
        echo
        echo "  Fertig. Ein Neustart ist noetig, damit der Kernel-Treiber"
        echo "  entladen wird:  sudo reboot"
    fi
}

# =====================================================================
case "$MODUS" in
    anzeigen)
        inventar
        echo
        echo "Deinstallationsbefehle anzeigen:  bash $0 --plan-entfernen"
        ;;
    abzug)
        DATEI="$HOME/hailo_abzug_$(hostname)_$(date +%Y%m%d_%H%M).txt"
        inventar | tee "$DATEI"
        echo
        echo "Abzug gespeichert: $DATEI"
        echo "Zum Vergleich zweier Geraete beide Dateien holen und diffen:"
        echo "  diff -u abzug_alt.txt abzug_neu.txt"
        ;;
    plan)
        zeige_plan
        echo "Nichts ausgefuehrt. Zum tatsaechlichen Entfernen: bash $0 --entfernen"
        ;;
    entfernen)
        fuehre_aus
        ;;
esac
