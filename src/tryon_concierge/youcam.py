"""Adapter for the Perfect Corp YouCam API.

The real provider talks to the YouCam REST API (``YOUCAM_BASE_URL``) using
``YOUCAM_API_KEY`` as a bearer token. The fake provider returns
deterministic placeholder images so the demo, tests, and Gradio UI all run
end-to-end without credentials.

Both providers share the same surface so the concierge does not care which
backend is wired in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import hashlib
import io
import os
import time

from PIL import Image, ImageDraw, ImageFilter, ImageFont


@dataclass(frozen=True)
class YouCamCallResult:
    """One YouCam API response, normalized.

    ``image_bytes`` is the resulting image (PNG bytes) when the call
    produces an image. ``data`` carries non-image structured fields like
    skin analysis scores. ``confidence`` is a 0..1 indicator that the
    concierge surfaces in the observability table.
    """

    api_name: str
    image_bytes: bytes | None
    data: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


class YouCamProvider(Protocol):
    def analyze_skin(self, image: bytes) -> YouCamCallResult:  # pragma: no cover - protocol
        ...

    def apply_makeup(self, image: bytes, look: str, **kwargs: Any) -> YouCamCallResult:  # pragma: no cover - protocol
        ...

    def change_hairstyle(self, image: bytes, style: str, **kwargs: Any) -> YouCamCallResult:  # pragma: no cover - protocol
        ...

    def call(self, api_name: str, image: bytes, params: dict[str, Any]) -> YouCamCallResult:  # pragma: no cover - protocol
        ...


# ----------------------------- helpers ---------------------------------


def _stable_seed(*parts: Any) -> int:
    """Tiny deterministic hash so fake outputs are reproducible per input."""

    digest = hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _open_or_blank(image_bytes: bytes | None, size: tuple[int, int] = (512, 512)) -> Image.Image:
    if not image_bytes:
        return Image.new("RGB", size, (220, 220, 220))
    try:
        return Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return Image.new("RGB", size, (220, 220, 220))


def _to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _label(img: Image.Image, text: str) -> Image.Image:
    out = img.copy()
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.load_default()
    except Exception:  # pragma: no cover - fallback
        font = None
    pad = 6
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        tw, th = (8 * len(text), 12)
    box = [0, out.height - th - pad * 2, tw + pad * 2, out.height]
    draw.rectangle(box, fill=(0, 0, 0))
    draw.text((pad, out.height - th - pad), text, fill=(255, 255, 255), font=font)
    return out


# ----------------------------- fake provider ---------------------------


class FakeYouCamProvider:
    """Deterministic offline provider.

    Each method produces a labelled placeholder image so a reviewer can
    immediately see which stage produced which output. The image
    transforms are intentionally simple (tint, blur, overlay) so they
    are obvious in the side-by-side gallery.
    """

    def __init__(self, latency_s: float = 0.0) -> None:
        self.latency_s = latency_s

    def _sleep(self) -> None:
        if self.latency_s:
            time.sleep(self.latency_s)

    def analyze_skin(self, image: bytes) -> YouCamCallResult:
        self._sleep()
        seed = _stable_seed("skin", len(image))
        moisture = 40 + (seed % 50)
        clarity = 50 + ((seed // 7) % 40)
        firmness = 45 + ((seed // 11) % 45)
        undertone = ("cool", "neutral", "warm", "olive", "deep")[seed % 5]
        img = _open_or_blank(image)
        img = _label(img, "skin analysis")
        return YouCamCallResult(
            api_name="skin_analysis",
            image_bytes=_to_png_bytes(img),
            data={
                "moisture": moisture,
                "clarity": clarity,
                "firmness": firmness,
                "undertone": undertone,
            },
            confidence=0.9,
        )

    def apply_makeup(self, image: bytes, look: str, **kwargs: Any) -> YouCamCallResult:
        self._sleep()
        img = _open_or_blank(image)
        seed = _stable_seed("makeup", look, len(image))
        tint = (
            180 + (seed % 60),
            120 + ((seed // 5) % 80),
            130 + ((seed // 11) % 70),
        )
        overlay = Image.new("RGB", img.size, tint)
        blended = Image.blend(img, overlay, 0.18)
        blended = _label(blended, f"makeup: {look}")
        return YouCamCallResult(
            api_name="ai_makeup_transfer",
            image_bytes=_to_png_bytes(blended),
            data={"look": look, **kwargs},
            confidence=0.85,
        )

    def change_hairstyle(self, image: bytes, style: str, **kwargs: Any) -> YouCamCallResult:
        self._sleep()
        img = _open_or_blank(image)
        # Simulate a hair restyle by blurring + slight tint at the top third.
        top = img.crop((0, 0, img.width, img.height // 3))
        top = top.filter(ImageFilter.GaussianBlur(radius=6))
        out = img.copy()
        out.paste(top, (0, 0))
        out = _label(out, f"hair: {style}")
        return YouCamCallResult(
            api_name="ai_hairstyle",
            image_bytes=_to_png_bytes(out),
            data={"style": style, **kwargs},
            confidence=0.78,
        )

    def try_earrings(self, image: bytes, style_family: str, **kwargs: Any) -> YouCamCallResult:
        self._sleep()
        img = _open_or_blank(image)
        draw = ImageDraw.Draw(img)
        # Two small circles where ears would be.
        cy = int(img.height * 0.55)
        r = max(4, img.width // 60)
        left = (int(img.width * 0.22), cy)
        right = (int(img.width * 0.78), cy)
        for cx, y in (left, right):
            draw.ellipse([cx - r, y - r, cx + r, y + r], fill=(230, 200, 90))
        out = _label(img, f"earrings: {style_family}")
        return YouCamCallResult(
            api_name="earrings_tryon",
            image_bytes=_to_png_bytes(out),
            data={"style_family": style_family, **kwargs},
            confidence=0.7,
        )

    def call(self, api_name: str, image: bytes, params: dict[str, Any]) -> YouCamCallResult:
        if api_name == "skin_analysis":
            return self.analyze_skin(image)
        if api_name in ("ai_makeup_transfer", "makeup_transfer"):
            look = str(params.get("look", "everyday_glow"))
            return self.apply_makeup(image, look, **{k: v for k, v in params.items() if k != "look"})
        if api_name in ("ai_hairstyle", "hairstyle"):
            style = str(params.get("style", "natural_blowout"))
            return self.change_hairstyle(image, style, **{k: v for k, v in params.items() if k != "style"})
        if api_name == "earrings_tryon":
            family = str(params.get("style_family", "everyday"))
            return self.try_earrings(image, family, **{k: v for k, v in params.items() if k != "style_family"})
        if api_name == "composite":
            img = _open_or_blank(image)
            out = _label(img, "composite")
            return YouCamCallResult(
                api_name="composite",
                image_bytes=_to_png_bytes(out),
                data={"note": "client-side composite stub"},
                confidence=1.0,
            )
        # Unknown API: return a labelled passthrough so the pipeline keeps moving.
        img = _open_or_blank(image)
        out = _label(img, f"passthrough: {api_name}")
        return YouCamCallResult(
            api_name=api_name,
            image_bytes=_to_png_bytes(out),
            data={"params": params, "note": "unknown api, passthrough"},
            confidence=0.5,
        )


# ----------------------------- real provider ---------------------------


class RealYouCamProvider:
    """HTTP client for the Perfect Corp YouCam API.

    The endpoint shape on the production API differs slightly per call,
    so this class keeps the protocol thin: it uploads the image, posts to
    ``{base_url}/{api_name}``, and returns the resulting image bytes plus
    any structured metadata. The exact request body for each YouCam API
    should be filled in per-endpoint when wiring this to production.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("YOUCAM_API_KEY", "")
        self.base_url = (base_url or os.environ.get("YOUCAM_BASE_URL", "https://yce-api-01.perfectcorp.com")).rstrip("/")
        self.timeout_s = timeout_s

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError("YOUCAM_API_KEY is not set; use FakeYouCamProvider for offline runs.")
        return {"Authorization": f"Bearer {self.api_key}"}

    def _post(self, path: str, image: bytes, params: dict[str, Any]) -> YouCamCallResult:  # pragma: no cover - network path
        import requests

        files = {"image": ("input.png", image, "image/png")}
        resp = requests.post(
            f"{self.base_url}/{path.lstrip('/')}",
            headers=self._headers(),
            data=params,
            files=files,
            timeout=self.timeout_s,
        )
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if content_type.startswith("image/"):
            return YouCamCallResult(api_name=path, image_bytes=resp.content, data={}, confidence=1.0)
        payload = resp.json()
        image_b64 = payload.get("image") or payload.get("result_image")
        image_bytes: bytes | None = None
        if image_b64:
            import base64

            image_bytes = base64.b64decode(image_b64)
        return YouCamCallResult(
            api_name=path,
            image_bytes=image_bytes,
            data={k: v for k, v in payload.items() if k not in ("image", "result_image")},
            confidence=float(payload.get("confidence", 1.0)),
        )

    def analyze_skin(self, image: bytes) -> YouCamCallResult:  # pragma: no cover - network path
        return self._post("skin-analysis", image, {})

    def apply_makeup(self, image: bytes, look: str, **kwargs: Any) -> YouCamCallResult:  # pragma: no cover - network path
        params = {"look": look, **{k: str(v) for k, v in kwargs.items()}}
        return self._post("ai-makeup-transfer", image, params)

    def change_hairstyle(self, image: bytes, style: str, **kwargs: Any) -> YouCamCallResult:  # pragma: no cover - network path
        params = {"style": style, **{k: str(v) for k, v in kwargs.items()}}
        return self._post("ai-hairstyle", image, params)

    def call(self, api_name: str, image: bytes, params: dict[str, Any]) -> YouCamCallResult:  # pragma: no cover - network path
        if api_name == "skin_analysis":
            return self.analyze_skin(image)
        if api_name in ("ai_makeup_transfer", "makeup_transfer"):
            return self.apply_makeup(image, str(params.get("look", "everyday_glow")), **{k: v for k, v in params.items() if k != "look"})
        if api_name in ("ai_hairstyle", "hairstyle"):
            return self.change_hairstyle(image, str(params.get("style", "natural_blowout")), **{k: v for k, v in params.items() if k != "style"})
        if api_name == "composite":
            # Composite is local; we never call out for it.
            return YouCamCallResult(api_name="composite", image_bytes=image, data={}, confidence=1.0)
        return self._post(api_name.replace("_", "-"), image, {k: str(v) for k, v in params.items()})
