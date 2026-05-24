"""tryon_concierge: a chat-style concierge over the Perfect Corp YouCam APIs.

The package decomposes a natural-language style request into a sequence of
YouCam API calls (skin analysis, makeup VTO, hairstyle generator) and returns
a side-by-side gallery plus a short observability report.
"""

from .intent import LookSpec, FakeLLM, OpenAILLM, IntentParser
from .planner import YouCamTask, plan_tasks
from .youcam import (
    YouCamProvider,
    FakeYouCamProvider,
    RealYouCamProvider,
    YouCamCallResult,
)
from .observability import CallRecord, Observability, load_rates
from .gallery import compose_gallery
from .concierge import Concierge, ConciergeRun

__all__ = [
    "LookSpec",
    "FakeLLM",
    "OpenAILLM",
    "IntentParser",
    "YouCamTask",
    "plan_tasks",
    "YouCamProvider",
    "FakeYouCamProvider",
    "RealYouCamProvider",
    "YouCamCallResult",
    "CallRecord",
    "Observability",
    "load_rates",
    "compose_gallery",
    "Concierge",
    "ConciergeRun",
]

__version__ = "0.1.0"
