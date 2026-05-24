"""End-to-end demo with no credentials.

Loads a fixture face, runs the full concierge pipeline through the fake
YouCam provider, prints the per-call observability table, and writes the
side-by-side gallery to ``out/gallery.png``.
"""

from __future__ import annotations

from pathlib import Path
import sys

# Allow `python examples/run_demo.py` from a clean clone before install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tryon_concierge import Concierge, FakeLLM, FakeYouCamProvider, IntentParser


REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "face_warm.png"


def main() -> int:
    if not FIXTURE_PATH.exists():
        # Generate fixtures the same way conftest.py does so the example
        # works even when pytest has not run.
        from tests.conftest import _ensure_fixtures  # type: ignore[import-not-found]

        _ensure_fixtures()

    concierge = Concierge(
        intent_llm=IntentParser(FakeLLM()),
        youcam_provider=FakeYouCamProvider(),
        out_dir=REPO_ROOT / "out",
    )

    request = "warm wedding guest look, olive skin, soft waves, statement earrings"
    print(f"request: {request}\n")

    run = concierge.run(FIXTURE_PATH, request)

    print("plan:")
    for i, task in enumerate(run.tasks, start=1):
        print(f"  {i}. {task.api_name}  {task.params}")
    print()

    print("call table (api / status / latency_ms / units / confidence):")
    for row in run.call_table:
        print(f"  {row}")
    print()

    summary = run.observability
    print(
        "summary: "
        f"calls={summary['total_calls']} "
        f"ok={summary['ok_calls']} "
        f"failed={summary['failed_calls']} "
        f"units={summary['total_units']} "
        f"p50_ms={summary['p50_latency_ms']:.2f} "
        f"p95_ms={summary['p95_latency_ms']:.2f}"
    )
    print()

    print(f"gallery: {run.gallery_path}")
    print(f"explanation: {run.explanation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
