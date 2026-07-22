from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from litho.canvas.items import TextBoxItem
from litho.canvas.scene import CanvasScene
from litho.canvas.view import CanvasView
from litho.tools.base import Style
from litho.tools.text import TextTool


def _tool(qtbot, show=False):
    scene = CanvasScene()
    view = CanvasView(scene)
    qtbot.addWidget(view)
    if show:
        view.show()
        QApplication.instance().processEvents()
    style = Style(stroke_color=QColor("#8fb8ff"), fill_color=QColor("#f5c451"), size=14, opacity=100)
    return TextTool(view, style), scene


def test_click_creates_a_text_box_item_at_the_click_point(qtbot):
    tool, scene = _tool(qtbot)

    tool.on_press(QPointF(30, 40))

    items = [item for item in scene.items() if isinstance(item, TextBoxItem)]
    assert len(items) == 1
    assert items[0].pos() == QPointF(30, 40)


def test_click_creates_an_item_already_in_edit_mode(qtbot):
    tool, scene = _tool(qtbot, show=True)

    tool.on_press(QPointF(0, 0))

    item = next(i for i in scene.items() if isinstance(i, TextBoxItem))
    assert item.hasFocus()


def test_created_item_uses_current_style(qtbot):
    tool, scene = _tool(qtbot)
    tool.style.stroke_color = QColor("#ff0000")
    tool.style.size = 22
    tool.style.opacity = 50

    tool.on_press(QPointF(0, 0))

    item = next(i for i in scene.items() if isinstance(i, TextBoxItem))
    assert item.defaultTextColor() == QColor("#ff0000")
    assert item.font().pointSize() == 22
    assert item.opacity() == 0.5


def test_text_tool_does_not_use_fill(qtbot):
    tool, scene = _tool(qtbot)

    assert not tool.uses_fill
    assert tool.uses_stroke
    assert tool.uses_size
    assert tool.uses_opacity
