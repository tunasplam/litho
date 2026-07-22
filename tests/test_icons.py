from litho import icons


def test_every_tool_icon_renders_something(qapp):
    for icon_fn in (
        icons.select_icon,
        icons.rectangle_icon,
        icons.line_icon,
        icons.arrow_icon,
        icons.double_arrow_icon,
        icons.freehand_icon,
        icons.highlighter_icon,
        icons.text_icon,
    ):
        icon = icon_fn()
        pixmap = icon.pixmap(icons.ICON_SIZE, icons.ICON_SIZE)
        assert not pixmap.isNull()
        image = pixmap.toImage()
        painted_pixels = sum(
            1
            for x in range(image.width())
            for y in range(image.height())
            if image.pixelColor(x, y).alpha() > 0
        )
        assert painted_pixels > 0
