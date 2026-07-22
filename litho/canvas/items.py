"""Annotation item types drawn on top of the canvas image.

Items only know how to draw and resize themselves. Creating and mutating
them is the job of tools/ (and, later, commands.py for undo/redo) — items
stay dumb on purpose.
"""

from __future__ import annotations

import math

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF
from PySide6.QtGui import QBrush, QColor, QPen, QPolygonF
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
)


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


class LineItem(QGraphicsLineItem):
    """A straight line, optionally with arrowheads at either end. One item
    type covers the toolbar's Line/Arrow/Double-arrow tools — they only
    differ in which ends get a head, via `head_style`.
    """

    HEAD_NONE = "none"
    HEAD_END = "end"
    HEAD_BOTH = "both"

    ARROW_LENGTH = 14
    ARROW_SPREAD_DEGREES = 25

    def __init__(
        self, line: QLineF, color: QColor, width: int, head_style: str = HEAD_NONE
    ) -> None:
        super().__init__(line)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.head_style = head_style
        self.setPen(
            QPen(
                color,
                width,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )

    def set_color(self, color: QColor) -> None:
        pen = self.pen()
        pen.setColor(color)
        self.setPen(pen)

    def boundingRect(self) -> QRectF:
        # The base line's bounding rect only accounts for pen width, not
        # the arrowheads that can stick out past either endpoint.
        if self.head_style == self.HEAD_NONE:
            return super().boundingRect()
        extra = self.ARROW_LENGTH + self.pen().widthF()
        return super().boundingRect().adjusted(-extra, -extra, extra, extra)

    def paint(self, painter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        if self.head_style == self.HEAD_NONE:
            return
        painter.setBrush(QBrush(self.pen().color()))
        painter.setPen(Qt.PenStyle.NoPen)
        line = self.line()
        painter.drawPolygon(self._arrowhead(line.p2(), line.p1()))
        if self.head_style == self.HEAD_BOTH:
            painter.drawPolygon(self._arrowhead(line.p1(), line.p2()))

    def _arrowhead(self, tip: QPointF, tail: QPointF) -> QPolygonF:
        angle = math.atan2(tip.y() - tail.y(), tip.x() - tail.x())
        spread = math.radians(self.ARROW_SPREAD_DEGREES)
        left = tip - QPointF(math.cos(angle - spread), math.sin(angle - spread)) * self.ARROW_LENGTH
        right = tip - QPointF(math.cos(angle + spread), math.sin(angle + spread)) * self.ARROW_LENGTH
        return QPolygonF([tip, left, right])


class TextBoxItem(QGraphicsTextItem):
    """An in-place editable text annotation. Starts non-interactive (so it
    moves/selects like every other item); double-click switches it into
    `TextEditorInteraction` for typing, and losing focus — click away, Esc,
    or committing — switches it back. See tools/text.py for how new ones
    get placed.
    """

    def __init__(self, pos: QPointF, color: QColor, font_size: int) -> None:
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setPos(pos)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.set_color(color)
        self.set_font_size(font_size)

    def set_color(self, color: QColor) -> None:
        self.setDefaultTextColor(color)

    def set_font_size(self, size: int) -> None:
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)

    def enter_edit_mode(self) -> None:
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setFocus(Qt.FocusReason.MouseFocusReason)

    def mouseDoubleClickEvent(self, event) -> None:
        if self.textInteractionFlags() == Qt.TextInteractionFlag.NoTextInteraction:
            self.enter_edit_mode()
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event) -> None:
        super().focusOutEvent(event)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        # An empty box committed with nothing typed into it is just a
        # stray, invisible-but-clickable item — drop it instead of
        # leaving it behind.
        if not self.toPlainText() and self.scene() is not None:
            self.scene().removeItem(self)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.clearFocus()
            return
        super().keyPressEvent(event)
