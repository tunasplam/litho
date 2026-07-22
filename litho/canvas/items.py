"""Annotation item types drawn on top of the canvas image.

Items only know how to draw and resize themselves. Creating and mutating
them is the job of tools/ (and, later, commands.py for undo/redo) — items
stay dumb on purpose.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem


class HighlightItem(QGraphicsRectItem):
    """A translucent rectangle used to highlight part of the image, the
    way a highlighter pen would. Selection is drawn for free by Qt (the
    dashed outline) since this subclasses a standard graphics item.
    """

    def __init__(self, rect: QRectF, color: QColor, opacity: float) -> None:
        super().__init__(rect)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.set_color(color)
        self.setOpacity(opacity)

    def set_color(self, color: QColor) -> None:
        self.setBrush(QBrush(color))
