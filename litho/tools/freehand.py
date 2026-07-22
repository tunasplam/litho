"""Freehand tool: drag to trace a stroke, one point per mouse move."""

from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsView

from litho.canvas.items import FreehandItem
from litho.tools.base import Tool


class FreehandTool(Tool):
    name = "freehand"

    def __init__(self, view, style) -> None:
        super().__init__(view, style)
        self._item: FreehandItem | None = None

    def activate(self) -> None:
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def on_press(self, scene_pos: QPointF) -> None:
        self._item = FreehandItem(scene_pos, self.style.stroke_color, self.style.size)
        self._item.setOpacity(self.style.opacity_fraction)
        self.scene.addItem(self._item)

    def on_move(self, scene_pos: QPointF) -> None:
        if self._item is None:
            return
        self._item.add_point(scene_pos)

    def on_release(self, scene_pos: QPointF) -> None:
        if self._item is not None:
            self._item.add_point(scene_pos)
        self._item = None
