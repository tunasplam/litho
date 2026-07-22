"""Line/arrow tool: drag out a straight line, optionally with arrowheads.
One tool class covers all three toolbar actions — Line, Arrow, and Double
arrow — distinguished only by which `head_style` they pass to LineItem.
"""

from __future__ import annotations

from PySide6.QtCore import QLineF, QPointF
from PySide6.QtWidgets import QGraphicsView

from litho.canvas.items import LineItem
from litho.tools.base import Tool


class LineTool(Tool):
    name = "line"

    # LineItem draws a pen only — no fill_color use, even for the
    # arrowhead (it's painted with the pen/stroke color, see items.py).
    uses_fill = False

    def __init__(self, view, style, head_style: str = LineItem.HEAD_NONE) -> None:
        super().__init__(view, style)
        self.head_style = head_style
        self._item: LineItem | None = None
        self._origin: QPointF | None = None

    def activate(self) -> None:
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def on_press(self, scene_pos: QPointF) -> None:
        self._origin = scene_pos
        self._item = LineItem(
            QLineF(scene_pos, scene_pos),
            self.style.stroke_color,
            self.style.size,
            self.head_style,
        )
        self._item.setOpacity(self.style.opacity_fraction)
        self.scene.addItem(self._item)

    def on_move(self, scene_pos: QPointF) -> None:
        if self._item is None or self._origin is None:
            return
        self._item.setLine(QLineF(self._origin, scene_pos))

    def on_release(self, scene_pos: QPointF) -> None:
        self._item = None
        self._origin = None
