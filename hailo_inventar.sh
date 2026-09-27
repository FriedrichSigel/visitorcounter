#!/bin/bash
#
# hailo_inventar.sh — zeigt, welche Hailo-/CV-/GStreamer-Bestandteile auf
# diesem Raspberry Pi installiert sind, und hilft beim sauberen Entfernen.
#
# ANWENDUNG:
#   bash hailo_inventar.sh                  # nur anzeigen (Standard, ändert nichts)
#   bash hailo_inventar.sh --status         # laufen gerade Prozesse? (Hailo, core.py, App)
#   bash hailo_inventar.sh --abzug          # anzeigen + in Datei schreiben (für Gerätevergleich)
#   bash hailo_inventar.sh --plan-entfernen # zeigt die Deinstallationsbefehle, führt sie NICHT aus
#   bash hailo_inventar.sh --entfernen      # stufenweise Deinstallation, nach Rückfrage
#   bash hailo_inventar.sh --entfernen-hailo     # nur Hailo-Reste (inkl. /usr/local/hailo)
#   bash hailo_inventar.sh --entfernen-gstreamer # nur GStreamer-apt-Pakete (mit Trockenlauf)
#
# Ohne Schalter wird nichts verändert. Alle Entfernen-Modi fragen vor jedem
# Schritt einzeln nach und lassen sich jederzeit mit "n" überspringen.

set -uo pipefail

VENV_NAME="${VENV_NAME:-venv_visitorcounter}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/${VENV_NAME}"

MODUS="anzeigen"
case "${1:-}" in
    --status)         MODUS="status" ;;
    --abzug)          MODUS="abzug" ;;
    --plan-entfernen) MODUS="plan" ;;
    --entfernen)      MODUS="entfernen" ;;
    --entfernen-hailo)     MODUS="hailo" ;;
    --entfernen-gstreamer) MODUS="gstreamer" ;;
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
# Achtung: `dpkg -l | grep -q` ist hier unbrauchbar — grep -q steigt frueh aus,
# dpkg bekommt SIGPIPE und mit `set -o pipefail` schlaegt die ganze Pipeline
# fehl, obwohl Treffer vorliegen. Deshalb erst in eine Variable einlesen.
HAILO_PKGS="$(dpkg-query -W -f='${Package}\t${Version}\t${Status}\n' \
    'hailo*' 'python3-hailo*' 2>/dev/null | grep -v 'not-installed')"
if [ -n "$HAILO_PKGS" ]; then
    echo "$HAILO_PKGS"
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

trenner "Hailo — Herkunft der Dateien (apt oder Installer-Skript?)"
# Wichtig vor dem Entfernen: per apt installierte Dateien gehoeren einem Paket
# und muessen per apt weg. Vom Hailo-Installer abgelegte Dateien gehoeren
# keinem Paket und muessen von Hand geloescht werden.
for PFAD in /usr/local/hailo /usr/lib/aarch64-linux-gnu/hailo \
            /usr/bin/hailortcli /lib/modules/$(uname -r)/updates/dkms/hailo_pci.ko; do
    if [ -e "$PFAD" ]; then
        BESITZER="$(dpkg -S "$PFAD" 2>/dev/null | cut -d: -f1)"
        if [ -n "$BESITZER" ]; then
            echo "  apt-Paket '$BESITZER'   -> $PFAD"
        else
            echo "  KEIN apt-Paket (Installer) -> $PFAD"
        fi
    fi
