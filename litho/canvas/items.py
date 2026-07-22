"""Annotation item types drawn on top of the canvas image.

Items only know how to draw and resize themselves. Creating and mutating
them is the job of tools/ (and, later, commands.py for undo/redo) — items
stay dumb on purpose.
"""

from __future__ import annotations

import math

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF
from PySide6.QtGui import QBrush, QColor, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QStyle,
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

    # Arrowheads scale with pen width — a fixed size gets swallowed by a
    # thick enough line — with a floor so thin lines still get a visible
    # head. At this spread angle, a `length` head is roughly `3 * width`
    # wide at the base, comfortably past the line's own thickness.
    ARROW_LENGTH_MIN = 14
    ARROW_LENGTH_SCALE = 3.0
    ARROW_SPREAD_DEGREES = 25

    # The shaft is cut exactly at the arrowhead's base edge, but two
    # separately-painted shapes meeting at an exact seam still leaves a
    # hairline anti-aliasing gap between them. Extending the shaft this
    # much further, into the head, guarantees a pixel or two of overlap
    # instead.
    ARROW_SHAFT_OVERLAP = 1.5

    def __init__(
        self, line: QLineF, color: QColor, width: int, head_style: str = HEAD_NONE
    ) -> None:
        super().__init__(line)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.head_style = head_style
        # A round cap on an arrow's shaft bulges out past the arrowhead's
        # sharp tip and past its straight base edge — flat reads clean
        # against both. (Qt's "SquareCap" is a false friend here: despite
        # the name it still extends half the pen width past the endpoint,
        # same as RoundCap's bounding box but square-shaped: FlatCap is
        # the one that actually terminates exactly at the endpoint.)
        # Plain lines (no head) keep the round cap.
        cap_style = (
            Qt.PenCapStyle.RoundCap if head_style == self.HEAD_NONE else Qt.PenCapStyle.FlatCap
        )
        self.setPen(
            QPen(
                color,
                width,
                Qt.PenStyle.SolidLine,
                cap_style,
                Qt.PenJoinStyle.RoundJoin,
            )
        )

    def set_color(self, color: QColor) -> None:
        pen = self.pen()
        pen.setColor(color)
        self.setPen(pen)

    @property
    def _arrow_length(self) -> float:
        return max(self.ARROW_LENGTH_MIN, self.pen().widthF() * self.ARROW_LENGTH_SCALE)

    @property
    def _arrow_base_distance(self) -> float:
        # Distance from the tip to the arrowhead's flat base edge (as
        # opposed to `_arrow_length`, the distance to its two side
        # corners) — this is where the shaft needs to stop so it doesn't
        # run into the head it's supposed to terminate under.
        return self._arrow_length * math.cos(math.radians(self.ARROW_SPREAD_DEGREES))

    def boundingRect(self) -> QRectF:
        # The base line's bounding rect only accounts for pen width, not
        # the arrowheads that can stick out past either endpoint.
        if self.head_style == self.HEAD_NONE:
            return super().boundingRect()
        extra = self._arrow_length + self.pen().widthF()
        return super().boundingRect().adjusted(-extra, -extra, extra, extra)

    def paint(self, painter, option, widget=None) -> None:
        if self.head_style == self.HEAD_NONE:
            super().paint(painter, option, widget)
            return
        # Custom-painted rather than delegating to QGraphicsLineItem's
        # paint(): the shaft has to stop at the arrowhead's base instead
        # of running under it, otherwise (especially at low opacity) the
        # overlap between shaft and head reads as a visible seam right at
        # the base, and a round cap pokes out past the head's sharp tip.
        painter.setPen(self.pen())
        painter.drawLine(self._shaft_line())
        painter.setBrush(QBrush(self.pen().color()))
        painter.setPen(Qt.PenStyle.NoPen)
        line = self.line()
        painter.drawPolygon(self._arrowhead(line.p2(), line.p1()))
        if self.head_style == self.HEAD_BOTH:
            painter.drawPolygon(self._arrowhead(line.p1(), line.p2()))
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(option.palette.windowText(), 0, Qt.PenStyle.DashLine))
            painter.drawRect(self.boundingRect())

    def _shaft_line(self) -> QLineF:
        """The line as actually drawn under the arrowhead(s) — shortened
        at whichever end(s) get a head so the stroke terminates at the
        head's base rather than running to the tip.
        """
        line = self.line()
        p1, p2 = line.p1(), line.p2()
        base = max(0.0, self._arrow_base_distance - self.ARROW_SHAFT_OVERLAP)
        if self.head_style in (self.HEAD_END, self.HEAD_BOTH):
            p2 = self._point_toward(p2, p1, base)
        if self.head_style == self.HEAD_BOTH:
            p1 = self._point_toward(p1, line.p2(), base)
        return QLineF(p1, p2)

    @staticmethod
    def _point_toward(origin: QPointF, other: QPointF, distance: float) -> QPointF:
        vector = other - origin
        vector_length = math.hypot(vector.x(), vector.y())
        if vector_length == 0:
            return origin
        return origin + vector * (distance / vector_length)

    def _arrowhead(self, tip: QPointF, tail: QPointF) -> QPolygonF:
        angle = math.atan2(tip.y() - tail.y(), tip.x() - tail.x())
        spread = math.radians(self.ARROW_SPREAD_DEGREES)
        length = self._arrow_length
        left = tip - QPointF(math.cos(angle - spread), math.sin(angle - spread)) * length
        right = tip - QPointF(math.cos(angle + spread), math.sin(angle + spread)) * length
        return QPolygonF([tip, left, right])


class FreehandItem(QGraphicsPathItem):
    """A freehand stroke traced by dragging the mouse. The path is built
    point by point as the drag continues; selection is drawn for free by
    Qt since this subclasses a standard graphics item.
    """

    def __init__(self, start: QPointF, color: QColor, width: int) -> None:
        super().__init__()
        # QGraphicsPathItem(path) silently drops the path in this PySide6
        # version — setPath() after construction is the reliable path.
        self.setPath(QPainterPath(start))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
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

    def add_point(self, point: QPointF) -> None:
        path = self.path()
        path.lineTo(point)
        self.setPath(path)


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
