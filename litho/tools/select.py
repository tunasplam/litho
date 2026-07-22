"""The select tool: click to select an item, drag to move it, drag on
empty space to rubber-band select. All of this is Qt's native
QGraphicsView/QGraphicsScene behavior — items just need ItemIsSelectable
and ItemIsMovable set (see canvas/items.py) — so this tool does nothing
but put the view into the right drag mode.
"""

from __future__ import annotations

from PySide6.QtWidgets import QGraphicsView

from litho.tools.base import Tool


class SelectTool(Tool):
    name = "select"
    handles_own_events = False

    def activate(self) -> None:
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

    def deactivate(self) -> None:
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