done
echo "  GStreamer-Plugin hailonet liegt in:"
gst-inspect-1.0 hailonet 2>/dev/null | grep -i 'Filename' || echo "    (nicht ermittelbar)"
echo "  hailo-Python-Modul im System-Python:"
python3 -c "import hailo, os; print('   ', os.path.dirname(hailo.__file__))" 2>&1 | tail -1
echo "  DKMS-Module:"
dkms status 2>/dev/null | grep -i hailo || echo "    (keine)"

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

  STUFE 4 — Hailo entfernen (ENTFERNT TREIBER UND FIRMWARE-TOOLS;
            danach ist das Hailo-Modul bis zur Neuinstallation unbenutzbar)

      bash hailo_inventar.sh --entfernen-hailo

      WICHTIG: paketeigene Pfade NIE per rm loeschen. Wer z. B.
      /usr/bin/hailortcli oder /usr/lib/aarch64-linux-gnu/hailo direkt
      loescht, hinterlaesst dpkg im Glauben, alles sei installiert -
      'apt install' meldet dann 'already the newest version' und
      installiert nichts nach. Reparatur in dem Fall:

          dpkg -V 'hailo*'      # zeigt fehlende Dateien
          sudo apt install --reinstall -y hailort hailo-tappas-core python3-hailort

      Nur /usr/local/hailo (die von hailo_apps geladenen Modelle) gehoert
      keinem Paket und darf per rm weg.

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
    if frage "STUFE 4: Hailo vom System entfernen?"; then
        # Nicht selbst loeschen — entferne_hailo() prueft fuer jeden Pfad, ob
        # ein apt-Paket ihn besitzt, und nimmt nur paketfremde Reste per rm.
        entferne_hailo
    fi
}


# ---------------------------------------------------------------------
# Gezieltes Entfernen: nur Hailo-Reste
# ---------------------------------------------------------------------
entferne_hailo() {
    echo
    echo "=== Hailo entfernen ==="
    echo
    echo "GRUNDREGEL: Pfade, die einem apt-Paket gehoeren, werden NIEMALS per"
    echo "rm geloescht - sonst denkt dpkg weiter, die Dateien waeren da, und"
    echo "'apt install' installiert nichts nach ('already the newest version')."
    echo "Solche Pfade verschwinden nur ueber 'apt remove'. Per rm entfernt"
    echo "werden hier ausschliesslich Reste, die keinem Paket gehoeren."
    echo

    # --- Stufe A: apt-Pakete (der richtige Weg fuer alles paketeigene) ----
    HAILO_INSTALLIERT="$(dpkg-query -W -f='${Package} ' 'hailo*' 'python3-hailo*' 2>/dev/null)"
    if [ -n "${HAILO_INSTALLIERT// /}" ]; then
        echo "  Installierte Hailo-apt-Pakete:"
        dpkg-query -W -f='    ${Package}\t${Version}\t${Status}\n' \
            'hailo*' 'python3-hailo*' 2>/dev/null | grep -v 'not-installed'
        echo
        if frage "Diese apt-Pakete entfernen (inkl. Treiber)?"; then
            sudo apt remove --purge -y 'hailo*' 'python3-hailo*'
            sudo apt autoremove --purge -y
        fi
    else
        echo "  (keine Hailo-apt-Pakete installiert)"
    fi

    # --- Stufe B: paketfremde Reste --------------------------------------
    # loesche_wenn_paketfrei <pfad> <beschreibung>
    loesche_wenn_paketfrei() {
        local PFAD="$1" BESCHREIBUNG="$2" BESITZER
        [ -e "$PFAD" ] || return 0
        BESITZER="$(dpkg -S "$PFAD" 2>/dev/null | cut -d: -f1)"
        echo
        if [ -n "$BESITZER" ]; then
            echo "  UEBERSPRUNGEN: $PFAD"
            echo "    gehoert dem apt-Paket '$BESITZER' - nur per 'apt remove $BESITZER'"
            echo "    entfernen, nicht per rm."
            return 0
        fi
        echo "  $PFAD ($BESCHREIBUNG)"
        echo "    gehoert keinem apt-Paket - kann per rm weg."
        frage "loeschen?" && sudo rm -rf "$PFAD"
    }

    loesche_wenn_paketfrei /usr/local/hailo \
        "Modelle/HEF-Dateien, von hailo_apps heruntergeladen, $(du -sh /usr/local/hailo 2>/dev/null | cut -f1)"
    loesche_wenn_paketfrei /usr/lib/aarch64-linux-gnu/hailo "TAPPAS-Bibliotheken"
    loesche_wenn_paketfrei /usr/bin/hailortcli "HailoRT-Kommandozeile"
    loesche_wenn_paketfrei /usr/local/bin/hailortcli "HailoRT-Kommandozeile (lokal)"
    loesche_wenn_paketfrei /usr/bin/hailo "hailo-Kommandozeile"

    # --- Stufe C: DKMS ----------------------------------------------------
    if [ -n "$(dkms status 2>/dev/null | grep -i hailo || true)" ]; then
        echo
        echo "  DKMS-Treiber hailo_pci gefunden."
        if frage "DKMS-Treiber deinstallieren?"; then
            dkms status 2>/dev/null | grep -i hailo | while IFS=, read -r MOD VER _; do
                sudo dkms remove "${MOD}/${VER#*/}" --all 2>/dev/null || true
            done
        fi
    fi

    # --- Abschluss: Konsistenz pruefen ------------------------------------
    echo
    echo "  --- Konsistenzpruefung (fehlende Dateien installierter Pakete) ---"
    FEHLT="$(dpkg -V 'hailo*' 'python3-hailo*' 2>/dev/null)"
    if [ -n "$FEHLT" ]; then
        echo "$FEHLT" | head -20
        echo
        echo "  Es fehlen Dateien, die laut dpkg installiert sein muessten."
        echo "  Reparieren mit:"
        echo "    sudo apt install --reinstall -y hailort hailo-tappas-core python3-hailort"
    else
        echo "  keine Abweichungen."
    fi

    echo
    echo "  Der Kernel-Treiber wird erst nach 'sudo reboot' entladen."
    echo "  Neu installieren:  sudo apt update && sudo apt install -y hailo-all"
}

