"""The main application window: builds the two top toolbars, the canvas,
and wires them together. Tool switching updates the canvas's active tool;
the stroke/fill/size/opacity controls feed a shared Style object that
tools read from when they create new items.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QPixmap
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QToolBar,
    QWidget,
)

from litho.canvas.items import LineItem
from litho.canvas.scene import CanvasScene
from litho.canvas.view import CanvasView
from litho.tools.base import Style, Tool
from litho.tools.highlighter import HighlighterTool
from litho.tools.line import LineTool
from litho.tools.select import SelectTool

WINDOW_TITLE = "Litho"
DEFAULT_WINDOW_SIZE = (1200, 800)

EXPORT_FORMATS = ["PNG", "JPG", "BMP"]

# Temporary, pending io.py: Qt's own image plugins are enough to get
# something on screen while the canvas is being built.
IMAGE_FILE_FILTER = "Images (*.png *.jpg *.jpeg *.bmp *.webp *.gif)"

DEFAULT_STROKE_COLOR = "#8fb8ff"
DEFAULT_FILL_COLOR = "#f5c451"


class MainWindow(QMainWindow):
    def __init__(self, initial_image: str | None = None) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(*DEFAULT_WINDOW_SIZE)

        self._build_toolbar_row1()
        self._build_toolbar_row2()
        self._build_canvas()
        self._connect_canvas_actions()
        self._build_tools()
        self._connect_style_controls()

        if initial_image:
            self.open_image_from_path(initial_image)

    # ---------------------------------------------------------------
    # Row 1: file / edit / zoom
    # ---------------------------------------------------------------
    def _build_toolbar_row1(self) -> None:
        toolbar = self._new_toolbar("File")

        self.action_new = toolbar.addAction("New")
        self.action_open = toolbar.addAction("Open")
        self.action_save = toolbar.addAction("Save")

        self.format_combo = QComboBox()
        self.format_combo.addItems(EXPORT_FORMATS)
        toolbar.addWidget(self.format_combo)

        toolbar.addSeparator()

        self.action_undo = toolbar.addAction("Undo")
        self.action_redo = toolbar.addAction("Redo")
        self.action_undo.setEnabled(False)
        self.action_redo.setEnabled(False)

        toolbar.addWidget(_stretch_spacer())

        self.action_zoom_out = toolbar.addAction("−")
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(42)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbar.addWidget(self.zoom_label)
        self.action_zoom_in = toolbar.addAction("+")
        self.action_fit = toolbar.addAction("Fit")

        self.addToolBar(toolbar)
        self.addToolBarBreak()

    # ---------------------------------------------------------------
    # Row 2: drawing tools + contextual object properties
    # ---------------------------------------------------------------
    def _build_toolbar_row2(self) -> None:
        toolbar = self._new_toolbar("Tools")

        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)

        self.action_select = self._add_tool_action(toolbar, "Select")
        self.action_polygon = self._add_tool_action(toolbar, "Polygon")
        self.action_line = self._add_tool_action(toolbar, "Line")
        self.action_arrow = self._add_tool_action(toolbar, "Arrow")
        self.action_double_arrow = self._add_tool_action(toolbar, "Double arrow")
        self.action_freehand = self._add_tool_action(toolbar, "Freehand")
        self.action_highlighter = self._add_tool_action(toolbar, "Highlighter")
        self.action_text = self._add_tool_action(toolbar, "Text box")

        self.action_select.setChecked(True)

        # Not implemented yet — disabled rather than clickable-but-broken.
        for action in (
            self.action_polygon,
            self.action_freehand,
            self.action_text,
        ):
            action.setEnabled(False)

        toolbar.addSeparator()

        self.stroke_swatch = _color_swatch(DEFAULT_STROKE_COLOR)
        self.fill_swatch = _color_swatch(DEFAULT_FILL_COLOR)
        toolbar.addWidget(QLabel("Stroke"))
        toolbar.addWidget(self.stroke_swatch)
        toolbar.addWidget(QLabel("Fill"))
        toolbar.addWidget(self.fill_swatch)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 200)
        self.size_spin.setValue(14)
        toolbar.addWidget(QLabel("Size"))
        toolbar.addWidget(self.size_spin)

        self.opacity_spin = QSpinBox()
        self.opacity_spin.setRange(0, 100)
        self.opacity_spin.setValue(100)
        self.opacity_spin.setSuffix("%")
        toolbar.addWidget(QLabel("Opacity"))
        toolbar.addWidget(self.opacity_spin)

        self.addToolBar(toolbar)

    def _add_tool_action(self, toolbar: QToolBar, label: str) -> QAction:
        action = toolbar.addAction(label)
        action.setCheckable(True)
        self.tool_group.addAction(action)
        return action

    # ---------------------------------------------------------------
    # Canvas
    # ---------------------------------------------------------------
    def _build_canvas(self) -> None:
        self.scene = CanvasScene()
        self.view = CanvasView(self.scene)
        self.setCentralWidget(self.view)

    def _connect_canvas_actions(self) -> None:
        self.action_open.triggered.connect(self._on_open)
        self.action_zoom_in.triggered.connect(self.view.zoom_in)
        self.action_zoom_out.triggered.connect(self.view.zoom_out)
        self.action_fit.triggered.connect(self.view.fit_to_window)
        self.view.zoom_changed.connect(self._on_zoom_changed)

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open image", "", IMAGE_FILE_FILTER)
        if not path:
            return
        self.open_image_from_path(path)

    def open_image_from_path(self, path: str) -> bool:
        """Load an image into the canvas. Used by both the Open action and
        the `litho <path>` command-line form. Returns whether it worked.
        """
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return False
        self.scene.set_image(pixmap)
        self.view.fit_to_window()
        return True

    def _on_zoom_changed(self, zoom: float) -> None:
        self.zoom_label.setText(f"{round(zoom * 100)}%")

    # ---------------------------------------------------------------
    # Tools + style
    # ---------------------------------------------------------------
    def _build_tools(self) -> None:
        self.style = Style(
            stroke_color=QColor(DEFAULT_STROKE_COLOR),
            fill_color=QColor(DEFAULT_FILL_COLOR),
            size=self.size_spin.value(),
            opacity=self.opacity_spin.value(),
        )
        self.tools: dict[QAction, Tool] = {
            self.action_select: SelectTool(self.view, self.style),
            self.action_highlighter: HighlighterTool(self.view, self.style),
            self.action_line: LineTool(self.view, self.style, head_style=LineItem.HEAD_NONE),
            self.action_arrow: LineTool(self.view, self.style, head_style=LineItem.HEAD_END),
            self.action_double_arrow: LineTool(
                self.view, self.style, head_style=LineItem.HEAD_BOTH
            ),
        }
        self.tool_group.triggered.connect(self._on_tool_changed)
        self.view.set_tool(self.tools[self.action_select])

    def _on_tool_changed(self, action: QAction) -> None:
        tool = self.tools.get(action)
        if tool is not None:
            self.view.set_tool(tool)

    def _connect_style_controls(self) -> None:
        self.stroke_swatch.clicked.connect(self._on_pick_stroke_color)
        self.fill_swatch.clicked.connect(self._on_pick_fill_color)
        self.size_spin.valueChanged.connect(self._on_size_changed)
        self.opacity_spin.valueChanged.connect(self._on_opacity_changed)

    def _on_pick_stroke_color(self) -> None:
        color = QColorDialog.getColor(self.style.stroke_color, self, "Stroke color")
        if color.isValid():
            self.style.stroke_color = color
            _set_swatch_color(self.stroke_swatch, color)

    def _on_pick_fill_color(self) -> None:
        color = QColorDialog.getColor(self.style.fill_color, self, "Fill color")
        if color.isValid():
            self.style.fill_color = color
            _set_swatch_color(self.fill_swatch, color)

    def _on_size_changed(self, value: int) -> None:
        self.style.size = value

    def _on_opacity_changed(self, value: int) -> None:
        self.style.opacity = value

    # ---------------------------------------------------------------
    def _new_toolbar(self, name: str) -> QToolBar:
        toolbar = QToolBar(name, self)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        return toolbar


def _color_swatch(color: str) -> QPushButton:
    button = QPushButton()
    button.setFixedSize(20, 20)
    button.setStyleSheet(
        f"background-color: {color}; border: 1px solid rgba(255,255,255,0.3);"
    )
    return button


def _set_swatch_color(button: QPushButton, color: QColor) -> None:
    button.setStyleSheet(
        f"background-color: {color.name(QColor.NameFormat.HexArgb)}; "
        "border: 1px solid rgba(255,255,255,0.3);"
    )


def _stretch_spacer() -> QWidget:
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    return spacer
