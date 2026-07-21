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
