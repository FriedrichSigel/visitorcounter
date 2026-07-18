# Auto-Konfiguration in Tab 5 isoliert + Zeitlimit entkoppelt

**Stand 15.07.2026.** Zwei zusammenhängende Änderungen in `app.py` und `config.py`.

## Der eigentliche Bug: Zeitlimit galt für ALLE Läufe

`config.py` hatte `RUN_DURATION_SECONDS = 300` als **Default**, wenn keine
Env-Var gesetzt war. Dadurch wurde **jeder** Lauf nach 300 s gestoppt — auch ein
ganz normaler Zähllauf ohne Datensammlung. Genau das war die Ursache für „wurde
nach [5 min] gestoppt, weil vom autoconfig noch ein Timelimit existiert".

**Fix:** `RUN_DURATION_SECONDS = int(_env_duration) if _env_duration else None`
→ Standard ist jetzt **kein Zeitlimit**. `core.py` war schon korrekt
abgesichert (`if RUN_DURATION_SECONDS is not None:`), der Timer wird also nur
noch gesetzt, wenn wirklich eine Dauer vorgegeben ist.

## Tab 5 „Auto-Konfiguration" (neu)

Der komplette Datensammlungs-Teil (früher als Block in Tab 3 „Start") ist jetzt
ein eigener Tab 5:
- **Sammeldauer**-Feld (= Zeitlimit, das NUR für die Datensammlung gilt).
- **Start/Stop**-Buttons, die `core.py` mit `AUTO_CONFIG_COLLECTION_ENABLED=true`
  und der Sammeldauer als `RUN_DURATION_SECONDS` starten.
- Klarer Ablauf-Hinweis: sammeln → in Tab 2 auswerten (Clustering/Randraster).

Die **Verfahrens-Auswertung** (DBSCAN/Randraster → `roi_config.json`) bleibt
bewusst in Tab 2, weil sie zur Geometrie-*Auswahl* gehört — Tab 5 ist nur das
Sammeln der Rohdaten. Das entspricht der getroffenen Entscheidung („3 nach Tab
5", Auswertung bleibt bei der übrigen Konfiguration).

## Tab 3 „Start" (normaler Zähllauf)

- Datensammlungs-Block entfernt.
- Neu: **optionales** Zeitlimit-Feld „Laufdauer (Sekunden, leer = kein Limit)".
  Standard leer → normale Läufe laufen ohne Timeout (bis Video-Ende oder Stopp).
- Hinweis ergänzt, dass die Live-Vorschau bei sehr langen Läufen instabil werden
  kann (Bezug zum Frame-Anzeige-Crash — ohne `--use-frame` lief es durch).

## Verhalten jetzt

| Start über | Datensammlung | Zeitlimit |
|---|---|---|
| Tab 3 (normaler Lauf) | nein | nur wenn Feld gefüllt, sonst KEINS |
| Tab 5 (Auto-Konfiguration) | ja | Sammeldauer (leer = unbegrenzt) |

`_start_pipeline(collection=False|True)` steuert beide Fälle; die Prozess-/
Button-Verwaltung (inkl. der Crash-Erkennung aus dem vorigen Fix) ist geteilt,
Tab-5-Buttons werden bei Prozessende mit zurückgesetzt.

## Verifiziert
- Syntax `app.py`, `config.py` OK.
- `RUN_DURATION_SECONDS`: ohne Env → None (kein Limit), mit Env → Wert.
- Keine verwaisten Referenzen (alte `collection_enabled_var` entfernt).

## Geänderte Dateien
```
app.py     Tab 5 neu, Tab 3 ohne Datensammlung + optionales Limit,
           _start_pipeline(collection=...) generalisiert
config.py  RUN_DURATION_SECONDS Default None statt 300
```

## Zusammenhang mit dem Frame-Crash
Deine Beobachtung „ohne View lief es durch" bestätigt: Der native Crash hängt an
der Live-Vorschau (`--use-frame`), nicht am Tracking. Für Dauerläufe also
Vorschau aus. Der separate Crash-Fix (Liveness-Check, deque-Deckel) bleibt
davon unberührt gültig.
