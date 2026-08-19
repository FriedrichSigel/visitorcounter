"""
tabs/pipeline_control.py — Start/Stopp von core.py als Subprozess, genutzt
sowohl von Seite 3 (normaler Zähllauf) als auch Seite 5 (Auto-Konfiguration:
Datensammlung). Eigene Datei, weil das Starten/Beenden/Überwachen des
Kernprozesses ein eigenständiges Thema ist, unabhängig davon, von welcher
Seite aus es angestoßen wird (Separation of Concerns). Siehe
tabs/__init__.py für die Mixin-Begründung.
"""

import os
import signal
import subprocess
import sys
import threading

import ctk_dialogs as messagebox


class PipelineControlMixin:
    """Start/Stopp/Überwachung von core.py. Setzt self.process; die
    LoRa-/MQTT-Sender (siehe lora_controls.py/mqtt_controls.py) werden erst
    NACH erfolgreichem core.py-Start mitgestartet bzw. beim Stoppen zuerst
    beendet."""

    def _start_pipeline(self, collection=False):
        """
        Startet core.py als Subprozess.

        collection=False (Tab 3, normaler Zähllauf): kein Zeitlimit, außer der
          Nutzer trägt in Tab 3 eines ein (run_duration_var). Keine Datensammlung.
        collection=True (Tab 5, Auto-Konfiguration): Datensammlung aktiv, mit der
          in Tab 5 gewählten Sammeldauer als Zeitlimit.
        """
        if not self.input_value:
            messagebox.showwarning("Fehlt noch", "Bitte zuerst auf Seite 1 einen Input auswählen.", parent=self.root)
            return
        if self.process is not None:
            messagebox.showinfo("Läuft bereits", "Die Pipeline läuft schon.", parent=self.root)
            return
        if self.warmup_running:
            messagebox.showinfo(
                "Aufwärmlauf läuft",
                "Die Pipeline wird gerade einmalig aufgewärmt (nach jedem "
                "Neustart des Geräts). Bitte kurz warten - danach startet der "
                "Zähllauf deutlich schneller.",
                parent=self.root)
            return

        # LoRa nur bei normalen Zählläufen (Tab 3), nicht bei der
        # Auto-Config-Datensammlung. Vor dem Start prüfen, damit nicht erst
        # core.py läuft und dann die LoRa-Eingabe scheitert.
        lora_settings = None
        if not collection and self.lora_enabled_var.get():
            lora_settings = self._validate_lora_settings()
            if lora_settings is None:
                return

        # MQTT genauso: vor dem Start prüfen. Beide Übertragungswege können
        # gleichzeitig laufen (z. B. zum Vergleich der Zuverlässigkeit).
        mqtt_settings = None
        if not collection and self.mqtt_enabled_var.get():
            mqtt_settings = self._validate_mqtt_settings()
            if mqtt_settings is None:
                return

        # Debug-Funktionen (Mitschnitt, Live-Vorschau, Zeitlimit, Debug-
        # Dateien) sind nur aktiv, wenn der Debug-Hauptschalter (Tab 3) an
        # ist - unabhängig vom Zustand der einzelnen Checkboxen darunter.
        # Erzwungen HIER statt nur über die Sichtbarkeit der Widgets, damit
        # eine im Labor gesetzte, aber ausgeblendete Checkbox nicht
        # versehentlich in einen Feldeinsatz mitgenommen wird. Nicht bei der
        # Auto-Config-Datensammlung (Tab 5) relevant, die hat ihre eigene,
        # unabhängige Sammeldauer/-logik.
        debug_active = not collection and self.debug_enabled_var.get()

        # Mitschnitt ebenfalls nur bei normalen Zählläufen (Tab 3) UND
        # aktivem Debug-Schalter. Bei der Auto-Config-Datensammlung wäre er
        # nutzlos und würde nur CPU kosten.
        recording_settings = None
        if debug_active and self.recording_enabled_var.get():
            recording_settings = self._validate_recording_settings()
            if recording_settings is None:
                return

        cmd = [sys.executable, "core.py", "--input", self.input_value]
        env = os.environ.copy()

        # Erkennungsmodell (Tab 1): --hef-path ist ein von hailo_apps selbst
        # definiertes CLI-Argument (core.py braucht dafür keine eigene
        # Argumentverarbeitung, siehe tabs/input_tab.py). Nur übergeben, wenn
        # tatsächlich eine Datei gewählt wurde - ohne das Argument wählt
        # hailo_apps automatisch sein Standardmodell zur erkannten
        # Hailo-Architektur, das gilt auch für die Auto-Config-Datensammlung
        # (Tab 5), deshalb außerhalb des if/else unten.
        model_path = getattr(self, "model_hef_path_var", None)
        model_path = model_path.get().strip() if model_path is not None else ""
        if model_path and os.path.isfile(model_path):
            cmd += ["--hef-path", model_path]

        if collection:
            # Auto-Config-Datensammlung: aktiviert das Punkte-Sammeln und nutzt
            # die Sammeldauer als Zeitlimit. Live-Vorschau bewusst AUS (stabiler
            # bei längeren Sammelläufen).
            env["AUTO_CONFIG_COLLECTION_ENABLED"] = "true"
            duration = self.collection_duration_var.get().strip()
            if duration:
                env["RUN_DURATION_SECONDS"] = duration
            self.collection_hint_var.set(
                f"⚠ Datensammlung AKTIV (Sammeldauer: {duration or 'unbegrenzt'}s). "
                f"Danach in Tab 2 auswerten (Clustering / Randraster).")
        else:
            # Normaler Zähllauf: KEIN Zeitlimit, außer der Nutzer trägt bei
            # aktivem Debug-Schalter in Tab 3 ausdrücklich eines ein. Keine
            # Datensammlung.
            if debug_active and self.use_frame_var.get():
                cmd.append("--use-frame")
            run_duration = self.run_duration_var.get().strip() if debug_active else ""
            if run_duration:
                env["RUN_DURATION_SECONDS"] = run_duration
            self.collection_hint_var.set("")

            # Debug-Dateien (ergebniss.csv, Bewegungsbilder) — zaehlung.csv
            # ist davon NICHT betroffen (siehe config.DEBUG_FILES_ENABLED),
            # die wird immer geschrieben.
            env["DEBUG_FILES_ENABLED"] = (
                "true" if (debug_active and self.debug_files_var.get()) else "false")

            if recording_settings is not None:
                env["RECORDING_ENABLED"] = "true"
                env["RECORDING_DIR"] = recording_settings["dir"]
                env["RECORDING_BITRATE_KBPS"] = str(recording_settings["bitrate"])
                env["RECORDING_FPS"] = str(recording_settings["fps"])
                env["RECORDING_SEGMENT_SECONDS"] = str(recording_settings["segment"])
                self.collection_hint_var.set(
                    "● Mitschnitt AKTIV - der genaue Zielordner und die Reichweite "
                    "stehen in der Ausgabe auf Seite 4.")

        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, env=env,
            )
        except Exception as e:
            messagebox.showerror("Fehler beim Starten", str(e), parent=self.root)
            self.process = None
            return

        threading.Thread(target=self._read_process_output, daemon=True).start()

        # LoRa-Sender als zweiten Subprozess mitstarten (liest die von core.py
        # geschriebene zaehlung.csv). Erst NACH erfolgreichem core-Start, damit
        # nicht gesendet wird, wenn die Zählung gar nicht läuft.
        if lora_settings is not None:
            interval_min, sensor_id = lora_settings
            self._start_lora_sender(interval_min, sensor_id)

        # MQTT-Sender ebenso - erst nach erfolgreichem core-Start.
        if mqtt_settings is not None:
            self._start_mqtt_sender(mqtt_settings)

        self.pipeline_status_var.set(f"Status: läuft (PID {self.process.pid})")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        if collection:
            self.autoconfig_start_button.configure(state="disabled")
            self.autoconfig_stop_button.configure(state="normal")
        self._show_page("4. Live-Auswertung")

    def _read_process_output(self):
        for line in self.process.stdout:
            self.output_queue.put(line)
        self.output_queue.put("__PROCESS_ENDED__")

    def _stop_pipeline(self):
        if self.process is None:
            return
        # LoRa- und MQTT-Sender zuerst beenden - ohne laufende Zählung soll
        # nicht weiter gesendet werden.
        self._stop_lora_sender()
        self._stop_mqtt_sender()
        self.process.send_signal(signal.SIGINT)
        self.pipeline_status_var.set("Status: wird beendet...")
        self.stop_button.configure(state="disabled")
        # Eskalation: Wenn der Prozess nach dem SIGINT nicht innerhalb weniger
        # Sekunden endet (z. B. weil er in nativem Hailo-/GStreamer-Code hängt),
        # hart nachfassen - erst SIGTERM, dann SIGKILL -, damit kein Zombie
        # zurückbleibt, der die PID/den Status blockiert.
        self.root.after(4000, self._escalate_stop)

    def _escalate_stop(self):
        if self.process is None:
            return
        if self.process.poll() is not None:
            return  # sauber beendet, nichts zu tun
        print("SIGINT wirkungslos - sende SIGTERM.")
        try:
            self.process.terminate()
        except Exception:
            pass
        self.root.after(3000, self._force_kill)

    def _force_kill(self):
        if self.process is None:
            return
        if self.process.poll() is not None:
            return
        print("SIGTERM wirkungslos - sende SIGKILL.")
        try:
            self.process.kill()
        except Exception:
            pass

    def _on_process_ended(self, exit_code=None):
        # Idempotent: kann sowohl über das stdout-Signal als auch über den
        # Liveness-Check (poll()) ausgelöst werden - der zweite Aufruf darf
        # nichts kaputtmachen.
        if self.process is None:
            return
        self.process = None

        # Falls LoRa- oder MQTT-Sender noch laufen (z. B. weil core.py
        # abgestürzt ist statt regulär gestoppt zu werden), ebenfalls beenden.
        self._stop_lora_sender()
        self._stop_mqtt_sender()

        if exit_code is None or exit_code == 0:
            self.pipeline_status_var.set("Status: gestoppt")
        elif exit_code < 0:
            # Negativer Code = durch Signal beendet (z. B. -2 = SIGINT beim
            # regulären Stopp, -6 = SIGABRT bei nativem terminate()/Crash).
            sig = -exit_code
            if sig == signal.SIGINT:
                self.pipeline_status_var.set("Status: gestoppt")
            else:
                self.pipeline_status_var.set(
                    f"Status: ABGESTÜRZT (Signal {sig}) - siehe Log. "
                    f"Neustart über 'Start' möglich.")
        else:
            self.pipeline_status_var.set(
                f"Status: ABGESTÜRZT (Exit {exit_code}) - siehe Log. "
                f"Neustart über 'Start' möglich.")

        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        # Auch die Auto-Config-Buttons (Tab 5) zurücksetzen, falls der Lauf von
        # dort gestartet wurde.
        if hasattr(self, "autoconfig_start_button"):
            self.autoconfig_start_button.configure(state="normal")
            self.autoconfig_stop_button.configure(state="disabled")
