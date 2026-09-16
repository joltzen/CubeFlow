# CubeFlow

Ein interaktiver Rubik's-Cube-Visualizer für Scrambles: CubeFlow generiert eine zufällige 20-Zug-Sequenz und lässt dich sie Schritt für Schritt (oder automatisch) mit einer echten 3D-Ebenendreh-Animation nachvollziehen.

Gebaut mit Python und [PySide6](https://doc.qt.io/qtforpython-6/) (Qt for Python) — das komplette 3D-Rendering (Projektion, Verdeckung, Schicht-Animation) ist selbst geschrieben, per `QPainter` auf ein 2D-Canvas gezeichnet, ganz ohne OpenGL/3D-Engine.

## Features

- **Zufälliger Scramble** — 20 Züge nach WCA-Notation (`R`, `U'`, `F2`, …), ohne zwei aufeinanderfolgende Züge auf derselben Fläche.
- **Schritt-für-Schritt-Navigation** — Vor/Zurück durch den Scramble, mit hervorgehobenem nächsten Zug (Text + Scramble-Anzeige + Outline auf dem Würfel).
- **Echte 3D-Dreh-Animation** — die betroffene Ebene löst sich sichtbar vom restlichen Würfel und dreht sich um die Zugachse, statt den Zustand nur zu "snappen".
- **Auto-Scramble** — spielt die komplette Sequenz automatisch ab, ohne dass für jeden Zug geklickt werden muss.
- **Einstellbare Geschwindigkeit** — Slider mit 5 Stufen (Sehr langsam … Sehr schnell), wirkt sofort auf laufende und künftige Züge.
- **Frei drehbare Kamera** — Ansicht per Maus-Drag rotierbar; die Kamera bewegt sich nie von selbst, außer der Nutzer dreht sie.
- **Neuer Scramble** — Würfel jederzeit zurücksetzen und neu mischen.

## Voraussetzungen

- Python ≥ 3.12
- PySide6 ≥ 6.8

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Starten

```bash
cubeflow
```

oder ohne Installation als Skript:

```bash
python -m cubeflow.main
```

## Projektstruktur

```
src/cubeflow/
├── main.py                        # Einstiegspunkt: QApplication, Stylesheet laden, MainWindow zeigen
├── cube/                          # Reine Würfel-Logik, UI-unabhängig
│   ├── enums.py                   # Face, Turn, INVERSE_TURN
│   ├── move.py                    # Move-Dataclass (Face + Turn, WCA-String-Repräsentation)
│   ├── cube_state.py              # CubeState: Cubie/Sticker-Modell, Zugausführung
│   └── scramble_generator.py      # Zufällige Scramble-Erzeugung
└── ui/
    ├── main_window.py             # Orchestriert Scramble-Fortschritt, Auto-Play, Status-Text
    ├── styles/main.qss            # Dark-Theme-Stylesheet
    └── widgets/
        ├── cube_widget.py         # 3D-Rendering + Ebenen-Dreh-Animation (das Herzstück)
        ├── navigation_widget.py   # Buttons (Zurück/Weiter/Neuer Scramble/Auto), Speed-Slider, Fortschrittsbalken
        └── scramble_widget.py     # Zeigt die Zugliste mit Hervorhebung/Durchstreichung an
```

## Architektur

### Würfelmodell (`cube/`)

Der Würfel wird **nicht** als Menge starrer 3×3×3-Facelets modelliert, sondern als 26 **Cubies** (alle Positionen `(x, y, z) ∈ {-1,0,1}³` außer dem Zentrum). Jeder Cubie ist ein Dict `{Normalenvektor → Face}` für seine sichtbaren Sticker:

```python
CubeState.cubies: dict[Vector3, dict[Vector3, Face]]
#                  Position  →   {Sticker-Normale → Farbe/Face}
```

Ein Zug (`apply_move`) wird als Rotation der betroffenen Schicht ausgeführt: Alle Cubies mit `position[axis] == layer_value` werden aus dem Dict entfernt, ihre Position **und** ihre Sticker-Normalen werden mit einer festen 90°-Transformationsfunktion (`_turn_right`, `_turn_up`, …) neu berechnet und wieder eingefügt. `Turn.COUNTERCLOCKWISE`/`DOUBLE` sind einfach 3×/2× dieselbe Vierteldrehung. Da jede Transformation eine reine Permutation ist, bleibt der Würfelzustand immer exakt konsistent — es gibt keine Fließkomma-Drift.

`build_state(moves)` baut aus einer Zugliste einen frischen `CubeState` — damit lässt sich der Zustand an jedem beliebigen Schritt des Scrambles verlustfrei neu berechnen, statt ihn inkrementell mitzuführen.

### Rendering (`ui/widgets/cube_widget.py`)

Kein 3D-Framework — stattdessen eine handgeschriebene Mini-Pipeline:

1. **Projektion**: Jeder der 54 sichtbaren Sticker (9 pro Fläche × 6 Flächen) wird aus 3D-Eckpunkten berechnet, erst um die Kamera-Rotation (`rotation_x`/`rotation_y`, per Maus-Drag änderbar), dann orthografisch auf den Bildschirm projiziert (`_project_vertex`).
2. **Tiefensortierung (Painter's Algorithm)**: Alle 54 Sticker-Polygone werden nach ihrer projizierten Tiefe sortiert und von hinten nach vorne gezeichnet (`paintEvent`/`_face_stickers`). Das passiert **pro Sticker**, nicht pro Fläche — wichtig, damit während einer Drehung einzelne Sticker korrekt vor/hinter benachbarten Flächen erscheinen.
3. **Schattierung**: Helligkeit pro Sticker ergibt sich aus der Tiefe seiner Normalen nach Rotation (`_sticker_brightness`) — Flächen, die schräger zur Kamera stehen, wirken dunkler.

### Zug-Animation

`animate_turn(state_before, move, state_after)` startet einen `QTimer` (`_layer_animation_timer`), der pro Frame den Rotationswinkel der betroffenen Schicht per Smoothstep-Easing von 0 auf den Zielwinkel (±90°/180°, abhängig von `Turn`) hochzählt. Während der Animation:

- werden nur die Sticker der **betroffenen Schicht** zusätzlich um die Zugachse rotiert (`_rotate_about_axis`), alle anderen bleiben unverändert;
- wird ein dunkles "Backer"-Polygon (`_layer_gap_backer`) an der ursprünglichen Position der drehenden Fläche eingefügt, das immer ganz hinten liegt — es füllt die Lücke, die entsteht, wenn sich die Schicht wegdreht, sodass es wie ein massiver Würfelkörper statt wie ein Loch in den Hintergrund wirkt.
- Am Ende der Animation "rastet" der Zustand exakt auf `state_after` ein, und das `turn_finished`-Signal wird emittiert.

Die Animationsgeschwindigkeit (`_layer_animation_steps_total`) ist zur Laufzeit über `set_turn_speed()` einstellbar (siehe Speed-Slider).

Die **Kamera** wird durch Züge nie automatisch bewegt — sie ändert sich ausschließlich durch Maus-Drag (`mouseMoveEvent`). Das cyan Outline um die hervorgehobene Fläche (`highlighted_face`) dreht während einer Animation korrekt mit, falls die hervorgehobene Fläche gerade die drehende ist.

### UI-Orchestrierung (`ui/main_window.py`)

`MainWindow` hält den eigentlichen Navigationszustand (`scramble: list[Move]`, `current_step: int`) und berechnet Vorher-/Nachher-Zustand für jeden Schritt per `build_state(scramble[:step])` — dadurch bleibt Vor-/Zurückspringen immer exakt, unabhängig von der Animation. Rückwärtsschritte animieren den **inversen** Zug (`INVERSE_TURN`).

Auto-Scramble verkettet `next_step()`-Aufrufe über das `turn_finished`-Signal von `CubeWidget`, statt einen eigenen Timer zu benutzen — jeder Zug wird also erst gestartet, wenn der vorherige fertig animiert ist.

## Code-Stil

Kurz gehaltene, reine Funktionen für die Würfel-Mathematik, benannte Konstanten statt Magic Numbers, keine Kommentare für offensichtlichen Code — nur dort, wo eine nicht offensichtliche Design-Entscheidung (z. B. die Backer-Fläche oder die Vorzeichen-Konvention der Rotationswinkel) sonst überraschend wäre.
