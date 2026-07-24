"""
Vergleichswerkzeug für Labortestläufe des Besucherzählsensors.

Zweck:
    Nach einem Laborlauf liegen zwei CSV-Dateien vor:
      - zaehlung.csv   — die Zählentscheidung je Objekt (Richtung, Übergang)
      - ergebniss.csv  — die zugehörige Spur (Start-/Endpunkt, Konfidenz)
    Beide sind über die Spalte display_id Zeile für Zeile gekoppelt.

    Dieses Werkzeug legt sie nebeneinander: einen Datensatz auswählen, seine
    Werte aus beiden Dateien im Klartext lesen und die Bewegung auf einer
    Fläche sehen, die den konfigurierten Zählzonen (roi_config.json)
    entspricht. So lässt sich prüfen, ob eine Zählentscheidung zum
    tatsächlichen Weg passt — die Grundlage der Genauigkeitsuntersuchung.

Kopplung Datensatz <-> Zeile:
    "Datensatz N" meint die N-te Datenzeile (1-basiert, ohne Kopfzeile) in
    BEIDEN Dateien. Stimmen die display_id einer Zeile nicht überein, wird das
    angezeigt statt stillschweigend gepaart — sonst vergliche man Äpfel mit
    Birnen.

Gestaltung:
    Eigenständiges Tkinter-Werkzeug, farblich und typografisch an die
    Steuer-App angelehnt (dunkle Fläche, ein ruhiger Blauton als Leitfarbe,
    Grün/Rot nur für Bedeutung: Übergang gezählt / nicht gezählt). Die Fläche
    ist der Star — Text bleibt zurückhaltend daneben.
"""

import csv
import json
import os
import tkinter as tk
from tkinter import filedialog, font as tkfont

# --- Farben -----------------------------------------------------------------
BG = "#1B2430"            # Grundfläche, tief und ruhig
PANEL = "#232F3E"         # abgesetzte Bedienfläche
CANVAS_BG = "#F5F7FA"     # helle Zeichenfläche — Kontrast zum dunklen Rahmen
INK = "#E7ECF2"           # heller Text auf dunklem Grund
INK_DIM = "#8A9BB0"       # Nebentext
ACCENT = "#3E9BE8"        # Leitfarbe
GREEN = "#3FB265"         # Übergang gezählt
RED = "#E0574B"           # kein Übergang
AMBER = "#E0A030"         # Warnung / Nichtübereinstimmung
GRID = "#D8DEE6"          # Rasterlinien auf der hellen Fläche

# Farben für die Zählzonen aus roi_config.json — dieselbe Reihenfolge wie im
# Konfigurationswerkzeug, damit ein Feld hier so aussieht wie dort.
REGION_FILLS = ["#DDEAF6", "#DCEEE2", "#FBE7CE", "#F6DCE7", "#EDEDED", "#F6D9D6"]
REGION_LINES = ["#3E9BE8", "#3FB265", "#E0A030", "#D6609A", "#9AA4AE", "#E0574B"]

# Bezugsauflösung — Spuren sind in Pixeln der Kamera gespeichert; die ROI-Punkte
# relativ (0..1). Beide müssen auf dieselbe Fläche. Wenn keine Auflösung
# gesetzt ist, wird sie aus den Daten geschätzt.
DEFAULT_W, DEFAULT_H = 1280, 720


