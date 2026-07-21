"""The graphics scene holding the background image and, eventually, every
annotation item drawn on top of it (see canvas/items.py, not yet built).
"""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene


class CanvasScene(QGraphicsScene):
    def __init__(self) -> None:
        super().__init__()
        self._background_item: QGraphicsPixmapItem | None = None

    @property
    def has_image(self) -> bool:
        return self._background_item is not None

    def set_image(self, pixmap: QPixmap) -> None:
        """Replace the background image. Also clears any existing
        annotations, since they belong to whatever image was open before.
        """
        self.clear()
        self._background_item = self.addPixmap(pixmap)
        self._background_item.setZValue(-1)
        self.setSceneRect(self._background_item.boundingRect())

    def image_size(self) -> QSize | None:
        if self._background_item is None:
            return None
        return self._background_item.pixmap().size()
