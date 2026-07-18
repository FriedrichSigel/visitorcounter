"""
auto_config_clustering.py — Paket 3 (Clustering) und Paket 4 (Cluster ->
Zählgeometrie) der automatischen Wegerkennung.

Bewusst in einer EIGENEN Datei, getrennt von auto_config.py (Paket 1+2):
Sammlung und Batch-Einteilung brauchen nur die Standardbibliothek, dieses
Modul braucht zusätzlich scikit-learn und scipy. Wer nur sammeln will,
muss diese Abhängigkeiten nicht installieren.

    pip install scikit-learn --break-system-packages
    (oder ohne --break-system-packages in der venv des Projekts —
    scipy kommt als Abhängigkeit von scikit-learn automatisch mit)

Paket 3 (Clustering): cluster_points() nutzt DBSCAN (dichtebasiertes
Clustering) statt eines reinen k-NN — k-NN allein sagt nur "wer sind meine
nächsten Nachbarn", bestimmt aber nicht, WIE VIELE Cluster es gibt. DBSCAN
bestimmt die Clusteranzahl automatisch anhand der Punktdichte und markiert
vereinzelte Ausreißer als Rauschen, statt sie einem Cluster zuzuwingen --
wichtig bei echten Tracking-Daten mit gelegentlichen Fehldetektionen.

Start- und Endpunkte werden standardmäßig GEMEINSAM geclustert (kein
Unterschied zwischen "wo Tracks anfangen" und "wo sie aufhören") — an
vielen Standorten sind das ohnehin dieselben Stellen (z. B. Ein-/Ausgänge).
cluster_points() akzeptiert weiterhin einen point_type-Filter, falls doch
mal getrennt geclustert werden soll.

Paket 4 (Cluster -> Zählgeometrie): clusters_to_regions() übersetzt
gefundene Cluster in das bestehende roi_config.json-Format
(mode="multi_roi") — automatisch benannte Flächen (konvexe Hülle um die
Cluster-Punkte), sofort kompatibel mit counting.build_counter() /
MultiRoiCounter, ohne dass ein neuer Laufzeit-Modus gebaut werden musste.

WICHTIG: auto_config_points.csv enthält nur Pixelkoordinaten, keine
Videoauflösung (um das bereits gesammelte Datenformat nicht zu brechen).
Für die Umrechnung in normalisierte Koordinaten (0.0-1.0) wird die
Auflösung deshalb hier separat übergeben (z. B. aus einem Beispielframe
des Quellvideos), nicht aus der CSV gelesen.

Kontrollbild: draw_cluster_debug_image() zeichnet alle Punkte (farblich
nach Cluster, grau = Ausreißer) und die daraus gebildeten Flächen auf den
Referenzframe — wird beim Ausführen als Skript automatisch unter
CLUSTER_DEBUG_IMAGE_PATH gespeichert (immer überschrieben), damit sich das
Ergebnis vor dem Speichern in roi_config.json anschauen lässt.
"""

import json

import cv2
import numpy as np
from sklearn.cluster import DBSCAN
from scipy.spatial import ConvexHull, QhullError

from counting import point_in_polygon, point_to_polygon_distance

# Wird von der Kontrollbild-Funktion geschrieben — IMMER überschrieben
# (kein Zeitstempel), damit das jeweils letzte Clustering-Ergebnis unter
# demselben Namen zu finden ist, auch nach mehreren Tuning-Durchläufen.
CLUSTER_DEBUG_IMAGE_PATH = "auto_config_clusters.png"
BORDER_DEBUG_IMAGE_PATH = "auto_config_border.png"


