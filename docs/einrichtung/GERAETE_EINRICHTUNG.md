# Geräte-Einrichtungsprotokoll — Zählsensor komplett
## Raspberry Pi 5 + Hailo-8 + Kamera + core-Projekt + LoRa (LA66)

**Zweck:** Reproduzierbare Neueinrichtung eines vollständigen Zählsensors.
Zielszenario: Ausrollen auf bis zu 17 Geräte (Volkspark Biosphäre, ein Sensor
pro Eingang). Referenzgerät: `stadtwerke2` (Raspberry Pi 5, 8 GB, Nutzer
`fritz`, Raspberry Pi OS Bookworm 64-bit).

**Pflegeregel (gilt fortlaufend):** Jeder Setup-Befehl, der auf einem Gerät
ausgeführt wird, wird hier ergänzt — mit Zweck und erwartetem Ergebnis.
Einmalige Debug-Kommandos → Abschnitt „Diagnose" des jeweiligen Bereichs,
dauerhafte Einrichtung → nummerierte Schritte. LoRa-Details stehen im
Unterdokument `lora_hardware_test/EINRICHTUNG_LA66.md`.

**Verifikationsstatus:**
- ✅ = auf dem Referenzgerät ausgeführt und bestätigt
- ⚠️ = Standard-Ablauf laut Herstellerdoku, auf dem Referenzgerät vor Beginn
  dieser Dokumentation gelaufen — **gegen eigene Shell-History prüfen**
  (`history | grep -i <stichwort>`) und Status hier aktualisieren

**Stand:** 14.07.2026

---

## 0. Betriebssystem-Grundlage

| Schritt | Befehl / Aktion | Status |
|---|---|---|
| 0.1 | Raspberry Pi OS **Bookworm 64-bit** per Raspberry Pi Imager auf SD/NVMe flashen (im Imager: Hostname, Nutzer, WLAN, SSH aktivieren) | ⚠️ |
| 0.2 | System aktualisieren: `sudo apt update && sudo apt full-upgrade -y` | ⚠️ |
| 0.3 | Neustart: `sudo reboot` | ⚠️ |

> **Für Volkspark-Rollout:** Hostname-Schema festlegen (z. B. `sensor-eingang-01`
> … `-17`), damit SSH-Zugriff und LoRa-`sensor_id` eindeutig zuzuordnen sind.
> Referenzgerät heißt `stadtwerke2`.

---

## 1. Hailo-8 KI-Beschleuniger

**Verbaut:** Hailo-8 über M.2/PCIe (AI Kit). Firmware auf dem Referenzgerät:
**4.23.0** (✅ verifiziert lauffähig).

| Schritt | Befehl | Zweck | Status |
|---|---|---|---|
| 1.1 | PCIe Gen 3 aktivieren: `sudo raspi-config` → Advanced Options → PCIe Speed → Gen 3, danach Neustart | volle Bandbreite für den Hailo-8 | ⚠️ |
| 1.2 | `sudo apt install -y hailo-all` | HailoRT-Treiber, Firmware, GStreamer-Plugins, `rpicam-apps`-Integration | ⚠️ |
| 1.3 | `sudo reboot` | Treiber laden | ⚠️ |
| 1.4 | Verifikation: `hailortcli fw-control identify` | muss Gerät + Firmware-Version (4.23.0) melden | ⚠️ |

### hailo-rpi5-examples (Pipeline-Grundlage des Projekts)

Das core-Projekt baut auf `hailo-rpi5-examples` auf; Repo liegt auf dem
Referenzgerät unter `~/hailo-rpi5-examples` (✅ Pfad verifiziert).

| Schritt | Befehl | Status |
|---|---|---|
| 1.5 | `git clone https://github.com/hailo-ai/hailo-rpi5-examples.git ~/hailo-rpi5-examples` | ⚠️ |
| 1.6 | `cd ~/hailo-rpi5-examples && ./install.sh` (richtet venv + Ressourcen/Modelle ein) | ⚠️ |
| 1.7 | Vor **jeder** Nutzung in neuer Shell: `source setup_env.sh` (im Repo-Ordner) | ⚠️ |
| 1.8 | Funktionstest: `python basic_pipelines/detection.py --input <testvideo>` | ⚠️ |

