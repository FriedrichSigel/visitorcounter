# Festes Layout 1/5 – 3/5 – 1/5, Fensterbreite fixiert

**Stand 15.07.2026.** `app.py` und `roi_config_app.py`.

## Anforderung
Feste Aufteilung: 1/5 Sidebar links, 3/5 Frame-Bereich Mitte, 1/5 Konfig-Spalte
rechts. Das Fenster darf unter keinen Umständen breiter werden.

## Ursache des bisherigen Verhaltens
Der Frame-Canvas in Tab 2 hatte eine feste Breite (960px) und lag in einem
Content-Bereich **ohne** Breitenbegrenzung. Dadurch diktierte der Canvas +
Bedienspalte die Mindestbreite von Tab 2 — größer als die übrigen Tabs, also
„brauchte die App auf einmal mehr Platz". Die Sidebar hatte zudem eine feste
Pixelbreite (210), kein Verhältnis.

## Lösung: alles aus einer festen Fensterbreite ableiten

In `app.py` zentrale Konstanten:
```
WINDOW_WIDTH  = 1150   (feste Fensterbreite)
SIDEBAR_WIDTH = 230    (1/5)
CONTENT_WIDTH = 920    (4/5)
CONFIG_FRAME_WIDTH = 640   (Canvas in Tab 2, ~3/5 des Fensters)
```

Umgesetzt:
- **Fenster in der Breite fixiert:** `minsize(WINDOW_WIDTH, …)` +
  `maxsize(WINDOW_WIDTH, Bildschirmhöhe)` — Breite unveränderlich, Höhe darf
  wachsen (für Scrollbereiche).
- **Sidebar = 1/5:** `width=SIDEBAR_WIDTH` (statt fester 210).
- **Content = 4/5 mit fester Breite:** `width=CONTENT_WIDTH` +
  `pack_propagate(False)` — der Inhalt kann die Content-Fläche nicht mehr
  aufweiten; überschüssige Breite wird begrenzt statt das Fenster zu sprengen.
- **Canvas an die 3/5-Spalte gebunden:** `RoiConfigApp` nimmt jetzt einen
  Parameter `frame_width`; `app.py` übergibt `CONFIG_FRAME_WIDTH`. Der Canvas
  ist damit 640×360 (16:9) und diktiert die Breite nicht mehr.

## Erreichtes Verhältnis (bei 1150px)
```
Sidebar   230px = 20%   ✓ 1/5
Frame     640px = 56%   ✓ ~3/5
Konfig    280px = 24%   ✓ ~1/5 (etwas mehr, damit Buttons/Labels lesbar bleiben)
```

Die Frame-Fläche trifft die geforderten ~60%; die Konfig-Spalte braucht inkl.
Ränder/Scrollbalken etwas mehr als exakt 20%, damit die Bedienelemente nicht
abgeschnitten werden. Wenn du exaktere 20/60/20 willst: `WINDOW_WIDTH` erhöhen
(z. B. 1280) — die Verhältnisse skalieren automatisch mit, weil alles daraus
abgeleitet ist.

## Standalone-Modus unverändert
`roi_config_app.py` als eigenständiges Tool (`main()`) ruft `RoiConfigApp` ohne
`frame_width` auf → Default `DISPLAY_WIDTH=960` greift weiter. Nur die in
`app.py` eingebettete Variante nutzt die feste 640er-Breite.

## Anpassen
Alles hängt an `WINDOW_WIDTH` in `app.py`. Größer/kleiner: nur diesen Wert
ändern, Sidebar und Content skalieren mit. Den Canvas (`CONFIG_FRAME_WIDTH`)
dabei so wählen, dass Canvas + ~280px Konfigspalte in `CONTENT_WIDTH` passen.

## Geänderte Dateien
```
app.py             WINDOW_WIDTH-Konstanten, feste Sidebar/Content-Breiten,
                   maxsize-Breitensperre, frame_width an RoiConfigApp
roi_config_app.py  RoiConfigApp(master, frame_width=None); Canvas + Skalierung
                   nutzen self.display_width/height statt Modulkonstanten
```
