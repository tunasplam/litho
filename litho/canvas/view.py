"""The view widget: zoom, pan, and fit-to-window over a CanvasScene."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsView

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
        self._active_tool = None

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(BACKGROUND_COLOR)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

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

    # ---------------------------------------------------------------
    # Active tool + event routing
    # ---------------------------------------------------------------
    def set_tool(self, tool) -> None:
        if self._active_tool is not None:
            self._active_tool.deactivate()
        self._active_tool = tool
        if tool is not None:
            tool.activate()

    def _is_editing_text(self) -> bool:
        """True while a text item is mid-edit — in that state, mouse/key
        input needs to reach the item itself (cursor placement, text
        selection, Backspace-to-delete-a-character, click-away-to-commit)
        instead of being intercepted by whatever tool is active.
        """
        scene = self.scene()
        if scene is None:
            return False
        focus_item = scene.focusItem()
        return (
            isinstance(focus_item, QGraphicsTextItem)
            and focus_item.textInteractionFlags() != Qt.TextInteractionFlag.NoTextInteraction
        )

    def mousePressEvent(self, event) -> None:
        if self._is_editing_text() or self._active_tool is None or not self._active_tool.handles_own_events:
            super().mousePressEvent(event)
            return
        self._active_tool.on_press(self.mapToScene(event.position().toPoint()))

    def mouseMoveEvent(self, event) -> None:
        if self._is_editing_text() or self._active_tool is None or not self._active_tool.handles_own_events:
            super().mouseMoveEvent(event)
            return
        self._active_tool.on_move(self.mapToScene(event.position().toPoint()))

    def mouseReleaseEvent(self, event) -> None:
        if self._is_editing_text() or self._active_tool is None or not self._active_tool.handles_own_events:
            super().mouseReleaseEvent(event)
            return
        self._active_tool.on_release(self.mapToScene(event.position().toPoint()))

    def keyPressEvent(self, event) -> None:
        if not self._is_editing_text() and event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self._delete_selected_items()
            return
        super().keyPressEvent(event)

    def _delete_selected_items(self) -> None:
        scene = self.scene()
        if scene is None:
            return
        for item in scene.selectedItems():
            scene.removeItem(item)
