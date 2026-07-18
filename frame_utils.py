"""
frame_utils.py — GUI-freie Frame-Beschaffung aus Bild- und Videodateien.

Bewusst OHNE Abhängigkeit zu tkinter/customtkinter/PIL: nur cv2 + os. Damit
können Module wie auto_config_clustering.py die Auflösung eines Referenzframes
bestimmen, ohne den kompletten GUI-Stack (roi_config_app.py) zu importieren —
wichtig für den Betrieb auf einem Pi ohne Display und für isolierte Tests der
Auto-Konfiguration.

Was hier NICHT liegt: die Snapshot-Aufnahme über die Hailo-Pipeline
(path in ("usb", "rpi")). Die startet core.py als Subprozess und gehört
konzeptionell zur Pipeline-/GUI-Seite — sie bleibt in roi_config_app.py.
frame_utils.py deckt nur den datei-basierten Fall ab (Bild oder Video).
"""

import os

import cv2

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp")

# Reihenfolge der OpenCV-Backends beim Öffnen von Videodateien. Manche
# opencv-python-Builds (u. a. auf dem Pi) haben unvollständige
# FFmpeg-Unterstützung; deshalb werden mehrere Backends nacheinander probiert.
_VIDEO_BACKENDS = [
    ("Standard", cv2.CAP_ANY),
    ("FFMPEG", cv2.CAP_FFMPEG),
    ("GSTREAMER", cv2.CAP_GSTREAMER),
]


def load_frame_from_file(path):
    """
    Lädt den ersten Frame aus einer Bild- ODER Videodatei und gibt ihn als
    BGR-numpy-Array zurück (wie cv2.imread / cv2.VideoCapture.read()).

    Löst ValueError mit einer erklärenden Meldung aus, wenn die Datei fehlt,
    kein Backend sie öffnen kann oder kein Frame lesbar ist. Für Kameras
    (path in ("usb", "rpi")) ist diese Funktion NICHT zuständig — dafür die
    Snapshot-Aufnahme in roi_config_app.py verwenden.
    """
    if path in ("usb", "rpi"):
        raise ValueError(
            "load_frame_from_file() ist nur für Datei-Eingaben gedacht. "
            "Für Kamera-Snapshots ('usb'/'rpi') die Aufnahme über core.py "
            "bzw. roi_config_app.py nutzen."
        )

    if not os.path.isfile(path):
        raise ValueError(f"Datei nicht gefunden: {os.path.abspath(path)}")

    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE_EXTENSIONS:
        frame = cv2.imread(path)
        if frame is None:
            raise ValueError(f"Bild konnte nicht geladen werden: {path}")
        return frame

    last_opened = False
    for name, backend in _VIDEO_BACKENDS:
        cap = cv2.VideoCapture(path, backend)
        opened = cap.isOpened()
        last_opened = last_opened or opened
        if opened:
            ok, frame = cap.read()
            cap.release()
            if ok and frame is not None:
                print(f"Frame erfolgreich gelesen (Backend: {name}).")
                return frame
            print(f"Backend {name}: Datei geöffnet, aber kein Frame lesbar.")
        else:
            print(f"Backend {name}: Datei konnte nicht geöffnet werden.")
        cap.release()

    if not last_opened:
        raise ValueError(
            f"Keines der OpenCV-Backends konnte '{path}' öffnen. "
            f"Vermutlich fehlt die passende Video-Unterstützung in der "
            f"installierten opencv-python-Version. Alternative: einen Frame "
            f"per ffmpeg als Bild extrahieren und den als --input nutzen:\n"
            f"  ffmpeg -i {path} -frames:v 1 frame.png\n"
            f"  python auto_config_clustering.py --input frame.png ..."
        )
    raise ValueError(
        f"Datei '{path}' ließ sich öffnen, aber kein Frame lesbar (evtl. "
        f"beschädigt oder falscher Codec)."
    )


def get_frame_size(path):
    """
    Bestimmt nur die Auflösung (width, height) einer Bild- oder Videodatei,
    ohne den Frame selbst zurückzugeben. Praktisch für die Auto-Konfiguration,
    die zur Normalisierung der Pixelkoordinaten ausschließlich die Auflösung
    braucht.
    """
    frame = load_frame_from_file(path)
    height, width = frame.shape[:2]
    return width, height
