# Server-Update: Konfiguration empfangen + LoRa-Kontrolle (Plus)

Damit der Server versteht, was dein Plus-Sender vom Sensor schickt
(`--konfig` und `--lora-spiegel`), müssen fünf Serverdateien ersetzt werden.
Dein hochgeladenes Repo ist der Basis-Stand — Format 3 (Übergänge) kann es
schon, Format 4 (Konfiguration) und Format 5 (LoRa-Kontrolle) noch nicht.

## Auf den SERVER (Repo zaehlsensor-server) — 5 Dateien ersetzen

| Datei | Was dazukommt |
|---|---|
| `dekoder.py` | `decode_konfig` (Format 4), `decode_lora_kontrolle` (Format 5) |
| `datenbank.py` | Tabellen `konfiguration` + `lora_kontrolle`, Abgleich-Abfrage |
| `ingest.py` | erkennt Format 4/5 und legt sie getrennt ab |
| `server.py` | liefert Konfig + LoRa-Abgleich an die Webseite (+2 Zeilen) |
| `dashboard.html` | zwei neue Karten: Konfiguration, LoRa-Abgleich |

Alle fünf sind abwärtskompatibel: die bestehenden 18-Byte- und Format-3-
Nachrichten laufen unverändert weiter, es kommen nur die zwei neuen Formate
dazu. Wenn du beim Basis-Server bleiben willst, spiel sie einfach nicht ein.

## Auf den SENSOR (Repo visitorcounter) — 2 Dateien NEU

Der Ordner `fuer_den_sensor/` hier enthält die zwei Bausteine, die dein
Plus-Sender braucht, um Konfig- und LoRa-Kontroll-Nachrichten zu bauen. Die
gehören neben `mqtt_send_loop.py` auf den Sensor:

- `konfig_payload.py`  — baut die Konfigurations-Nachricht (Format 4)
- `lora_spiegel.py`    — baut die LoRa-Kontroll-Nachricht (Format 5)

Ob du `mqtt_send_loop.py` selbst auch auf die Plus-Fassung hebst, hängt davon
ab, ob du die Zusatzfunktionen wirklich nutzt — die Basis-Fassung (nur
Zählwerte/Übergänge) reicht, wenn du `--konfig`/`--lora-spiegel` nicht brauchst.

## Für den Modus „mitlesen" der LoRa-Kontrolle

Damit die gespiegelten Frames bit-genau denen über LoRa entsprechen, muss
`lora_send_loop.py` jeden gesendeten Frame protokollieren:

```python
from lora_spiegel import frame_protokollieren
# nach bestätigtem Uplink, mit dem gerade gesendeten Frame + Sequenz:
frame_protokollieren(".lora_gesendet.log", payload_hex, sequenz)
```

Ohne diesen Aufruf `--lora-spiegel-modus eigen` verwenden.

## Nach dem Einspielen

```bash
# auf dem Server
python3 -c "import paho.mqtt; print(paho.mqtt.__version__)"
# bei 2.x:  pip3 install "paho-mqtt<2.0" --break-system-packages --force-reinstall
sudo systemctl restart zaehlsensor-server   # falls als Dienst

# Testnachricht (Format 4) einspielen und auf der Webseite prüfen:
mosquitto_pub -h localhost -t zaehlsensor/1/konfig \
  -m '{"format":4,"sensor_id":1,"umfang":"kompakt","modus":"multi_roi","in_feld":"office","felder":["office","ausgang"],"klassen":["person"],"snap_to_nearest":true}'
```

Danach muss auf dem Dashboard die Karte „Konfiguration" erscheinen.
