"""
tabs/mqtt_controls.py — MQTT-Abschnitt von Seite 3 (Aufbau, Validierung,
Subprozess-Start/Stop des MQTT-Senders). Eigene Datei aus demselben Grund wie
tabs/recording_controls.py und tabs/lora_controls.py. Siehe tabs/__init__.py
für die Mixin-Begründung.
"""

import signal
import subprocess
import sys
import threading

import customtkinter as ctk
import ctk_dialogs as messagebox

from .constants import ROI_CONFIG_PATH, ZAEHLUNG_CSV


class MqttControlsMixin:
    """Checkbox + Einstellungen für den MQTT-Versand (Alternative/Ergänzung
    zu LoRa), inkl. Subprozess-Verwaltung von mqtt_send_loop.py."""

    def _build_mqtt_section(self, frame):
        """Baut den MQTT-Abschnitt in `frame` (Tab 3) auf.

        Zweiter Übertragungsweg neben LoRa: schickt dieselben Zählwerte per
        MQTT an den Stadtwerke-Server. Sinnvoll dort, wo LoRa am Standort
        nicht durchkommt (siehe HANDOFF.md/ToDo.md). Eigener Subprozess
        (mqtt_send_loop.py), entkoppelt von der Zähl-Pipeline.
        """
        mqtt_frame = ctk.CTkFrame(frame, corner_radius=8)
        mqtt_frame.pack(anchor="w", fill="x", pady=(0, 15))
        ctk.CTkCheckBox(
            mqtt_frame, text="Daten per MQTT senden",
            variable=self.mqtt_enabled_var, command=self._on_mqtt_toggle,
            font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        # Broker-Adresse und Port
        mqtt_row1 = ctk.CTkFrame(mqtt_frame, fg_color="transparent")
        mqtt_row1.pack(anchor="w", padx=12, pady=(0, 6))
        ctk.CTkLabel(mqtt_row1, text="Server (Broker):").pack(side="left")
        self.mqtt_broker_entry = ctk.CTkEntry(
            mqtt_row1, textvariable=self.mqtt_broker_var, width=140)
        self.mqtt_broker_entry.pack(side="left", padx=(5, 20))
        ctk.CTkLabel(mqtt_row1, text="Port:").pack(side="left")
        self.mqtt_port_entry = ctk.CTkEntry(
            mqtt_row1, textvariable=self.mqtt_port_var, width=70)
        self.mqtt_port_entry.pack(side="left", padx=5)

        # Intervall und Sensor-ID
        mqtt_row2 = ctk.CTkFrame(mqtt_frame, fg_color="transparent")
        mqtt_row2.pack(anchor="w", padx=12, pady=(0, 6))
        ctk.CTkLabel(mqtt_row2, text="Sende-Intervall (Minuten):").pack(side="left")
        self.mqtt_interval_entry = ctk.CTkEntry(
            mqtt_row2, textvariable=self.mqtt_interval_var, width=60)
        self.mqtt_interval_entry.pack(side="left", padx=(5, 20))
        ctk.CTkLabel(mqtt_row2, text="Sensor-ID:").pack(side="left")
        self.mqtt_sensor_entry = ctk.CTkEntry(
            mqtt_row2, textvariable=self.mqtt_sensor_id_var, width=60)
        self.mqtt_sensor_entry.pack(side="left", padx=5)

        # Übergangsmatrix statt 18-Byte-Frame (über MQTT sinnvoll, da keine
        # Größengrenze). Standard an, weil das der eigentliche Mehrwert ist.
        self.mqtt_transitions_check = ctk.CTkCheckBox(
            mqtt_frame,
            text="Vollständige Übergänge senden (von Fläche zu Fläche, je Klasse)",
            variable=self.mqtt_transitions_var)
        self.mqtt_transitions_check.pack(anchor="w", padx=12, pady=(0, 10))

        self._on_mqtt_toggle()   # setzt Feld-Zustände

    def _on_mqtt_toggle(self):
        """Aktiviert/deaktiviert die MQTT-Eingabefelder."""
        # Felder existieren erst nach _build_start_tab - defensiv prüfen.
        if not hasattr(self, "mqtt_broker_entry"):
            return
        state = "normal" if self.mqtt_enabled_var.get() else "disabled"
        for widget in (self.mqtt_broker_entry, self.mqtt_port_entry,
                       self.mqtt_interval_entry, self.mqtt_sensor_entry,
                       self.mqtt_transitions_check):
            widget.configure(state=state)

    def _validate_mqtt_settings(self):
        """Prüft Broker, Port, Intervall und Sensor-ID vor dem Start.
        Rückgabe: dict mit den Werten oder None bei ungültiger Eingabe."""
        broker = self.mqtt_broker_var.get().strip()
        if not broker:
            messagebox.showwarning(
                "Kein Server angegeben",
                "Bitte die Adresse des MQTT-Servers (Broker) eintragen - "
                "die feste IP des Server-Pi.", parent=self.root)
            return None
        try:
            port = int(self.mqtt_port_var.get().strip())
            if not (1 <= port <= 65535):
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Ungültiger Port",
                "Der Port muss eine ganze Zahl zwischen 1 und 65535 sein "
                "(Standard 1883).", parent=self.root)
            return None
        try:
            interval = int(self.mqtt_interval_var.get().strip())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Ungültiges Intervall",
                "Bitte ein Sende-Intervall in ganzen Minuten (> 0) angeben.",
                parent=self.root)
            return None
        try:
            sensor_id = int(self.mqtt_sensor_id_var.get().strip())
            if not (0 <= sensor_id <= 255):
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Ungültige Sensor-ID",
                "Die Sensor-ID muss eine ganze Zahl zwischen 0 und 255 sein.",
                parent=self.root)
            return None
        return {"broker": broker, "port": port, "interval": interval,
                "sensor_id": sensor_id,
                "transitions": self.mqtt_transitions_var.get()}

    def _start_mqtt_sender(self, settings):
        """Startet mqtt_send_loop.py als eigenen Subprozess. Dessen Ausgabe
        wird (mit Präfix) in dasselbe Live-Log geleitet."""
        cmd = [
            sys.executable, "mqtt_send_loop.py",
            "--broker", settings["broker"],
            "--port", str(settings["port"]),
            "--pause", str(settings["interval"]),
            "--sensor-id", str(settings["sensor_id"]),
            "--config", ROI_CONFIG_PATH,
            "--counts-csv", ZAEHLUNG_CSV,
            "--pipeline-ok",
        ]
        # Entweder die volle Übergangsmatrix oder die kompakten Zählwerte.
        if settings["transitions"]:
            cmd.append("--uebergaenge")
        else:
            cmd.append("--live-counts")
        try:
            self.mqtt_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
        except Exception as e:
            # MQTT-Fehler darf den Zähllauf nicht abbrechen - nur melden.
            self.output_queue.put(f"[MQTT] Start fehlgeschlagen: {e}\n")
            self.mqtt_process = None
            return
        threading.Thread(target=self._read_mqtt_output, daemon=True).start()
        art = "Übergänge" if settings["transitions"] else "Zählwerte"
        self.output_queue.put(
            f"[MQTT] Sender gestartet ({art}, Server {settings['broker']}:"
            f"{settings['port']}, Intervall {settings['interval']} min, "
            f"Sensor-ID {settings['sensor_id']}).\n")

    def _read_mqtt_output(self):
        for line in self.mqtt_process.stdout:
            self.output_queue.put(f"[MQTT] {line}")
        self.output_queue.put("__MQTT_ENDED__")

    def _stop_mqtt_sender(self):
        """Beendet den MQTT-Subprozess (SIGINT, wie Strg-C), falls er läuft."""
        if self.mqtt_process is None:
            return
        try:
            self.mqtt_process.send_signal(signal.SIGINT)
        except Exception:
            pass
