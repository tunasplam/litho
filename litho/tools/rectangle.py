"""Rectangle tool: drag out an unfilled rectangle outline."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QGraphicsView

from litho.canvas.items import RectangleItem
from litho.tools.base import Tool


class RectangleTool(Tool):
    name = "rectangle"

    # RectangleItem draws an outline only — no fill_color use.
    uses_fill = False

    def __init__(self, view, style) -> None:
        super().__init__(view, style)
        self._item: RectangleItem | None = None
        self._origin: QPointF | None = None

    def activate(self) -> None:
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def on_press(self, scene_pos: QPointF) -> None:
        self._origin = scene_pos
        self._item = RectangleItem(QRectF(scene_pos, scene_pos), self.style.stroke_color, self.style.size)
        self._item.setOpacity(self.style.opacity_fraction)
        self.scene.addItem(self._item)

    def on_move(self, scene_pos: QPointF) -> None:
        if self._item is None or self._origin is None:
            return
        self._item.setRect(QRectF(self._origin, scene_pos).normalized())

    def on_release(self, scene_pos: QPointF) -> None:
        self._item = None
        self._origin = None
