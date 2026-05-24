# DevNetwork [AI+ML] Hackathon 2026, Perfect Corp track

**Project:** PerfectCorp Try-On Concierge
**Track:** Perfect Corp, "AI-Driven Consumer Experiences" ($2,500 prize)
**Repo:** https://github.com/MukundaKatta/perfectcorp-tryon-concierge
**License:** MIT

## Problem

The Perfect Corp YouCam platform exposes 26+ powerful APIs (skin analysis,
makeup transfer, hairstyle generator, hair color, face swap, jewelry try-on,
image enhance, and more). The capability is incredible, but the consumer-facing
surface still asks shoppers to pick the right combination of APIs themselves.

Real users do not think in API names. They think in occasions: "warm wedding
guest look, olive skin", "polished office", "bold date night with statement
earrings". They want one button, one preview, and one short explanation of
what was applied and why.

## Approach

`tryon_concierge` is a small Python package + Gradio UI that puts an AI agent
in front of the YouCam APIs. The agent:

1. **Reads the user's request in plain language** through a single LLM call
   that returns a strict JSON `LookSpec(occasion, undertone, intensity,
   hair_change_ok, jewelry_ok)`. A deterministic `FakeLLM` is wired by
   default so the demo works without an OpenAI key; `OpenAILLM` is a drop-in
   replacement.
2. **Plans the YouCam calls.** A deterministic planner emits an ordered list:
   `skin_analysis -> ai_makeup_transfer -> ai_hairstyle? -> earrings_tryon?
   -> composite`. Hair and jewelry steps are conditional on the parsed
   `LookSpec`.
3. **Executes against YouCam.** A `YouCamProvider` protocol has two
   implementations: `FakeYouCamProvider` (offline, deterministic, labelled
   placeholder images) and `RealYouCamProvider` (multipart POST to
   `YOUCAM_BASE_URL` with `YOUCAM_API_KEY`).
4. **Observes every call.** Per-call latency, unit cost (from a versioned
   `rates.json`), and confidence are aggregated into a small report
   (total calls, total units, p50/p95 latency, breakdown by API).
5. **Returns a side-by-side gallery** plus a one-paragraph "why this look"
   explanation grounded in the skin analysis output.

The whole pipeline is wrapped behind one facade: `Concierge.run(selfie, request)
-> ConciergeRun`. Tests, the example script, and the Gradio UI all call the
same method.

## Demo

* **Offline demo (no credentials):** `python examples/run_demo.py`
  Prints the plan, the per-call observability table, and writes
  `out/gallery.png`.
* **Gradio UI:** `python app.py` then upload a selfie and type a request.
  The UI shows the gallery and a live observability dataframe.
* **Tests:** `pytest -q` runs 20+ unit tests against the fake provider.
* **Live mode:** swap `FakeYouCamProvider` for `RealYouCamProvider`. See
  `DEPLOY.md` for the env vars and the request body shape per YouCam API.

## Why this fits the Perfect Corp "AI-Driven Consumer Experiences" criteria

* **Consumer-friendly surface.** One image upload, one sentence, one preview.
  No API picker, no parameter sliders.
* **Uses multiple YouCam APIs in one flow.** Skin analysis, makeup transfer,
  hairstyle, and jewelry are composed end-to-end, with the makeup and hair
  presets keyed off the parsed occasion.
* **Grounded recommendation.** The "why this look" paragraph cites the
  skin analysis output (undertone, moisture) so the user sees that the
  recommendation is informed by their own image, not a generic preset.
* **Honest observability.** Every call surfaces its latency and unit cost,
  so a brand integrating this pattern can see exactly what 1,000 free units
  buys them and where to cache.
* **Production-shaped code.** Provider protocol, structured plans, MIT
  license, 20+ tests, dependency-light (gradio + pillow + requests only).
  Real provider wired and documented, ready to flip on with a key.
* **Hackathon-ready.** The fake provider lets judges reproduce the full
  experience without provisioning a key, while the real adapter shows the
  team understands the production wire format.

## Tech stack

* Python 3.10+, Pillow for image composition, Gradio for the UI, Requests
  for HTTP, pytest for tests. No other runtime deps.
* Code organized under `src/tryon_concierge/` so the package can be reused
  outside the Gradio app.

## What's next

* Add a caching layer keyed off `(api_name, params_hash, image_hash)` so
  repeat try-ons hit zero new units.
* Wire the OpenAI adapter into the Gradio UI as an opt-in via env var.
* Add a per-call retry policy with exponential backoff for the real provider.
* Ship a small product gallery: pre-populated celebrity-inspired looks the
  Concierge can copy onto the user's selfie.

## Author

Mukunda Katta, mukunda.vjcs6@gmail.com, https://github.com/MukundaKatta
