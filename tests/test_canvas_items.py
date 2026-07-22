import math

import pytest
from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QGraphicsItem, QGraphicsScene, QGraphicsView

from litho.canvas.items import FreehandItem, HighlightItem, LineItem, RectangleItem, TextBoxItem


def _active_scene(qtbot):
    """A scene embedded in a shown, active view — QGraphicsItem.setFocus()
    is a no-op until the scene is actually active, which requires this.
    """
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    qtbot.addWidget(view)
    view.show()
    QApplication.instance().processEvents()
    return scene


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


def test_rectangle_item_stores_rect(qapp):
    rect = QRectF(10, 20, 100, 50)
    item = RectangleItem(rect, QColor("#8fb8ff"), width=4)

    assert item.rect() == rect


def test_rectangle_item_is_selectable_and_movable(qapp):
    item = RectangleItem(QRectF(0, 0, 10, 10), QColor("#8fb8ff"), width=4)

    assert item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
    assert item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable


def test_rectangle_item_has_no_fill(qapp):
    item = RectangleItem(QRectF(0, 0, 10, 10), QColor("#8fb8ff"), width=4)

    assert item.brush().style() == Qt.BrushStyle.NoBrush


def test_rectangle_item_pen_uses_stroke_color_and_width(qapp):
    item = RectangleItem(QRectF(0, 0, 10, 10), QColor("#8fb8ff"), width=6)

    assert item.pen().color() == QColor("#8fb8ff")
    assert item.pen().widthF() == 6


def test_rectangle_item_set_color_updates_pen(qapp):
    item = RectangleItem(QRectF(0, 0, 10, 10), QColor("#8fb8ff"), width=4)

    item.set_color(QColor("#f5c451"))

    assert item.pen().color() == QColor("#f5c451")


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


def test_arrowhead_grows_with_pen_width(qapp):
    thin = LineItem(QLineF(0, 0, 200, 0), QColor("#8fb8ff"), width=4, head_style=LineItem.HEAD_END)
    thick = LineItem(QLineF(0, 0, 200, 0), QColor("#8fb8ff"), width=40, head_style=LineItem.HEAD_END)

    assert thick._arrow_length > thin._arrow_length
    assert thick.boundingRect().width() > thin.boundingRect().width()


def test_arrowhead_length_has_a_floor_for_thin_lines(qapp):
    item = LineItem(QLineF(0, 0, 100, 0), QColor("#8fb8ff"), width=1, head_style=LineItem.HEAD_END)

    assert item._arrow_length == LineItem.ARROW_LENGTH_MIN


def test_arrowhead_stays_wider_than_the_line_itself(qapp):
    # The bug being fixed: at large enough widths a fixed-size arrowhead
    # gets fully covered by the line's own thickness. The base of the
    # head (2 * length * sin(spread)) must stay comfortably wider than
    # the pen so the head is still visible on top of the line.
    for width in (4, 40, 120):
        item = LineItem(QLineF(0, 0, 300, 0), QColor("#8fb8ff"), width=width, head_style=LineItem.HEAD_END)
        base_width = 2 * item._arrow_length * math.sin(math.radians(LineItem.ARROW_SPREAD_DEGREES))
        assert base_width > width


def test_plain_line_keeps_a_round_cap(qapp):
    item = LineItem(QLineF(0, 0, 100, 0), QColor("#8fb8ff"), width=4, head_style=LineItem.HEAD_NONE)

    assert item.pen().capStyle() == Qt.PenCapStyle.RoundCap


def test_arrow_lines_use_a_flat_cap(qapp):
    # Qt's "SquareCap" is a false friend: it still extends half the pen
    # width past the endpoint. FlatCap is the one that actually stops
    # exactly there, which is what keeps the shaft from overshooting the
    # arrowhead base it's meant to terminate at.
    end = LineItem(QLineF(0, 0, 100, 0), QColor("#8fb8ff"), width=4, head_style=LineItem.HEAD_END)
    both = LineItem(QLineF(0, 0, 100, 0), QColor("#8fb8ff"), width=4, head_style=LineItem.HEAD_BOTH)

    assert end.pen().capStyle() == Qt.PenCapStyle.FlatCap
    assert both.pen().capStyle() == Qt.PenCapStyle.FlatCap


def test_shaft_line_is_unchanged_for_plain_lines(qapp):
    line = QLineF(0, 0, 100, 0)
    item = LineItem(line, QColor("#8fb8ff"), width=4, head_style=LineItem.HEAD_NONE)

    assert item._shaft_line() == line


def test_shaft_line_stops_just_past_the_arrowhead_base_for_head_end(qapp):
    item = LineItem(QLineF(0, 0, 100, 0), QColor("#8fb8ff"), width=4, head_style=LineItem.HEAD_END)

    shaft = item._shaft_line()
    expected_x = 100 - (item._arrow_base_distance - LineItem.ARROW_SHAFT_OVERLAP)

    assert shaft.p1() == QPointF(0, 0)
    assert shaft.p2().x() == pytest.approx(expected_x)
    assert shaft.p2().y() == pytest.approx(0)
    # The shaft must not reach all the way to the tip, but should
    # deliberately overshoot the exact base line a little, into the head,
    # so there's no anti-aliasing seam between the two shapes.
    assert shaft.length() < item.line().length()
    assert shaft.p2().x() > 100 - item._arrow_base_distance


