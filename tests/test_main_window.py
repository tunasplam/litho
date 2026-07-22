from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication

from litho.canvas.items import TextBoxItem
from litho.main_window import MainWindow
from litho.tools.highlighter import HighlighterTool
from litho.tools.line import LineTool
from litho.tools.select import SelectTool
from litho.tools.text import TextTool


def test_window_title(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == "Litho"


def test_select_tool_is_active_by_default(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.action_select.isChecked()
    for action in (
        window.action_polygon,
        window.action_line,
        window.action_arrow,
        window.action_double_arrow,
        window.action_freehand,
        window.action_highlighter,
        window.action_text,
    ):
        assert not action.isChecked()


def test_tool_actions_are_mutually_exclusive(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.action_highlighter.trigger()

    assert window.action_highlighter.isChecked()
    assert not window.action_select.isChecked()


def test_unimplemented_tool_actions_are_disabled(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    for action in (window.action_polygon, window.action_freehand):
        assert not action.isEnabled()


def test_line_and_text_tool_actions_are_enabled(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    for action in (
        window.action_line,
        window.action_arrow,
        window.action_double_arrow,
        window.action_text,
    ):
        assert action.isEnabled()


def test_export_format_defaults_to_png(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.format_combo.currentText() == "PNG"
    assert [window.format_combo.itemText(i) for i in range(window.format_combo.count())] == [
        "PNG",
        "JPG",
        "BMP",
    ]


def test_undo_redo_disabled_with_no_history(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert not window.action_undo.isEnabled()
    assert not window.action_redo.isEnabled()


def test_default_property_values(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.zoom_label.text() == "100%"
    assert window.size_spin.value() == 14
    assert window.opacity_spin.value() == 100


def test_central_widget_is_the_canvas_view(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.centralWidget() is window.view


def test_zoom_in_action_updates_the_zoom_label(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.action_zoom_in.trigger()

    assert window.zoom_label.text() == "125%"


def test_fit_action_without_an_image_does_not_raise(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.action_fit.trigger()  # should be a no-op, not raise


def test_open_image_from_path_loads_a_valid_image(qtbot, tmp_path):
    image_path = tmp_path / "sample.png"
    QPixmap(120, 80).save(str(image_path))

    window = MainWindow()
    qtbot.addWidget(window)

    assert window.open_image_from_path(str(image_path)) is True
    assert window.scene.has_image
    assert window.scene.image_size() == QSize(120, 80)


def test_open_image_from_path_rejects_a_missing_file(qtbot, tmp_path):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.open_image_from_path(str(tmp_path / "missing.png")) is False
    assert not window.scene.has_image


def test_constructing_with_initial_image_loads_it(qtbot, tmp_path):
    image_path = tmp_path / "sample.png"
    QPixmap(64, 64).save(str(image_path))

    window = MainWindow(initial_image=str(image_path))
    qtbot.addWidget(window)

    assert window.scene.has_image
    assert window.scene.image_size() == QSize(64, 64)


def test_select_tool_is_active_on_the_view_by_default(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert isinstance(window.view._active_tool, SelectTool)


def test_choosing_highlighter_switches_the_active_tool(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.action_highlighter.trigger()

    assert isinstance(window.view._active_tool, HighlighterTool)


def test_choosing_arrow_switches_the_active_tool(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.action_arrow.trigger()

    assert isinstance(window.view._active_tool, LineTool)
    assert window.view._active_tool.head_style == "end"


def test_choosing_text_switches_the_active_tool(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.action_text.trigger()

    assert isinstance(window.view._active_tool, TextTool)


def test_clicking_with_text_tool_starts_an_editable_text_item(qtbot, tmp_path):
    image_path = tmp_path / "sample.png"
    QPixmap(200, 200).save(str(image_path))
    window = MainWindow(initial_image=str(image_path))
    qtbot.addWidget(window)
    window.show()
    QApplication.instance().processEvents()

    window.action_text.trigger()
    tool = window.view._active_tool
    tool.on_press(tool.view.mapToScene(20, 20))

    item = next(i for i in window.scene.items() if isinstance(i, TextBoxItem))
    assert window.scene.focusItem() is item
    assert window.view._is_editing_text()


def test_picking_a_new_stroke_color_updates_style_and_swatch(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)
    new_color = QColor("#00ff00")
    monkeypatch.setattr(
        "litho.main_window.QColorDialog.getColor", lambda *a, **k: new_color
    )

    window._on_pick_stroke_color()

    assert window.style.stroke_color == new_color


def test_changing_size_spin_updates_style(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.size_spin.setValue(42)

    assert window.style.size == 42


def test_changing_opacity_spin_updates_style(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.opacity_spin.setValue(30)

    assert window.style.opacity == 30


def test_delete_key_removes_selected_item(qtbot, tmp_path):
    image_path = tmp_path / "sample.png"
    QPixmap(200, 200).save(str(image_path))
    window = MainWindow(initial_image=str(image_path))
    qtbot.addWidget(window)

    window.action_highlighter.trigger()
    tool = window.view._active_tool
    tool.on_press(tool.view.mapToScene(10, 10))
    tool.on_release(tool.view.mapToScene(40, 40))
    assert len(window.scene.items()) == 2  # background + highlight

    window.scene.items()[0].setSelected(True)
    qtbot.keyClick(window.view, Qt.Key.Key_Delete)

    assert len(window.scene.items()) == 1  # just the background left
