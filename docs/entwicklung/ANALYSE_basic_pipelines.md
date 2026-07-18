# Analyse: Welche Dateien aus `basic_pipelines/` braucht der core-Ordner?

**Stand 16.07.2026.** Antwort auf die Frage, ob die einzelnen Dateien im
`basic_pipelines`-Ordner (neben `core/`) noch nötig sind.

## Kurzantwort

**Keine der Dateien direkt in `basic_pipelines/` wird von `core/` importiert
oder zur Laufzeit gebraucht.** Der core-Ordner ist eigenständig — er importiert
nur (a) seine eigenen Module und (b) `hailo_apps` (kommt aus der venv/SDK, nicht
aus `basic_pipelines`). Für den reinen Sensor-Betrieb kann der core-Ordner allein
stehen.

## Datei-für-Datei

| Datei in `basic_pipelines/` | Von `core/` gebraucht? | Zweck / Empfehlung |
|---|---|---|
| `detection.py` | Nein | Hailos Beispiel-Detektionsskript. `core.py` ist die eigene, erweiterte Variante davon. Nicht nötig. |
| `detection_simple.py` | Nein | Minimalbeispiel. Nicht nötig. |
| `pose_estimation.py` | Nein | Anderes Hailo-Beispiel (Pose). Nicht nötig. |
| `depth.py` | Nein | Anderes Hailo-Beispiel (Tiefe). Nicht nötig. |
| `instance_segmentation.py` | Nein | Anderes Hailo-Beispiel. Nicht nötig. |
| `VideoApp.py` | Nein | Beispiel-Video-App. Nicht nötig. |
| `core.py` (im Parent) | — | Ältere/parallele Kopie außerhalb von `core/`. Die maßgebliche Version liegt in `core/core.py`. Die Parent-Kopie kann weg. |
| `config.yaml` | Nein | Konfiguration der Hailo-Beispiele. `core/` nutzt `config.py`, nicht diese YAML. Nicht nötig. |
| `ci.yaml` | Nein | CI-Definition des Beispiel-Repos. Für core irrelevant. |
| `install.sh` | Indirekt | Installiert die Hailo-Umgebung systemweit. Einmalig fürs Setup nützlich, gehört aber zur Hailo-Installation, nicht zum core-Paket. |
| `hailo_python_installation.sh` | Indirekt | Lädt HailoRT-/Tappas-Wheels. Teil des Hailo-Setups, nicht des core-Betriebs. |
| `download_resources.sh` | Indirekt | Lädt Modell-/Video-Ressourcen (HEF, mp4). Das Standard-Detektionsmodell wird von `hailo_apps` bezogen; core braucht keine eigenen Ressourcen. Nur relevant, falls ein spezifisches HEF nachgeladen werden soll. |
| `setup_env.sh` (im Parent) | Ersetzt | Durch das neue `core/setup_env.sh` abgelöst (setzt PYTHONPATH auf core). |
| `run_tests.sh` | Nein | Testrunner der Beispiele. Nicht nötig. |
| `__init__.py` | Nein | Macht `basic_pipelines` zum Paket. Für den eigenständigen core-Ordner nicht nötig (core nutzt flache Imports ohne Paketpräfix). |
| `resources/` | Indirekt | Modell-/Videodateien. Siehe `download_resources.sh`. Für den USB-Kamerabetrieb nicht erforderlich. |
| `camera_test/` | Nein | Kameratest-Hilfsskript. Optional, kann separat behalten werden. |
| `lora_hardware_test/` | Nein (separat) | LoRa-Probe-Skripte — bewusst eigener Ordner, gehört nicht in core. |

## Empfehlung

**Für ein sauberes, eigenständiges core-Repository:**
- Es reicht, den `core/`-Ordner mit den neu erstellten Dateien (`setup_env.sh`,
  `requirements.txt`, `.gitignore`, `README.md`) zu versionieren.
- Die Hailo-Beispielskripte (`detection.py`, `pose_estimation.py`, `depth.py`,
  `instance_segmentation.py`, `detection_simple.py`, `VideoApp.py`,
  `config.yaml`, `ci.yaml`, `run_tests.sh`, `__init__.py`, die Parent-`core.py`)
  müssen **nicht** mitgenommen werden.
- Die Setup-Skripte (`install.sh`, `hailo_python_installation.sh`,
  `download_resources.sh`) gehören zur **Hailo-Installation** und werden einmalig
  gebraucht — im README ist darauf verwiesen. Sie müssen nicht Teil des
  core-Repos sein, schaden dort aber auch nicht, wenn man sie zur Bequemlichkeit
  beilegt.

**Einzige echte Abhängigkeit nach außen:** Das `hailo_apps`-Framework
(`from hailo_apps.hailo_app_python...`). Das ist ein installiertes Paket in der
venv, kein Ordner neben core — deshalb steht der core-Ordner unabhängig von
`basic_pipelines`.

## Was wurde neu erstellt (im core-Ordner)

| Datei | Zweck |
|---|---|
| `setup_env.sh` | venv aktivieren + PYTHONPATH auf core setzen (findet venv in core/, ../ oder \$HOME) |
| `requirements.txt` | pip-Abhängigkeiten: numpy<2, opencv-python, Pillow, customtkinter, scikit-learn, scipy |
| `.gitignore` | schließt venv, Laufzeit-Ausgaben (CSVs, Bilder, `vorherige_laeufe/`), Caches und die gerätespezifische `roi_config.json` aus |
| `README.md` | eigenständige Installations- und Nutzungsanleitung nur mit dem core-Ordner |

## Hinweis zu `.git`
Ein `.git`-Verzeichnis wird nicht als Datei erstellt — es entsteht durch
`git init` im core-Ordner. Vorgehen für ein eigenständiges Repo:
```bash
cd core
git init
git add .
git commit -m "Eigenständiges core-Paket des Besucherzählsensors"
```
Die `.gitignore` sorgt dafür, dass venv, Laufzeit-Ausgaben und die
gerätespezifische Konfiguration nicht eingecheckt werden.
