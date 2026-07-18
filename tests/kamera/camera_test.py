"""
camera_test.py — einfacher, von Hailo komplett unabhängiger Kameratest.
Nur OpenCV als Abhängigkeit, kein Bezug zum core-Projekt.

Prüft, ob sich eine Kamera überhaupt öffnen lässt, zeigt die tatsächlich
ausgehandelte Auflösung/FPS, speichert einen Snapshot, und zeigt optional
ein Live-Vorschaufenster — nützlich, um Kamera-Probleme (Gerät nicht
gefunden, falsche Auflösung, Spiegelung) von Hailo-/Pipeline-Problemen zu
unterscheiden.

Nutzung:
    python camera_test.py                  # probiert Geräteindizes 0-4 durch
    python camera_test.py --device 0        # gezielt ein bestimmtes Gerät
    python camera_test.py --no-preview      # nur Snapshot, kein Live-Fenster
                                             # (z.B. über SSH ohne Display)
    python camera_test.py --seconds 10      # Live-Vorschau 10s statt Standard 5s
"""

import argparse
import time

import cv2

SNAPSHOT_PATH = "camera_test_snapshot.png"


def find_camera(max_device_index=5):
    """Probiert Geräteindizes durch, gibt (index, geöffnetes VideoCapture) zurück oder (None, None)."""
    for index in range(max_device_index):
        print(f"Versuche Geräteindex {index} ...")
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ok, frame = cap.read()
            if ok and frame is not None:
                print(f"  -> Geräteindex {index} funktioniert.")
                return index, cap
            print(f"  -> Geräteindex {index} öffnet sich, liefert aber keinen Frame.")
        cap.release()
    return None, None


def main():
    parser = argparse.ArgumentParser(description="Einfacher, Hailo-unabhängiger Kameratest")
    parser.add_argument("--device", type=int, default=None,
                         help="Gezielter Geräteindex (z.B. 0 für /dev/video0). "
                              "Ohne Angabe werden Indizes 0-4 durchprobiert.")
    parser.add_argument("--no-preview", action="store_true",
                         help="Kein Live-Vorschaufenster anzeigen (z.B. über SSH ohne Display)")
    parser.add_argument("--seconds", type=float, default=5.0,
                         help="Dauer der Live-Vorschau in Sekunden (Standard: 5)")
    args = parser.parse_args()

    if args.device is not None:
        print(f"Öffne Geräteindex {args.device} ...")
        cap = cv2.VideoCapture(args.device)
        index = args.device
        if not cap.isOpened():
            print(f"FEHLER: Geräteindex {args.device} lässt sich nicht öffnen.")
            return
    else:
        index, cap = find_camera()
        if cap is None:
            print("FEHLER: Keine funktionierende Kamera gefunden (Indizes 0-4 probiert).")
            print("Prüfen: ist die Kamera angeschlossen? 'ls /dev/video*' zeigt verfügbare Geräte.")
            return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    backend = cap.getBackendName()

    print(f"\n--- Kamera-Info (Geräteindex {index}) ---")
    print(f"Auflösung: {width}x{height}")
    print(f"FPS (gemeldet): {fps}")
    print(f"Backend: {backend}")

    ok, frame = cap.read()
    if not ok or frame is None:
        print("FEHLER: Konnte keinen Frame lesen.")
        cap.release()
        return

    cv2.imwrite(SNAPSHOT_PATH, frame)
    print(f"\nSnapshot gespeichert als {SNAPSHOT_PATH} ({frame.shape[1]}x{frame.shape[0]}).")
    print("Schau ihn dir an, um Ausrichtung (gespiegelt?) und Bildausschnitt zu prüfen.")

    if args.no_preview:
        cap.release()
        return

    print(f"\nLive-Vorschau für {args.seconds:.0f} Sekunden (Fenster schließen oder 'q' drücken zum Abbrechen) ...")
    start = time.time()
    frame_count = 0
    while time.time() - start < args.seconds:
        ok, frame = cap.read()
        if not ok:
            print("WARNUNG: Frame konnte nicht gelesen werden, breche Vorschau ab.")
            break
        frame_count += 1
        elapsed = time.time() - start
        live_fps = frame_count / elapsed if elapsed > 0 else 0
        cv2.putText(frame, f"{live_fps:.1f} FPS  |  {frame.shape[1]}x{frame.shape[0]}  |  'q' zum Beenden",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imshow("Kamera-Test (camera_test.py)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nVorschau beendet. {frame_count} Frames in {time.time()-start:.1f}s "
          f"({frame_count/(time.time()-start):.1f} FPS im Schnitt).")


if __name__ == "__main__":
    main()