# ---------------------------------------------------------------------
# Gezieltes Entfernen: GStreamer
# ---------------------------------------------------------------------
entferne_gstreamer() {
    echo
    echo "=========================== WARNUNG ==========================="
    echo "GStreamer ist auf Raspberry Pi OS eine Abhaengigkeit des Desktops"
    echo "und vieler Standardprogramme. Ein pauschales Entfernen reisst per"
    echo "Autoremove haeufig auch Desktop-Bestandteile mit heraus - im"
    echo "schlimmsten Fall bootet das Geraet nur noch in die Konsole."
    echo
    echo "Deshalb wird hier NICHTS blind entfernt. Zuerst zeigt apt an, was"
    echo "genau wegfallen wuerde (Trockenlauf), und du entscheidest danach."
    echo "==============================================================="
    echo

    PAKETE="gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav \
gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-gl gstreamer1.0-alsa \
gstreamer1.0-pulseaudio python3-gst-1.0 gir1.2-gstreamer-1.0 \
gir1.2-gst-plugins-base-1.0 gir1.2-gst-plugins-bad-1.0 libgstreamer1.0-0"

    echo "--- TROCKENLAUF: was apt entfernen wuerde ---"
    # shellcheck disable=SC2086
    sudo apt remove --purge --simulate $PAKETE 2>&1 | grep -E '^(Remv|REMOVING|Die folgenden|The following)' | head -60
    echo
    echo "--- Anzahl betroffener Pakete ---"
    # shellcheck disable=SC2086
    sudo apt remove --purge --simulate $PAKETE 2>&1 | grep -c '^Remv' || true
    echo
    echo "Pruefe die Liste. Stehen dort Pakete wie 'raspberrypi-ui-mods',"
    echo "'lxde*', 'labwc', 'chromium*' oder 'pipewire', dann brich ab -"
    echo "sonst verlierst du den Desktop."
    echo

    if frage "Liste geprueft - GStreamer jetzt wirklich entfernen?"; then
        # shellcheck disable=SC2086
        sudo apt remove --purge -y $PAKETE
        echo
        if frage "Zusaetzlich 'apt autoremove --purge' ausfuehren?"; then
            sudo apt autoremove --purge -y
        fi
        echo
        echo "  Neu installieren mit:"
        echo "    sudo apt update"
        echo "    sudo apt install -y python3-gi python3-gst-1.0 \\"
        echo "                        gstreamer1.0-plugins-good gstreamer1.0-tools"
    fi
}


