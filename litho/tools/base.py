"""Shared tool interface. Each tool is a small state machine that turns
mouse events on the canvas into item creation/edits — see canvas/items.py
for the items themselves, and canvas/view.py for how events get routed
to whichever tool is active.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor


@dataclass
class Style:
    """The current stroke/fill/size/opacity settings from the toolbar.
    Tools read this at the moment they create a new item; main_window.py
    keeps it updated as the user changes the toolbar controls.
    """

    stroke_color: QColor
    fill_color: QColor
    size: int
    opacity: int  # percent, 0-100

    @property
    def opacity_fraction(self) -> float:
        return self.opacity / 100


class Tool:
    """Base class for every tool. Subclasses override the hooks they need.

    `handles_own_events = True` means CanvasView routes mouse events to
    this tool's on_press/on_move/on_release instead of letting Qt's
    default QGraphicsView behavior run — that's what every *drawing* tool
    wants. The select tool is the one exception (see tools/select.py).
    """

    name = ""
    handles_own_events = True

    def __init__(self, view, style: Style) -> None:
        self.view = view
        self.style = style

    @property
    def scene(self):
        return self.view.scene()

    def activate(self) -> None:
        """Called when this tool becomes the active tool."""

    def deactivate(self) -> None:
        """Called when switching away from this tool."""

    def on_press(self, scene_pos: QPointF) -> None:
        pass

    def on_move(self, scene_pos: QPointF) -> None:
        pass

    def on_release(self, scene_pos: QPointF) -> None:
        pass
