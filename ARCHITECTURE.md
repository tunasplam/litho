# Litho — Architecture

A small, personal image annotation tool: open an image, draw polygons, text
boxes, highlights, freehand strokes, and lines/arrows on top of it, adjust
their color/size/opacity, and save/export back out (with format conversion
between PNG/JPG/BMP/etc.).

**Status snapshot** (update this line each session)
`2026-07-21` — package skeleton and `main_window.py` are up: a window shell
with both toolbars laid out (text-only actions, no icons yet) and a
placeholder central widget. No canvas, tools, or file I/O yet. Next step:
`canvas/view.py` and `canvas/scene.py`.

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
| `canvas/view.py` + `canvas/scene.py` | Not started | Next up — replaces the central placeholder label. |
| `canvas/items.py` | Not started | |
| `tools/select.py` | Not started | |
| `tools/polygon.py` | Not started | |
| `tools/line.py` | Not started | |
| `tools/freehand.py` | Not started | |
| `tools/highlighter.py` | Not started | |
| `tools/text.py` | Not started | |
| `commands.py` (undo/redo) | Not started | |
| `io.py` (open/save/convert) | Not started | |
| `icons.py` | Not started | |
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

---

## 9. Open questions

- Exact keyboard shortcuts (delete selected item, escape to cancel an
  in-progress polygon, etc.) — decide while building `tools/`.
- Packaging specifics (PyInstaller vs. Nuitka, icon/desktop-file
  integration) — deferred until there's a working app to package.

---

*Update §7 and §8 as components land — that's what keeps this document
worth reading.*
