"""Top-level facade that ties intent + planner + youcam + gallery together.

A ``Concierge`` is constructed with an ``IntentParser`` and a
``YouCamProvider`` (real or fake). ``run`` is the single entrypoint the
demo, the tests, and the Gradio app all use; it returns a
``ConciergeRun`` with the final composite image, every intermediate
panel, the structured plan, the observability summary, and a short
human-readable explanation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import time

from .gallery import compose_gallery
from .intent import IntentParser, LookSpec, LLM
from .observability import Observability, load_rates
from .planner import YouCamTask, plan_tasks
from .youcam import YouCamProvider, YouCamCallResult


@dataclass
class ConciergeRun:
    """Result bundle returned by ``Concierge.run``."""

    request: str
    spec: LookSpec
    tasks: list[YouCamTask]
    panels: list[tuple[str, bytes]]
    final_image: bytes
    gallery_path: Path
    observability: dict[str, Any]
    call_table: list[list[Any]]
    explanation: str
    skin: dict[str, Any] = field(default_factory=dict)


class Concierge:
    """Compose the full pipeline behind a single ``run`` method."""

    def __init__(
        self,
        intent_llm: LLM | IntentParser,
        youcam_provider: YouCamProvider,
        *,
        out_dir: str | Path = "out",
        rates_path: str | Path | None = None,
    ) -> None:
        self.parser = intent_llm if isinstance(intent_llm, IntentParser) else IntentParser(intent_llm)
        self.provider = youcam_provider
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.rates = load_rates(rates_path)

    def run(self, selfie_path: str | Path, request: str) -> ConciergeRun:
        selfie = Path(selfie_path)
        if not selfie.exists():
            raise FileNotFoundError(f"selfie not found: {selfie}")
        original = selfie.read_bytes()
        return self.run_bytes(original, request, original_name=selfie.name)

    def run_bytes(self, original: bytes, request: str, *, original_name: str = "selfie.png") -> ConciergeRun:
        spec = self.parser.parse(request)
        tasks = plan_tasks(spec)
        obs = Observability(rates=self.rates)

        panels: list[tuple[str, bytes]] = [("original", original)]
        skin_data: dict[str, Any] = {}
        current = original

        for task in tasks:
            if task.api_name == "composite":
                # Local step: use the most recent panel as the composite.
                panels.append(("final composite", current))
                obs.record("composite", latency_ms=0.0, confidence=1.0, ok=True)
                continue

            label = _label_for(task)
            start = time.perf_counter()
            try:
                result: YouCamCallResult = self.provider.call(task.api_name, current, task.params)
                latency_ms = (time.perf_counter() - start) * 1000.0
                obs.record(task.api_name, latency_ms=latency_ms, confidence=result.confidence, ok=True)
                if task.api_name == "skin_analysis":
                    skin_data = dict(result.data)
                if result.image_bytes is not None:
                    current = result.image_bytes
                panels.append((label, result.image_bytes if result.image_bytes is not None else current))
            except Exception as exc:  # surface failure without aborting the pipeline
                latency_ms = (time.perf_counter() - start) * 1000.0
                obs.record(task.api_name, latency_ms=latency_ms, confidence=0.0, ok=False, error=str(exc))
                panels.append((f"{label} (failed)", current))

        gallery_path = self.out_dir / "gallery.png"
        compose_gallery(panels, gallery_path)

        explanation = _explain(spec, skin_data)
        return ConciergeRun(
            request=request,
            spec=spec,
            tasks=list(tasks),
            panels=panels,
            final_image=current,
            gallery_path=gallery_path,
            observability=obs.summary(),
            call_table=obs.as_table_rows(),
            explanation=explanation,
            skin=skin_data,
        )


def _label_for(task: YouCamTask) -> str:
    if task.api_name == "skin_analysis":
        return "skin analysis"
    if task.api_name in ("ai_makeup_transfer", "makeup_transfer"):
        return f"makeup: {task.params.get('look', 'glow')}"
    if task.api_name in ("ai_hairstyle", "hairstyle"):
        return f"hair: {task.params.get('style', 'natural')}"
    if task.api_name == "earrings_tryon":
        return f"earrings: {task.params.get('style_family', 'classic')}"
    return task.api_name


def _explain(spec: LookSpec, skin: dict[str, Any]) -> str:
    """Single paragraph 'why this look' note for the user."""

    pieces: list[str] = []
    pieces.append(f"For a {spec.occasion.replace('_', ' ')} feel,")
    pieces.append(f"the plan leans into a {spec.intensity} {spec.undertone} palette")
    if spec.hair_change_ok:
        pieces.append("and tries a matching hairstyle preset.")
    else:
        pieces.append("and keeps your current hair as-is.")
    if spec.jewelry_ok:
        pieces.append("Earrings are layered on after the makeup pass.")
    if skin:
        moisture = skin.get("moisture")
        undertone = skin.get("undertone")
        if moisture is not None and undertone is not None:
            pieces.append(
                f"Skin analysis read a {undertone} undertone with moisture around {moisture}, "
                "so warm pigments were nudged up and cool pigments held back."
            )
    return " ".join(pieces)
