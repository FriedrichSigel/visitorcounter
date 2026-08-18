"""
tabs/output_tab.py — Seite 4: Live-Konsolenausgabe + aktuelle Zählerstände.
Siehe tabs/__init__.py für die Mixin-Begründung.
"""

import csv
import os
import queue

import customtkinter as ctk

from .constants import ZAEHLUNG_CSV


class OutputTabMixin:
    """Seite 4: liest die Ausgabe-Queue (befüllt von core.py/LoRa/MQTT-
    Subprozessen, siehe pipeline_control.py/lora_controls.py/
    mqtt_controls.py) und die zaehlung.csv, zeigt beides live an."""

    def _build_output_tab(self):
        frame = self.page_frames["4. Live-Auswertung"]

        ctk.CTkLabel(frame, text="Live-Konsolenausgabe", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", pady=(0, 5))
        self.log_text = ctk.CTkTextbox(frame, height=320, fg_color="#151515", text_color="#4CAF50",
                                        font=ctk.CTkFont(family="Courier", size=12))
        self.log_text.pack(fill="both", expand=True, pady=(0, 10))

        ctk.CTkLabel(frame, text=f"Aktuelle Zählerstände (aus {ZAEHLUNG_CSV}, nur echte Übergänge)",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.counts_text = ctk.CTkTextbox(frame, height=140)
        self.counts_text.pack(fill="x")

    def _poll_output(self):
        try:
            while True:
                line = self.output_queue.get_nowait()
                if line == "__PROCESS_ENDED__":
                    self._on_process_ended()
                elif line == "__LORA_ENDED__":
                    # LoRa-Sender ist beendet (regulär oder Fehler) - Referenz
                    # freigeben, Rest läuft normal weiter.
                    self.lora_process = None
                    self.log_text.insert("end", "[LoRa] Sender beendet.\n")
                    self.log_text.see("end")
                elif line == "__MQTT_ENDED__":
                    # MQTT-Sender beendet - Referenz freigeben, Rest läuft weiter.
                    self.mqtt_process = None
                    self.log_text.insert("end", "[MQTT] Sender beendet.\n")
                    self.log_text.see("end")
                elif self._should_show_console_line(line):
                    self.log_text.insert("end", line)
                    self.log_text.see("end")
        except queue.Empty:
            pass

        # Liveness-Check: Auch wenn KEIN "__PROCESS_ENDED__" über stdout kam
        # (z. B. weil core.py durch einen nativen C++-Fehler hart abgestürzt
        # ist - terminate()/std::system_error -, ohne stdout sauber zu
        # schließen), erkennen wir hier direkt am Prozessstatus, dass er weg
        # ist. Ohne diesen Check bliebe die App auf "läuft (PID …)" hängen und
        # ein Neustart wäre blockiert.
        if self.process is not None:
            exit_code = self.process.poll()
            if exit_code is not None:
                self._on_process_ended(exit_code)

        self._refresh_counts()
        self.root.after(500, self._poll_output)

    def _should_show_console_line(self, line):
        """
        Blendet die "Frame count:"/"Detection:"-Zeilen aus core.py aus,
        solange nicht Debug UND "Frame-/Detection-Zeilen anzeigen" (Tab 3)
        beides aktiv sind — reduziert die Konsole im Normalbetrieb auf das
        Wesentliche (Status, Warnungen, [LoRa]/[MQTT]-Zeilen), ohne core.py
        selbst anzufassen oder etwas davon wegzulassen, was tatsächlich
        gebraucht wird.
        """
        if self.debug_enabled_var.get() and self.verbose_console_var.get():
            return True
        stripped = line.lstrip()
        return not (stripped.startswith("Frame count:") or stripped.startswith("Detection:"))

    def _refresh_counts(self):
        if not os.path.isfile(ZAEHLUNG_CSV):
            return
        try:
            with open(ZAEHLUNG_CSV, newline="") as f:
                rows = list(csv.DictReader(f))
        except (OSError, csv.Error):
            return

        tally = {}
        for row in rows:
            if row.get("is_transition") == "True":
                key = (row.get("label", "?"), row.get("direction", "?"))
                tally[key] = tally.get(key, 0) + 1

        self.counts_text.delete("1.0", "end")
        if not tally:
            self.counts_text.insert("end", "(noch keine Zählungen)")
        for (label, direction), count in sorted(tally.items()):
            self.counts_text.insert("end", f"{label}: {direction}: {count}\n")
