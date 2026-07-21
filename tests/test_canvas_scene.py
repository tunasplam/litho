from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap

from litho.canvas.scene import CanvasScene


def _solid_pixmap(width: int, height: int) -> QPixmap:
    pixmap = QPixmap(width, height)
    pixmap.fill()
    return pixmap


def test_scene_starts_without_an_image(qapp):
    scene = CanvasScene()

    assert not scene.has_image
    assert scene.image_size() is None


def test_set_image_stores_background(qapp):
    scene = CanvasScene()
    scene.set_image(_solid_pixmap(200, 100))

    assert scene.has_image
    assert scene.image_size() == QSize(200, 100)
    assert scene.sceneRect().width() == 200
    assert scene.sceneRect().height() == 100


def test_set_image_replaces_previous_image(qapp):
    scene = CanvasScene()
    scene.set_image(_solid_pixmap(200, 100))
    scene.set_image(_solid_pixmap(50, 50))

    assert scene.image_size() == QSize(50, 50)
    assert len(scene.items()) == 1
