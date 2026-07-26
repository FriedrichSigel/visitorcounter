"""
mqtt_send_loop.py — Gegenstück zu lora_send_loop.py, aber über MQTT.

GEHÖRT AUF DEN SENSOR, nicht auf den Server. Hier mitgeliefert, damit beide
Seiten zusammenpassen; auf dem Sensor neben lora_send_loop.py legen.

Warum das so einfach ist:
    Die eigentliche Arbeit — Konfiguration lesen, Zählstände aus zaehlung.csv
    holen, das Delta seit dem letzten bestätigten Versand bilden, Statusbits
    setzen — steckt bereits in LivePayloadProvider aus lora_send_loop.py.
    Das ist transportunabhängig. Getauscht wird nur der Versandweg: statt
    AT-Befehl über die serielle Schnittstelle eine MQTT-Veröffentlichung.

    Deshalb wird der Provider hier importiert statt nachgebaut. Ändert sich
    die Zähllogik, ändert sie sich für beide Wege gleichzeitig.

Der Sendeweg (WLAN oder LTE-Dongle) spielt für dieses Skript keine Rolle —
MQTT läuft über IP, und welche Netzwerkschnittstelle das Betriebssystem
benutzt, ist seine Sache.

Aufruf:
    python mqtt_send_loop.py --broker 192.168.1.50 --live-counts \
        --sensor-id 1 --pause 5

    python mqtt_send_loop.py --broker localhost --once      # ein Testframe
"""

import argparse
import json
import sys
import time
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("FEHLER: paho-mqtt fehlt. Installieren mit:\n"
          "  pip install paho-mqtt", file=sys.stderr)
    raise

# Die Zähl-/Delta-Logik aus dem LoRa-Sender wiederverwenden.
try:
    from lora_send_loop import LivePayloadProvider, StaticProvider
except ImportError:
    LivePayloadProvider = StaticProvider = None

# Format 3: vollstaendige Uebergangsmatrix als JSON. Nur ueber MQTT sinnvoll —
# ueber LoRa wuerde die Nachricht nicht in ein Funktelegramm passen.
try:
    from uebergangs_payload import UebergangsProvider
except ImportError:
    UebergangsProvider = None

STANDARD_BROKER = "localhost"
STANDARD_PORT = 1883
STANDARD_TOPIC = "zaehlsensor/{sensor_id}/zaehlwerte"
STANDARD_PAUSE_MINUTEN = 5
STANDARD_TESTFRAME = "020100050701000000000000000000000000"


def log(text):
    print(f"[{datetime.now():%H:%M:%S}] {text}", flush=True)


def senden(client, topic, payload_hex, als_json=True, qos=1):
    """
    Veröffentlicht einen Frame.

    als_json=True schickt ein kleines JSON-Objekt mit der Hex-Nutzlast — gut
    lesbar in mosquitto_sub und für Menschen nachvollziehbar. Der Server
    versteht beide Formen.

    WICHTIG: Auch über MQTT wird bewusst NUR der 18-Byte-Frame übertragen,
    also dieselben aggregierten Zählwerte wie über LoRa. Der Verzicht auf
    Einzelereignisse, Zeitpunkte und Positionen ist eine Entwurfsentscheidung
    und keine Beschränkung des Funkprotokolls — siehe
    docs/entwicklung/Mitschnitt_Benchmark_und_Datenschutz.md
    """
    if als_json:
        inhalt = json.dumps({
            "payload": payload_hex,
            "gesendet_am": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        })
    else:
        inhalt = bytes.fromhex(payload_hex)

    ergebnis = client.publish(topic, inhalt, qos=qos)
    ergebnis.wait_for_publish(timeout=10)
    return ergebnis.is_published()


def senden_json(client, topic, nachricht, qos=1):
    """
    Veröffentlicht die Übergangs-Nachricht (Format 3) als JSON.

    qos=1 statt 0: Die Nachricht enthält Zählwerte, die beim Verlust nicht
    wiederkommen. Der Broker bestätigt den Empfang, erst dann schiebt der
    Provider seinen Merker nach.
    """
    inhalt = json.dumps(nachricht, ensure_ascii=False, separators=(",", ":"))
    ergebnis = client.publish(topic, inhalt, qos=qos)
    ergebnis.wait_for_publish(timeout=10)
    return ergebnis.is_published()


