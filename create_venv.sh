#!/bin/bash
#
# create_venv.sh — eigene virtuelle Umgebung für den Besucherzählsensor anlegen.
#
# Ersetzt das Mitbenutzen der venv aus hailo-rpi5-examples. Diese venv gehört
# zum Projekt, wird hier reproduzierbar erzeugt und ist per .gitignore vom
# Repository ausgeschlossen — es wandert also nie fremder Code ins eigene Repo.
#
# ANWENDUNG (einmalig, auf dem Raspberry Pi):
#   bash create_venv.sh
#   source setup_env.sh
#   python app.py
#
# Umgebungsvariablen:
#   VENV_NAME            Name der zu erzeugenden venv (Standard: venv_visitorcounter)
#   HAILO_APPS_VERSION   Git-Tag des hailo-apps-infra-Repos (Standard: 25.7.0 —
#                        die Version, gegen die dieses Projekt entwickelt wurde)
#   HAILO_VENV           Nur als Rückfall: Pfad zu einer bestehenden Hailo-venv,
#                        falls die Online-Installation von hailo_apps scheitert.

set -euo pipefail

VENV_NAME="${VENV_NAME:-venv_visitorcounter}"
HAILO_APPS_VERSION="${HAILO_APPS_VERSION:-25.7.0}"
HAILO_VENV="${HAILO_VENV:-$HOME/hailo-rpi5-examples/venv_hailo_rpi_examples}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/${VENV_NAME}"

echo "=== Besucherzählsensor: venv anlegen ==="
echo "Ziel: ${VENV_DIR}"

if [ -d "$VENV_DIR" ]; then
    echo "Es existiert bereits eine venv unter ${VENV_DIR}."
    read -r -p "Neu anlegen (löscht die bestehende)? [j/N] " ANTWORT
    case "$ANTWORT" in
        [jJyY]) rm -rf "$VENV_DIR" ;;
        *) echo "Abbruch — bestehende venv bleibt unverändert."; exit 0 ;;
    esac
fi

# --system-site-packages ist zwingend: `hailo` (HailoRT-Bindings) und `gi`
# (PyGObject/GStreamer) sind System-/SDK-Pakete und nicht per pip installierbar.
python3 -m venv --system-site-packages "$VENV_DIR"
echo "venv erzeugt."

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r "${SCRIPT_DIR}/requirements.txt"

# --- hailo_apps installieren --------------------------------------------------
# Das App-Framework ist ein reines Python-Paket (py3-none-any) und wird direkt
# aus dem offiziellen Hailo-Repository installiert — kein Kopieren fremder
# Dateien ins eigene Projekt, keine Abhängigkeit von einer fremden venv.
# Die HailoRT-Bindings (`hailo`) und `gi` kommen weiterhin aus den
# System-Paketen, sichtbar über --system-site-packages.
echo "--- Installiere hailo_apps ${HAILO_APPS_VERSION} ---"
if python -m pip install \
        "hailo-apps @ git+https://github.com/hailo-ai/hailo-apps-infra.git@${HAILO_APPS_VERSION}"; then
    echo "hailo_apps installiert."
else
    echo "WARNUNG: Installation von hailo_apps fehlgeschlagen (Netzwerk? SSH-Key?)."
    echo "  Rückfall: Einbindung per .pth aus einer vorhandenen Hailo-venv."
    # Kandidaten: explizit gesetzter Pfad, eine Kopie direkt im Projektordner,
    # sowie die üblichen Orte des hailo-rpi5-examples-Setups.
    HAILO_SP=""
    for VENV_CAND in "$HAILO_VENV" \
                     "${SCRIPT_DIR}/venv_hailo_rpi_examples" \
                     "${SCRIPT_DIR}/../venv_hailo_rpi_examples" \
                     "${HOME}/venv_hailo_rpi_examples"; do
        for CANDIDATE in "$VENV_CAND"/lib/python*/site-packages; do
            if [ -d "$CANDIDATE/hailo_apps" ]; then
                HAILO_SP="$CANDIDATE"
                break 2
            fi
        done
    done
    if [ -n "$HAILO_SP" ]; then
        OWN_SP="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
        echo "$HAILO_SP" > "${OWN_SP}/hailo_apps.pth"
        echo "  hailo_apps eingebunden über: ${HAILO_SP}"
    else
        echo "  Auch keine Hailo-venv mit hailo_apps gefunden (u. a. geprüft:"
        echo "  ${HAILO_VENV}, ${SCRIPT_DIR}/venv_hailo_rpi_examples)."
        echo "  Setze HAILO_VENV=<pfad> und starte dieses Skript erneut."
    fi
fi

# --- Selbsttest ---------------------------------------------------------------
echo "--- Selbsttest der Importe ---"
PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python - <<'PY'
import importlib
for name in ("numpy", "cv2", "PIL", "customtkinter", "sklearn", "scipy",
             "gi", "hailo", "hailo_apps"):
    try:
        importlib.import_module(name)
        print(f"  OK      {name}")
    except Exception as exc:
        print(f"  FEHLT   {name}  ({exc})")
PY

echo
echo "Fertig. Weiter mit:"
echo "  source setup_env.sh"
echo "  python app.py"
