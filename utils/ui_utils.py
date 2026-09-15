"""
ui_utils.py — kleine, wiederverwendbare CustomTkinter-Hilfsfunktion.

Bewusst in einer eigenen Datei statt in roi_config_app.py oder app.py:
beide brauchen dieselbe Scroll-Logik (app.py für seine Seiten,
roi_config_app.py für die eigenständige Nutzung ohne app.py).
"""

import customtkinter as ctk


def make_scrollable(parent):
    """
    Erstellt einen scrollbaren Container in `parent` (CTkScrollableFrame,
    CustomTkinters eingebaute Lösung — mit Bildlaufleiste und Mausrad-
    Unterstützung schon eingebaut) und gibt ihn zurück. Dort hineinbauen,
    wo man sonst direkt in `parent` gebaut hätte.

    Notwendig, weil ein einzelner Bereich (z. B. die Konfigurations-Seite
    mit Auto-Konfigurations-Panel) auf kleineren Bildschirmen mehr Platz
    braucht, als sichtbar ist.
    """
    scroll_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll_frame.pack(fill="both", expand=True)
    return scroll_frame
