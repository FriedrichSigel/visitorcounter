"""
tabs/lora_controls.py — LoRa-Abschnitt von Seite 3 (Aufbau, Validierung,
Hinweistext, Subprozess-Start/Stop des LoRa-Senders). Eigene Datei aus
demselben Grund wie tabs/recording_controls.py: ein abgeschlossenes Thema,
das start_tab.py nur über _build_lora_section() einbindet. Siehe
tabs/__init__.py für die Mixin-Begründung.
"""

import json
import signal
import subprocess
import sys
import threading

import customtkinter as ctk
import ctk_dialogs as messagebox

import lora_message

from .constants import ROI_CONFIG_PATH, ZAEHLUNG_CSV, LORA_HINT_HEIGHT_OFF, LORA_HINT_HEIGHT_ON


class LoraControlsMixin:
    """Checkbox + Einstellungen für den LoRa-Versand (Dragino LA66), inkl.
    Struktur-Hinweisbox und Subprozess-Verwaltung von lora_send_loop.py."""

    def _build_lora_section(self, frame):
        """Baut den LoRa-Abschnitt in `frame` (Tab 3) auf.

        Läuft als eigener Subprozess (lora_send_loop.py --live-counts), der
        die von core.py geschriebene zaehlung.csv liest - die Zähl-Pipeline
        selbst bleibt davon unberührt (bewusst entkoppelt, siehe
        HANDOFF.md/ToDo.md).
        """
        lora_frame = ctk.CTkFrame(frame, corner_radius=8)
        lora_frame.pack(anchor="w", fill="x", pady=(0, 15))
        ctk.CTkCheckBox(
            lora_frame, text="Daten per LoRa senden (LA66)",
            variable=self.lora_enabled_var, command=self._on_lora_toggle,
            font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        lora_row = ctk.CTkFrame(lora_frame, fg_color="transparent")
        lora_row.pack(anchor="w", padx=12, pady=(0, 6))
        ctk.CTkLabel(lora_row, text="Sende-Intervall (Minuten):").pack(side="left")
        self.lora_interval_entry = ctk.CTkEntry(
            lora_row, textvariable=self.lora_interval_var, width=60)
        self.lora_interval_entry.pack(side="left", padx=(5, 20))
        ctk.CTkLabel(lora_row, text="Sensor-ID:").pack(side="left")
        self.lora_sensor_entry = ctk.CTkEntry(
            lora_row, textvariable=self.lora_sensor_id_var, width=60)
        self.lora_sensor_entry.pack(side="left", padx=5)

        # Hinweis mit der Struktur der Nachricht - richtet sich nach der
        # Konfiguration (roi_config.json). Monospace, damit die Byte-Tabelle
        # ausgerichtet bleibt.
        #
        # Bewusst eine CTkTextbox statt eines CTkLabel: das Label war breiter
        # als die scrollbare Seite, wurde deshalb rechts abgeschnitten
        # ("Inaktive Klassen belegen il...") und hat das Layout der
        # nachfolgenden Abschnitte zerschossen. Eine Textbox hat eine feste
        # Größe, scrollt ihren Inhalt selbst (waagerecht dank wrap="none") und
        # lässt den Rest der Seite dadurch in Ruhe. read-only über state.
        self.lora_hint_box = ctk.CTkTextbox(
            lora_frame, height=LORA_HINT_HEIGHT_OFF, wrap="none", activate_scrollbars=True,
            text_color=("gray30", "gray70"), font=ctk.CTkFont(family="Courier", size=11))
        self.lora_hint_box.pack(anchor="w", fill="x", padx=12, pady=(4, 4))
        self.lora_hint_box.configure(state="disabled")
        ctk.CTkButton(
            lora_frame, text="Struktur aus Konfiguration aktualisieren",
            command=self._refresh_lora_hint, width=280, height=26,
            fg_color="transparent", border_width=1).pack(anchor="w", padx=12, pady=(0, 10))

        # Hint aktualisiert sich mit, wenn Intervall/Sensor-ID geändert werden.
        self.lora_interval_var.trace_add("write", lambda *_: self._refresh_lora_hint())
        self.lora_sensor_id_var.trace_add("write", lambda *_: self._refresh_lora_hint())
        self._on_lora_toggle()   # setzt Feld-Zustände + baut den Hint einmal auf

    def _on_lora_toggle(self):
        """Aktiviert/deaktiviert die LoRa-Eingabefelder und baut den Hint neu."""
        state = "normal" if self.lora_enabled_var.get() else "disabled"
        # Felder existieren erst nach _build_start_tab - defensiv prüfen.
        if hasattr(self, "lora_interval_entry"):
            self.lora_interval_entry.configure(state=state)
            self.lora_sensor_entry.configure(state=state)
        self._refresh_lora_hint()
        # Die Hinweisbox ändert beim Umschalten ihre Höhe; alles darunter rutscht
        # und muss neu gezeichnet werden (sonst bleiben Restflächen schwarz).
        if hasattr(self, "page_frames"):
            self.root.after(20, lambda: self._redraw_tree(self.page_frames["3. Start"]))

    def _load_roi_config(self):
        """Liest roi_config.json (für den Struktur-Hint). Fällt bei Fehler auf
        eine leere Standardstruktur zurück, ohne die GUI zu stören."""
        try:
            with open(ROI_CONFIG_PATH) as f:
                return json.load(f)
        except (OSError, ValueError):
            return {"mode": "line", "classes": list(lora_message.CANONICAL_CLASSES)}

    def _refresh_lora_hint(self):
        """Baut den Hinweistext mit der Nachrichtenstruktur neu - abhängig von
        der aktuellen Konfiguration, dem gewählten Intervall und der Sensor-ID."""
        if not hasattr(self, "lora_hint_box"):
            return
        if not self.lora_enabled_var.get():
            self._set_lora_hint(
                "LoRa-Versand aus. Aktivieren, um die Nachrichtenstruktur "
                "und das Sende-Intervall zu sehen.", LORA_HINT_HEIGHT_OFF)
            return

        cfg = self._load_roi_config()
        interval = self.lora_interval_var.get().strip()
        interval_display = interval if interval else "?"
        try:
            sensor_id = int(self.lora_sensor_id_var.get().strip() or "0")
        except ValueError:
            sensor_id = 0

        # Aktuelle Zählerstände (falls schon vorhanden) mit anzeigen.
        if cfg.get("mode") == "multi_roi":
            hint = lora_message.describe_multi_roi_structure(
                cfg, interval_minutes=interval_display, sensor_id=sensor_id,
                counts_csv=ZAEHLUNG_CSV)
        else:
            counts_in, counts_out = lora_message.read_counts_from_zaehlung(
                ZAEHLUNG_CSV, cfg.get("classes", []))
            hint = lora_message.describe_structure(
                cfg, interval_minutes=interval_display, sensor_id=sensor_id,
                counts_in=counts_in, counts_out=counts_out)
        self._set_lora_hint(hint, LORA_HINT_HEIGHT_ON)

    def _set_lora_hint(self, text, height):
        """Schreibt Text in die (sonst schreibgeschützte) Hinweis-Textbox und
        passt ihre Höhe an - kurz bei ausgeschaltetem LoRa, hoch genug für die
        vollständige Byte-Tabelle bei eingeschaltetem."""
        box = self.lora_hint_box
        box.configure(state="normal", height=height)
        box.delete("1.0", "end")
        box.insert("1.0", text)
        box.configure(state="disabled")

    def _validate_lora_settings(self):
        """Prüft Intervall und Sensor-ID vor dem Start. Rückgabe: (interval_min,
        sensor_id) oder None bei ungültiger Eingabe (Dialog wurde gezeigt)."""
        interval_raw = self.lora_interval_var.get().strip()
        try:
            interval = int(interval_raw)
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Ungültiges Intervall",
                "Bitte ein Sende-Intervall in ganzen Minuten (> 0) angeben.",
                parent=self.root)
            return None
        if interval < 2:
            # EU868-Duty-Cycle 1 % - unter ~2 min riskiert man Verstöße.
            if not messagebox.askyesno(
                    "Sehr kurzes Intervall",
                    f"Ein Intervall von {interval} min kann den EU868-Duty-Cycle "
                    f"(1 %) verletzen. Trotzdem verwenden?", parent=self.root):
                return None
        try:
            sensor_id = int(self.lora_sensor_id_var.get().strip())
            if not (0 <= sensor_id <= 255):
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Ungültige Sensor-ID",
                "Die Sensor-ID muss eine ganze Zahl zwischen 0 und 255 sein.",
                parent=self.root)
            return None
        return interval, sensor_id

    def _start_lora_sender(self, interval_min, sensor_id):
        """Startet lora_send_loop.py --live-counts als eigenen Subprozess.
        Dessen Ausgabe wird (mit Präfix) in dasselbe Live-Log geleitet."""
        cmd = [
            sys.executable, "lora_send_loop.py", "--live-counts",
            "--pause", str(interval_min),
            "--sensor-id", str(sensor_id),
            "--config", ROI_CONFIG_PATH,
            "--counts-csv", ZAEHLUNG_CSV,
            # Wird nur aufgerufen, nachdem core.py erfolgreich gestartet ist -
            # setzt die Status-Bits für Kamera/Hailo im Frame (Byte 4).
            "--pipeline-ok",
        ]
        try:
            self.lora_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
        except Exception as e:
            # LoRa-Fehler darf den Zähllauf nicht abbrechen - nur melden.
            self.output_queue.put(f"[LoRa] Start fehlgeschlagen: {e}\n")
            self.lora_process = None
            return
        threading.Thread(target=self._read_lora_output, daemon=True).start()
        self.output_queue.put(
            f"[LoRa] Sender gestartet (Intervall {interval_min} min, "
            f"Sensor-ID {sensor_id}).\n")

    def _read_lora_output(self):
        for line in self.lora_process.stdout:
            self.output_queue.put(f"[LoRa] {line}")
        self.output_queue.put("__LORA_ENDED__")

    def _stop_lora_sender(self):
        """Beendet den LoRa-Subprozess (SIGINT, wie Strg-C), falls er läuft."""
        if self.lora_process is None:
            return
        try:
            self.lora_process.send_signal(signal.SIGINT)
        except Exception:
            pass
