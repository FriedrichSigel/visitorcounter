"""
tabs/ — Seiten der App (app.py), je Seite/Bereich ein Mixin.

app.py bleibt dadurch die "Klammer": Fenster, Sidebar, Navigation, Autostart/
Aufwärmlauf, Design-Umschaltung. Alles, was zu einer einzelnen Seite gehört
(Aufbau der Widgets + zugehörige Ereignis-Handler), lebt in einem eigenen
Modul hier und wird über eine Mixin-Klasse in MainApp eingemischt.

Warum Mixins statt eigener Objekte je Seite: alle Seiten teilen sich denselben
Tk-Zustand (Variablen, Prozess-Handles, Ausgabe-Queue) und rufen sich
gegenseitig auf (z. B. startet Tab 5 dieselbe Pipeline wie Tab 3). Eigene
Objekte bräuchten dafür eine breite Schnittstelle zurück zu MainApp - ein
Mixin pro Datei erreicht dieselbe Trennung der Zuständigkeiten (Separation of
Concerns) ohne diesen Umweg. Details und Begründung:
../docs/entwicklung/cleancode.md.
"""