> **LÜCKE — bitte ausfüllen:** exakte damals installierte Paketversionen
> (`apt list --installed 2>/dev/null | grep hailo`) und ob 1.6 zusätzliche
> Nachfragen hatte. Einmal ausführen und Ausgabe hier einfügen:
> ```
> [Ausgabe von: apt list --installed 2>/dev/null | grep hailo]
> ```

### Diagnose Hailo

| Befehl | Zweck |
|---|---|
| `hailortcli fw-control identify` | Chip erreichbar? Firmware-Version |
| `ps aux \| grep hailo` | hängende Prozesse finden (bei `HAILO_OUT_OF_PHYSICAL_DEVICES(74)`) |
| `sudo systemctl restart hailort` | gesperrten Chip freigeben (mildester Eingriff) |
| Neustart | letzter Ausweg bei gesperrtem Chip |

**Gelernter Stolperstein (✅ dokumentiert):** Der Chip kann in gesperrtem
Zustand zurückbleiben, wenn ein `core.py`-Prozess per SIGKILL abgeschossen
wird (Ursache des `HAILO_OUT_OF_PHYSICAL_DEVICES(74)`-Fehlers). Deshalb
beendet das Projekt Subprozesse grundsätzlich SIGINT-zuerst. Außerdem: Der
**allererste** Pipeline-Start nach einem Neustart dauert deutlich länger
(HailoRT-/PCIe-Aufbau, Modell laden) — Timeouts entsprechend großzügig
(`SNAPSHOT_TIMEOUT_SECONDS = 240` in `config.py`).

---

## 2. Kamera

**Verbaut:** USB-Kamera (✅ in Betrieb; genaues Modell hier nachtragen: ______)

| Schritt | Befehl | Zweck | Status |
|---|---|---|---|
| 2.1 | Kamera anschließen, prüfen: `ls /dev/video*` | Gerät erkannt? | ✅ |
| 2.2 | Unabhängiger Funktionstest ohne Hailo: `python3 camera_test.py` (liegt im Projektstamm) | grenzt Kamera-/Treiberprobleme von Pipeline-Problemen ab | ✅ bereitgestellt |

**Gelernte Stolpersteine (✅ dokumentiert):**
1. Referenzbild fürs Konfigurationstool **muss aus derselben Hailo-Pipeline**
   stammen wie der Live-Betrieb (`CORE_SNAPSHOT_ONLY`-Modus in `core.py`) —
   eine unabhängige `cv2.VideoCapture()`-Aufnahme lieferte abweichende
   Auflösung/Bildausschnitt.
2. Hailos Pipeline für `--input usb` spiegelt horizontal
   (`videoflip video-direction=horiz` im Pipeline-String). Gegenmaßnahme
   fürs Anzeigefenster: `LIVE_PREVIEW_HORIZONTAL_FLIP` in `config.py`
   (Wirksamkeit noch offen — Status beim nächsten Test hier aktualisieren).

---

## 3. core-Projekt (Zählsoftware)

**Repo:** `github.com/FriedrichSigel/personenzaehlung` (privat, Zugriff via SSH).

| Schritt | Befehl | Zweck | Status |
|---|---|---|---|
| 3.1 | SSH-Key erzeugen: `ssh-keygen -t ed25519 -C "sensor-XX"` und Public Key bei GitHub hinterlegen (Deploy Key, read-only reicht für reine Sensoren) | Repo-Zugriff ohne Passwort/Token | ⚠️ auf Referenzgerät erledigt, Befehl rekonstruiert |
| 3.2 | `git clone git@github.com:FriedrichSigel/personenzaehlung.git` | Code aufs Gerät | ✅ (Repo vorhanden) |
| 3.3 | `pip install customtkinter --break-system-packages` | GUI-Framework für `app.py` / `roi_config_app.py` | ✅ |
| 3.4 | Start Standardweg: `python app.py` (Seite 1 Input → 2 Konfiguration → 3 Start → 4 Live-Auswertung) | Betrieb ohne Kommandozeile | ✅ |
| 3.5 | Autostart einrichten (03.08.): `chmod +x start_app.sh`, dann `~/.config/autostart/visitorcounter.desktop` anlegen (Inhalt und Erklärung siehe `../entwicklung/AENDERUNGEN-mehrere-inout-lightmode-autostart.md`, Abschnitt 4) | Terminal öffnet sich beim Hochfahren automatisch, wärmt die Pipeline auf und startet die Zählung ohne manuellen Klick | ✅ |

