"""The view widget: zoom, pan, and fit-to-window over a CanvasScene."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QGraphicsView

from litho.canvas.scene import CanvasScene

MIN_ZOOM = 0.1
MAX_ZOOM = 8.0
ZOOM_STEP = 1.25

BACKGROUND_COLOR = QColor("#1c1f26")


class CanvasView(QGraphicsView):
    zoom_changed = Signal(float)

    def __init__(self, scene: CanvasScene) -> None:
        super().__init__(scene)
        # QGraphicsView does not take Python-side ownership of the scene,
        # so without this the caller must keep their own reference alive
        # for as long as the view exists, or PySide6 will garbage-collect
        # it out from under us.
        self._scene = scene
        self._zoom = 1.0

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(BACKGROUND_COLOR)

    @property
    def zoom(self) -> float:
        return self._zoom

    def zoom_in(self) -> None:
        self.set_zoom(self._zoom * ZOOM_STEP)

    def zoom_out(self) -> None:
        self.set_zoom(self._zoom / ZOOM_STEP)

    def set_zoom(self, zoom: float) -> None:
        zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
        self._zoom = zoom
        transform = self.transform()
        transform.reset()
        transform.scale(zoom, zoom)
        self.setTransform(transform)
        self.zoom_changed.emit(self._zoom)

    def fit_to_window(self) -> None:
        scene = self.scene()
        if scene is None or not isinstance(scene, CanvasScene) or not scene.has_image:
            return
        self.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom = self.transform().m11()
        self.zoom_changed.emit(self._zoom)
