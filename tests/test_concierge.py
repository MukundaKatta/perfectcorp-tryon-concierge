from pathlib import Path

import pytest

from tryon_concierge.concierge import Concierge, ConciergeRun
from tryon_concierge.intent import FakeLLM, IntentParser
from tryon_concierge.youcam import FakeYouCamProvider, YouCamCallResult

FIXTURE = Path(__file__).parent / "fixtures" / "face_warm.png"


def _make(tmp_path: Path) -> Concierge:
    return Concierge(
        intent_llm=IntentParser(FakeLLM()),
        youcam_provider=FakeYouCamProvider(),
        out_dir=tmp_path / "out",
    )


def test_concierge_runs_full_pipeline_offline(tmp_path: Path) -> None:
    concierge = _make(tmp_path)
    run = concierge.run(FIXTURE, "warm wedding guest look, olive skin")
    assert isinstance(run, ConciergeRun)
    assert run.spec.occasion == "wedding_guest"
    assert run.spec.undertone == "olive"
    # Plan covers skin, makeup, hair, composite by default.
    api_names = [t.api_name for t in run.tasks]
    assert api_names[0] == "skin_analysis"
    assert "ai_makeup_transfer" in api_names
    assert api_names[-1] == "composite"
    # Gallery + final image were produced.
    assert run.gallery_path.exists()
    assert len(run.final_image) > 0
    # Skin data made it back into the run.
    assert "undertone" in run.skin


def test_concierge_accepts_raw_llm_or_parser(tmp_path: Path) -> None:
    bare = Concierge(intent_llm=FakeLLM(), youcam_provider=FakeYouCamProvider(), out_dir=tmp_path / "o1")
    wrapped = Concierge(intent_llm=IntentParser(FakeLLM()), youcam_provider=FakeYouCamProvider(), out_dir=tmp_path / "o2")
    r1 = bare.run(FIXTURE, "office polish, cool undertone")
    r2 = wrapped.run(FIXTURE, "office polish, cool undertone")
    assert r1.spec == r2.spec


def test_concierge_skips_hair_panel_when_requested(tmp_path: Path) -> None:
    concierge = _make(tmp_path)
    run = concierge.run(FIXTURE, "everyday glow, keep my hair as is")
    api_names = [t.api_name for t in run.tasks]
    assert "ai_hairstyle" not in api_names
    labels = [p[0] for p in run.panels]
    assert not any("hair" in lbl for lbl in labels)


def test_concierge_records_observability(tmp_path: Path) -> None:
    concierge = _make(tmp_path)
    run = concierge.run(FIXTURE, "warm wedding guest look, olive skin")
    obs = run.observability
    assert obs["total_calls"] >= 3
    assert obs["total_units"] >= 3
    by_api = obs["by_api"]
    assert "skin_analysis" in by_api
    assert "ai_makeup_transfer" in by_api


def test_concierge_explanation_mentions_occasion(tmp_path: Path) -> None:
    concierge = _make(tmp_path)
    run = concierge.run(FIXTURE, "bold date night look, smokey")
    assert "date night" in run.explanation


def test_concierge_missing_selfie_raises(tmp_path: Path) -> None:
    concierge = _make(tmp_path)
    with pytest.raises(FileNotFoundError):
        concierge.run(tmp_path / "does_not_exist.png", "anything")


def test_concierge_survives_provider_failure(tmp_path: Path) -> None:
    class Flaky(FakeYouCamProvider):
        def call(self, api_name: str, image: bytes, params):
            if api_name == "ai_hairstyle":
                raise RuntimeError("simulated upstream 500")
            return super().call(api_name, image, params)

    concierge = Concierge(intent_llm=FakeLLM(), youcam_provider=Flaky(), out_dir=tmp_path / "o")
    run = concierge.run(FIXTURE, "warm wedding guest look")
    failed = [r for r in run.call_table if "error" in str(r[1])]
    assert failed, "expected at least one failed call in the observability table"
    # Pipeline still produced a gallery.
    assert run.gallery_path.exists()


def test_concierge_jewelry_panel_appears_when_requested(tmp_path: Path) -> None:
    concierge = _make(tmp_path)
    run = concierge.run(FIXTURE, "bold red carpet look with statement earrings")
    labels = [p[0] for p in run.panels]
    assert any("earrings" in lbl for lbl in labels)


def test_concierge_call_table_includes_units(tmp_path: Path) -> None:
    concierge = _make(tmp_path)
    run = concierge.run(FIXTURE, "warm wedding guest look")
    units = [row[3] for row in run.call_table]
    assert all(isinstance(u, int) for u in units)
    assert sum(units) >= 3


def test_concierge_youcam_result_type_shape() -> None:
    res = YouCamCallResult(api_name="x", image_bytes=b"abc", data={"k": 1}, confidence=0.5)
    assert res.api_name == "x"
    assert res.image_bytes == b"abc"
    assert res.data == {"k": 1}
    assert res.confidence == 0.5
