from litho.__main__ import parse_args


def test_parse_args_with_no_image():
    args = parse_args([])

    assert args.image is None


def test_parse_args_with_an_image_path():
    args = parse_args(["photo.png"])

    assert args.image == "photo.png"
