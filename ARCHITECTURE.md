# Litho — Architecture

A small, personal image annotation tool: open an image, draw polygons, text
boxes, highlights, freehand strokes, and lines/arrows on top of it, adjust
their color/size/opacity, and save/export back out (with format conversion
between PNG/JPG/BMP/etc.).

**Status snapshot** (update this line each session)
`2026-07-22` — Three trial-usage fixes landed on the Arrow tools today.
(1) Arrow/Double-arrow heads were a fixed 14px regardless of stroke size,
so a large enough Size value made the line thickness swallow the
arrowhead entirely — `LineItem`'s arrowhead length (canvas/items.py) now
scales with pen width (`max(ARROW_LENGTH_MIN, width *
ARROW_LENGTH_SCALE)`). (2) The shaft was drawn all the way to the tip and
the arrowhead painted on top, which left a visible seam at the head's
base (worse at partial opacity, where the overlap double-composites) —
`LineItem.paint()` now custom-draws a shortened `_shaft_line()` that
stops exactly at the arrowhead's base (`_arrow_base_distance = length *
cos(spread)`, not `length` itself — that's the distance to the base's
*corners*, not the base line) instead of delegating to
`QGraphicsLineItem.paint()`. Losing that delegation meant losing Qt's
free selection-highlight rendering too, so arrow lines now paint their
own dashed selection rect. (3) Along the way, switched the shaft's pen
cap from Round to `Qt.PenCapStyle.FlatCap` for any line with a head —
first tried `SquareCap`, which turned out to be a false friend: despite
the name it still extends half the pen width past the endpoint (same
bounding box as RoundCap, just square-shaped), which reintroduced the
seam at large widths; `FlatCap` is the one that actually stops exactly at
the endpoint. Plain lines (no head) are untouched by any of this — same
round cap, same `QGraphicsLineItem.paint()` delegation as before. (4)
Even cut exactly at the base, two separately-painted shapes meeting at a
precise seam still left a hairline anti-aliasing gap — added
`ARROW_SHAFT_OVERLAP = 1.5`, subtracted from the cutoff distance so the
shaft deliberately runs a little way into the head instead of stopping
exactly at its edge. Confirmed clean (no gap, no seam) at the toolbar's
default 100% opacity; at reduced opacity the overlap band very slightly
double-composites, which is a real but much more minor trade-off than the
gap it replaces — not fixed here, noted below.
Also landed the Freehand tool this session — `FreehandItem` subclasses
`QGraphicsPathItem`; `tools/freehand.py`'s `FreehandTool` starts a path
on press and calls `add_point()` on every subsequent move, same drag
lifecycle as the Highlighter tool. And audited which of the four style
controls (Stroke/Fill/Size/Opacity) each tool actually reads — several
were dead for a given tool with no indication in the UI — each `Tool`
subclass now declares `uses_stroke`/`uses_fill`/`uses_size`/
`uses_opacity` (tools/base.py), and
`MainWindow._update_style_controls_for_tool` greys out whichever don't
apply to the active tool. You can open an image, draw a highlight, a
line/arrow/double-arrow, a freehand stroke, place and edit text, switch
to Select, move any of them, and press Delete to remove it. Only Polygon
remains present but disabled — not implemented yet. Two known
inconsistencies from the style-control audit are still open: arrowheads
are filled with the Stroke color despite being a filled shape, and
Highlighter's Opacity is capped at a 0.4× multiplier while every other
tool applies it directly. Next: Polygon, then `commands.py` (undo/redo)
and `io.py` (save/export).

---

## 1. Goals / non-goals

**Goals**
- Fast to open, fast to annotate, fast to save. Single user, single machine.
- Small enough for one person to hold the whole codebase in their head.
- Runs on any general Linux distribution without dependency headaches.

**Non-goals** (explicitly out of scope, revisit only if a real need shows up)
- No layers panel, no multi-image tabs/workspaces, no plugin system.
- No cloud sync, accounts, or collaboration features.
- No raster editing (no brush/paint tools, filters, or pixel-level retouching)
  — this is an *annotation* tool over an existing image, not a paint program.
- No mobile/web build. Desktop Linux only.

Keeping this list visible is meant to stop scope creep as we go — if a
feature isn't on the toolbar mockup we agreed on, it needs a deliberate
decision to add, not a quiet drift.

---

## 2. Tech stack

| Concern | Choice | Why |
|---|---|---|
| Language | Python 3.13 | Fast to write/maintain; fast enough for this app's scale (rendering is the bottleneck, not Python itself). |
| GUI toolkit | PySide6 (Qt 6) | `QGraphicsView`/`QGraphicsScene` gives selectable, movable, resizable items almost for free — maps directly onto our tool set. LGPL, no licensing friction. |
| Env/deps | [`uv`](https://docs.astral.sh/uv/) | Fast, single tool for venv + dependency management + running scripts. |
| Testing | `pytest` + `pytest-qt` | `qtbot` fixture simulates clicks/drags/keystrokes for tool tests; plain pytest for everything else. |
| Packaging (later) | PyInstaller or Nuitka | Bundles the interpreter + Qt libs into one standalone executable — no venv needed at runtime. Not needed until the app actually works. |

No dependencies are pinned yet beyond what `uv init` created. `PySide6` (and
`pytest-qt` as a dev dependency) get added when we start on the first
component that needs them.

---

## 3. Design principles

- **Items vs. Tools vs. Commands, kept separate.**
  - *Items* (`canvas/items.py`) are `QGraphicsItem` subclasses — they only
    know how to draw and resize themselves.
  - *Tools* (`tools/`) are small state machines that turn mouse events into
    item creation/edits. One file per tool.
  - *Commands* (`commands.py`) are `QUndoCommand` subclasses that wrap every
    mutation (add/move/resize/delete/edit-text), giving us undo/redo via
    Qt's `QUndoStack` instead of hand-rolled state snapshots.

  This split means adding a new tool later touches two small files instead
  of one large one, and undo/redo isn't bolted on after the fact.

- **`main_window.py` stays thin.** It builds the toolbar UI and forwards
  input to whichever tool is active. It should never need to know *how* a
  polygon gets drawn.

- **`io.py` is separate from `canvas/scene.py`.** Loading/saving/format
  conversion is a different concern from scene management and should be
  testable (and tweakable) on its own.

- **GUI tests run headless.** `QT_QPA_PLATFORM=offscreen` lets the full Qt
  test suite run without a real display — same behavior on a desktop, over
  SSH, or in CI.

---

## 4. Project layout

Target structure. Items marked `(scaffold)` already exist from `uv init`;
everything else is created as we build each component.

```
litho/
├── pyproject.toml            (scaffold — uv-managed)
├── README.md                 (scaffold)
├── ARCHITECTURE.md           (this file)
├── .python-version           (scaffold — 3.13)
├── main.py                   (scaffold — becomes a thin shim into litho.__main__)
│
├── litho/                    # the application package
│   ├── __init__.py
│   ├── __main__.py           # entry point — `uv run python -m litho`
│   ├── main_window.py        # QMainWindow: builds the two toolbars, wires actions to tools/commands
│   │
│   ├── canvas/
│   │   ├── __init__.py
│   │   ├── scene.py          # QGraphicsScene — background image + all annotation items
│   │   ├── view.py           # QGraphicsView — zoom, pan, fit-to-window
│   │   └── items.py          # PolygonItem, TextBoxItem, LineItem, FreehandItem, HighlightItem
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py           # Tool interface (mouse press/move/release hooks)
│   │   ├── select.py         # move/resize/select existing items
│   │   ├── polygon.py        # click-to-place-vertex, double-click/enter to close
│   │   ├── line.py           # line / arrow / double-arrow via a mode flag
│   │   ├── freehand.py       # drag-to-draw path
│   │   ├── highlighter.py    # drag-to-draw translucent rect
│   │   └── text.py           # place a text box; enter/exit edit mode
│   │
│   ├── commands.py           # QUndoCommand subclasses — powers undo/redo
│   ├── io.py                 # open/save, format conversion, flatten annotations on export
│   └── icons.py              # toolbar icons (from the mockup SVGs)
│
└── tests/
    ├── conftest.py            # session-scoped QApplication fixture, shared fixtures
    ├── fixtures/
    │   └── sample.png
    ├── test_items.py          # resize math, bounding boxes
    ├── test_commands.py       # undo/redo correctness
    ├── test_io.py             # open/save round-trips, format conversion
    ├── test_export.py         # annotations flatten onto exported image correctly
    ├── test_tools_polygon.py
    ├── test_tools_line.py
    └── test_tools_text.py