def cluster_points(points, point_type=None, eps_pixels=50, min_samples=3):
    """
    Clustert Punkte aus einer Punktliste (siehe auto_config.load_collected_points()
    bzw. auto_config.split_into_batches()).

    point_type: "start", "end", oder None (Standard) — bei None werden
    Start- und Endpunkte GEMEINSAM geclustert, ohne zwischen ihnen zu
    unterscheiden (sinnvoll, wenn dieselben Stellen im Bild sowohl als
    Start- als auch als Endpunkt auftauchen, z. B. Ein-/Ausgänge).

    eps_pixels: maximaler Abstand zwischen zwei Punkten (in Pixeln), damit
    sie als "Nachbarn" gelten (DBSCAN-Parameter).
    min_samples: Mindestanzahl Punkte, um einen Cluster zu bilden.

    Gibt (clusters, noise_points) zurück. clusters ist eine Liste von dicts:
    {"cluster_id": int, "center": (x, y), "points": [...], "count": int}.
    noise_points ist die Liste der als Rauschen eingestuften Punkte
    (DBSCAN-Label -1) — tauchen NICHT als Cluster auf, werden aber
    zurückgegeben, damit sie z. B. im Kontrollbild sichtbar gemacht werden
    können.
    """
    filtered = points if point_type is None else [p for p in points if p["point_type"] == point_type]
    if not filtered:
        return [], []

    coords = np.array([[p["x"], p["y"]] for p in filtered])
    labels = DBSCAN(eps=eps_pixels, min_samples=min_samples).fit_predict(coords)

    clusters = []
    noise_points = []
    for cluster_id in sorted(set(labels)):
        member_indices = [i for i, lbl in enumerate(labels) if lbl == cluster_id]
        if cluster_id == -1:
            noise_points = [filtered[i] for i in member_indices]
            continue
        member_points = [filtered[i] for i in member_indices]
        member_coords = coords[member_indices]
        center = (float(member_coords[:, 0].mean()), float(member_coords[:, 1].mean()))
        clusters.append({
            "cluster_id": int(cluster_id),
            "center": center,
            "points": member_points,
            "count": len(member_points),
        })

    return clusters, noise_points


def cluster_to_polygon(cluster, fallback_radius_pixels=20):
    """
    Berechnet die konvexe Hülle der Punkte eines Clusters — die kleinste
    konvexe Fläche, die alle beobachteten Punkte umschließt. Ergebnis:
    Liste von (x, y)-Eckpunkten in Pixelkoordinaten, kompatibel mit
    counting.point_in_polygon().

    Fällt auf ein kleines Quadrat um den Cluster-Mittelpunkt zurück, wenn
    weniger als 3 Punkte vorliegen oder die Punkte (fast) auf einer Linie
    liegen (ConvexHull scheitert dann) — so entsteht immer eine gültige
    Fläche, auch wenn sie in diesem Fall grob ist.
    """
    coords = [(p["x"], p["y"]) for p in cluster["points"]]

    if len(coords) >= 3:
        try:
            pts = np.array(coords)
            hull = ConvexHull(pts)
            return [tuple(pts[i]) for i in hull.vertices]
        except QhullError:
            pass  # z. B. (fast) kollineare Punkte -> Fallback unten

    cx, cy = cluster["center"]
    r = fallback_radius_pixels
    return [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)]


def clusters_to_regions(clusters, frame_width, frame_height, prefix="Zone"):
    """
    Baut aus gefundenen Clustern eine Liste benannter Flächen im
    roi_config.json-Format (Eckpunkte normalisiert 0.0-1.0), fertig zum
    Speichern mit mode="multi_roi". Start- und Endpunkte werden nicht
    unterschieden — beide fließen in dieselben Cluster ein (siehe
    cluster_points(), point_type=None).
    """
    regions = []
    for i, cluster in enumerate(clusters, start=1):
        polygon_px = cluster_to_polygon(cluster)
        polygon_norm = [[x / frame_width, y / frame_height] for x, y in polygon_px]
        regions.append({"name": f"{prefix}_{i}", "points": polygon_norm})
    return regions


