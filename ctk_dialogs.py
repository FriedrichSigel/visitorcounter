"""
ctk_dialogs.py — CustomTkinter-Dialoge im dunklen App-Design als Ersatz für
tkinter.messagebox und tkinter.simpledialog.

Die Funktionssignaturen entsprechen den Originalen (showwarning/showerror/
showinfo/askyesno/askstring), damit bestehende Aufrufstellen nur den Modulnamen
wechseln müssen. Alle Dialoge sind modal (grab_set + wait_window) und liefern
denselben Rückgabetyp wie ihre tkinter-Pendants:
  - show*  -> None
  - askyesno -> bool
  - askstring -> str | None (None bei Abbrechen)
"""

import customtkinter as ctk

# Akzentfarben je Dialogtyp (Kopfzeile/Button), passend zum App-Design.
_ACCENT = {
    "info":    "#2E8B57",   # Grün wie der Speichern-/Start-Button
    "warning": "#D9A441",   # Gelb wie die Hinweis-Labels
    "error":   "#B23A3A",   # Rot wie der Stop-Button
    "question":"#3B7DD8",   # Blau (Theme-Akzent)
}
_HOVER = {
    "info":    "#256e46",
    "warning": "#b8862f",
    "error":   "#8f2e2e",
    "question":"#2f66b0",
}


def _center(win, parent, w, h):
    """Positioniert das Fenster mittig über dem Parent (oder Bildschirm)."""
    win.update_idletasks()
    try:
        px = parent.winfo_rootx() + parent.winfo_width() // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        x, y = px - w // 2, py - h // 2
    except Exception:
        x = (win.winfo_screenwidth() - w) // 2
        y = (win.winfo_screenheight() - h) // 2
    win.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")


def _base_dialog(title, message, kind, parent=None):
    """Baut ein modales Dialogfenster mit Kopfzeile, Nachricht und Button-Bereich.
    Gibt (Fenster, Button-Container) zurück — die Buttons setzt der Aufrufer."""
    win = ctk.CTkToplevel(parent)
    win.title(title)
    win.resizable(False, False)
    win.configure(fg_color="#242424")

    # Farbiger Kopfstreifen mit Titel
    header = ctk.CTkFrame(win, fg_color=_ACCENT.get(kind, "#3B7DD8"), corner_radius=0, height=44)
    header.pack(fill="x")
    header.pack_propagate(False)
    ctk.CTkLabel(header, text=title, font=ctk.CTkFont(size=15, weight="bold"),
                 text_color="white").pack(anchor="w", padx=16, pady=8)

    # Nachrichtentext
    ctk.CTkLabel(win, text=message, font=ctk.CTkFont(size=13),
                 wraplength=380, justify="left").pack(padx=20, pady=(18, 12), anchor="w")

    btn_row = ctk.CTkFrame(win, fg_color="transparent")
    btn_row.pack(pady=(0, 16), padx=20, anchor="e")

    return win, btn_row


def _run_modal(win, parent):
    """Macht den Dialog modal und wartet, bis er geschlossen wird."""
    win.transient(parent)
    win.grab_set()
    if parent is not None:
        win.wait_window()
    else:
        win.wait_window(win)


def _show(title, message, kind, parent=None):
    win, btn_row = _base_dialog(title, message, kind, parent)
    _center(win, parent, 440, 200)
    ctk.CTkButton(btn_row, text="OK", width=100,
                  fg_color=_ACCENT.get(kind), hover_color=_HOVER.get(kind),
                  command=win.destroy).pack(side="right")
    win.bind("<Return>", lambda e: win.destroy())
    _run_modal(win, parent)


# --- messagebox-kompatible API -------------------------------------------

def showinfo(title, message, parent=None):
    _show(title, message, "info", parent)


def showwarning(title, message, parent=None):
    _show(title, message, "warning", parent)


def showerror(title, message, parent=None):
    _show(title, message, "error", parent)


def askyesno(title, message, parent=None):
    """Ja/Nein-Abfrage. Gibt True (Ja) oder False (Nein/Schließen) zurück."""
    result = {"value": False}
    win, btn_row = _base_dialog(title, message, "question", parent)
    _center(win, parent, 440, 200)

    def yes():
        result["value"] = True
        win.destroy()

    def no():
        result["value"] = False
        win.destroy()

    ctk.CTkButton(btn_row, text="Ja", width=90, fg_color=_ACCENT["question"],
                  hover_color=_HOVER["question"], command=yes).pack(side="right", padx=(8, 0))
    ctk.CTkButton(btn_row, text="Nein", width=90, fg_color="gray35",
                  hover_color="gray25", command=no).pack(side="right")
    win.bind("<Return>", lambda e: yes())
    win.bind("<Escape>", lambda e: no())
    _run_modal(win, parent)
    return result["value"]


def askstring(title, prompt, parent=None):
    """Texteingabe. Gibt den eingegebenen String zurück oder None bei Abbruch.
    Signatur-kompatibel zu tkinter.simpledialog.askstring."""
    result = {"value": None}
    win, btn_row = _base_dialog(title, prompt, "question", parent)

    entry = ctk.CTkEntry(win, width=340)
    entry.pack(padx=20, pady=(0, 8))
    entry.focus_set()

    _center(win, parent, 440, 230)

    def ok():
        result["value"] = entry.get()
        win.destroy()

    def cancel():
        result["value"] = None
        win.destroy()

    ctk.CTkButton(btn_row, text="OK", width=90, fg_color=_ACCENT["question"],
                  hover_color=_HOVER["question"], command=ok).pack(side="right", padx=(8, 0))
    ctk.CTkButton(btn_row, text="Abbrechen", width=90, fg_color="gray35",
                  hover_color="gray25", command=cancel).pack(side="right")
    win.bind("<Return>", lambda e: ok())
    win.bind("<Escape>", lambda e: cancel())
    _run_modal(win, parent)
    return result["value"]
