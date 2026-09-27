"""
Kompatibilitätsschicht zu hailo_apps und GStreamer.

Zwei Dinge haben sich zwischen den Versionen geändert, die das Projekt
benutzt. Beide werden hier gekapselt, damit der restliche Code nur eine
Importquelle kennt und auf alten wie neuen Geräten unverändert läuft.

1) PAKETSTRUKTUR VON hailo_apps
   Bis 25.7.0:  hailo_apps.hailo_app_python.core.common.buffer_utils
                hailo_apps.hailo_app_python.apps.detection.detection_pipeline
                hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app
   Ab 26.03.x:  hailo_apps.python.core.common.buffer_utils
                hailo_apps.python.pipeline_apps.detection.detection_pipeline
                hailo_apps.python.core.gstreamer.gstreamer_app
   Der Zwischenordner heisst jetzt `python` statt `hailo_app_python`, und die
   Pipelines liegen unter `pipeline_apps` statt `apps`.

2) Gst.Caps.get_structure() IN GSTREAMER 1.26.2
   In 1.26.2 liefert get_structure() einen `StructureWrapper`, der die
   Methoden des eigentlichen Gst.Structure nicht durchreicht — weder
   .get_value() noch dict-artigen Zugriff. hailo_apps ruft aber
   structure.get_value('format'), auch noch in 26.03.1, und laeuft damit in
   einen AttributeError.

   Das ist besonders tueckisch, weil der Aufruf im GStreamer-Pad-Probe-
   Callback steckt: wirft der eine Exception, gibt PyGObject `None` an
   GStreamer zurueck, was als PadProbeReturn.DROP (= 0) gilt. Jeder Frame
   wird verworfen, die Pipeline scheint einzufrieren, und der Traceback
   erscheint nur einmal.

   Behoben ist der Bug in GStreamer 1.26.3. Solange ein Geraet auf 1.26.2
   steht, packt get_caps_from_pad() hier den Wrapper ueber sein privates
   Attribut `_StructureWrapper__structure` aus.
   Siehe: https://discourse.gstreamer.org/t/python-get-structure-api-change/4767

   SOBALD ALLE GERAETE AUF GSTREAMER >= 1.26.3 SIND, kann get_caps_from_pad()
   hier entfallen und wieder direkt aus hailo_apps importiert werden.
"""

# ---------------------------------------------------------------------------
# 1) Importe aus hailo_apps — neues Layout zuerst, altes als Rueckfall
# ---------------------------------------------------------------------------
try:                                                  # ab 26.03.x
    from hailo_apps.python.core.common.buffer_utils import get_numpy_from_buffer
    from hailo_apps.python.pipeline_apps.detection.detection_pipeline import (
        GStreamerDetectionApp,
    )
    from hailo_apps.python.core.gstreamer.gstreamer_app import app_callback_class
    HAILO_APPS_LAYOUT = "python"
except ImportError:                                   # bis 25.7.0
    from hailo_apps.hailo_app_python.core.common.buffer_utils import (
        get_numpy_from_buffer,
    )
    from hailo_apps.hailo_app_python.apps.detection.detection_pipeline import (
        GStreamerDetectionApp,
    )
    from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import (
        app_callback_class,
    )
    HAILO_APPS_LAYOUT = "hailo_app_python"


# ---------------------------------------------------------------------------
# 2) Caps auslesen, unabhaengig von der GStreamer-Version
# ---------------------------------------------------------------------------
def _entpacke_structure(structure):
    """Gibt ein Objekt zurueck, das .get_value() versteht.

    In GStreamer 1.26.2 ist `structure` ein StructureWrapper, der die echte
    Struktur im privaten Attribut `_StructureWrapper__structure` haelt.
    Ab 1.26.3 kommt das Gst.Structure direkt und wird unveraendert
    durchgereicht.
    """
    if hasattr(structure, "get_value"):
        return structure
    return getattr(structure, "_StructureWrapper__structure", None)


def get_caps_from_pad(pad):
    """Videoformat, Breite und Hoehe aus den Pad-Capabilities lesen.

    Ersetzt hailo_apps' gleichnamige Funktion (siehe Modulkopf, Punkt 2).
    Gibt (None, None, None) zurueck, wenn die Caps noch nicht ausgehandelt
    sind oder ein Feld fehlt — nie eine Exception, damit der Pad-Probe-
    Callback nicht versehentlich alle Buffer verwirft.
    """
    if pad is None:
        return None, None, None

    caps = pad.get_current_caps()
    if caps is None or caps.get_size() == 0:
        return None, None, None

    structure = _entpacke_structure(caps.get_structure(0))
    if structure is None:
        return None, None, None

    def feld(name):
        try:
            return structure.get_value(name)
        except Exception:
            return None

    return feld("format"), feld("width"), feld("height")


# ---------------------------------------------------------------------------
# 3) Callback-Signatur, unabhaengig von der hailo_apps-Version
# ---------------------------------------------------------------------------
# Bis 25.7.0 haengt der Pro-Frame-Callback als Pad-Probe am identity-Element
# und bekommt (pad, info, user_data); der Buffer kommt aus info.get_buffer(),
# und der Rueckgabewert muss ein Gst.PadProbeReturn sein.
#
# Ab 26.03.x haengt er am `handoff`-Signal desselben Elements und bekommt
# (element, buffer, user_data) — der Buffer also direkt. Der Rueckgabewert
# wird ignoriert. Ausserdem ruft der Wrapper von hailo_apps bereits selbst
# user_data.increment() auf; wer das im eigenen Callback wiederholt, zaehlt
# jeden Frame doppelt. Dafuer gibt es WRAPPER_ZAEHLT_FRAMES.

# True, wenn hailo_apps den Frame-Zaehler selbst hochzaehlt (ab 26.03.x).
WRAPPER_ZAEHLT_FRAMES = (HAILO_APPS_LAYOUT == "python")


def entpacke_callback_argumente(erstes, zweites):
    """Normalisiert die beiden ersten Callback-Argumente auf (pad, buffer).

    Nimmt sowohl (pad, info) der alten als auch (element, buffer) der neuen
    Signatur entgegen und liefert immer ein Pad (fuer get_caps_from_pad) und
    den Gst.Buffer. Einer von beiden kann None sein, wenn er sich nicht
    ermitteln laesst — der Aufrufer muss das abfangen.
    """
    # Alte Form: das zweite Argument ist ein Pad-Probe-Info-Objekt.
    if hasattr(zweites, "get_buffer"):
        return erstes, zweites.get_buffer()

    # Neue Form: das zweite Argument ist bereits der Buffer, das erste das
    # GStreamer-Element (identity_callback), von dem wir das Pad holen.
    pad = None
    if hasattr(erstes, "get_static_pad"):
        pad = erstes.get_static_pad("sink") or erstes.get_static_pad("src")
    elif hasattr(erstes, "get_current_caps"):
        pad = erstes                      # es war doch schon ein Pad
    return pad, zweites


__all__ = [
    "get_caps_from_pad",
    "get_numpy_from_buffer",
    "GStreamerDetectionApp",
    "app_callback_class",
    "entpacke_callback_argumente",
    "HAILO_APPS_LAYOUT",
    "WRAPPER_ZAEHLT_FRAMES",
]
