"""
app.py - zentrale Steuer-App: ein Fenster mit Sidebar-Navigation (statt
Tabs), um die gesamte Pipeline zu bedienen, ohne zwischen mehreren
Terminals/Skripten zu wechseln. UI-Bibliothek: customtkinter (dunkles
Design mit blauen Akzenten).

    1. Input             - Videodatei, USB- oder Pi-Kamera wählen
    2. Konfiguration      - Zählgeometrie setzen (nutzt roi_config_app.RoiConfigApp),
                            inkl. manueller Verfahren (Linie / ROI / Mehrere Flächen)
                            und der Auto-Verfahren (Clustering / Randraster)
    3. Start              - core.py als Subprozess starten/stoppen (normaler Zähllauf,
                            standardmäßig OHNE Zeitlimit)
    4. Live-Auswertung    - Konsolen-Ausgabe live mitlesen + aktuelle Zählerstände
    5. Auto-Konfiguration - Datensammlung für die Auto-Verfahren: Start-/Endpunkte
                            sammeln (mit Zeitlimit), danach in Tab 2 auswerten

Ersetzt NICHT die einzelnen Skripte - core.py, roi_config_app.py,
auto_config*.py bleiben eigenständig auf der Kommandozeile nutzbar.

Nutzung:
    python app.py

Voraussetzung: customtkinter (pip install customtkinter --break-system-packages).

Aufbau dieser Datei:
    MainApp bündelt nur noch das Fenster selbst (Sidebar, Navigation,
    Autostart/Aufwärmlauf, Design-Umschaltung). Jede Seite lebt als eigenes
    Mixin in tabs/ und wird unten eingemischt - Begründung und Übersicht in
    tabs/__init__.py bzw. docs/entwicklung/cleancode.md.
"""

import argparse
import os
import queue
import threading
import tkinter as tk

import customtkinter as ctk
import ctk_dialogs as messagebox   # CustomTkinter-Dialoge im App-Design

import config as app_config
import warmup
from tabs import settings_store
from tabs.constants import WINDOW_WIDTH, WINDOW_HEIGHT, SIDEBAR_WIDTH, CONTENT_WIDTH, ROI_CONFIG_PATH
from tabs.input_tab import InputTabMixin
from tabs.config_tab import ConfigTabMixin
from tabs.recording_controls import RecordingControlsMixin
from tabs.lora_controls import LoraControlsMixin
from tabs.mqtt_controls import MqttControlsMixin
from tabs.pipeline_control import PipelineControlMixin
from tabs.start_tab import StartTabMixin
from tabs.output_tab import OutputTabMixin
from tabs.autoconfig_tab import AutoConfigTabMixin

PAGE_NAMES = ["1. Input", "2. Konfiguration", "3. Start", "4. Live-Auswertung"]
if app_config.SHOW_AUTO_CONFIG:
    PAGE_NAMES.append("5. Auto-Konfiguration")

# Einmalig beim Modul-Import geladen: bestimmt sowohl den Appearance-Mode
# (muss VOR dem ersten ctk.CTk() feststehen) als auch die Startwerte aller
# Bedienelemente in MainApp.__init__ (siehe dort). Fehlt app_settings.json,
# legt load_settings() sie mit den aktuellen Default-Werten neu an.
_settings = settings_store.load_settings()

ctk.set_appearance_mode(_settings["appearance_mode"])
ctk.set_default_color_theme("blue")


