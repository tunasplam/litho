import pytest
from PySide6.QtGui import QPixmap

from litho.canvas.scene import CanvasScene
from litho.canvas.view import MAX_ZOOM, MIN_ZOOM, ZOOM_STEP, CanvasView


def _view(qtbot) -> CanvasView:
    scene = CanvasScene()
    view = CanvasView(scene)
    qtbot.addWidget(view)
    return view


def test_default_zoom_is_1(qtbot):
    view = _view(qtbot)

    assert view.zoom == 1.0


def test_zoom_in_increases_zoom(qtbot):
    view = _view(qtbot)
    view.zoom_in()

    assert view.zoom == pytest.approx(ZOOM_STEP)


def test_zoom_out_decreases_zoom(qtbot):
    view = _view(qtbot)
    view.zoom_out()

    assert view.zoom == pytest.approx(1 / ZOOM_STEP)


def test_zoom_is_clamped_to_bounds(qtbot):
    view = _view(qtbot)

    for _ in range(50):
        view.zoom_in()
    assert view.zoom <= MAX_ZOOM

    for _ in range(50):
        view.zoom_out()
    assert view.zoom >= MIN_ZOOM


def test_zoom_changed_signal_emits_new_zoom(qtbot):
    view = _view(qtbot)

    with qtbot.waitSignal(view.zoom_changed, timeout=1000) as blocker:
        view.zoom_in()

    assert blocker.args == [pytest.approx(ZOOM_STEP)]


def test_fit_to_window_on_empty_scene_is_a_no_op(qtbot):
    view = _view(qtbot)

    view.fit_to_window()  # should not raise

    assert view.zoom == 1.0


def test_fit_to_window_with_an_image_sets_a_positive_zoom(qtbot):
    view = _view(qtbot)
    pixmap = QPixmap(400, 300)
    pixmap.fill()
    view.scene().set_image(pixmap)
    view.resize(800, 600)

    view.fit_to_window()

    assert view.zoom > 0
