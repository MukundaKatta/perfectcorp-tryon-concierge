"""Parse a free-form style request into a structured LookSpec.

Two adapters are provided:

* ``FakeLLM`` is a deterministic keyword-based stub for tests and the offline demo.
* ``OpenAILLM`` calls an OpenAI-compatible chat completion endpoint and
  returns the same ``LookSpec`` shape. It is wired but not required for
  the default run path.

The parser keeps the LLM contract narrow: the model is asked for a JSON
object with five known keys, and the wrapper validates and normalizes the
values before constructing ``LookSpec``.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping, Protocol
import json
import os
import re


_OCCASIONS = (
    "wedding_guest",
    "office",
    "date_night",
    "everyday",
    "festival",
    "interview",
    "brunch",
    "red_carpet",
)
_UNDERTONES = ("cool", "neutral", "warm", "olive", "deep")
_INTENSITY = ("subtle", "natural", "bold")


@dataclass(frozen=True)
class LookSpec:
    """Structured style request used by the planner.

    Attributes are deliberately small and enumerated so the planner can
    branch on them without re-parsing strings.
    """

    occasion: str
    undertone: str
    intensity: str
    hair_change_ok: bool
    jewelry_ok: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LLM(Protocol):
    def complete(self, prompt: str) -> str:  # pragma: no cover - protocol
        ...


class FakeLLM:
    """Deterministic stand-in for an LLM. No network, no surprises.

    Pattern-matches a handful of keywords in the request and returns a
    JSON string with the same schema the real adapter would emit.
    """

    def __init__(self, default_occasion: str = "everyday") -> None:
        self.default_occasion = default_occasion

    def complete(self, prompt: str) -> str:
        # The prompt template wraps the user request between a "Request:"
        # marker and a "Return JSON" footer. Strip the template chrome so
        # the keyword matcher only sees the user's actual words.
        text = _extract_user_request(prompt).lower()

        occasion = self.default_occasion
        for candidate, keywords in {
            "wedding_guest": ("wedding", "bridal", "ceremony"),
            "office": ("office", "work", "boardroom", "meeting"),
            "date_night": ("date", "dinner", "evening", "night out"),
            "festival": ("festival", "concert", "party"),
            "interview": ("interview", "recruiter"),
            "brunch": ("brunch", "weekend"),
            "red_carpet": ("red carpet", "premiere", "gala"),
        }.items():
            if any(k in text for k in keywords):
                occasion = candidate
                break

        # Prefer specific skin descriptors (olive, deep) before the warmth
        # axis (cool / warm / neutral) so "warm wedding guest look, olive
        # skin" reads as olive, not warm.
        undertone = "neutral"
        for candidate in ("olive", "deep", "cool", "warm", "neutral"):
            if candidate in text:
                undertone = candidate
                break

        intensity = "natural"
        if any(k in text for k in ("subtle", "soft", "minimal", "barely")):
            intensity = "subtle"
        elif any(k in text for k in ("bold", "statement", "dramatic", "smokey", "smoky")):
            intensity = "bold"

        hair_change_ok = not any(k in text for k in ("keep my hair", "no hair", "do not change hair"))
        if "hair" in text and any(k in text for k in ("change", "new", "try", "swap")):
            hair_change_ok = True

        jewelry_ok = any(k in text for k in ("jewelry", "jewellery", "earring", "necklace"))

        return json.dumps(
            {
                "occasion": occasion,
                "undertone": undertone,
                "intensity": intensity,
                "hair_change_ok": hair_change_ok,
                "jewelry_ok": jewelry_ok,
            }
        )


class OpenAILLM:
    """Thin OpenAI-compatible chat adapter.

    Requires ``requests`` and ``OPENAI_API_KEY``. Kept here so the demo
    can be flipped to a real LLM without touching the rest of the pipeline.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_s: float = 20.0,
    ) -> None:
        self.model = model
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.timeout_s = timeout_s

    def complete(self, prompt: str) -> str:  # pragma: no cover - network path
        import requests  # local import; keeps tests offline

        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set; use FakeLLM for offline runs.")
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "Return only a JSON object with the requested keys."},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=self.timeout_s,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


_PROMPT_TEMPLATE = """You are a beauty try-on planner.
Given the user's free-form style request, return a strict JSON object with these keys:

- occasion: one of {occasions}
- undertone: one of {undertones}
- intensity: one of {intensity}
- hair_change_ok: boolean (true if the user is open to trying a different hairstyle)
- jewelry_ok: boolean (true if the user explicitly wants to try earrings or necklaces)

Request:
{request}

Return JSON only, no prose."""


class IntentParser:
    """Wraps an LLM and validates the response into a ``LookSpec``."""

    def __init__(self, llm: LLM) -> None:
        self.llm = llm

    def parse(self, request: str) -> LookSpec:
        prompt = _PROMPT_TEMPLATE.format(
            occasions=", ".join(_OCCASIONS),
            undertones=", ".join(_UNDERTONES),
            intensity=", ".join(_INTENSITY),
            request=request.strip(),
        )
        raw = self.llm.complete(prompt)
        data = _coerce_json(raw)
        return self._normalize(data)

    @staticmethod
    def _normalize(data: Mapping[str, Any]) -> LookSpec:
        occasion = str(data.get("occasion", "everyday"))
        if occasion not in _OCCASIONS:
            occasion = "everyday"
        undertone = str(data.get("undertone", "neutral"))
        if undertone not in _UNDERTONES:
            undertone = "neutral"
        intensity = str(data.get("intensity", "natural"))
        if intensity not in _INTENSITY:
            intensity = "natural"
        hair_change_ok = _truthy(data.get("hair_change_ok", True))
        jewelry_ok = _truthy(data.get("jewelry_ok", False))
        return LookSpec(
            occasion=occasion,
            undertone=undertone,
            intensity=intensity,
            hair_change_ok=hair_change_ok,
            jewelry_ok=jewelry_ok,
        )


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("true", "yes", "1", "y", "on")
    return False


_REQUEST_MARKER = "Request:"
_REQUEST_FOOTER = "Return JSON only"


def _extract_user_request(prompt: str) -> str:
    """Return just the user request portion of a templated prompt.

    Falls back to the full prompt when the markers are not present, which
    is what callers passing a raw request string will see.
    """

    if _REQUEST_MARKER in prompt:
        tail = prompt.split(_REQUEST_MARKER, 1)[1]
        if _REQUEST_FOOTER in tail:
            tail = tail.split(_REQUEST_FOOTER, 1)[0]
        return tail.strip()
    return prompt


def _coerce_json(text: str) -> dict[str, Any]:
    """Pull the first JSON object out of an LLM response.

    Real models occasionally wrap JSON in code fences or chatter; this
    helper extracts the first ``{...}`` block and parses it.
    """

    text = text.strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}