```

---

## 5. UI reference

Two toolbars, both docked at the top (see the interface mockup). No status
bar, no side panels.

**Row 1 — file / edit / zoom**
New · Open · Save · export format dropdown (PNG/JPG/BMP) · Undo · Redo ·
zoom out / percentage / zoom in / fit-to-window

**Row 2 — tools + contextual properties**
Select · Polygon · Line · Arrow · Double-arrow · Freehand · Highlighter ·
Text box — then, for whatever's currently selected: stroke color, fill
color, size (stroke width for shapes, font size for text), opacity.

Text boxes are edited in place: double-click to enter edit mode, click away
or Esc to commit.

---

## 6. Development workflow

```bash
uv sync                        # create/update the venv from pyproject.toml
uv run python -m litho         # run the app in dev mode
uv run pytest                  # run the test suite
QT_QPA_PLATFORM=offscreen uv run pytest   # run tests with no display attached
uv add PySide6                 # add a runtime dependency
uv add --dev pytest pytest-qt  # add a dev-only dependency
```

Each component gets built, manually run/tested via `uv run python -m
litho`, and committed on its own before moving to the next.

---

## 7. Component status

| Component | Status | Notes |
|---|---|---|
| Project scaffold (`uv init`) | Done | Flat `main.py`, now a thin shim into `litho.__main__`. |
| Package skeleton (`litho/` package, `__main__.py`) | Done | |
| `main_window.py` + toolbars (no working tools yet) | Done | Text-only actions; both toolbar rows laid out and tested. Icons come later via `icons.py`. |
| `canvas/view.py` + `canvas/scene.py` | Done | Zoom in/out/fit-to-window; a minimal `_on_open` in `main_window.py` loads an image via `QFileDialog` + `QPixmap` so the canvas is exercisable before `io.py` exists. |
| `canvas/items.py` | Partial | `HighlightItem`, `LineItem`, `TextBoxItem`, `FreehandItem`. Polygon item follows the same base pattern (subclass a standard `QGraphicsItem` type, get selection styling for free). |
| `tools/base.py` (`Tool`, `Style`) | Done | `Style` is the shared stroke/fill/size/opacity state tools read at creation time; `main_window.py` owns and mutates it. `Tool` also declares `uses_stroke`/`uses_fill`/`uses_size`/`uses_opacity` (default all `True`), which each subclass narrows to what it actually reads — drives which toolbar controls `main_window.py` greys out per active tool. |
| `tools/select.py` | Done | Delegates to Qt's native item selection/move — just sets `RubberBandDrag` on activate. Delete/Backspace removes the selection (`CanvasView._delete_selected_items`). |
| `tools/polygon.py` | Not started | |
| `tools/line.py` | Done | One `LineTool`/`LineItem` pair, instantiated three times (Line/Arrow/Double-arrow) with different `head_style` values. |
| `tools/freehand.py` | Done | Drag-to-draw `FreehandItem` (`QGraphicsPathItem`); `on_press` starts the path, `on_move` appends a point per event via `add_point()`. |
| `tools/highlighter.py` | Done | Drag-to-draw `HighlightItem`; always translucent (`BASE_OPACITY = 0.4`) scaled further by the Opacity control — a highlighter that isn't translucent by default isn't very useful. |
| `tools/text.py` | Done | Click places a `TextBoxItem` and immediately calls `enter_edit_mode()`. Re-editing an existing box (double-click), cursor placement/selection, and click-away/Esc-to-commit all rely on `CanvasView._is_editing_text()` handing events to Qt's native item dispatch instead of the active tool. |
| `commands.py` (undo/redo) | Not started | |
| `io.py` (open/save/convert) | Not started | |
| `icons.py` | Not started | |
| CLI image argument (`litho <path>`) | Done | `litho/__main__.py:parse_args`; `MainWindow(initial_image=...)` and `open_image_from_path()` shared with the Open action. |
| Test scaffold (`conftest.py`, fixtures) | Partial | `test_main_window.py` in place, using pytest-qt's built-in `qtbot`/`qapp` fixtures directly — no hand-rolled `conftest.py` needed yet. Will add one once tests need shared fixtures (e.g. sample images for `io.py`). |
| Packaging (PyInstaller/Nuitka) | Not started | Deferred until the app works end to end. |

---

## 8. Decisions log

- **2026-07-21** — Chose Python + PySide6 over C++/Qt and Rust+Slint.
  Reasoning: `QGraphicsView` gives selection/move/resize behavior for free,
  which matches this app's needs closely; prioritizes maintainability for a
  solo personal project over raw performance headroom we don't need at this
  scale.
- **2026-07-21** — Chose `uv` for environment/dependency management.
- **2026-07-21** — Will run from a venv during development (`uv run`); will
  package as a standalone binary via PyInstaller or Nuitka later, once the
  app is functionally complete. No Flatpak/AppImage — unnecessary overhead
  for software only one person runs.
- **2026-07-21** — Architecture split into Items / Tools / Commands (see
  §3) to keep files small and undo/redo consistent from the start.
- **2026-07-21** — UI is top-toolbar-only, no status bar, no side panels
  (see §5) — confirmed against the interface mockup.
- **2026-07-21** — `main.py` kept as a two-line shim into `litho.__main__`;
  both `uv run python main.py` and `uv run python -m litho` work.
- **2026-07-21** — No `[build-system]`/packaging metadata added to
  `pyproject.toml`. The app isn't meant to be `pip install`-ed — we're
  packaging as a standalone binary later (§2) — so instead
  `tool.pytest.ini_options.pythonpath = ["."]` lets pytest find the
  `litho/` package without installing it into the venv.
- **2026-07-21** — Tests use pytest-qt's built-in `qtbot`/`qapp` fixtures
  directly; no custom `conftest.py` yet. Run headless with
  `QT_QPA_PLATFORM=offscreen`.
- **2026-07-21** — `main_window.py`'s Open action loads images directly via
  `QFileDialog` + `QPixmap` rather than waiting for `io.py`. This is
  temporary scaffolding to make the canvas testable now; `io.py` will take
  over open/save/format-conversion and this call site gets swapped over
  then.
- **2026-07-21** — Fixed a real GC bug in `CanvasView`: `QGraphicsView`
  does not take Python-side ownership of the scene passed to its
  constructor, so without an explicit `self._scene = scene` reference,
  PySide6 can garbage-collect the scene out from under the view once the
  caller's own reference goes out of scope. `main_window.py` happened to
  avoid this by keeping `self.scene` around, but it's now fixed at the
  source in `CanvasView` itself so nothing else can hit it.
- **2026-07-21** — Added `litho <path>` CLI support via `argparse` in
  `litho/__main__.py`. Image-loading logic was factored out of `_on_open`
  into `MainWindow.open_image_from_path()` so both the toolbar Open action
  and the CLI argument share one code path. No `[project.scripts]` entry
  point added yet — that's still `uv run python -m litho <path>` for now;
  a bare `litho <path>` command comes for free once we package a binary
  later (§2), since argv works the same way there.
- **2026-07-21** — Item classes subclass Qt's standard graphics items
  (`QGraphicsRectItem`, and later `QGraphicsPolygonItem`/`QGraphicsLineItem`/
  `QGraphicsPathItem`/`QGraphicsTextItem`) rather than a from-scratch
  `QGraphicsItem`. They draw their own selection indicator (the dashed
  outline) for free, which is most of what `tools/select.py` needed.
- **2026-07-21** — `SelectTool` does almost nothing itself: Qt's own
  `QGraphicsView`/`QGraphicsScene` already handle click-to-select,
  rubber-band multi-select, and drag-to-move once an item has
  `ItemIsSelectable`/`ItemIsMovable` set. The tool just puts the view in
  `RubberBandDrag` mode; `CanvasView` calls Qt's default mouse handling
  instead of a custom handler whenever `SelectTool` (or any future tool
  with `handles_own_events = False`) is active.
- **2026-07-21** — Introduced `tools/base.py:Style`, a small dataclass
  holding the current stroke/fill/size/opacity from the toolbar.
  `main_window.py` owns one instance and mutates it as the controls
  change; every tool gets a reference to the same object at construction,
  so a newly created item always picks up whatever's currently set
  without tools needing to know about `MainWindow` itself.
- **2026-07-21** — `HighlighterTool` applies a fixed `BASE_OPACITY = 0.4`
  multiplied by the toolbar's Opacity control, rather than using Opacity
  directly. A highlight at 100% opacity would fully obscure the image,
  which defeats the point of a highlighter — real highlighter pens are
  translucent by nature, so that's the default here too.
- **2026-07-21** — Delete/Backspace removes selected items, handled in
  `CanvasView.keyPressEvent` rather than as a toolbar action — matches how
  every other image/drawing tool does it, and keeps the toolbar from
  growing a button for something a key already does well.
- **2026-07-21** — One `LineItem`/`LineTool` pair covers Line, Arrow, and
  Double-arrow rather than three separate item/tool classes: they only
  differ in a `head_style` flag (`"none"`/`"end"`/`"both"`), and
  `main_window.py` just constructs `LineTool` three times with different
  arguments. `LineItem` subclasses `QGraphicsLineItem` for the free
  selection outline, then overrides `paint()` to add arrowhead triangles
  on top and `boundingRect()` to pad for them (only when a head is
  actually drawn, so plain lines don't get an oversized hit/repaint
  region for arrowheads they'll never have).
- **2026-07-22** — `TextBoxItem` subclasses `QGraphicsTextItem` directly
  rather than wrapping a separate edit widget: it starts with
  `NoTextInteraction` (so it moves/selects like every other item) and
  switches to `TextEditorInteraction` on double-click or on creation via
  `TextTool`, switching back on `focusOutEvent`. This meant `CanvasView`
  needed a new rule — while a text item holds edit focus
  (`_is_editing_text()`), mouse and key events skip the active tool and
  go through Qt's default handling instead, since e.g. the Highlighter or
  Text tool would otherwise swallow every click (including the clicks
  needed to place a cursor or drag-select text) before Qt's own item
  dispatch ever saw them. The same check gates
  `CanvasView.keyPressEvent`'s Delete/Backspace handling, since Backspace
  is also "delete a character" while editing.
- **2026-07-22** — "Click away to commit" is deliberately *just* a commit,
  not also a placement gesture: clicking outside the box you're editing
  falls through to Qt's default handling (which clears focus off the text
  item, triggering the commit), rather than `TextTool` creating a second
  box at that point. Placing another box after that takes a second,
  separate click. This avoids a click racing an in-flight commit and
  spawning two live text items on the same click.
- **2026-07-22** — Committing an empty `TextBoxItem` (focus lost with no
  text ever typed in) removes it from the scene rather than leaving it
  behind. Otherwise a click that isn't followed by typing leaves an
  invisible-but-selectable/movable item on the canvas — confusing on
  later Select-tool interaction.
- **2026-07-22** — `FreehandItem` subclasses `QGraphicsPathItem` rather
  than sampling points into a polygon/line list itself: `QPainterPath`
  already accumulates `lineTo()` segments and Qt derives bounding
  rect/selection outline/hit-testing from it for free, same reasoning as
  every other item here subclassing a standard graphics item instead of
  a bare `QGraphicsItem`.
- **2026-07-22** — Fixed (trial-usage bug report): `LineItem`'s arrowhead
  was a constant `ARROW_LENGTH = 14` regardless of pen width, so at large
  enough Size values the line itself was thicker than the arrowhead was
  long, visually swallowing it. Replaced with `_arrow_length` derived
  from pen width — `max(ARROW_LENGTH_MIN, width * ARROW_LENGTH_SCALE)` —
  floored at the old constant so thin lines look the same as before.
  `ARROW_SPREAD_DEGREES` stays a fixed angle rather than also scaling: the
  arrowhead's base width is `2 * length * sin(spread)`, so it already
  grows proportionally as `length` grows without the angle needing to
  change too.
- **2026-07-22** — Found and worked around a PySide6 6.11.1 binding bug
  while testing the above: `QGraphicsPathItem(path)`'s constructor
  overload silently drops the path (reads back as empty, and calling
  `elementAt()` on the result segfaults the interpreter). `setPath()`
  called after a no-arg construction works correctly. `FreehandItem`
  already used this pattern by luck of how it was written; noting it here
  since it'll bite again if a `Polygon`/other path-based item is
  constructed the more obvious way.
- **2026-07-22** — Chose "grey out the controls that don't apply" over
  the alternatives (hide/show controls dynamically per tool, or relabel
  per tool) for surfacing which of Stroke/Fill/Size/Opacity a given tool
  actually uses. Keeps the toolbar layout static — no reflow as tools
  change — while still making "this control does nothing right now"
  visually obvious. Implemented as boolean flags on `Tool`
  (`uses_stroke`/`uses_fill`/`uses_size`/`uses_opacity`, tools/base.py,
  default all `True`) rather than inferring usage by inspecting each
  item class, since the mapping is a handful of tools and an explicit
  per-tool declaration is easier to audit and keep correct than reflection
  over item constructors. The color swatches needed their own fix
  alongside this: they set `background-color` via a plain stylesheet
  rule, which Qt does not automatically mute on `setEnabled(False)` the
  way it does for native-drawn widgets — added a `QPushButton:disabled`
  stylesheet rule so a disabled swatch actually reads as grey instead of
  staying at full color.
- **2026-07-22** — Fixed (trial-usage bug report): arrow shafts drew all
  the way to the tip, with the arrowhead triangle painted on top to
  (mostly) cover the overrun. Two follow-on decisions:
  - `LineItem.paint()` for a headed line no longer delegates to
    `QGraphicsLineItem.paint()` at all; it draws the shortened
    `_shaft_line()` and the arrowhead polygon(s) itself, then — since
    that delegation was also where the free selection-highlight painting
    came from — draws its own dashed selection rect when
    `option.state & QStyle.StateFlag.State_Selected`. Plain (headless)
    lines still take the `super().paint()` fast path, unchanged.
  - The shaft has to stop at the arrowhead's *base edge*, not at
    `_arrow_length` — that constant is the distance from the tip to the
    base's two *corners*, which sit farther out than the base edge
    itself once the spread angle is factored in. Added
    `_arrow_base_distance = _arrow_length * cos(spread)` for the actual
    cutoff point, computed via a small `_point_toward()` helper that
    walks a given distance from one endpoint toward the other.
  - First attempt used `Qt.PenCapStyle.SquareCap` for the shaft, which
    looked identical to the bug it was meant to fix: `SquareCap` still
    extends half the pen width past the endpoint (a square-shaped
    version of `RoundCap`'s overrun, not a true flat cut).
    `Qt.PenCapStyle.FlatCap` is the one that actually terminates exactly
    at the given point — verified by rendering both to a `QImage` at a
    thick pen width and comparing pixel output before settling on it.
- **2026-07-22** — Follow-up fix (trial-usage report): even with the
  shaft cut exactly at `_arrow_base_distance`, a hairline gap remained —
  two shapes independently anti-aliased along a shared edge don't
  necessarily agree pixel-for-pixel on that edge, a standard seam/
  t-junction problem in vector rendering. Standard fix is the one applied
  here: deliberately overlap the two shapes a little rather than trying
  to align them exactly. Added `ARROW_SHAFT_OVERLAP = 1.5` (scene units),
  subtracted from the cutoff distance in `_shaft_line()` and clamped at
  zero so it can never push the cutoff past the tip on a very short/thin
  arrow. Verified via a zoomed `QImage` render at the default 100%
  opacity (no visible seam) and separately at 60% opacity, where the
  overlap band does very slightly double-composite (reads marginally
  brighter than the rest of the translucent arrow) — a real but far more
  minor artifact than the gap it replaces, and only noticeable zoomed
  in on a heavily transparent arrow. Left as-is rather than fixed, since
  fixing it properly would mean compositing the shaft and head into an
  offscreen buffer at full alpha and applying `Style.opacity` once to
  the merged result, which is more machinery than this warrants unless
  it turns out to matter in practice.

---

## 9. Open questions

- Exact keyboard shortcuts (delete selected item, escape to cancel an
  in-progress polygon, etc.) — decide while building `tools/`.
- Packaging specifics (PyInstaller vs. Nuitka, icon/desktop-file
  integration) — deferred until there's a working app to package.

---

*Update §7 and §8 as components land — that's what keeps this document
worth reading.*
