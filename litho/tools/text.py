"""Text tool: click empty canvas to place a new text box and start typing
immediately. Editing an existing box (double-click to re-enter, click-away
or Esc to commit) is handled by TextBoxItem itself plus a couple of
CanvasView routing rules (see canvas/view.py) — this tool only places new
ones.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsView

from litho.canvas.items import TextBoxItem
from litho.tools.base import Tool


class TextTool(Tool):
    name = "text"

    # TextBoxItem uses stroke_color as the text color and size as the
    # font's point size — no fill_color use.
    uses_fill = False

    def activate(self) -> None:
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def on_press(self, scene_pos: QPointF) -> None:
        item = TextBoxItem(scene_pos, self.style.stroke_color, self.style.size)
        item.setOpacity(self.style.opacity_fraction)
        self.scene.addItem(item)
        item.enter_edit_mode()
