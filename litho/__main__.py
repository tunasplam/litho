"""Entry point — run with `uv run python -m litho [image]`."""

from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from litho.main_window import MainWindow


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="litho", description="A minimal image annotation tool."
    )
    parser.add_argument(
        "image", nargs="?", default=None, help="Image file to open on startup."
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()

    app = QApplication(sys.argv)
    window = MainWindow(initial_image=args.image)
    window.show()

    if args.image and not window.scene.has_image:
        print(f"litho: could not open '{args.image}'", file=sys.stderr)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
