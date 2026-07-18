# Crash nach ~8389 Frames + hängende Pipeline — Diagnose & Fix

**Stand 15.07.2026.** Zwei getrennte Probleme, unterschiedlich behandelbar.

## Symptome
1. `terminate called after throwing an instance of 'std::system_error' — what(): Invalid argument` nach ~8389 Frames.
2. App bleibt danach auf „Status: läuft (PID 4945)" hängen, Neustart blockiert.

---

## Problem B (sicher gefixt): App hängt auf „läuft"

**Ursache:** `core.py` stürzt durch einen **nativen C++-Fehler** ab
(`terminate()` → SIGABRT). Dabei durchläuft der Prozess NICHT den sauberen
SIGINT-Shutdown und schließt `stdout` nicht ordentlich — das Signal
`__PROCESS_ENDED__` kommt nie in der App an. Der bisherige `_poll_output()`
verließ sich allein auf dieses stdout-Signal und merkte daher nie, dass der
Prozess tot ist. Folge: `self.process` blieb gesetzt, Status blieb „läuft",
Start-Button blockiert.

**Fix in `app.py`:**
- **Liveness-Check im Poll:** `_poll_output()` prüft jetzt zusätzlich
  `self.process.poll()`. Sobald der Prozess weg ist (egal ob sauber oder hart
  abgestürzt), wird aufgeräumt — auch ohne stdout-Signal.
- **Exit-Code sichtbar:** `_on_process_ended(exit_code)` unterscheidet
  reguläres Ende, SIGINT-Stopp und Absturz. Ein nativer Crash zeigt jetzt
  „Status: ABGESTÜRZT (Signal 6) — siehe Log. Neustart über 'Start' möglich."
  statt stumm hängen zu bleiben. Idempotent (stdout-Signal UND poll() dürfen
  beide feuern).
- **Stop eskaliert:** `_stop_pipeline()` schickt SIGINT und fasst bei Bedarf
  nach — nach 4 s SIGTERM, nach weiteren 3 s SIGKILL. So bleibt kein Zombie
  zurück, wenn der Prozess in nativem Hailo-/GStreamer-Code festhängt.

**Verifiziert:** Exit-Code-Interpretation korrekt für Ende(0), SIGINT(-2),
SIGABRT(-6, dein Fall) und Fehler-Exit(1).

**Wirkung:** Der native Crash lässt sich damit zwar nicht verhindern, aber die
App erholt sich davon sauber — Status wird korrekt, Neustart ist sofort möglich,
kein hängender PID mehr.

---

## Problem A (abgefedert): der native Crash selbst

`std::system_error: Invalid argument` stammt aus der Hailo/GStreamer-C++-Ebene,
nicht aus dem Python-Code. Der Frame-Callback ist sauber (keine Threads, keine
offenen Dateien, keine matplotlib-Figures pro Frame). Ein solcher Fehler nach
mehreren tausend Frames deutet auf **Ressourcenerschöpfung in der nativen
Ebene** (Thread-/Handle-Limit) — ein bekanntes Muster bei Hailo-Dauerläufen,
das sich aus Python heraus nicht sicher beheben lässt.

**Was ich beheben konnte — ein realer Speicher-Wachstumspfad:**
`TrackingState.flushed_objects` war eine **unbegrenzt wachsende Liste** — bei
8389 Frames mit hoher Track-Dichte sammeln sich dort tausende dicts an. Das ist
zwar nicht sicher die Crash-Ursache, aber ein echtes Leck. Fix in `tracking.py`:
Liste → `collections.deque(maxlen=MAX_FLUSHED_OBJECTS)` (Default 500 in
`config.py`). Die Deque behält nur die letzten 500 Tracks fürs Flush-Bild;
**`ergebniss.csv` enthält weiterhin ALLE Tracks**. Nebeneffekt: Das
Flush-Bewegungsbild wird bei Langläufen wieder lesbar statt tausende
überlagerte Linien.

**Verifiziert:** 8389 Appends → deque hält konstant 500 Objekte.

---

## Empfehlungen zur weiteren Eingrenzung von Problem A

Falls der Crash trotz Abfederung wiederkehrt, hilft folgendes beim Eingrenzen
(reihenfolge nach Aufwand):

1. **Thread-Zahl beobachten** während eines Laufs:
   ```bash
   watch -n 5 'ls /proc/$(pgrep -f core.py)/task | wc -l'
   ```
   Steigt die Zahl monoton, ist es ein Thread-Leck in der nativen Ebene →
   Hailo-Version/Issue prüfen.
2. **File-Descriptors beobachten:**
   ```bash
   watch -n 5 'ls /proc/$(pgrep -f core.py)/fd | wc -l'
   ```
3. **HailoRT-/Tappas-Version** notieren und gegen bekannte Issues zu
   Langzeitstabilität abgleichen (Hailo Community). Firmware ist 4.23.0.
4. **Reproduzierbarkeit:** Tritt der Crash immer um ~8389 Frames auf oder
   variabel? Konstant → deterministisch (eher Puffer/Index); variabel → eher
   Ressourcenerschöpfung.
5. **Watchdog-Ansatz** (falls der Crash nicht behebbar ist): Da die App den
   Absturz jetzt sauber erkennt, könnte sie optional automatisch neu starten.
   Bewusst NICHT eingebaut, weil ein Auto-Restart einen wiederkehrenden Bug
   verschleiern würde — erst Ursache verstehen. Für den Dauerbetrieb am
   Volkspark (17 Sensoren) wäre ein solcher Watchdog aber sinnvoll.

---

## Geänderte Dateien
```
app.py       Liveness-Check im Poll, Exit-Code-Anzeige, Stop-Eskalation
tracking.py  flushed_objects als deque(maxlen=MAX_FLUSHED_OBJECTS)
config.py    MAX_FLUSHED_OBJECTS = 500
```

## Für die Arbeit (Limitationen / Ausblick)
Der native Langzeit-Crash ist eine belegbare Limitation für den unbeaufsichtigten
Dauerbetrieb (Kapitel 5.d / 6.d). Relevanter Punkt: Ein produktiver 24/7-Sensor
am Volkspark braucht einen Prozess-Watchdog (systemd `Restart=on-failure` o. ä.),
der abgestürzte Läufe automatisch neu startet — die App-seitige saubere
Absturzerkennung ist dafür die Voraussetzung.
