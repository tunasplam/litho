"""Toolbar icons for the tool-selection actions.

Drawn programmatically with QPainter rather than shipped as image
assets — no icon library dependency, no files to keep in sync with the
toolbar, and each icon is recolored from the current palette so it reads
correctly in both light and dark themes.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPalette, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QApplication

ICON_SIZE = 20
_STROKE_WIDTH = 1.6


def _icon_color() -> QColor:
    return QApplication.palette().color(QPalette.ColorRole.WindowText)


def _painter(color: QColor) -> tuple[QPixmap, QPainter]:
    pixmap = QPixmap(ICON_SIZE, ICON_SIZE)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(
        QPen(color, _STROKE_WIDTH, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    )
    painter.setBrush(Qt.BrushStyle.NoBrush)
    return pixmap, painter


def _finish(pixmap: QPixmap, painter: QPainter) -> QIcon:
    painter.end()
    return QIcon(pixmap)


def _arrowhead(tip: QPointF, tail: QPointF, length: float = 5, spread_degrees: float = 28) -> QPolygonF:
    angle = math.atan2(tip.y() - tail.y(), tip.x() - tail.x())
    spread = math.radians(spread_degrees)
    left = tip - QPointF(math.cos(angle - spread), math.sin(angle - spread)) * length
    right = tip - QPointF(math.cos(angle + spread), math.sin(angle + spread)) * length
    return QPolygonF([tip, left, right])


def select_icon() -> QIcon:
    # A dashed rectangle — SelectTool's actual behavior is Qt's native
    # rubber-band drag selection, so this reads as "what it does" rather
    # than a generic cursor glyph.
    color = _icon_color()
    pixmap, painter = _painter(color)
    pen = painter.pen()
    pen.setStyle(Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.drawRect(QRectF(4, 4, 12, 12))
    return _finish(pixmap, painter)


def rectangle_icon() -> QIcon:
    color = _icon_color()
    pixmap, painter = _painter(color)
    painter.drawRect(QRectF(4, 4, 12, 12))
    return _finish(pixmap, painter)


def line_icon() -> QIcon:
    color = _icon_color()
    pixmap, painter = _painter(color)
    painter.drawLine(QPointF(4, 16), QPointF(16, 4))
    return _finish(pixmap, painter)


def arrow_icon() -> QIcon:
    color = _icon_color()
    pixmap, painter = _painter(color)
    tail, tip = QPointF(4, 16), QPointF(16, 4)
    painter.drawLine(tail, tip)
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPolygon(_arrowhead(tip, tail))
    return _finish(pixmap, painter)


def double_arrow_icon() -> QIcon:
    color = _icon_color()
    pixmap, painter = _painter(color)
    tail, tip = QPointF(4, 16), QPointF(16, 4)
    painter.drawLine(tail, tip)
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPolygon(_arrowhead(tip, tail))
    painter.drawPolygon(_arrowhead(tail, tip))
    return _finish(pixmap, painter)


def freehand_icon() -> QIcon:
    color = _icon_color()
    pixmap, painter = _painter(color)
    path = QPainterPath(QPointF(3, 13))
    path.cubicTo(QPointF(5, 4), QPointF(9, 4), QPointF(10, 10))
    path.cubicTo(QPointF(11, 16), QPointF(15, 16), QPointF(17, 6))
    painter.drawPath(path)
    return _finish(pixmap, painter)


def highlighter_icon() -> QIcon:
    # A chisel-tip marker: an angled pen body plus the stroke it lays
    # down, echoing HighlightItem's own translucent-rectangle look.
    color = _icon_color()
    pixmap, painter = _painter(color)
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    body = QPolygonF([QPointF(11, 3), QPointF(16, 8), QPointF(10, 14), QPointF(7, 11)])
    painter.drawPolygon(body)
    translucent = QColor(color)
    translucent.setAlpha(110)
    painter.setBrush(translucent)
    painter.drawRect(QRectF(3, 14, 9, 3))
    return _finish(pixmap, painter)


def text_icon() -> QIcon:
    color = _icon_color()
    pixmap, painter = _painter(color)
    font = painter.font()
    font.setBold(True)
    font.setPixelSize(15)
    painter.setFont(font)
    painter.setPen(color)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "T")
    return _finish(pixmap, painter)
