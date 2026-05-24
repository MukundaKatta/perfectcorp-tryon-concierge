"""Compose the intermediate stages into a single side-by-side gallery image.

Pure Pillow, no other deps. The gallery is a horizontal strip of equal-height
panels with a small label under each one so a reviewer can tell which stage
produced which image. The caller passes ``(label, image_bytes)`` pairs in the
order they want them rendered.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence
import io

from PIL import Image, ImageDraw, ImageFont


def compose_gallery(
    panels: Sequence[tuple[str, bytes]],
    out_path: str | Path,
    *,
    panel_height: int = 360,
    label_height: int = 28,
    background: tuple[int, int, int] = (245, 245, 248),
    gap: int = 12,
) -> Path:
    """Write a horizontal strip of labelled panels to ``out_path``.

    Returns the resolved output path. Raises ``ValueError`` if ``panels``
    is empty.
    """

    if not panels:
        raise ValueError("compose_gallery requires at least one panel")

    images = [_normalize(b, panel_height) for _, b in panels]
    labels = [label for label, _ in panels]

    total_width = sum(img.width for img in images) + gap * (len(images) + 1)
    total_height = panel_height + label_height + gap * 2
    canvas = Image.new("RGB", (total_width, total_height), background)
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.load_default()
    except Exception:  # pragma: no cover - fallback
        font = None

    x = gap
    for img, label in zip(images, labels):
        canvas.paste(img, (x, gap))
        try:
            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
        except Exception:
            tw = 8 * len(label)
        text_x = x + max(0, (img.width - tw) // 2)
        draw.text((text_x, gap + panel_height + 4), label, fill=(20, 20, 30), font=font)
        x += img.width + gap

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, format="PNG")
    return out


def _normalize(image_bytes: bytes, target_height: int) -> Image.Image:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if img.height == target_height:
        return img
    scale = target_height / float(img.height)
    new_width = max(1, int(img.width * scale))
    return img.resize((new_width, target_height), Image.LANCZOS)


def panels_from_iter(items: Iterable[tuple[str, bytes]]) -> list[tuple[str, bytes]]:
    """Materialize a panels iterable for callers that want a list."""

    return list(items)