class VergleichApp:
    def __init__(self, root):
        self.root = root
        root.title("Labortest — Datensätze vergleichen")
        root.configure(bg=BG)
        root.geometry("1240x760")
        root.minsize(1040, 640)

        self.zaehlung = []       # Liste dicts
        self.ergebniss = []      # Liste dicts
        self.regions = []        # aus roi_config.json
        self.in_field = None
        self.index = 0           # 0-basiert intern
        self.frame_w = DEFAULT_W
        self.frame_h = DEFAULT_H
        self.show_history = False

        self._build_fonts()
        self._build_layout()
        self._set_loaded(False)

    # -- Schrift -------------------------------------------------------------
    def _build_fonts(self):
        self.f_title = tkfont.Font(family="DejaVu Sans", size=15, weight="bold")
        self.f_label = tkfont.Font(family="DejaVu Sans", size=10)
        self.f_value = tkfont.Font(family="DejaVu Sans", size=11, weight="bold")
        self.f_mono = tkfont.Font(family="DejaVu Sans Mono", size=10)
        self.f_big = tkfont.Font(family="DejaVu Sans Mono", size=20, weight="bold")

    # -- Aufbau --------------------------------------------------------------
    def _build_layout(self):
        # Kopfzeile mit den drei Dateiauswahlen
        top = tk.Frame(self.root, bg=PANEL)
        top.pack(side="top", fill="x")

        self.path_vars = {}
        self._file_row(top, "Zählung (zaehlung.csv)", "zaehlung",
                       [("CSV", "*.csv")])
        self._file_row(top, "Ergebnis (ergebniss.csv)", "ergebniss",
                       [("CSV", "*.csv")])
        self._file_row(top, "Konfiguration (roi_config.json)", "config",
                       [("JSON", "*.json")], optional=True)

        action = tk.Frame(top, bg=PANEL)
        action.pack(fill="x", padx=14, pady=(4, 12))
        self.load_button = tk.Button(
            action, text="Daten laden", command=self.load_data,
            bg=ACCENT, fg="white", relief="flat", font=self.f_value,
            activebackground="#2F7CBE", activeforeground="white",
            padx=18, pady=6, cursor="hand2")
        self.load_button.pack(side="left")
        self.load_status = tk.Label(action, text="", bg=PANEL, fg=INK_DIM,
                                    font=self.f_label)
        self.load_status.pack(side="left", padx=14)

        # Hauptbereich: links Fläche, rechts Werte
        main = tk.Frame(self.root, bg=BG)
        main.pack(side="top", fill="both", expand=True, padx=14, pady=(6, 14))
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=0, minsize=360)
        main.grid_rowconfigure(0, weight=1)

        # Zeichenfläche
        canvas_wrap = tk.Frame(main, bg=PANEL, bd=0)
        canvas_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.canvas = tk.Canvas(canvas_wrap, bg=CANVAS_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas.bind("<Configure>", lambda e: self._draw())

        # Rechte Spalte
        side = tk.Frame(main, bg=BG)
        side.grid(row=0, column=1, sticky="nsew")

        self._build_navigation(side)
        self._build_detail(side)
        self._build_legend(side)

    def _file_row(self, parent, label, key, types, optional=False):
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", padx=14, pady=(12 if key == "zaehlung" else 4, 0))
        tk.Label(row, text=label, bg=PANEL, fg=INK, font=self.f_label,
                 width=30, anchor="w").pack(side="left")
        var = tk.StringVar()
        self.path_vars[key] = var
        entry = tk.Entry(row, textvariable=var, bg="#1B2430", fg=INK,
                         insertbackground=INK, relief="flat", font=self.f_mono)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=4)
        tk.Button(row, text="Durchsuchen", command=lambda: self._pick(key, types),
                  bg="#33465C", fg=INK, relief="flat", font=self.f_label,
                  activebackground="#3E556F", activeforeground="white",
                  padx=10, pady=3, cursor="hand2").pack(side="left")

    def _pick(self, key, types):
        path = filedialog.askopenfilename(filetypes=types + [("Alle", "*.*")])
        if path:
            self.path_vars[key].set(path)

    def _build_navigation(self, parent):
        nav = tk.Frame(parent, bg=PANEL)
        nav.pack(fill="x", pady=(0, 10))

        head = tk.Frame(nav, bg=PANEL)
        head.pack(fill="x", padx=14, pady=(12, 4))
        tk.Label(head, text="Datensatz", bg=PANEL, fg=INK,
                 font=self.f_title).pack(side="left")
        self.count_label = tk.Label(head, text="", bg=PANEL, fg=INK_DIM,
                                    font=self.f_label)
        self.count_label.pack(side="right")

        ctr = tk.Frame(nav, bg=PANEL)
        ctr.pack(fill="x", padx=14, pady=(0, 12))
        self.prev_button = tk.Button(
            ctr, text="◀  Zurück", command=self.prev, bg="#33465C", fg=INK,
            relief="flat", font=self.f_value, activebackground="#3E556F",
            activeforeground="white", padx=12, pady=6, cursor="hand2")
        self.prev_button.pack(side="left")

        self.index_var = tk.StringVar()
        self.index_entry = tk.Entry(
            ctr, textvariable=self.index_var, width=6, justify="center",
            bg="#1B2430", fg=INK, insertbackground=INK, relief="flat",
            font=self.f_value)
        self.index_entry.pack(side="left", padx=8, ipady=5)
        self.index_entry.bind("<Return>", lambda e: self._goto_typed())

        self.next_button = tk.Button(
            ctr, text="Weiter  ▶", command=self.next, bg="#33465C", fg=INK,
            relief="flat", font=self.f_value, activebackground="#3E556F",
            activeforeground="white", padx=12, pady=6, cursor="hand2")
        self.next_button.pack(side="left")

        self.history_button = tk.Button(
            nav, text="Frühere Datensätze einblenden", command=self.toggle_history,
            bg="#33465C", fg=INK, relief="flat", font=self.f_label,
            activebackground="#3E556F", activeforeground="white",
            padx=10, pady=5, cursor="hand2")
        self.history_button.pack(fill="x", padx=14, pady=(0, 6))

        # Nur gezählte Übergänge durchgehen: bei einem Zähllauf sind die
        # meisten Datensätze "kein Wechsel"; zum Prüfen der Zählgenauigkeit
        # zählt vor allem, ob die echten Übergänge stimmen.
        self.only_transitions = tk.BooleanVar(value=False)
        self.trans_check = tk.Checkbutton(
            nav, text="Nur gezählte Übergänge", variable=self.only_transitions,
            command=self._on_filter_change, bg=PANEL, fg=INK,
            selectcolor="#1B2430", activebackground=PANEL, activeforeground=INK,
            font=self.f_label, anchor="w")
        self.trans_check.pack(fill="x", padx=12, pady=(0, 12))

    def _build_detail(self, parent):
        det = tk.Frame(parent, bg=PANEL)
        det.pack(fill="both", expand=True, pady=(0, 10))

        # Übergangs-Kopf: die zentrale Aussage gross
        self.transition_label = tk.Label(
            det, text="—", bg=PANEL, fg=INK, font=self.f_big,
            anchor="w", justify="left", wraplength=330)
        self.transition_label.pack(fill="x", padx=14, pady=(14, 2))
        self.transition_sub = tk.Label(
            det, text="", bg=PANEL, fg=INK_DIM, font=self.f_label, anchor="w")
        self.transition_sub.pack(fill="x", padx=14, pady=(0, 12))

        # Wertetabelle
        self.detail_rows = {}
        for feld in ["display_id", "Klasse", "Konfidenz", "Zeit",
                     "Startpunkt", "Endpunkt", "Distanz", "Art (kind)"]:
            r = tk.Frame(det, bg=PANEL)
            r.pack(fill="x", padx=14, pady=2)
            tk.Label(r, text=feld, bg=PANEL, fg=INK_DIM, font=self.f_label,
                     width=13, anchor="w").pack(side="left")
            val = tk.Label(r, text="", bg=PANEL, fg=INK, font=self.f_value,
                           anchor="w", justify="left", wraplength=210)
            val.pack(side="left", fill="x", expand=True)
            self.detail_rows[feld] = val

    def _build_legend(self, parent):
        leg = tk.Frame(parent, bg=PANEL)
        leg.pack(fill="x")
        tk.Label(leg, text="Legende", bg=PANEL, fg=INK,
                 font=self.f_title).pack(anchor="w", padx=14, pady=(12, 6))
        items = [
            (GREEN, "Startpunkt der Spur"),
            (RED, "Endpunkt der Spur"),
            (ACCENT, "aktuelle Bewegung"),
            (INK_DIM, "frühere Datensätze (optional)"),
        ]
        for color, text in items:
            r = tk.Frame(leg, bg=PANEL)
            r.pack(fill="x", padx=14, pady=2)
            c = tk.Canvas(r, width=16, height=16, bg=PANEL, highlightthickness=0)
            c.create_oval(3, 3, 13, 13, fill=color, outline="")
            c.pack(side="left")
            tk.Label(r, text=text, bg=PANEL, fg=INK_DIM,
                     font=self.f_label).pack(side="left", padx=6)
        tk.Frame(leg, bg=PANEL, height=12).pack()

    # -- Laden ---------------------------------------------------------------
    def load_data(self):
        z_path = self.path_vars["zaehlung"].get().strip()
        e_path = self.path_vars["ergebniss"].get().strip()
        c_path = self.path_vars["config"].get().strip()

        if not z_path or not e_path:
            self._status("Bitte beide CSV-Dateien angeben.", AMBER)
            return

        try:
            self.zaehlung = self._read_csv(z_path)
            self.ergebniss = self._read_csv(e_path)
        except (OSError, csv.Error) as exc:
            self._status(f"CSV nicht lesbar: {exc}", RED)
            return

        if not self.zaehlung or not self.ergebniss:
            self._status("Mindestens eine Datei enthält keine Datensätze.", RED)
            return

        # Konfiguration ist optional.
        self.regions = []
        self.in_field = None
        if c_path:
            try:
                with open(c_path) as f:
                    cfg = json.load(f)
                self.regions = cfg.get("regions", [])
                self.in_field = cfg.get("in_field")
            except (OSError, json.JSONDecodeError) as exc:
                self._status(f"Konfiguration übersprungen: {exc}", AMBER)

        self._determine_frame_size()
        self.index = 0
        self._set_loaded(True)
        self._update()

        n = min(len(self.zaehlung), len(self.ergebniss))
        extra = ""
        if len(self.zaehlung) != len(self.ergebniss):
            extra = (f"  Achtung: unterschiedliche Zeilenzahl "
                     f"({len(self.zaehlung)} / {len(self.ergebniss)}).")
        self._status(f"{n} Datensätze geladen. Fläche {self.frame_w}×{self.frame_h}."
                     + extra, GREEN if not extra else AMBER)

    def _read_csv(self, path):
        with open(path, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))

    def _determine_frame_size(self):
        """Bezugsfläche festlegen: aus den Koordinaten, mind. Default."""
        xs, ys = [], []
        for r in self.ergebniss:
            for kx, ky in (("start_x", "start_y"), ("end_x", "end_y")):
                try:
                    xs.append(int(float(r[kx])))
                    ys.append(int(float(r[ky])))
                except (KeyError, ValueError):
                    pass
        # Auf die naechste "runde" Kameraaufloesung aufrunden, nicht knapp auf
        # den groessten Punkt — sonst klebt die Spur am Rand.
        max_x = max(xs) if xs else DEFAULT_W
        max_y = max(ys) if ys else DEFAULT_H
        self.frame_w = DEFAULT_W if max_x <= DEFAULT_W else max_x + 20
        self.frame_h = DEFAULT_H if max_y <= DEFAULT_H else max_y + 20

    # -- Navigation ----------------------------------------------------------
    def _count(self):
        return min(len(self.zaehlung), len(self.ergebniss))

    def next(self):
        target = self._step(self.index, +1)
        if target is not None:
            self.index = target
            self._update()

    def prev(self):
        target = self._step(self.index, -1)
        if target is not None:
            self.index = target
            self._update()

    def _step(self, start, direction):
        """Nächster/voriger Index; überspringt Nicht-Übergänge, wenn der Filter
        aktiv ist. None, wenn es in der Richtung keinen passenden mehr gibt."""
        i = start + direction
        while 0 <= i < self._count():
            if not self.only_transitions.get() or self._is_transition(i):
                return i
            i += direction
        return None

    def _is_transition(self, i):
        return str(self.zaehlung[i].get("is_transition", "")).lower() == "true"

    def _on_filter_change(self):
        # Steht der Cursor gerade auf einem Nicht-Übergang, zum nächsten
        # passenden springen — sonst zeigt der Filter etwas Gefiltertes.
        if self.only_transitions.get() and not self._is_transition(self.index):
            nxt = self._step(self.index, +1)
            if nxt is None:
                nxt = self._step(self.index, -1)
            if nxt is not None:
                self.index = nxt
        self._update_count_label()
        self._update()

    def _goto_typed(self):
        raw = self.index_var.get().strip()
        try:
            n = int(raw)
        except ValueError:
            self._status(f"'{raw}' ist keine Zeilennummer.", AMBER)
            return
        if not (1 <= n <= self._count()):
            self._status(f"Bitte 1 bis {self._count()} eingeben.", AMBER)
            return
        self.index = n - 1
        self._update()

    def toggle_history(self):
        self.show_history = not self.show_history
        self.history_button.configure(
            text=("Frühere Datensätze ausblenden" if self.show_history
                  else "Frühere Datensätze einblenden"),
            bg=(ACCENT if self.show_history else "#33465C"))
        self._draw()

    # -- Anzeige aktualisieren ----------------------------------------------
    def _update(self):
        if not self._count():
            return
        self.index_var.set(str(self.index + 1))
        self._update_count_label()

        z = self.zaehlung[self.index]
        e = self.ergebniss[self.index]

        # Übergangsaussage
        direction = z.get("direction", "—")
        is_trans = str(z.get("is_transition", "")).lower() == "true"
        if is_trans:
            self.transition_label.configure(text=direction, fg=GREEN)
            self.transition_sub.configure(text="als Übergang gezählt")
        else:
            self.transition_label.configure(text=direction, fg=INK)
            self.transition_sub.configure(text="kein Wechsel — nicht gezählt")

        # display_id-Abgleich
        zid = z.get("display_id", "")
        eid = e.get("display_id", "")
        id_text = zid if zid == eid else f"{zid}  ≠  {eid}"
        self.detail_rows["display_id"].configure(
            text=id_text, fg=(INK if zid == eid else AMBER))

        self.detail_rows["Klasse"].configure(text=e.get("label", z.get("label", "—")))
        conf = e.get("avg_confidence", "")
        try:
            conf_f = float(conf)
            conf_txt = f"{conf_f:.3f}"
            conf_col = GREEN if conf_f >= 0.5 else AMBER
        except ValueError:
            conf_txt, conf_col = "—", INK
        self.detail_rows["Konfidenz"].configure(text=conf_txt, fg=conf_col)

        self.detail_rows["Zeit"].configure(text=z.get("timestamp", "—"))

        sx, sy, ex, ey = self._coords(e)
        self.detail_rows["Startpunkt"].configure(
            text=f"({sx}, {sy})" if sx is not None else "—")
        self.detail_rows["Endpunkt"].configure(
            text=f"({ex}, {ey})" if ex is not None else "—")
        if None not in (sx, sy, ex, ey):
            dist = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
            self.detail_rows["Distanz"].configure(text=f"{dist:.0f} px")
        else:
            self.detail_rows["Distanz"].configure(text="—")
        self.detail_rows["Art (kind)"].configure(text=e.get("kind", "—"))

        self._draw()

    def _update_count_label(self):
        total = self._count()
        if self.only_transitions.get():
            trans = sum(1 for i in range(total) if self._is_transition(i))
            self.count_label.configure(text=f"von {total}  ({trans} Übergänge)")
        else:
            self.count_label.configure(text=f"von {total}")

    def _coords(self, e):
        def g(k):
            try:
                return int(float(e[k]))
            except (KeyError, ValueError):
                return None
        return g("start_x"), g("start_y"), g("end_x"), g("end_y")

    # -- Zeichnen ------------------------------------------------------------
    def _transform(self):
        """Skalierung + Offset, um die Bezugsfläche in den Canvas zu legen."""
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 20 or ch < 20:
            return None
        margin = 16
        scale = min((cw - 2 * margin) / self.frame_w,
                    (ch - 2 * margin) / self.frame_h)
        disp_w = self.frame_w * scale
        disp_h = self.frame_h * scale
        ox = (cw - disp_w) / 2
        oy = (ch - disp_h) / 2
        return scale, ox, oy, disp_w, disp_h

    def _pt(self, x, y, tf):
        scale, ox, oy, _, _ = tf
        return ox + x * scale, oy + y * scale

    def _draw(self):
        self.canvas.delete("all")
        tf = self._transform()
        if tf is None:
            return
        scale, ox, oy, disp_w, disp_h = tf

        # Rahmen der Bezugsfläche
        self.canvas.create_rectangle(ox, oy, ox + disp_w, oy + disp_h,
                                     outline=GRID, width=1)
        # Zehntel-Raster
        for i in range(1, 10):
            gx = ox + disp_w * i / 10
            gy = oy + disp_h * i / 10
            self.canvas.create_line(gx, oy, gx, oy + disp_h, fill=GRID)
            self.canvas.create_line(ox, gy, ox + disp_w, gy, fill=GRID)

        if not self._count():
            self.canvas.create_text(ox + disp_w / 2, oy + disp_h / 2,
                                    text="Noch keine Daten geladen.",
                                    fill=INK_DIM, font=self.f_label)
            return

        self._draw_regions(tf)
        if self.show_history:
            self._draw_history(tf)
        self._draw_current(tf)

    def _draw_regions(self, tf):
        """Zählzonen aus roi_config.json (relative Koordinaten)."""
        for i, region in enumerate(self.regions):
            pts = region.get("points", [])
            if len(pts) < 3:
                continue
            flat = []
            for nx, ny in pts:
                px, py = self._pt(nx * self.frame_w, ny * self.frame_h, tf)
                flat += [px, py]
            fill = REGION_FILLS[i % len(REGION_FILLS)]
            line = REGION_LINES[i % len(REGION_LINES)]
            self.canvas.create_polygon(flat, fill=fill, outline=line,
                                       width=2, stipple="gray50")
            # Name mittig
            cx = sum(flat[0::2]) / (len(flat) // 2)
            cy = sum(flat[1::2]) / (len(flat) // 2)
            name = region.get("name", "?")
            if name == self.in_field:
                name += "  (IN)"
            self.canvas.create_text(cx, cy, text=name, fill="#334", font=self.f_label)

    def _draw_history(self, tf):
        """Alle Datensätze mit kleinerer Nummer blass einzeichnen."""
        for j in range(self.index):
            e = self.ergebniss[j]
            sx, sy, ex, ey = self._coords(e)
            if None in (sx, sy, ex, ey):
                continue
            p1 = self._pt(sx, sy, tf)
            p2 = self._pt(ex, ey, tf)
            self.canvas.create_line(*p1, *p2, fill="#B7C2D0", width=1)
            self.canvas.create_oval(p1[0]-2, p1[1]-2, p1[0]+2, p1[1]+2,
                                    fill="#9FB0C2", outline="")

    def _draw_current(self, tf):
        e = self.ergebniss[self.index]
        sx, sy, ex, ey = self._coords(e)
        if None in (sx, sy, ex, ey):
            return
        p1 = self._pt(sx, sy, tf)
        p2 = self._pt(ex, ey, tf)

        # Bewegungslinie
        self.canvas.create_line(*p1, *p2, fill=ACCENT, width=3,
                                arrow="last", arrowshape=(12, 15, 5))
        # Start grün, Ende rot
        r = 7
        self.canvas.create_oval(p1[0]-r, p1[1]-r, p1[0]+r, p1[1]+r,
                                fill=GREEN, outline="white", width=2)
        self.canvas.create_oval(p2[0]-r, p2[1]-r, p2[0]+r, p2[1]+r,
                                fill=RED, outline="white", width=2)
        # Beschriftung
        zid = e.get("display_id", "")
        self.canvas.create_text(p1[0], p1[1]-16, text=zid, fill="#334",
                                font=self.f_label)

    # -- Zustand / Statuszeile ----------------------------------------------
    def _set_loaded(self, loaded):
        state = "normal" if loaded else "disabled"
        for w in (self.prev_button, self.next_button, self.index_entry,
                  self.history_button):
            w.configure(state=state)
        if not loaded:
            self.count_label.configure(text="")
            self.index_var.set("")

    def _status(self, text, color=INK_DIM):
        self.load_status.configure(text=text, fg=color)


def main():
    root = tk.Tk()
    VergleichApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
