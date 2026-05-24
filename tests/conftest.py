"""Shared fixture builders.

Generates three deterministic placeholder face images on import so the
fixtures directory is always populated, even on a fresh clone.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _draw_face(path: Path, base: tuple[int, int, int], accent: tuple[int, int, int]) -> None:
    img = Image.new("RGB", (256, 256), (245, 245, 248))
    draw = ImageDraw.Draw(img)
    # Face oval
    draw.ellipse([48, 40, 208, 224], fill=base, outline=(60, 60, 60), width=2)
    # Eyes
    draw.ellipse([90, 110, 110, 130], fill=(30, 30, 30))
    draw.ellipse([146, 110, 166, 130], fill=(30, 30, 30))
    # Nose
    draw.line([(128, 130), (128, 160)], fill=(60, 40, 30), width=2)
    # Mouth
    draw.arc([108, 160, 148, 200], start=10, end=170, fill=accent, width=4)
    # Hair (top arc)
    draw.chord([48, 30, 208, 130], start=180, end=360, fill=(40, 28, 24))
    img.save(path, format="PNG")


def _ensure_fixtures() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    presets = [
        ("face_warm.png", (232, 196, 168), (180, 80, 80)),
        ("face_cool.png", (220, 188, 176), (160, 70, 110)),
        ("face_olive.png", (200, 176, 140), (150, 80, 60)),
    ]
    for name, base, accent in presets:
        p = FIXTURE_DIR / name
        if not p.exists():
            _draw_face(p, base, accent)


_ensure_fixtures()
