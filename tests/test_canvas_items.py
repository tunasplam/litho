from PySide6.QtCore import QLineF, QRectF
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsItem

from litho.canvas.items import HighlightItem, LineItem


def test_highlight_item_stores_rect(qapp):
    rect = QRectF(10, 20, 100, 50)
    item = HighlightItem(rect, QColor("#f5c451"), opacity=0.4)

    assert item.rect() == rect


def test_highlight_item_stores_opacity(qapp):
    item = HighlightItem(QRectF(0, 0, 10, 10), QColor("#f5c451"), opacity=0.4)

    assert item.opacity() == 0.4


def test_highlight_item_is_selectable_and_movable(qapp):
    item = HighlightItem(QRectF(0, 0, 10, 10), QColor("#f5c451"), opacity=0.4)

    assert item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
    assert item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable


def test_set_color_updates_brush(qapp):
    item = HighlightItem(QRectF(0, 0, 10, 10), QColor("#f5c451"), opacity=0.4)

    item.set_color(QColor("#8fb8ff"))

    assert item.brush().color() == QColor("#8fb8ff")


def test_line_item_stores_line(qapp):
    line = QLineF(0, 0, 100, 50)
    item = LineItem(line, QColor("#8fb8ff"), width=4)

    assert item.line() == line


def test_line_item_is_selectable_and_movable(qapp):
    item = LineItem(QLineF(0, 0, 10, 10), QColor("#8fb8ff"), width=4)

    assert item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
    assert item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable


def test_line_item_defaults_to_no_head(qapp):
    item = LineItem(QLineF(0, 0, 10, 10), QColor("#8fb8ff"), width=4)

    assert item.head_style == LineItem.HEAD_NONE


def test_line_item_set_color_updates_pen(qapp):
    item = LineItem(QLineF(0, 0, 10, 10), QColor("#8fb8ff"), width=4)

    item.set_color(QColor("#f5c451"))

    assert item.pen().color() == QColor("#f5c451")


def test_line_item_bounding_rect_is_padded_for_arrowheads(qapp):
    plain = LineItem(QLineF(0, 0, 100, 0), QColor("#8fb8ff"), width=4, head_style=LineItem.HEAD_NONE)
    arrow = LineItem(QLineF(0, 0, 100, 0), QColor("#8fb8ff"), width=4, head_style=LineItem.HEAD_END)

    assert arrow.boundingRect().width() > plain.boundingRect().width()