class MainApp(
    InputTabMixin, ConfigTabMixin,
    RecordingControlsMixin, LoraControlsMixin, MqttControlsMixin,
    PipelineControlMixin, StartTabMixin,
    OutputTabMixin, AutoConfigTabMixin,
):
    """
    Fenster-Klammer: Sidebar, Seitennavigation, Autostart/Aufwärmlauf,
    Design-Umschaltung. Die eigentlichen Seiteninhalte kommen aus den oben
    eingemischten Tab-Klassen (tabs/) - diese Klasse kennt nur, DASS es sie
    gibt (über die _build_*_tab()-Methoden), nicht WIE sie aufgebaut sind.
    """

    def __init__(self, root, autostart=False):
        self.root = root
        self.root.title("Besucherzähler-Steuerung")
        # --autostart (siehe start_app.sh): startet die Zähl-Pipeline
        # automatisch mit dem Standard-Input (USB), sobald das Fenster steht
        # und ein eventueller Aufwärmlauf durch ist. Für den unbeaufsichtigten
        # Start beim Hochfahren des Geräts.
        self.autostart = autostart

        # Zuletzt gespeicherte Einstellungen (siehe tabs/settings_store.py) -
        # dienen unten als Startwert jedes Bedienelements, das mit dem
        # Stromausfall überstehen soll (Input-Quelle, alles auf Seite 3,
        # Design). self.settings wird danach bei JEDER Änderung eines dieser
        # Elemente aktualisiert und neu geschrieben (_wire_settings_autosave).
        self.settings = _settings

        # Feste Layout-Maße. Die gesamte App leitet ihre Breiten aus WINDOW_WIDTH
        # ab (1/5 Sidebar, 4/5 Content; in Tab 2 davon wiederum 3/5 Frame + 1/5
        # Konfig). Das Fenster wird in der Breite NICHT vergrößerbar gemacht,
        # damit keine Komponente die App unbeabsichtigt breiter zieht.
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        # Höhe darf wachsen (Scrollbereiche), Breite bleibt fest.
        self.root.minsize(WINDOW_WIDTH, 500)
        self.root.maxsize(WINDOW_WIDTH, self.root.winfo_screenheight())

        self.input_value = None      # Pfad zur Videodatei, oder "usb"/"rpi"
        self.process = None          # subprocess.Popen von core.py, solange die Pipeline läuft
        self.lora_process = None     # subprocess.Popen von lora_send_loop.py (nur wenn LoRa aktiv)
        self.output_queue = queue.Queue()

        # Auto-Config-Datensammlung (Tab 5): Sammeldauer als Zeitlimit. Nicht
        # Teil von app_settings.json (siehe settings_store.py) - Tab 5 ist
        # ein einmaliger Sammelvorgang, kein Dauerzustand wie die übrigen
        # Seite-3-Optionen.
        self.collection_duration_var = tk.StringVar(value="300")
        # Optionales Zeitlimit für normale Zählläufe (Tab 3). Leer = kein Limit
        # (Standard). Nur setzen, wer einen Lauf bewusst zeitlich begrenzen will.
        self.run_duration_var = tk.StringVar(value=self.settings["run_duration"])

        # --- LoRa-Versand (Tab 3) ---
        # An/aus, Sende-Intervall (Minuten, Pause nach erfolgreichem Uplink)
        # und Sensor-ID (Byte 1 der Nachricht). Wird beim Start als eigener
        # Subprozess (lora_send_loop.py --live-counts) mitgestartet.
        # --- Aufwärmlauf (einmal pro Systemstart) ---
        # Der erste Pipeline-Start nach einem Neustart dauert lange. Die App
        # faehrt die Pipeline deshalb beim ersten Start nach dem Booten einmal
        # kurz hoch und wieder herunter, damit spaeter niemand vor einer
        # scheinbar haengenden Oberflaeche sitzt. Details: warmup.py
        self.warmup_running = False
        self.warmup_status_var = tk.StringVar(value="")

        # --- Mitschnitt (Tab 3) ---
        # Zeichnet parallel zum Zähllauf ein Video mit eingebrannter Uhrzeit
        # auf, um die Zählergebnisse hinterher am Bildmaterial zu prüfen.
        # Wird core.py über Umgebungsvariablen mitgegeben (siehe config.py).
        self.recording_enabled_var = tk.BooleanVar(value=self.settings["recording_enabled"])
        self.recording_dir_var = tk.StringVar(value=self.settings["recording_dir"])
        self.recording_bitrate_var = tk.StringVar(value=self.settings["recording_bitrate"])
        self.recording_fps_var = tk.StringVar(value=self.settings["recording_fps"])
        self.recording_segment_var = tk.StringVar(value=self.settings["recording_segment"])

        self.lora_enabled_var = tk.BooleanVar(value=self.settings["lora_enabled"])
        self.lora_interval_var = tk.StringVar(value=self.settings["lora_interval"])
        self.lora_sensor_id_var = tk.StringVar(value=self.settings["lora_sensor_id"])

        # --- MQTT-Versand (Tab 3) ---
        # Alternative/Ergänzung zu LoRa: schickt dieselben Zählwerte per MQTT
        # an den Stadtwerke-Server. Läuft ebenfalls als eigener Subprozess
        # (mqtt_send_loop.py), der die von core.py geschriebene zaehlung.csv
        # liest - die Zähl-Pipeline bleibt unberührt. Broker-Adresse ist die
        # feste IP des Server-Pi; --uebergaenge sendet die volle Übergangs-
        # matrix (von-Feld → nach-Feld je Klasse) statt des 18-Byte-Frames.
        self.mqtt_process = None
        self.mqtt_enabled_var = tk.BooleanVar(value=self.settings["mqtt_enabled"])
        self.mqtt_broker_var = tk.StringVar(value=self.settings["mqtt_broker"])
        self.mqtt_port_var = tk.StringVar(value=self.settings["mqtt_port"])
        self.mqtt_interval_var = tk.StringVar(value=self.settings["mqtt_interval"])
        self.mqtt_sensor_id_var = tk.StringVar(value=self.settings["mqtt_sensor_id"])
        self.mqtt_transitions_var = tk.BooleanVar(value=self.settings["mqtt_transitions"])

        # --- Sidebar links (1/5 der Fensterbreite) ---
        self.sidebar = ctk.CTkFrame(root, width=SIDEBAR_WIDTH, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header.pack(fill="x", padx=(20, 10), pady=(25, 30))
        ctk.CTkLabel(header, text="Besucherzähler",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        is_dark = ctk.get_appearance_mode() == "Dark"
        # Einfarbige Textsymbole statt Vollfarb-Emoji (z. B. 🌙): Windows
        # rendert Vollfarb-Emojis mit eigenem, weißem Hintergrund-Glyph statt
        # in text_color — auf dem schwarzen Knopf im Light-Mode sah das
        # kaputt aus.
        self.appearance_button = ctk.CTkButton(
            header, text="☀" if is_dark else "☾", width=40, height=40, corner_radius=20,
            font=ctk.CTkFont(size=18),
            # (Wert für Light-Mode, Wert für Dark-Mode): Knopf schwarz im
            # hellen Design, weiß im dunklen Design — jeweils Kontrast zum
            # Text der umgekehrten Farbe.
            fg_color=("black", "white"), text_color=("white", "black"),
            hover_color=("gray20", "gray80"),
            command=self._toggle_appearance_mode,
        )
        self.appearance_button.pack(side="right")

        self.nav_buttons = {}
        for name in PAGE_NAMES:
            btn = ctk.CTkButton(
                self.sidebar, text=name, anchor="w", corner_radius=6,
                fg_color="transparent", text_color=("gray10", "gray90"),
                hover_color=("gray80", "gray28"),
                command=lambda n=name: self._show_page(n),
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[name] = btn

        # --- Inhaltsbereich rechts (4/5 der Fensterbreite, feste Breite) ---
        self.content = ctk.CTkFrame(root, width=CONTENT_WIDTH, corner_radius=0, fg_color="transparent")
        self.content.pack(side="right", fill="both", expand=True)
        self.content.pack_propagate(False)

        self.page_frames = {name: ctk.CTkFrame(self.content, fg_color="transparent") for name in PAGE_NAMES}

        self._build_input_tab()
        self._build_config_tab()
        self._build_start_tab()
        self._build_output_tab()
        if app_config.SHOW_AUTO_CONFIG:
            self._build_autoconfig_tab()

        # Erst jetzt existieren alle Variablen (werden in den _build_*_tab()-
        # Aufrufen oben angelegt) - ab hier speichert jede Änderung sofort in
        # app_settings.json, siehe _wire_settings_autosave().
        self._wire_settings_autosave()

        self._show_page(PAGE_NAMES[0])

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._poll_output()

        # Noch keine Zählgeometrie gespeichert (z. B. ganz neues Gerät): die
        # App soll trotzdem einfach starten (Seite 1 "Input" ist ohnehin
        # PAGE_NAMES[0], also schon zu sehen) - nur auf die fehlende
        # Konfiguration hinweisen und die Pipeline NICHT automatisch starten,
        # weil sie sonst mit einer bedeutungslosen Default-Geometrie zählen
        # würde (siehe config.py _DEFAULT_ROI_CONFIG).
        self.config_missing = not os.path.isfile(ROI_CONFIG_PATH)
        if self.config_missing:
            self.root.after(300, self._warn_missing_config)

        # Aufwärmlauf anstossen, sobald die Oberflaeche steht (verzoegert,
        # damit das Fenster zuerst sichtbar ist).
        self.root.after(800, self._maybe_run_warmup)

        if self.autostart and not self.config_missing:
            self.root.after(1000, self._maybe_autostart_pipeline)

    def _warn_missing_config(self):
        messagebox.showwarning(
            "Konfiguration fehlt",
            "Bitte Besucherzähler konfigurieren.\n\n"
            "Es wurde noch keine Zählgeometrie gespeichert. Auf Seite 2 "
            "(Konfiguration) einen Frame laden, Zählmodus und -fläche(n) "
            "setzen und speichern - danach lässt sich die Pipeline starten.",
            parent=self.root)

    def _maybe_autostart_pipeline(self):
        """
        --autostart: startet die Zähl-Pipeline automatisch, sobald ein
        eventueller Aufwärmlauf durch ist (self.warmup_running wieder False).

        Läuft normalerweise gar kein Aufwärmlauf mehr, weil start_app.sh vorher
        schon 'python warmup.py' ausgeführt hat - dann greift dieser Check
        praktisch sofort. Rein zur Sicherheit (z. B. App manuell während des
        Bootens neu gestartet) wird trotzdem gewartet, statt die Warnung aus
        _start_pipeline() für einen laufenden Aufwärmlauf zu riskieren.
        """
        if self.warmup_running:
            self.root.after(1000, self._maybe_autostart_pipeline)
            return
        if self.process is not None:
            return  # lief inzwischen schon (z. B. manuell gestartet)
        self._start_pipeline()

    def _maybe_run_warmup(self):
        """
        Startet den Aufwärmlauf, falls seit dem Systemstart noch keiner lief.

        Laeuft in einem Hintergrund-Thread, damit die Oberflaeche bedienbar
        bleibt - der Lauf kann beim ersten Mal nach dem Booten bis zu zwei
        Minuten dauern.
        """
        if not warmup.needs_warmup():
            return

        self.warmup_running = True
        self.warmup_status_var.set(
            "Aufwärmlauf läuft - die Pipeline wird einmal kurz gestartet, damit "
            "spätere Starts schnell gehen. Es öffnet sich kurz ein "
            "Vorschaufenster. Bitte solange nicht starten.")

        def report(text):
            # Aus dem Thread heraus nicht direkt in Tk schreiben - ueber die
            # vorhandene Ausgabe-Queue und ein after() in den Hauptthread.
            self.output_queue.put(f"[Aufwärmlauf] {text}\n")
            self.root.after(0, lambda t=text: self.warmup_status_var.set(t))

        def worker():
            try:
                # Wärmt USB UND den aktuell in Tab 1 gewählten Input
                # nacheinander auf (siehe warmup.run_warmup_all) - beide
                # sollen nach dem Booten schnell starten, nicht nur der
                # zuerst genutzte.
                warmup.run_warmup_all(on_message=report)
            except Exception as exc:
                report(f"fehlgeschlagen: {exc}")
            finally:
                self.warmup_running = False
                # Meldung nach kurzer Zeit wieder ausblenden.
                self.root.after(8000, lambda: self.warmup_status_var.set(""))

        threading.Thread(target=worker, daemon=True).start()

    def _toggle_appearance_mode(self):
        """Wechselt zwischen dunklem und hellem Design. Betrifft die gesamte
        App (customtkinter-Einstellung ist global), inkl. eingebetteter
        RoiConfigApp in Tab 2."""
        is_dark = ctk.get_appearance_mode() == "Dark"
        new_mode = "light" if is_dark else "dark"
        ctk.set_appearance_mode(new_mode)
        self.appearance_button.configure(text="☾" if is_dark else "☀")
        self.settings["appearance_mode"] = new_mode
        settings_store.save_settings(self.settings)

    # -----------------------------------------------------------------
    # Einstellungen automatisch speichern (Stromausfall-sicher: siehe
    # tabs/settings_store.py - jede Änderung wird sofort geschrieben,
    # nicht erst beim Beenden).
    # -----------------------------------------------------------------
    def _wire_settings_autosave(self):
        """Hängt an jede in app_settings.json persistierte tk-Variable einen
        Schreib-Trace, der den neuen Wert sofort speichert."""
        self._settings_vars = {
            "input_mode": self.input_mode_var,
            "input_file_path": self.file_path_var,
            "model_hef_path": self.model_hef_path_var,
            "model_labels_path": self.model_labels_path_var,
            "debug_enabled": self.debug_enabled_var,
            "debug_files_enabled": self.debug_files_var,
            "verbose_console_enabled": self.verbose_console_var,
            "recording_enabled": self.recording_enabled_var,
            "recording_dir": self.recording_dir_var,
            "recording_bitrate": self.recording_bitrate_var,
            "recording_fps": self.recording_fps_var,
            "recording_segment": self.recording_segment_var,
            "use_frame": self.use_frame_var,
            "lora_enabled": self.lora_enabled_var,
            "lora_interval": self.lora_interval_var,
            "lora_sensor_id": self.lora_sensor_id_var,
            "mqtt_enabled": self.mqtt_enabled_var,
            "mqtt_broker": self.mqtt_broker_var,
            "mqtt_port": self.mqtt_port_var,
            "mqtt_interval": self.mqtt_interval_var,
            "mqtt_sensor_id": self.mqtt_sensor_id_var,
            "mqtt_transitions": self.mqtt_transitions_var,
            "run_duration": self.run_duration_var,
        }
        for key, var in self._settings_vars.items():
            var.trace_add("write", lambda *_args, k=key, v=var: self._on_setting_changed(k, v))

    def _on_setting_changed(self, key, var):
        try:
            value = var.get()
        except Exception:
            # z. B. leeres Zahlenfeld während des Tippens - überspringen statt
            # mit einem ungültigen Zwischenstand zu speichern.
            return
        self.settings[key] = value
        settings_store.save_settings(self.settings)

    def _show_page(self, name):
        for frame in self.page_frames.values():
            frame.pack_forget()
        self.page_frames[name].pack(fill="both", expand=True, padx=15, pady=15)
        for n, btn in self.nav_buttons.items():
            is_active = (n == name)
            btn.configure(fg_color=("gray75", "gray25") if is_active else "transparent")

        # Seite nach dem Einblenden einmal komplett neu zeichnen lassen.
        #
        # Hintergrund: alle fünf Seiten werden im __init__ gebaut, aber nur die
        # erste wird sofort gepackt. customtkinter zeichnet seine Widgets auf
        # interne Canvas-Elemente, und diese Zeichenoperation läuft bei einem
        # noch nicht eingeblendeten (unmapped) Widget gegen eine Größe von 1x1.
        # Ergebnis: Flächen bleiben schwarz oder werden nur teilweise gefüllt
        # (abgeschnittene Kopfleiste bei "Optionales Zeitlimit"), bis ein
        # <Enter>- oder <Configure>-Ereignis - also z. B. Mauszeiger drüber -
        # ein Neuzeichnen auslöst. Deshalb hier explizit anstoßen, sobald die
        # Seite tatsächlich sichtbar ist.
        self.root.after(20, lambda: self._redraw_tree(self.page_frames[name]))

    def _redraw_tree(self, widget):
        """Ruft rekursiv das interne Neuzeichnen jedes customtkinter-Widgets auf.

        Vor dem ersten Zeichnen müssen die Geometrie-Berechnungen abgeschlossen
        sein, sonst kennt das Widget seine endgültige Größe noch nicht und der
        Fehler wiederholt sich nur mit anderen Maßen.
        """
        try:
            self.root.update_idletasks()
        except Exception:
            return
        self._redraw_recursive(widget)

    def _redraw_recursive(self, widget):
        draw = getattr(widget, "_draw", None)
        if callable(draw):
            try:
                draw(no_color_updates=False)
            except Exception:
                # Einzelne Widgets dürfen scheitern, ohne den Rest der Seite
                # ungezeichnet zu lassen.
                pass
        try:
            children = widget.winfo_children()
        except Exception:
            return
        for child in children:
            self._redraw_recursive(child)

    def _on_close(self):
        if self.process is not None:
            if messagebox.askyesno("Beenden", "Die Pipeline läuft noch. Trotzdem beenden?", parent=self.root):
                self._stop_pipeline()
                self.root.after(1000, self.root.destroy)
            return
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description="Besucherzähler-Steuerung (GUI)")
    parser.add_argument(
        "--autostart", action="store_true",
        help="Zähl-Pipeline nach dem Öffnen automatisch starten (Input: USB). "
             "Für den unbeaufsichtigten Start beim Hochfahren, siehe start_app.sh.")
    args = parser.parse_args()

    root = ctk.CTk()
    MainApp(root, autostart=args.autostart)
    root.mainloop()


if __name__ == "__main__":
    main()
