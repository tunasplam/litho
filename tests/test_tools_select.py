from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsView

from litho.canvas.scene import CanvasScene
from litho.canvas.view import CanvasView
from litho.tools.base import Style
from litho.tools.select import SelectTool


def _view_and_style(qtbot):
    scene = CanvasScene()
    view = CanvasView(scene)
    qtbot.addWidget(view)
    style = Style(stroke_color=QColor("#8fb8ff"), fill_color=QColor("#f5c451"), size=14, opacity=100)
    return view, style


def test_select_tool_does_not_handle_its_own_events(qtbot):
    view, style = _view_and_style(qtbot)
    tool = SelectTool(view, style)

    assert tool.handles_own_events is False


def test_activating_select_tool_enables_rubber_band_drag(qtbot):
    view, style = _view_and_style(qtbot)
    tool = SelectTool(view, style)

    tool.activate()

    assert view.dragMode() == QGraphicsView.DragMode.RubberBandDrag