def test_shaft_line_stops_just_past_both_arrowhead_bases_for_head_both(qapp):
    item = LineItem(QLineF(0, 0, 100, 0), QColor("#8fb8ff"), width=4, head_style=LineItem.HEAD_BOTH)

    shaft = item._shaft_line()

    base = item._arrow_base_distance - LineItem.ARROW_SHAFT_OVERLAP
    assert shaft.p1().x() == pytest.approx(base)
    assert shaft.p2().x() == pytest.approx(100 - base)


def test_shaft_overlap_does_not_push_the_cut_point_negative(qapp):
    # width=1 hits the ARROW_LENGTH_MIN floor, giving the smallest
    # possible base distance — the overlap subtraction must still clamp
    # at zero rather than sending the cut point past the tip itself.
    item = LineItem(QLineF(0, 0, 100, 0), QColor("#8fb8ff"), width=1, head_style=LineItem.HEAD_END)

    shaft = item._shaft_line()

    assert 0 <= shaft.p2().x() <= 100


def test_arrow_base_distance_is_shorter_than_arrow_length(qapp):
    # The base (where the shaft should stop) sits in front of the two
    # side corners (which are `_arrow_length` from the tip) — otherwise
    # the shaft either overshoots the head or leaves a gap before it.
    item = LineItem(QLineF(0, 0, 100, 0), QColor("#8fb8ff"), width=4, head_style=LineItem.HEAD_END)

    assert 0 < item._arrow_base_distance < item._arrow_length


def test_freehand_item_starts_path_at_first_point(qapp):
    item = FreehandItem(QPointF(5, 5), QColor("#8fb8ff"), width=4)

    assert item.path().elementAt(0).x == 5
    assert item.path().elementAt(0).y == 5


def test_freehand_item_is_selectable_and_movable(qapp):
    item = FreehandItem(QPointF(0, 0), QColor("#8fb8ff"), width=4)

    assert item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
    assert item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable


def test_freehand_item_add_point_extends_the_path(qapp):
    item = FreehandItem(QPointF(0, 0), QColor("#8fb8ff"), width=4)

    item.add_point(QPointF(10, 0))
    item.add_point(QPointF(10, 10))

    assert item.path().elementCount() == 3
    last = item.path().elementAt(2)
    assert (last.x, last.y) == (10, 10)


def test_freehand_item_set_color_updates_pen(qapp):
    item = FreehandItem(QPointF(0, 0), QColor("#8fb8ff"), width=4)

    item.set_color(QColor("#f5c451"))

    assert item.pen().color() == QColor("#f5c451")


def test_text_box_item_stores_position(qapp):
    item = TextBoxItem(QPointF(15, 25), QColor("#8fb8ff"), font_size=14)

    assert item.pos() == QPointF(15, 25)


def test_text_box_item_is_selectable_and_movable(qapp):
    item = TextBoxItem(QPointF(0, 0), QColor("#8fb8ff"), font_size=14)

    assert item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
    assert item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable


def test_text_box_item_starts_not_editable(qapp):
    item = TextBoxItem(QPointF(0, 0), QColor("#8fb8ff"), font_size=14)

    assert item.textInteractionFlags() == Qt.TextInteractionFlag.NoTextInteraction


def test_text_box_item_set_color_updates_default_text_color(qapp):
    item = TextBoxItem(QPointF(0, 0), QColor("#8fb8ff"), font_size=14)

    item.set_color(QColor("#f5c451"))

    assert item.defaultTextColor() == QColor("#f5c451")


def test_text_box_item_set_font_size_updates_font(qapp):
    item = TextBoxItem(QPointF(0, 0), QColor("#8fb8ff"), font_size=14)

    item.set_font_size(28)

    assert item.font().pointSize() == 28


def test_enter_edit_mode_makes_it_editable_and_focused(qtbot):
    scene = _active_scene(qtbot)
    item = TextBoxItem(QPointF(0, 0), QColor("#8fb8ff"), font_size=14)
    scene.addItem(item)

    item.enter_edit_mode()

    assert item.textInteractionFlags() == Qt.TextInteractionFlag.TextEditorInteraction
    assert item.hasFocus()


def test_losing_focus_while_empty_removes_the_item(qtbot):
    scene = _active_scene(qtbot)
    item = TextBoxItem(QPointF(0, 0), QColor("#8fb8ff"), font_size=14)
    scene.addItem(item)
    item.enter_edit_mode()

    item.clearFocus()

    assert item not in scene.items()


def test_losing_focus_with_text_keeps_the_item_and_exits_edit_mode(qtbot):
    scene = _active_scene(qtbot)
    item = TextBoxItem(QPointF(0, 0), QColor("#8fb8ff"), font_size=14)
    scene.addItem(item)
    item.enter_edit_mode()
    item.setPlainText("hello")

    item.clearFocus()

    assert item in scene.items()
    assert item.textInteractionFlags() == Qt.TextInteractionFlag.NoTextInteraction


def test_escape_while_editing_clears_focus(qtbot):
    scene = _active_scene(qtbot)
    item = TextBoxItem(QPointF(0, 0), QColor("#8fb8ff"), font_size=14)
    scene.addItem(item)
    item.enter_edit_mode()

    item.keyPressEvent(_key_event(Qt.Key.Key_Escape))

    assert not item.hasFocus()


def _key_event(key):
    from PySide6.QtCore import QEvent
    from PySide6.QtGui import QKeyEvent

    return QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)
