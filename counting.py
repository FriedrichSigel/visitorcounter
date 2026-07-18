"""
Eigentliche Zähllogik: erkennt, wann ein Track eine konfigurierte Zähl-
geometrie (Linie oder Fläche) kreuzt, bestimmt die Richtung (rein/raus) und
führt pro Klasse einen laufenden Zählerstand.

Bewusst als eigenes Modul, getrennt von tracking.py: tracking.py verwaltet
den Zustand einzelner Objekte über die Zeit, counting.py wertet die
Bewegung zwischen zwei Positionen geometrisch aus. Zwei unterschiedliche
Zuständigkeiten.

LineCounter, RoiCounter und MultiRoiCounter haben absichtlich dieselbe
Schnittstelle (check_crossing, counts, summary_lines, get_geometry_pixels,
mode) — damit tracking.py und die Visualisierung nicht wissen müssen,
welcher Modus gerade aktiv ist.

check_crossing() gibt immer ein Tupel (text, ist_uebergang) zurueck:
- (None, False): nichts zu protokollieren (z. B. fehlende Frame-Maße)
- (text, True): ein echter Uebergang/Kreuzung — wird gezaehlt UND protokolliert
- (text, False): kein echter Uebergang, aber trotzdem protokollierenswert
  (aktuell nur bei MultiRoiCounter: Start und Ende im selben Bereich)
"""


