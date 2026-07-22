"""Highlighter tool: drag out a translucent rectangle over the image."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QGraphicsView

from litho.canvas.items import HighlightItem
from litho.tools.base import Tool

# Highlighters are inherently translucent — this is the base opacity at
# 100% on the toolbar's Opacity control, which then scales it further.
BASE_OPACITY = 0.4


class HighlighterTool(Tool):
    name = "highlighter"

    def __init__(self, view, style) -> None:
        super().__init__(view, style)
        self._item: HighlightItem | None = None
        self._origin: QPointF | None = None

    def activate(self) -> None:
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def on_press(self, scene_pos: QPointF) -> None:
        self._origin = scene_pos
        opacity = BASE_OPACITY * self.style.opacity_fraction
        self._item = HighlightItem(QRectF(scene_pos, scene_pos), self.style.fill_color, opacity)
        self.scene.addItem(self._item)

    def on_move(self, scene_pos: QPointF) -> None:
        if self._item is None or self._origin is None:
            return
        self._item.setRect(QRectF(self._origin, scene_pos).normalized())

    def on_release(self, scene_pos: QPointF) -> None:
        self._item = None
        self._origin = None