# ---------------------------------------------------------------------
# Laufende Prozesse und Geraetebelegung
# ---------------------------------------------------------------------
status() {

trenner "Laufende Projekt-Prozesse"
GEFUNDEN=0
for MUSTER in "core/core.py" "core/app.py" "utils/warmup.py" \
              "lora_send_loop" "mqtt_send_loop"; do
    TREFFER="$(pgrep -af "$MUSTER" 2>/dev/null | grep -v 'hailo_inventar' || true)"
    if [ -n "$TREFFER" ]; then
        GEFUNDEN=1
        echo "  $MUSTER:"
        echo "$TREFFER" | sed 's/^/    /'
    fi
done
[ "$GEFUNDEN" -eq 0 ] && echo "  (keiner dieser Prozesse laeuft)"

trenner "Wer benutzt gerade das Hailo-Geraet?"
# /dev/hailo0 kann immer nur von einem Prozess gleichzeitig belegt werden.
# Ein hier gelisteter Prozess ist der Grund, wenn ein zweiter Start mit
# "Device in use" oder aehnlich scheitert.
if [ -e /dev/hailo0 ]; then
    if command -v fuser >/dev/null 2>&1; then
        BELEGT="$(sudo fuser -v /dev/hailo0 2>&1 | grep -v '^$' || true)"
        if [ -n "$BELEGT" ]; then
            echo "$BELEGT" | sed 's/^/  /'
        else
            echo "  /dev/hailo0 ist frei."
        fi
    elif command -v lsof >/dev/null 2>&1; then
        sudo lsof /dev/hailo0 2>/dev/null | sed 's/^/  /' || echo "  /dev/hailo0 ist frei."
    else
        echo "  (weder fuser noch lsof installiert:  sudo apt install -y psmisc)"
    fi
else
    echo "  /dev/hailo0 existiert nicht — Treiber nicht geladen?"
fi

trenner "Auslastung des Hailo-Beschleunigers"
if command -v hailortcli >/dev/null 2>&1; then
    timeout 5 hailortcli monitor 2>&1 | head -25 \
        || echo "  (kein laufender Prozess nutzt das Geraet)"
else
    echo "  (hailortcli nicht im PATH)"
fi

trenner "Kamera belegt?"
for DEV in /dev/video0 /dev/video1; do
    if [ -e "$DEV" ]; then
        BELEGT="$(sudo fuser -v "$DEV" 2>&1 | grep -v '^$' || true)"
        if [ -n "$BELEGT" ]; then
            echo "  $DEV:"; echo "$BELEGT" | sed 's/^/    /'
        else
            echo "  $DEV ist frei."
        fi
    fi
done

trenner "Autostart eingerichtet?"
AUTOSTART="$HOME/.config/autostart/visitorcounter.desktop"
if [ -f "$AUTOSTART" ]; then
    echo "  vorhanden: $AUTOSTART"
    sed 's/^/    /' "$AUTOSTART"
else
    echo "  (kein Autostart-Eintrag unter $AUTOSTART)"
fi

}

# =====================================================================
case "$MODUS" in
    anzeigen)
        inventar
        echo
        echo "Deinstallationsbefehle anzeigen:  bash $0 --plan-entfernen"
        ;;
    status)
        status
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
    hailo)
        entferne_hailo
        ;;
    gstreamer)
        entferne_gstreamer
        ;;
esac
