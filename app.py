"""Gradio UI for the tryon_concierge.

Run:
    python app.py
    python app.py --share=false
    python app.py --port 7860
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import gradio as gr  # noqa: E402

from tryon_concierge import Concierge, FakeLLM, FakeYouCamProvider, IntentParser  # noqa: E402


_CONCIERGE = Concierge(
    intent_llm=IntentParser(FakeLLM()),
    youcam_provider=FakeYouCamProvider(),
    out_dir=REPO_ROOT / "out",
)


def _pil_to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


def _bytes_to_pil(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGB")


def run(selfie: Image.Image | None, request: str):
    if selfie is None:
        raise gr.Error("Upload a selfie first.")
    if not request or not request.strip():
        raise gr.Error("Type a style request, for example: warm wedding guest look, olive skin.")

    image_bytes = _pil_to_bytes(selfie)
    result = _CONCIERGE.run_bytes(image_bytes, request)

    gallery_panels = [(_bytes_to_pil(b), label) for label, b in result.panels]
    summary = result.observability
    summary_md = (
        f"**Plan:** {' -> '.join(t.api_name for t in result.tasks)}\n\n"
        f"**Calls:** {summary['total_calls']} "
        f"(ok={summary['ok_calls']}, failed={summary['failed_calls']})\n\n"
        f"**Total units:** {summary['total_units']}\n\n"
        f"**Latency p50/p95 (ms):** "
        f"{summary['p50_latency_ms']:.1f} / {summary['p95_latency_ms']:.1f}\n\n"
        f"**Why this look:** {result.explanation}"
    )
    return gallery_panels, result.call_table, summary_md


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="PerfectCorp Try-On Concierge") as demo:
        gr.Markdown(
            "## PerfectCorp Try-On Concierge\n"
            "Upload a selfie, describe the look in plain language, and the agent will plan "
            "skin analysis, makeup, and hairstyle calls against the Perfect Corp YouCam API "
            "(fake provider by default for the demo)."
        )
        with gr.Row():
            with gr.Column(scale=1):
                selfie = gr.Image(label="Selfie", type="pil", sources=["upload", "webcam"])
                request = gr.Textbox(
                    label="Style request",
                    placeholder="warm wedding guest look, olive skin, statement earrings",
                    lines=2,
                )
                run_btn = gr.Button("Run try-on", variant="primary")
            with gr.Column(scale=2):
                gallery = gr.Gallery(label="Before / intermediate / after", columns=4, height=380)
                table = gr.Dataframe(
                    headers=["api", "status", "latency_ms", "units", "confidence"],
                    label="YouCam call observability",
                    wrap=True,
                )
                summary = gr.Markdown()

        run_btn.click(fn=run, inputs=[selfie, request], outputs=[gallery, table, summary])

        gr.Markdown(
            "<sub>Demo uses the offline `FakeYouCamProvider`. "
            "Set `YOUCAM_API_KEY` and swap in `RealYouCamProvider` for live calls. "
            "See DEPLOY.md for the wiring.</sub>"
        )
    return demo


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", default=False, type=lambda v: str(v).lower() in ("true", "1", "yes"))
    parser.add_argument("--inbrowser", default=False, type=lambda v: str(v).lower() in ("true", "1", "yes"))
    args = parser.parse_args()

    demo = build_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=args.port,
        share=args.share,
        inbrowser=args.inbrowser,
        prevent_thread_lock=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
