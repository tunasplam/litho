from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

from litho.canvas.items import HighlightItem
from litho.canvas.scene import CanvasScene
from litho.canvas.view import CanvasView
from litho.tools.base import Style
from litho.tools.highlighter import BASE_OPACITY, HighlighterTool


def _tool(qtbot):
    scene = CanvasScene()
    view = CanvasView(scene)
    qtbot.addWidget(view)
    style = Style(stroke_color=QColor("#8fb8ff"), fill_color=QColor("#f5c451"), size=14, opacity=100)
    return HighlighterTool(view, style), scene


def test_drag_creates_a_highlight_item(qtbot):
    tool, scene = _tool(qtbot)

    tool.on_press(QPointF(10, 10))
    tool.on_move(QPointF(60, 40))
    tool.on_release(QPointF(60, 40))

    items = [item for item in scene.items() if isinstance(item, HighlightItem)]
    assert len(items) == 1
    rect = items[0].rect()
    assert rect.x() == 10
    assert rect.y() == 10
    assert rect.width() == 50
    assert rect.height() == 30


def test_created_item_uses_current_style(qtbot):
    tool, scene = _tool(qtbot)
    tool.style.fill_color = QColor("#ff0000")
    tool.style.opacity = 50

    tool.on_press(QPointF(0, 0))
    tool.on_release(QPointF(20, 20))

    item = next(i for i in scene.items() if isinstance(i, HighlightItem))
    assert item.brush().color() == QColor("#ff0000")
    assert item.opacity() == BASE_OPACITY * 0.5


def test_release_clears_in_progress_state(qtbot):
    tool, scene = _tool(qtbot)

    tool.on_press(QPointF(0, 0))
    tool.on_release(QPointF(20, 20))

    assert tool._item is None
    assert tool._origin is None