> **LÜCKE — bitte ausfüllen:** weitere pip-Pakete, die über `hailo-rpi5-examples`
> hinaus nötig waren (OpenCV/Pillow kommen i. d. R. über die Hailo-venv mit;
> falls einzeln installiert, Befehl hier ergänzen):
> ```
> pip install ______ --break-system-packages
> ```

**Hinweis `--break-system-packages`:** auf Bookworm nötig (PEP 668). Projekt-
entscheidung: systemweit statt venv, damit spätere systemd-Services ohne
venv-Aktivierung starten können. Konsequenz: Paketliste hier im Protokoll
aktuell halten, da es kein `requirements.txt`-isoliertes Environment gibt.

---

## 4. LoRa (Dragino LA66 USB, EU868)

**Vollständiges Detailprotokoll: → `lora_hardware_test/EINRICHTUNG_LA66.md`** ✅

Kurzfassung der auf dem Referenzgerät am 14.07.2026 ausgeführten Schritte
(alle ✅ verifiziert):

```bash
pip install pyserial --break-system-packages
sudo usermod -aG dialout $USER
sudo reboot
# LA66 mit Antenne einstecken, dann:
ls -l /dev/serial/by-id/          # by-id-Pfad notieren → LORA_PORT
python3 lora_hardware_test/test1_offline/test1_offline.py
```

Befunde Referenzgerät: CP2102 auf `/dev/ttyUSB0`, AT-Konsole antwortet bei
9600 Baud, kein Passwortschutz aktiv (Details und Stolpersteine im
Unterdokument). Ausstehend: Registrierung der Keys bei einem Network Server
(TTN-Test oder direkt Stadtwerke).

---

## 5. Checkliste Komplettaufbau (Kurzfassung zum Abhaken)

```
Betriebssystem
[ ] Raspberry Pi OS Bookworm 64-bit flashen (Hostname nach Schema!)
[ ] apt update && full-upgrade, Neustart

Hailo
[ ] raspi-config: PCIe Gen 3, Neustart
[ ] sudo apt install hailo-all, Neustart
[ ] hailortcli fw-control identify  →  Firmware wird gemeldet
[ ] hailo-rpi5-examples klonen, ./install.sh
[ ] source setup_env.sh + Detection-Beispiel läuft

Kamera
[ ] USB-Kamera anschließen, ls /dev/video*
[ ] python3 camera_test.py  →  Bild kommt

core-Projekt
[ ] SSH-Deploy-Key erzeugen + bei GitHub hinterlegen
[ ] Repo klonen
[ ] pip install customtkinter --break-system-packages
[ ] python app.py  →  alle vier Seiten erreichbar
[ ] Autostart einrichten: chmod +x start_app.sh + ~/.config/autostart/visitorcounter.desktop

LoRa (Details: EINRICHTUNG_LA66.md)
[ ] pip install pyserial --break-system-packages
[ ] usermod -aG dialout + Neustart
[ ] LA66 einstecken, by-id-Pfad → LORA_PORT
[ ] Test 1 offline: 7/7
[ ] Keys an Network-Server-Betreiber, Join prüfen

Abschluss
[ ] Dieses Protokoll: alle ⚠️ und Lücken für das neue Gerät verifizieren/füllen
[ ] sensor_id des Geräts festlegen und notieren (1–17)
```

---

## Änderungshistorie dieses Protokolls

| Datum | Änderung |
|---|---|
| 14.07.2026 | Erstfassung; LoRa-Abschnitt vollständig verifiziert (Erstinbetriebnahme LA66 auf `stadtwerke2`), Hailo-/OS-Abschnitte rückwirkend rekonstruiert (⚠️-Status) |