def _cross(o, a, b):
    """2D-Kreuzprodukt der Vektoren OA und OB. Vorzeichen zeigt die
    Drehrichtung (Orientierung) von O->A->B an."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def point_side(line_a, line_b, point):
    """
    Auf welcher Seite der Linie (line_a -> line_b) liegt point?
    Rückgabe: 1 (eine Seite), -1 (andere Seite), 0 (exakt auf der Linie).
    """
    value = _cross(line_a, line_b, point)
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def segments_intersect(p1, p2, p3, p4):
    """
    Prüft, ob sich die Strecken p1-p2 und p3-p4 schneiden (Standard-
    Orientierungstest). Kollineare Grenzfälle werden bewusst nicht
    gesondert behandelt — bei einer Bewegung, die zufällig exakt auf der
    Zähllinie liegt, wird der Schnitt im nächsten Frame ohnehin erkannt.
    """
    d1 = _cross(p3, p4, p1)
    d2 = _cross(p3, p4, p2)
    d3 = _cross(p1, p2, p3)
    d4 = _cross(p1, p2, p4)
    return ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
           ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0))


def point_in_polygon(point, polygon):
    """
    Standard-Ray-Casting-Test: liegt point innerhalb des Polygons (Liste von
    (x, y)-Punkten in Pixelkoordinaten)? Das Polygon muss nicht explizit
    geschlossen sein (letzter Punkt muss nicht gleich dem ersten sein).
    """
    x, y = point
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > y) != (yj > y):
            x_intersect = (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi
            if x < x_intersect:
                inside = not inside
        j = i
    return inside


def _point_to_segment_distance(point, a, b):
    """Kürzester Abstand von point zur Strecke a-b (Pixelkoordinaten)."""
    px, py = point
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))  # auf die Strecke begrenzen, nicht die unendliche Gerade
    closest_x = ax + t * dx
    closest_y = ay + t * dy
    return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5


def point_to_polygon_distance(point, polygon):
    """
    Kürzester Abstand von point zum RAND des Polygons (Minimum über alle
    Kanten) — nicht zum Mittelpunkt, das wäre bei großen/länglichen Flächen
    ungenau.
    """
    n = len(polygon)
    return min(
        _point_to_segment_distance(point, polygon[i], polygon[(i + 1) % n])
        for i in range(n)
    )


def should_count_track(data):
    """
    Wird geprüft, BEVOR ein abgeschlossener Track auf eine Kreuzung der
    Zählgeometrie getestet wird. Platzhalter für einen künftigen Filter
    (z. B. um sehr kurze oder instabile Tracks von der Zählung
    auszuschließen). Aktuell akzeptiert er jeden Track — hier ansetzen,
    sobald der Filter konkret spezifiziert ist.
    """
    return True


def build_counter(mode, geometry, labels, reverse=False, snap_to_nearest=False):
    """
    Fabrikfunktion für die Zähllogik.

    mode: "line" (zwei Punkte, Kreuzungstest), "roi" (drei oder mehr Punkte,
    Punkt-in-Polygon-Test) oder "multi_roi" (mehrere benannte Flächen,
    zählt Übergänge zwischen ihnen). "auto" (automatische Wegerkennung per
    Clustering auf ergebniss.csv, siehe ToDo.md) ist für später vorgesehen.

    geometry: bei "line"/"roi" eine Liste/Tupel von (x,y)-Punkten; bei
    "multi_roi" eine Liste von {"name": str, "points": [(x,y), ...]}.

    snap_to_nearest: nur bei "multi_roi" relevant (siehe MultiRoiCounter).
    """
    if mode == "multi_roi":
        return MultiRoiCounter(geometry, labels, reverse=reverse, snap_to_nearest=snap_to_nearest)
    if mode == "roi":
        return RoiCounter(geometry, labels, reverse=reverse)
    if mode != "line":
        print(f"WARNUNG: Zählmodus '{mode}' ist unbekannt — nutze 'line' als Fallback.")
    return LineCounter(geometry, labels, reverse=reverse)


class LineCounter:
    """
    Führt für eine konfigurierte Zähllinie (in normalisierten Koordinaten,
    0.0-1.0) pro Klasse einen laufenden "in"/"out"-Zählerstand.

    Richtungskonvention: "in" = Bewegung von der Seite mit negativem
    point_side-Vorzeichen zur Seite mit positivem Vorzeichen, "out"
    umgekehrt. Welche Seite in der Realität "rein" oder "raus" bedeutet,
    hängt von der Kameraausrichtung ab und muss vor Ort geprüft werden —
    dafür existiert reverse (siehe config.REVERSE_COUNTING_DIRECTION),
    um die Konvention ohne Codeänderung umzudrehen.
    """

    mode = "line"

    def __init__(self, points_normalized, labels, reverse=False):
        self.points_normalized = tuple(tuple(p) for p in points_normalized)  # (A, B), je 0.0-1.0
        self.reverse = reverse
        self.counts = {label: {"in": 0, "out": 0} for label in labels}

    def _pixel_points(self, frame_width, frame_height):
        (x1, y1), (x2, y2) = self.points_normalized
        return (
            (x1 * frame_width, y1 * frame_height),
            (x2 * frame_width, y2 * frame_height),
        )

    def check_crossing(self, label, prev_pos, new_pos, frame_width, frame_height):
        """
        Prüft, ob die Bewegung von prev_pos zu new_pos die Zähllinie kreuzt.
        Gibt ("in"/"out", True) bei einer Kreuzung zurück, sonst (None, False).
        Erhöht bei einer Kreuzung sofort den passenden Zähler in self.counts.
        """
        if not frame_width or not frame_height:
            return None, False

        line_a, line_b = self._pixel_points(frame_width, frame_height)
        if not segments_intersect(line_a, line_b, prev_pos, new_pos):
            return None, False

        side_before = point_side(line_a, line_b, prev_pos)
        side_after = point_side(line_a, line_b, new_pos)
        if side_before == 0 or side_after == 0 or side_before == side_after:
            # Kein echter Seitenwechsel (z. B. Bewegung endet exakt auf der
            # Linie) — als Grenzfall ignorieren statt falsch zu zählen.
            return None, False

        direction = "in" if side_before < side_after else "out"
        if self.reverse:
            direction = "out" if direction == "in" else "in"

        self.counts.setdefault(label, {"in": 0, "out": 0})
        self.counts[label][direction] += 1
        return direction, True

    def get_geometry_pixels(self, frame_width, frame_height):
        """Für die Visualisierung: Zähllinie in Pixelkoordinaten, [A, B]."""
        return list(self._pixel_points(frame_width, frame_height))

    def summary_lines(self):
        """Liste von Textzeilen für Konsolen-/Overlay-Ausgabe, z. B. 'person: IN 5 / OUT 2'."""
        lines = []
        for label, c in self.counts.items():
            if c["in"] or c["out"]:
                lines.append(f"{label}: IN {c['in']} / OUT {c['out']}")
        return lines


class RoiCounter:
    """
    Führt für eine konfigurierte Fläche (Polygon aus 3+ Punkten, normalisiert
    0.0-1.0) pro Klasse einen laufenden "in"/"out"-Zählerstand.

    Ein Track gilt als "in" (eingetreten), wenn seine Startposition
    außerhalb und seine Endposition innerhalb der Fläche liegt — und
    umgekehrt als "out" (ausgetreten). Anders als bei der Linie gibt es
    hier keine zwei beliebigen "Seiten" — "innerhalb"/"außerhalb" der
    Fläche ist eindeutig. reverse existiert trotzdem, für den Fall, dass
    "in"/"out" in der Auswertung vertauscht berichtet werden sollen.
    """

    mode = "roi"

    def __init__(self, points_normalized, labels, reverse=False):
        self.points_normalized = tuple(tuple(p) for p in points_normalized)  # 3+ Punkte, je 0.0-1.0
        self.reverse = reverse
        self.counts = {label: {"in": 0, "out": 0} for label in labels}

    def _pixel_polygon(self, frame_width, frame_height):
        return [(x * frame_width, y * frame_height) for x, y in self.points_normalized]

    def check_crossing(self, label, prev_pos, new_pos, frame_width, frame_height):
        """
        Prüft, ob prev_pos und new_pos auf unterschiedlichen Seiten der
        Flächengrenze liegen (eine davon innen, die andere außen). Gibt
        ("in"/"out", True) bei einem Übertritt zurück, sonst (None, False).
        """
        if not frame_width or not frame_height or len(self.points_normalized) < 3:
            return None, False

        polygon = self._pixel_polygon(frame_width, frame_height)
        was_inside = point_in_polygon(prev_pos, polygon)
        is_inside = point_in_polygon(new_pos, polygon)

        if was_inside == is_inside:
            return None, False  # kein Übertritt — durchgehend innerhalb oder außerhalb

        direction = "in" if is_inside else "out"
        if self.reverse:
            direction = "out" if direction == "in" else "in"

        self.counts.setdefault(label, {"in": 0, "out": 0})
        self.counts[label][direction] += 1
        return direction, True

    def get_geometry_pixels(self, frame_width, frame_height):
        """Für die Visualisierung: Eckpunkte der Fläche in Pixelkoordinaten."""
        return self._pixel_polygon(frame_width, frame_height)

    def summary_lines(self):
        """Liste von Textzeilen für Konsolen-/Overlay-Ausgabe, z. B. 'person: IN 5 / OUT 2'."""
        lines = []
        for label, c in self.counts.items():
            if c["in"] or c["out"]:
                lines.append(f"{label}: IN {c['in']} / OUT {c['out']}")
        return lines


class MultiRoiCounter:
    """
    Zählt Übergänge zwischen mehreren benannten Flächen. Liegt eine Position
    in keiner der Flächen, gilt sie als "außerhalb".

    Wie LineCounter/RoiCounter wird nur Start- und Endposition des gesamten
    Tracks verglichen (nicht jeder Frame): ein Track, der Fläche A verlässt,
    durch "außerhalb" läuft und in Fläche B ankommt, wird als ein einziger
    Übergang "A -> B" gezählt — der Zwischenstopp bei "außerhalb" geht nicht
    gesondert ein. Bei sich überlappenden Flächen entscheidet die
    Reihenfolge in der Konfiguration (die zuerst definierte Fläche gewinnt).

    reverse wird hier nicht sinnvoll genutzt (es gibt keine zwei Seiten wie
    bei einer Linie) — Parameter bleibt für eine einheitliche Schnittstelle
    mit LineCounter/RoiCounter erhalten.

    snap_to_nearest (Opt-in in roi_config_app.py): wenn True, wird ein Punkt,
    der in KEINER Fläche liegt, statt "außerhalb" der Fläche zugeordnet, zu
    deren Rand er am nächsten liegt — statt als "außerhalb" gezählt zu
    werden. Default False (bisheriges Verhalten: echtes "außerhalb").
    """

    mode = "multi_roi"
    OUTSIDE = "außerhalb"

    def __init__(self, regions_normalized, labels, reverse=False, snap_to_nearest=False):
        # regions_normalized: Liste von {"name": str, "points": [(x,y), ...]}, je 0.0-1.0
        self.regions_normalized = regions_normalized
        self.reverse = reverse
        self.snap_to_nearest = snap_to_nearest
        self.counts = {label: {} for label in labels}  # {label: {"A->B": n, ...}}

    def _regions_pixel(self, frame_width, frame_height):
        """Alle Flächen einmalig in Pixelkoordinaten umgerechnet — gemeinsam
        genutzt von check_crossing() (dort für beide Positionen) und
        get_geometry_pixels(), um die Umrechnung nicht mehrfach zu wiederholen."""
        return [
            (region["name"], [(x * frame_width, y * frame_height) for x, y in region["points"]])
            for region in self.regions_normalized
        ]

    def _region_for_point(self, point, regions_pixel):
        """
        Name der Fläche, die point enthält. Liegt point in keiner Fläche:
        bei snap_to_nearest=True die Fläche mit dem geringsten Randabstand,
        sonst OUTSIDE.
        """
        for name, polygon in regions_pixel:
            if point_in_polygon(point, polygon):
                return name

        if self.snap_to_nearest and regions_pixel:
            nearest_name, _ = min(
                regions_pixel,
                key=lambda item: point_to_polygon_distance(point, item[1])
            )
            return nearest_name

        return self.OUTSIDE

    def check_crossing(self, label, prev_pos, new_pos, frame_width, frame_height):
        """
        Prüft, ob prev_pos und new_pos in unterschiedlichen Flächen liegen.

        Gibt ein Tupel zurück:
        - (None, False): keine Frame-Maße bekannt oder keine Flächen konfiguriert
        - ("A->B", True): echter Übergang zwischen zwei unterschiedlichen
          Bereichen — wird gezählt
        - ("A (kein Wechsel)", False): Start und Ende liegen im selben
          Bereich (egal ob echte Fläche oder "außerhalb") — wird NICHT
          gezählt, aber trotzdem protokolliert, damit sichtbar bleibt, dass
          der Track existierte und keine (uns bekannte) Bewegung zwischen
          Flächen stattfand
        """
        if not frame_width or not frame_height or not self.regions_normalized:
            return None, False

        # Einmal pro Aufruf berechnen und für beide Positionen wiederverwenden
        # (vorher wurde das für jede Position separat neu berechnet)
        regions_pixel = self._regions_pixel(frame_width, frame_height)
        from_region = self._region_for_point(prev_pos, regions_pixel)
        to_region = self._region_for_point(new_pos, regions_pixel)

        if from_region == to_region:
            return f"{from_region} (kein Wechsel)", False

        transition = f"{from_region}->{to_region}"
        self.counts.setdefault(label, {})
        self.counts[label][transition] = self.counts[label].get(transition, 0) + 1
        return transition, True

    def get_geometry_pixels(self, frame_width, frame_height):
        """Für die Visualisierung: Liste von (name, [Pixelpunkte]) je Fläche."""
        return self._regions_pixel(frame_width, frame_height)

    def summary_lines(self):
        """Liste von Textzeilen für Konsolen-/Overlay-Ausgabe, z. B. 'person: A->B: 3'."""
        lines = []
        for label, transitions in self.counts.items():
            for transition, count in transitions.items():
                if count:
                    lines.append(f"{label}: {transition}: {count}")
        return lines