def draw_cluster_debug_image(frame_bgr, clusters, noise_points, regions):
    """
    Zeichnet ein Kontrollbild auf Basis des übergebenen Frames: alle
    geclusterten Punkte (farblich nach Cluster sortiert), Ausreißer (grau)
    und die daraus abgeleiteten Flächen (regions, bereits mit Namen) —
    damit sich vor dem Speichern prüfen lässt, ob die automatisch erkannten
    Zonen tatsächlich zu den beobachteten Start-/Endpunkten passen.

    Gibt ein neues Bild zurück (frame_bgr selbst wird nicht verändert).
    """
    img = frame_bgr.copy()
    frame_height, frame_width = img.shape[:2]

    # BGR-Farben (OpenCV-Reihenfolge), eine je Cluster, wird bei Bedarf wiederholt
    colors_bgr = [
        (0, 255, 0), (255, 0, 0), (0, 0, 255), (0, 255, 255),
        (255, 0, 255), (255, 255, 0), (128, 0, 255), (0, 128, 255),
    ]

    # Punkte je Cluster einfärben
    for i, cluster in enumerate(clusters):
        color = colors_bgr[i % len(colors_bgr)]
        for p in cluster["points"]:
            cv2.circle(img, (int(p["x"]), int(p["y"])), 4, color, -1)

    # Ausreißer grau, etwas kleiner, damit sie sich optisch unterordnen
    for p in noise_points:
        cv2.circle(img, (int(p["x"]), int(p["y"])), 3, (128, 128, 128), -1)

    # Flächen (Regionen, bereits normalisiert) zurück in Pixelkoordinaten und zeichnen
    for i, region in enumerate(regions):
        color = colors_bgr[i % len(colors_bgr)]
        pts = np.array(
            [[int(x * frame_width), int(y * frame_height)] for x, y in region["points"]],
            dtype=np.int32,
        )
        cv2.polylines(img, [pts], isClosed=True, color=color, thickness=2)
        cx, cy = int(pts[:, 0].mean()), int(pts[:, 1].mean())
        cv2.putText(img, region["name"], (cx - 20, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    return img


def generate_border_regions(frame_width, frame_height, segments_per_edge=4, border_depth_ratio=0.08):
    """
    Erzeugt ein FESTES Raster aus ROI-Flächen entlang der vier Bildränder,
    statt Zonen aus den gesammelten Punkten zu clustern (Alternative zu
    cluster_points()/clusters_to_regions()).

    Hintergrund: Die Objekterkennung verliert einen Track manchmal
    zwischendurch (Verdeckung, kurze Fehldetektion) und nimmt ihn als NEUEN
    Track mitten im Bild wieder auf. Das erzeugt Start-/Endpunkte in der
    Bildmitte, die keine echten Ein-/Ausgänge sind und das Clustering
    verfälschen (viele kleine Cluster/Ausreißer in der Mitte statt sauberer
    Randcluster). Da reale Ein-/Ausgänge fast immer am Bildrand liegen,
    wird hier stattdessen ein fester Rand-Raster erzeugt — jeder gesammelte
    Punkt wird anschließend der nächstgelegenen Randfläche zugeordnet
    (siehe assign_tracks_to_border()), inklusive der Distanz dorthin.

    segments_per_edge: Anzahl Flächen je Bildkante (oben/unten/links/rechts)
    border_depth_ratio: wie weit die Flächen von der Kante ins Bild
    hineinragen, als Anteil der jeweiligen Kantenlänge (0.08 = 8 %)

    Gibt eine Liste von {"name": str, "points": [[x,y], ...]} zurück,
    normalisiert 0.0-1.0 — direkt kompatibel mit roi_config.json (mode="multi_roi").
    """
    regions = []
    d = border_depth_ratio

    for i in range(segments_per_edge):
        x0 = i / segments_per_edge
        x1 = (i + 1) / segments_per_edge
        regions.append({"name": f"Rand_oben_{i + 1}", "points": [[x0, 0.0], [x1, 0.0], [x1, d], [x0, d]]})
        regions.append({"name": f"Rand_unten_{i + 1}", "points": [[x0, 1 - d], [x1, 1 - d], [x1, 1.0], [x0, 1.0]]})

    for i in range(segments_per_edge):
        y0 = i / segments_per_edge
        y1 = (i + 1) / segments_per_edge
        regions.append({"name": f"Rand_links_{i + 1}", "points": [[0.0, y0], [d, y0], [d, y1], [0.0, y1]]})
        regions.append({"name": f"Rand_rechts_{i + 1}", "points": [[1 - d, y0], [1.0, y0], [1.0, y1], [1 - d, y1]]})

    return regions


def _nearest_region_and_distance(point_xy, regions, frame_width, frame_height):
    """
    Für einen einzelnen Punkt (x, y in Pixelkoordinaten): Name der
    nächstgelegenen Fläche aus regions (normalisiert) und Abstand dorthin
    in Pixeln. Abstand 0.0, wenn der Punkt bereits innerhalb der Fläche liegt.
    """
    best_name, best_distance = None, None
    for region in regions:
        polygon = [(x * frame_width, y * frame_height) for x, y in region["points"]]
        if point_in_polygon(point_xy, polygon):
            return region["name"], 0.0
        dist = point_to_polygon_distance(point_xy, polygon)
        if best_distance is None or dist < best_distance:
            best_distance = dist
            best_name = region["name"]
    return best_name, best_distance


def assign_tracks_to_border(points, regions, frame_width, frame_height, min_track_distance_pixels=40):
    """
    Gruppiert die Punkte nach Track (display_id) und ordnet Start- und
    Endpunkt je Track der nächstgelegenen Randfläche zu (inkl. Distanz).

    Filtert dabei Tracks heraus, die vermutlich KEINE echte Randüberquerung
    sind:
    - Start und Ende werden derselben Randfläche zugeordnet, ODER
    - der reale Pixelabstand zwischen Start und Ende ist kleiner als
      min_track_distance_pixels — das Objekt wurde wahrscheinlich kurz
      verloren und an fast derselben Stelle wieder aufgenommen, keine
      echte Bewegung.

    Gibt (crossings, filtered_out) zurück — beide Listen von dicts:
    {display_id, label, start_xy, end_xy, start_region, start_distance,
     end_region, end_distance, track_length_pixels}
    crossings = als echte Randüberquerung gewertete Tracks,
    filtered_out = aussortierte Tracks (zur Kontrolle im Kontrollbild).
    """
    by_track = {}
    for p in points:
        by_track.setdefault(p["display_id"], {"label": p["label"]})[p["point_type"]] = p

    crossings, filtered_out = [], []

    for display_id, data in by_track.items():
        if "start" not in data or "end" not in data:
            continue  # unvollständiger Datensatz (z. B. noch nicht abgeschlossener Track), überspringen

        start_p, end_p = data["start"], data["end"]
        start_xy, end_xy = (start_p["x"], start_p["y"]), (end_p["x"], end_p["y"])

        start_region, start_dist = _nearest_region_and_distance(start_xy, regions, frame_width, frame_height)
        end_region, end_dist = _nearest_region_and_distance(end_xy, regions, frame_width, frame_height)

        track_length = ((start_xy[0] - end_xy[0]) ** 2 + (start_xy[1] - end_xy[1]) ** 2) ** 0.5

        entry = {
            "display_id": display_id,
            "label": data["label"],
            "start_xy": start_xy, "end_xy": end_xy,
            "start_region": start_region, "start_distance": start_dist,
            "end_region": end_region, "end_distance": end_dist,
            "track_length_pixels": track_length,
        }

        is_real_crossing = (start_region != end_region) and (track_length >= min_track_distance_pixels)
        (crossings if is_real_crossing else filtered_out).append(entry)

    return crossings, filtered_out


def draw_border_debug_image(frame_bgr, regions, crossings, filtered_out):
    """
    Zeichnet das Randraster sowie Start->Ende-Linien aller Tracks: grün für
    als echte Randüberquerung gewertete Tracks, grau/dünn für aussortierte
    (zu kurz oder Start/Ende in derselben Randfläche) — hilft zu beurteilen,
    ob min_track_distance_pixels sinnvoll gewählt ist.
    """
    img = frame_bgr.copy()
    frame_height, frame_width = img.shape[:2]

    for region in regions:
        pts = np.array(
            [[int(x * frame_width), int(y * frame_height)] for x, y in region["points"]],
            dtype=np.int32,
        )
        cv2.polylines(img, [pts], isClosed=True, color=(0, 255, 255), thickness=1)

    for f in filtered_out:
        sx, sy = int(f["start_xy"][0]), int(f["start_xy"][1])
        ex, ey = int(f["end_xy"][0]), int(f["end_xy"][1])
        cv2.line(img, (sx, sy), (ex, ey), (128, 128, 128), 1)

    for c in crossings:
        sx, sy = int(c["start_xy"][0]), int(c["start_xy"][1])
        ex, ey = int(c["end_xy"][0]), int(c["end_xy"][1])
        cv2.line(img, (sx, sy), (ex, ey), (0, 255, 0), 2)
        cv2.circle(img, (sx, sy), 4, (255, 0, 0), -1)
        cv2.circle(img, (ex, ey), 4, (0, 0, 255), -1)

    return img


def save_auto_regions(regions, classes, path="roi_config.json", reverse_direction=False):
    """
    Speichert automatisch erkannte Flächen im bestehenden roi_config.json-
    Format (mode="multi_roi") — core.py liest das genauso ein wie eine per
    Hand mit roi_config_app.py erstellte Konfiguration, ohne Änderungen an
    der Laufzeit-Logik.
    """
    config = {
        "mode": "multi_roi",
        "points": [],
        "regions": regions,
        "classes": sorted(classes),
        "reverse_direction": reverse_direction,
        "snap_to_nearest": False,
    }
    with open(path, "w") as f:
        json.dump(config, f, indent=2)


if __name__ == "__main__":
    import argparse

    from auto_config import load_collected_points, split_into_batches
    from config import (
        AUTO_CONFIG_BATCH_STRATEGY, AUTO_CONFIG_BATCH_SECONDS, AUTO_CONFIG_BATCH_SIZE,
        AUTO_CONFIG_DBSCAN_EPS_PIXELS, AUTO_CONFIG_DBSCAN_MIN_SAMPLES,
        AUTO_CONFIG_BORDER_SEGMENTS_PER_EDGE, AUTO_CONFIG_BORDER_DEPTH_RATIO,
        AUTO_CONFIG_MIN_TRACK_DISTANCE_PIXELS,
    )

    parser = argparse.ArgumentParser(
        description="Gesammelte Punkte auswerten und automatisch Zählflächen erzeugen")
    parser.add_argument("--input", required=True,
                         help="Videodatei oder Bild, um die Auflösung für die Normalisierung zu bestimmen")
    parser.add_argument("--batch", type=int, default=None,
                         help="Nur diesen Batch auswerten (1-basiert). Standard: alle Batches zusammen.")
    parser.add_argument("--border", action="store_true",
                         help="Festes Randraster statt Clustering nutzen (siehe generate_border_regions()) "
                              "— empfohlen, wenn viele Start-/Endpunkte in der Bildmitte auftauchen, weil "
                              "die Objekterkennung Tracks zwischendurch verliert")
    parser.add_argument("--save", action="store_true",
                         help="Ergebnis in roi_config.json schreiben (ÜBERSCHREIBT eine bestehende Datei!)")
    args = parser.parse_args()

    # Auflösung für die Normalisierung bestimmen. Bewusst über frame_utils
    # (nur cv2, GUI-frei) statt über roi_config_app — so läuft die
    # Auto-Konfiguration ohne tkinter/customtkinter, auch auf einem Pi ohne
    # Display und in einer schlanken venv. Für Kamera-Eingaben ("usb"/"rpi")
    # zuerst mit roi_config_app.py bzw. core.py ein camera_raw.png aufnehmen
    # und dieses als --input übergeben.
    from frame_utils import load_frame_from_file
    frame = load_frame_from_file(args.input)
    frame_height, frame_width = frame.shape[:2]
    print(f"Videoauflösung für Normalisierung: {frame_width}x{frame_height}")

    points = load_collected_points()
    print(f"{len(points)} gesammelte Punkte geladen")

    batches = split_into_batches(points, strategy=AUTO_CONFIG_BATCH_STRATEGY,
                                  batch_seconds=AUTO_CONFIG_BATCH_SECONDS,
                                  batch_size=AUTO_CONFIG_BATCH_SIZE)
    print(f"{len(batches)} Batch(es) gefunden (Strategie: {AUTO_CONFIG_BATCH_STRATEGY})")

    if args.batch is not None:
        selected_points = batches[args.batch - 1]
        print(f"Werte nur Batch {args.batch} aus ({len(selected_points)} Punkte)")
    else:
        selected_points = points
        print(f"Werte alle Batches zusammen aus ({len(selected_points)} Punkte)")

    if args.border:
        regions = generate_border_regions(
            frame_width, frame_height,
            segments_per_edge=AUTO_CONFIG_BORDER_SEGMENTS_PER_EDGE,
            border_depth_ratio=AUTO_CONFIG_BORDER_DEPTH_RATIO,
        )
        print(f"\n{len(regions)} Randflächen erzeugt "
              f"({AUTO_CONFIG_BORDER_SEGMENTS_PER_EDGE} je Kante).")

        crossings, filtered_out = assign_tracks_to_border(
            selected_points, regions, frame_width, frame_height,
            min_track_distance_pixels=AUTO_CONFIG_MIN_TRACK_DISTANCE_PIXELS,
        )
        print(f"{len(crossings)} Tracks als echte Randüberquerung gewertet, "
              f"{len(filtered_out)} aussortiert (gleiche Randfläche oder Track "
              f"kürzer als {AUTO_CONFIG_MIN_TRACK_DISTANCE_PIXELS}px — vermutlich "
              f"kurz verlorene und wieder aufgenommene Erkennung).")

        pair_counts = {}
        for c in crossings:
            key = (c["start_region"], c["end_region"])
            pair_counts[key] = pair_counts.get(key, 0) + 1
        if pair_counts:
            print("\nHäufigste Randübergänge:")
            for (a, b), n in sorted(pair_counts.items(), key=lambda kv: -kv[1]):
                print(f"  {a} -> {b}: {n}")

        debug_img = draw_border_debug_image(frame, regions, crossings, filtered_out)
        cv2.imwrite(BORDER_DEBUG_IMAGE_PATH, debug_img)
        print(f"\nKontrollbild gespeichert als {BORDER_DEBUG_IMAGE_PATH} — grün "
              f"= gewertete Überquerung, grau = aussortiert. Vor dem Speichern anschauen!")

        classes = sorted(set(p["label"] for p in selected_points))
        if args.save:
            save_auto_regions(regions, classes)
            print("Gespeichert in roi_config.json (mode=multi_roi, Randraster) — "
                  "core.py normal starten, um es zu nutzen.")
        else:
            print("Nicht gespeichert (--save nicht angegeben). Mit --save in roi_config.json schreiben.")

    else:
        clusters, noise_points = cluster_points(
            selected_points, point_type=None,
            eps_pixels=AUTO_CONFIG_DBSCAN_EPS_PIXELS, min_samples=AUTO_CONFIG_DBSCAN_MIN_SAMPLES)

        print(f"\nCluster gefunden: {len(clusters)} (+ {len(noise_points)} Ausreißer)")
        for c in clusters:
            print(f"  Cluster {c['cluster_id']}: {c['count']} Punkte, Zentrum ({c['center'][0]:.0f}, {c['center'][1]:.0f})")

        if not clusters:
            print("\nKeine Cluster gefunden — eps/min_samples in config.py anpassen oder mehr Daten sammeln.")
        else:
            classes = sorted(set(p["label"] for p in selected_points))
            regions = clusters_to_regions(clusters, frame_width, frame_height)
            print(f"\n{len(regions)} Flächen erzeugt: {[r['name'] for r in regions]}")

            debug_img = draw_cluster_debug_image(frame, clusters, noise_points, regions)
            cv2.imwrite(CLUSTER_DEBUG_IMAGE_PATH, debug_img)
            print(f"Kontrollbild gespeichert als {CLUSTER_DEBUG_IMAGE_PATH} — zeigt alle "
                  f"Punkte (farblich nach Cluster, grau = Ausreißer) und die daraus "
                  f"gebildeten Flächen. Vor dem Speichern anschauen!")
            print("Hinweis: Falls viele Punkte in der Bildmitte auftauchen (Objekterkennung "
                  "verliert Tracks zwischendurch), --border ausprobieren statt Clustering.")

            if args.save:
                save_auto_regions(regions, classes)
                print("Gespeichert in roi_config.json (mode=multi_roi) — core.py normal starten, um es zu nutzen.")
            else:
                print("Nicht gespeichert (--save nicht angegeben). Mit --save in roi_config.json schreiben.")