def main():
    ap = argparse.ArgumentParser(description="Sendet die Zählwerte per MQTT.")
    ap.add_argument("--broker", default=STANDARD_BROKER)
    ap.add_argument("--port", type=int, default=STANDARD_PORT)
    ap.add_argument("--benutzer", default=None)
    ap.add_argument("--passwort", default=None)
    ap.add_argument("--tls", action="store_true", help="TLS verwenden")
    ap.add_argument("--topic", default=None,
                    help=f"Standard: {STANDARD_TOPIC}")
    ap.add_argument("--sensor-id", type=int, default=1)
    ap.add_argument("--pause", type=int, default=STANDARD_PAUSE_MINUTEN,
                    help="Minuten zwischen zwei Sendungen")
    ap.add_argument("--live-counts", action="store_true",
                    help="echte Zählwerte statt Testframe")
    ap.add_argument("--config", default="roi_config.json")
    ap.add_argument("--counts-csv", default="zaehlung.csv")
    ap.add_argument("--pipeline-ok", action="store_true")
    ap.add_argument("--payload", default=STANDARD_TESTFRAME)
    ap.add_argument("--once", action="store_true", help="nur einmal senden")
    ap.add_argument("--roh", action="store_true",
                    help="18 rohe Bytes statt JSON senden (nur ohne --uebergaenge)")
    ap.add_argument("--uebergaenge", action="store_true",
                    help="vollstaendige Uebergangsmatrix als JSON senden "
                         "(von-Feld -> nach-Feld je Klasse) statt des "
                         "18-Byte-Rahmens")
    args = ap.parse_args()

    topic = (args.topic or STANDARD_TOPIC).format(sensor_id=args.sensor_id)

    if args.uebergaenge:
        if UebergangsProvider is None:
            print("FEHLER: uebergangs_payload.py nicht gefunden — für "
                  "--uebergaenge nötig.", file=sys.stderr)
            return 1
        provider = UebergangsProvider(
            args.config, args.counts_csv, args.sensor_id,
            interval_min=args.pause, pipeline_ok=args.pipeline_ok)
        log(f"Übergangs-Modus: vollständige Matrix aus {args.config} + "
            f"{args.counts_csv}")
    elif args.live_counts:
        if LivePayloadProvider is None:
            print("FEHLER: lora_send_loop.py nicht gefunden — für --live-counts "
                  "nötig (die Zähllogik wird von dort übernommen).", file=sys.stderr)
            return 1
        provider = LivePayloadProvider(
            args.config, args.counts_csv, args.sensor_id,
            interval_min=args.pause, pipeline_ok=args.pipeline_ok)
    else:
        provider = StaticProvider(args.payload) if StaticProvider else None
        if provider is None:
            class _Fest:
                def __init__(self, hexstr): self.hexstr = hexstr
                def build(self): return self.hexstr
                def commit(self): pass
            provider = _Fest(args.payload)

    client = mqtt.Client(client_id=f"zaehlsensor-{args.sensor_id}")
    if args.benutzer:
        client.username_pw_set(args.benutzer, args.passwort or "")
    if args.tls:
        client.tls_set()

    log(f"Verbinde mit {args.broker}:{args.port}, Topic {topic}")
    try:
        client.connect(args.broker, args.port, keepalive=60)
    except OSError as exc:
        print(f"FEHLER: Verbindung zum Broker fehlgeschlagen: {exc}", file=sys.stderr)
        return 1
    client.loop_start()

    try:
        while True:
            nachricht = provider.build()

            if nachricht is None:
                # Nichts Neues zu melden — kein leeres Paket senden.
                log("Keine neuen Übergänge — warte auf den nächsten Zyklus.")
                if args.once:
                    break
                time.sleep(max(1, args.pause) * 60)
                continue

            try:
                if args.uebergaenge:
                    erfolg = senden_json(client, topic, nachricht)
                    beschreibung = UebergangsProvider.zusammenfassen(nachricht)
                else:
                    erfolg = senden(client, topic, nachricht,
                                    als_json=not args.roh)
                    beschreibung = nachricht
            except Exception as exc:
                log(f"Senden fehlgeschlagen: {exc}")
                erfolg = False
                beschreibung = ""

            if erfolg:
                # Nur nach Erfolg den Zählstand nachschieben — sonst gehen
                # Zählungen verloren. Gleiche Logik wie beim LoRa-Sender.
                provider.commit()
                log(f"Gesendet: {beschreibung}")
            else:
                if hasattr(provider, "mark_failed"):
                    provider.mark_failed()
                log("Nicht bestätigt — Werte bleiben stehen und kommen "
                    "beim nächsten Mal mit.")

            if args.once:
                break
            time.sleep(max(1, args.pause) * 60)
    except KeyboardInterrupt:
        log("Beendet.")
    finally:
        client.loop_stop()
        client.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
