# 3-minute demo script

This is the script for the Devpost video. The whole thing should fit in
**three minutes**, with crisp on-screen captions, no music over voice, and
no slides. The agent is the demo.

| Time      | What is on screen                              | Voiceover |
| --------- | ---------------------------------------------- | --------- |
| 00:00 - 00:15 | Title card: "PerfectCorp Try-On Concierge". Brief logo strip (Perfect Corp + DevNetwork). | "Perfect Corp's YouCam platform has 26 powerful try-on APIs. The problem: real shoppers do not think in API names. They think in occasions. This is the Concierge that closes that gap." |
| 00:15 - 00:30 | Terminal: `pytest -q` runs and shows the test count + pass line. | "Quick proof of life: 20+ tests, all green against the offline provider. No credentials needed to reproduce." |
| 00:30 - 00:55 | Browser opens to `http://127.0.0.1:7860`. Upload a selfie from the fixtures folder. | "The whole UI is one screen. Drop a selfie in. Type one sentence." |
| 00:55 - 01:25 | Type: `warm wedding guest look, olive skin, statement earrings`. Click Run. Gallery appears. | "The agent parses the request into a structured LookSpec, plans the YouCam calls, and stitches the before, intermediate, and final panels into one strip." |
| 01:25 - 01:55 | Camera pans across the gallery: original, skin analysis, makeup, hair, earrings, composite. Highlight each label. | "Every panel is labelled with which YouCam API produced it. Skin analysis, makeup transfer, hairstyle, jewelry, composite. You can see exactly what the agent did." |
| 01:55 - 02:15 | Scroll to the observability dataframe. Highlight units + latency p50/p95. | "Below the gallery: a per-call observability table. Latency, units, confidence. This is how a brand sees what 1,000 free units actually buys them." |
| 02:15 - 02:35 | Show the "why this look" paragraph below the table. | "And a one-paragraph explanation that cites the skin analysis output: undertone and moisture. The recommendation is grounded in the user's image, not a generic preset." |
| 02:35 - 02:50 | Briefly show DEPLOY.md in an editor: `export YOUCAM_API_KEY` + the provider swap snippet. | "Live mode is one env var and one provider swap. The real adapter is already wired; the fake one is just there so the demo runs without keys." |
| 02:50 - 03:00 | Title card again with the repo URL: `github.com/MukundaKatta/perfectcorp-tryon-concierge`. | "MIT licensed, 20+ tests, deterministic offline path, real adapter ready. Thanks for watching." |

## Pre-flight checklist (before hitting record)

* Clean shell: `cd ~/perfectcorp-tryon-concierge && rm -rf out/ flagged/`.
* Activate venv: `source .venv/bin/activate`.
* Test selfie ready in `tests/fixtures/face_warm.png` (auto-generated on
  first pytest or example run).
* Browser zoom at 110% so the gallery panels read on a 1080p capture.
* Terminal font at least 16pt.

## One-take commands

```bash
.venv/bin/pytest -q
.venv/bin/python examples/run_demo.py
.venv/bin/python app.py
```
