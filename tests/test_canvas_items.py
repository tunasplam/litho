from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsItem

from litho.canvas.items import HighlightItem


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
