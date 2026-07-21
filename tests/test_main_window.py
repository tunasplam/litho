from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap

from litho.main_window import MainWindow


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

    window.action_polygon.trigger()

    assert window.action_polygon.isChecked()
    assert not window.action_select.isChecked()


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
