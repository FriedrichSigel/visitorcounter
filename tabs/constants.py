"""
tabs/constants.py — von app.py und den Tab-Mixins gemeinsam genutzte
Konstanten (Dateipfade, Layout-Maße).

Eigene Datei statt in app.py: die Mixins in tabs/ werden von app.py
eingemischt (MainApp erbt von ihnen) und dürfen deshalb nicht ihrerseits aus
app.py importieren - das gäbe einen Zirkelimport. Diese Datei hat keine
Abhängigkeit in die andere Richtung und kann daher von beiden Seiten sicher
importiert werden.
"""

ZAEHLUNG_CSV = "zaehlung.csv"
ROI_CONFIG_PATH = "roi_config.json"

# --- Feste Layout-Maße (alles aus der Fensterbreite abgeleitet) ---
# Das Fenster wird in der Breite nie größer. Aufteilung: 1/5 Sidebar,
# 4/5 Content. In Tab 2 (Konfiguration) teilt sich der Content in 3/4 Frame-
# Bereich (= 3/5 des Fensters) und 1/4 Konfig-Spalte (= 1/5 des Fensters).
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 760
SIDEBAR_WIDTH = WINDOW_WIDTH // 5           # 1/5 = 256
CONTENT_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH  # 4/5 = 1024
# Innerhalb von Tab 2: Frame-Bereich (~3/5 des Fensters). Wert so gewählt,
# dass Canvas + Bedienspalte + Scrollbalken sicher in CONTENT_WIDTH passen.
CONFIG_FRAME_WIDTH = 660    # Canvas-Breite (16:9 -> 371 hoch), ~0.52 der Fensterbreite

# Höhe der LoRa-Hinweisbox in Pixeln: klein, solange LoRa aus ist,
# hoch genug für die komplette Byte-Tabelle, sobald es an ist.
LORA_HINT_HEIGHT_OFF = 54
LORA_HINT_HEIGHT_ON = 300
