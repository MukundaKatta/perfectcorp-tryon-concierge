# PerfectCorp Try-On Concierge

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-pytest-green.svg)](tests/)
[![Hackathon](https://img.shields.io/badge/DevNetwork-2026-purple.svg)](https://devnetwork.devpost.com/)

A chat-style AI agent that turns a free-form style request into a sequence of
**Perfect Corp YouCam API** calls and returns a side-by-side before/after
gallery with per-call latency, units used, and a one-paragraph "why this look"
explanation.

> Submission for **DevNetwork [AI+ML] Hackathon 2026, Perfect Corp track
> (AI-Driven Consumer Experiences).**

![hero screenshot placeholder](docs/hero.png)

(Screenshot will be added after demo recording. Run `python app.py` to see the
real UI locally.)

## Why this matters

Beauty try-on APIs are extremely capable, but consumer-facing flows still ask
the user to pick the right tool: makeup transfer, hairstyle, jewelry, skin
analysis. The Concierge collapses that into one sentence in plain English and
plans the API calls for you. The whole agent is observable, deterministic in
the offline path, and ships with a working Gradio UI.

## Quickstart

```bash
git clone https://github.com/MukundaKatta/perfectcorp-tryon-concierge
cd perfectcorp-tryon-concierge

python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# Run the test suite (no credentials needed)
.venv/bin/pytest -q

# Run the offline demo
.venv/bin/python examples/run_demo.py

# Launch the Gradio UI on http://127.0.0.1:7860
.venv/bin/python app.py
```

## How it works

```
                  +-----------------+        +-----------------+
  user request -> |  IntentParser   |  --->  |     planner     |
  + selfie        |  (LLM -> JSON)  |        | (LookSpec ->    |
                  +-----------------+        |  YouCamTask[])  |
                          |                  +-----------------+
                          v                          |
                  +-----------------+                v
                  |   LookSpec      |       +-----------------+
                  | occasion        |       |  YouCamProvider |
                  | undertone       |       | Fake | Real     |
                  | intensity       |       +-----------------+
                  | hair_change_ok  |                |
                  | jewelry_ok      |                v
                  +-----------------+       +-----------------+
                                            | Observability   |
                                            | per-call ms +   |
                                            | units + p50/p95 |
                                            +-----------------+
                                                     |
                                                     v
                                            +-----------------+
                                            |    gallery.py   |
                                            | side-by-side    |
                                            | strip + caption |
                                            +-----------------+
```

The pipeline is intentionally small and deterministic:

1. **Intent.** A single LLM call (or `FakeLLM` for offline runs) produces a
   `LookSpec(occasion, undertone, intensity, hair_change_ok, jewelry_ok)`.
2. **Plan.** `planner.plan_tasks(spec)` emits a fixed ordering:
   `skin_analysis -> ai_makeup_transfer -> ai_hairstyle? -> earrings_tryon? -> composite`.
3. **Execute.** Each task goes through `YouCamProvider.call(api_name, image, params)`.
   The fake provider returns deterministic labelled images. The real provider
   posts multipart form data to the YouCam REST API.
4. **Observe.** Latency, unit cost (from `rates.json`), and confidence are
   captured per call.
5. **Compose.** All panels are stitched into a horizontal strip and written
   to `out/gallery.png`.

## Modules

| File | Responsibility |
| --- | --- |
| `src/tryon_concierge/intent.py` | LookSpec dataclass, FakeLLM, OpenAILLM, IntentParser |
| `src/tryon_concierge/planner.py` | LookSpec -> ordered list of YouCamTask |
| `src/tryon_concierge/youcam.py` | YouCamProvider protocol, FakeYouCamProvider, RealYouCamProvider |
| `src/tryon_concierge/observability.py` | per-call latency + unit cost rollup |
| `src/tryon_concierge/gallery.py` | side-by-side gallery composer (Pillow only) |
| `src/tryon_concierge/concierge.py` | facade `Concierge.run(selfie, request) -> ConciergeRun` |
| `src/tryon_concierge/rates.json` | versioned unit cost table |
| `app.py` | Gradio UI |
| `examples/run_demo.py` | end-to-end run with no credentials |

## Live mode (real Perfect Corp YouCam API)

1. Get a hackathon credit code from Perfect Corp (1000 free units).
2. `export YOUCAM_API_KEY="..."` and optionally `YOUCAM_BASE_URL`.
3. Swap the provider in `app.py` or your script:

```python
from tryon_concierge import Concierge, IntentParser, FakeLLM, RealYouCamProvider

concierge = Concierge(
    intent_llm=IntentParser(FakeLLM()),
    youcam_provider=RealYouCamProvider(),
)
```

See [DEPLOY.md](DEPLOY.md) for the full wiring, env var list, and per-API
request shapes.

## Tests

```bash
.venv/bin/pytest -q
```

20+ unit tests cover intent parsing, planner ordering, the fake provider,
gallery composition, observability rollup, and the full concierge pipeline.

## License

MIT. See [LICENSE](LICENSE).
