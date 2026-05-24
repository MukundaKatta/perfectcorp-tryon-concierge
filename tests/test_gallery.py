import io
from pathlib import Path

import pytest
from PIL import Image

from tryon_concierge.gallery import compose_gallery, panels_from_iter


def _solid_panel(color: tuple[int, int, int]) -> bytes:
    img = Image.new("RGB", (200, 200), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_compose_gallery_writes_a_horizontal_strip(tmp_path: Path) -> None:
    panels = [
        ("original", _solid_panel((255, 0, 0))),
        ("makeup", _solid_panel((0, 255, 0))),
        ("hair", _solid_panel((0, 0, 255))),
    ]
    out = compose_gallery(panels, tmp_path / "gallery.png", panel_height=180)
    assert out.exists()
    img = Image.open(out)
    assert img.width > img.height
    # Should fit three panels of equal height plus gaps.
    assert img.height >= 180


def test_compose_gallery_handles_two_panels(tmp_path: Path) -> None:
    panels = [
        ("a", _solid_panel((10, 20, 30))),
        ("b", _solid_panel((200, 220, 240))),
    ]
    out = compose_gallery(panels, tmp_path / "g2.png")
    assert out.exists()


def test_compose_gallery_rejects_empty(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        compose_gallery([], tmp_path / "x.png")


def test_panels_from_iter_returns_list() -> None:
    items = iter([("a", _solid_panel((1, 2, 3)))])
    out = panels_from_iter(items)
    assert isinstance(out, list)
    assert out[0][0] == "a"
