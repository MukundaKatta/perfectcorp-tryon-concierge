# DEPLOY

How to flip the demo from the offline `FakeYouCamProvider` to the live
Perfect Corp YouCam API.

## 1. Get a hackathon credit code

Perfect Corp gives hackathon participants a code that unlocks **1000 free
units** against the YouCam APIs.

1. Register at the YouCam Developer Console: https://yce.perfectcorp.com/
2. Apply the hackathon code from the DevNetwork [AI+ML] 2026 Perfect Corp
   track to your workspace.
3. Provision an API key in the console. The key is a bearer token.

## 2. Environment variables

```bash
export YOUCAM_API_KEY="pcorp_..."         # required
export YOUCAM_BASE_URL="https://yce-api-01.perfectcorp.com"  # optional, defaults to this
```

If you also want a real LLM for intent parsing (the demo defaults to
`FakeLLM` for deterministic offline runs):

```bash
export OPENAI_API_KEY="sk-..."            # any OpenAI-compatible endpoint
export OPENAI_BASE_URL="https://api.openai.com/v1"  # optional
```

## 3. Swap the provider in code

In `app.py` or your own script:

```python
from tryon_concierge import (
    Concierge,
    IntentParser,
    FakeLLM,
    OpenAILLM,
    RealYouCamProvider,
)

concierge = Concierge(
    intent_llm=IntentParser(OpenAILLM(model="gpt-4o-mini")),  # or FakeLLM()
    youcam_provider=RealYouCamProvider(),                     # reads env vars
)

run = concierge.run("path/to/selfie.png", "warm wedding guest look, olive skin")
print(run.observability)
print(run.gallery_path)
```

## 4. Per-API request shapes

The `RealYouCamProvider` ships with a generic multipart POST helper:

```
POST {YOUCAM_BASE_URL}/{path}
Authorization: Bearer {YOUCAM_API_KEY}
Content-Type: multipart/form-data
fields: <task params>
files: image=<png bytes>
```

The default path mapping is:

| api_name              | POST path             |
| --------------------- | --------------------- |
| `skin_analysis`       | `/skin-analysis`      |
| `ai_makeup_transfer`  | `/ai-makeup-transfer` |
| `ai_hairstyle`        | `/ai-hairstyle`       |
| `earrings_tryon`      | `/earrings-tryon`     |
| `<other>`             | `/<dashed-name>`      |

The response is auto-detected:

* If the response `Content-Type` starts with `image/`, the bytes are used
  directly.
* Otherwise the body is parsed as JSON, and the keys `image` or
  `result_image` are decoded from base64.

When Perfect Corp publishes a different request shape for a specific API
(for example a two-step "submit + poll" flow for hairstyle generation),
extend the matching method in `src/tryon_concierge/youcam.py` and keep the
`YouCamCallResult` shape stable.

## 5. Unit costs

`src/tryon_concierge/rates.json` holds the unit-cost-per-call estimate. The
shape is:

```json
{
  "_meta": {"version": "2026-05-24", "fallback_unit_cost": 1},
  "skin_analysis": 1,
  "ai_makeup_transfer": 2,
  "ai_hairstyle": 3,
  ...
}
```

Bump the version string and update the per-API integers when Perfect Corp
publishes their official rate card. The `Observability.unit_cost` lookup
falls back to `_meta.fallback_unit_cost` for any API not in the table, so
adding new APIs never crashes the report.

## 6. Quick smoke test (real provider)

```bash
.venv/bin/python - <<'PY'
import os
from tryon_concierge import Concierge, FakeLLM, IntentParser, RealYouCamProvider

assert os.environ.get("YOUCAM_API_KEY"), "set YOUCAM_API_KEY first"

c = Concierge(IntentParser(FakeLLM()), RealYouCamProvider())
run = c.run("tests/fixtures/face_warm.png", "office polish")
print(run.observability)
print("gallery:", run.gallery_path)
PY
```

## 7. Hosting the Gradio app

```bash
.venv/bin/python app.py --port 7860            # local
.venv/bin/python app.py --share=true           # temporary public link via gradio.live
```

For a permanent deployment, the Gradio app fits cleanly on:

* HuggingFace Spaces (Python SDK, `pip install -e .`).
* Fly.io (small VM, port 7860).
* Any container host (the package is dep-light: `pip install -e .`).

Set `YOUCAM_API_KEY` as a secret on the host before promoting to the live
provider.
