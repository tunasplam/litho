from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QGraphicsItem, QGraphicsScene, QGraphicsView

from litho.canvas.items import HighlightItem, LineItem, TextBoxItem


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
