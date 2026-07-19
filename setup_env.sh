#!/bin/bash
#
# setup_env.sh — Environment für den Besucherzählsensor (core) einrichten.
#
# Aktiviert die virtuelle Umgebung und setzt den PYTHONPATH so, dass sowohl
# die core-Module untereinander als auch das Hailo-App-Framework gefunden
# werden. Analog zum setup_env.sh des hailo-rpi5-examples-Projekts, aber auf
# den core-Ordner zugeschnitten.
#
# ANWENDUNG (muss GESOURCED werden, nicht ausgeführt):
#   source setup_env.sh
#
# Danach ist der PYTHONPATH für die aktuelle Terminal-Sitzung gesetzt und die
# venv aktiv. Start der App: python app.py

# Name der virtuellen Umgebung. Standard: die vom Hailo-Setup erzeugte venv.
# Per Umgebungsvariable überschreibbar:  VENV_NAME=meinvenv source setup_env.sh
VENV_NAME="${VENV_NAME:-venv_hailo_rpi_examples}"

# --- Prüfen, ob das Skript gesourced wird (sonst wirkt export nicht) ---
is_sourced() {
    if [ -n "$ZSH_VERSION" ]; then
        [[ -o sourced ]]
    elif [ -n "$BASH_VERSION" ]; then
        [[ "${BASH_SOURCE[0]}" != "$0" ]]
    else
        echo "Nicht unterstützte Shell. Bitte bash oder zsh verwenden."
        return 1
    fi
}

if ! is_sourced; then
    echo "FEHLER: Dieses Skript muss gesourced werden:  source setup_env.sh"
    exit 1
fi

# --- Kernel-Check (bekannte inkompatible Raspberry-Pi-Kernel) ---
if uname -a | grep -q "Linux raspberrypi"; then
    INVALID_KERNELS=("6.12.21" "6.12.22" "6.12.23" "6.12.24" "6.12.25")
    CURRENT_VERSION=$(uname -r | cut -d '+' -f 1)
    if [[ " ${INVALID_KERNELS[@]} " =~ " ${CURRENT_VERSION} " ]]; then
        echo "WARNUNG: Kernel $CURRENT_VERSION ist mit Hailo bekannt inkompatibel."
        echo "Siehe: https://community.hailo.ai/t/raspberry-pi-kernel-compatibility-issue-temporary-fix/15322"
    fi
fi

# --- Verzeichnis dieses Skripts bestimmen (= core-Ordner) ---
if [ -n "$BASH_VERSION" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "${(%):-%N}")" && pwd)"
fi

# --- PYTHONPATH setzen ---
# 1) den core-Ordner selbst, damit die Module (config, tracking, ...) sich
#    gegenseitig finden, egal von wo die App gestartet wird.
# 2) das Elternverzeichnis (basic_pipelines) ist NICHT nötig — core importiert
#    nichts mehr von dort. hailo_apps kommt aus der venv/den System-Paketen.
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"
echo "PYTHONPATH um core-Ordner ergänzt:"
echo "  ${SCRIPT_DIR}"

# --- venv aktivieren ---
# Suchreihenfolge: im core-Ordner, im Elternverzeichnis, im $HOME. So wird
# sowohl die projektlokale als auch die vom Hailo-Setup zentral angelegte venv
# gefunden.
VENV_FOUND=""
for CANDIDATE in "${SCRIPT_DIR}/${VENV_NAME}" \
                 "${SCRIPT_DIR}/../${VENV_NAME}" \
                 "${HOME}/${VENV_NAME}"; do
    if [ -d "$CANDIDATE" ]; then
        VENV_FOUND="$CANDIDATE"
        break
    fi
done

if [ -n "$VENV_FOUND" ]; then
    source "${VENV_FOUND}/bin/activate"
    echo "Virtuelle Umgebung aktiviert: ${VENV_FOUND}"
else
    echo "WARNUNG: venv '${VENV_NAME}' nicht gefunden (gesucht in core/, ../, \$HOME)."
    echo "Anlegen z. B. mit:"
    echo "  python3 -m venv --system-site-packages ${VENV_NAME}"
    echo "  source ${VENV_NAME}/bin/activate"
    echo "  pip install -r requirements.txt"
    return 1
fi

echo "Fertig. App starten mit:  python app.py"
