from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

from litho.canvas.items import FreehandItem
from litho.canvas.scene import CanvasScene
from litho.canvas.view import CanvasView
from litho.tools.base import Style
from litho.tools.freehand import FreehandTool


def _tool(qtbot):
    scene = CanvasScene()
    view = CanvasView(scene)
    qtbot.addWidget(view)
    style = Style(stroke_color=QColor("#8fb8ff"), fill_color=QColor("#f5c451"), size=4, opacity=100)
    return FreehandTool(view, style), scene


def test_drag_creates_a_freehand_item_with_one_point_per_move(qtbot):
    tool, scene = _tool(qtbot)

    tool.on_press(QPointF(0, 0))
    tool.on_move(QPointF(5, 5))
    tool.on_move(QPointF(10, 0))
    tool.on_release(QPointF(10, 0))

    items = [item for item in scene.items() if isinstance(item, FreehandItem)]
    assert len(items) == 1
    assert items[0].path().elementCount() == 3


def test_created_item_uses_current_style(qtbot):
    tool, scene = _tool(qtbot)
    tool.style.stroke_color = QColor("#ff0000")
    tool.style.opacity = 50

    tool.on_press(QPointF(0, 0))
    tool.on_release(QPointF(20, 20))

    item = next(i for i in scene.items() if isinstance(i, FreehandItem))
    assert item.pen().color() == QColor("#ff0000")
    assert item.opacity() == 0.5


def test_release_clears_in_progress_state(qtbot):
    tool, scene = _tool(qtbot)

    tool.on_press(QPointF(0, 0))
    tool.on_release(QPointF(20, 20))

    assert tool._item is None


def test_move_without_press_is_a_no_op(qtbot):
    tool, scene = _tool(qtbot)

    tool.on_move(QPointF(5, 5))  # should not raise

    assert not [item for item in scene.items() if isinstance(item, FreehandItem)]
