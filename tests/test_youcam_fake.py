from pathlib import Path

from tryon_concierge.youcam import FakeYouCamProvider, YouCamCallResult

FIXTURE = Path(__file__).parent / "fixtures" / "face_warm.png"


def test_fake_skin_analysis_returns_structured_data() -> None:
    provider = FakeYouCamProvider()
    res = provider.analyze_skin(FIXTURE.read_bytes())
    assert isinstance(res, YouCamCallResult)
    assert res.api_name == "skin_analysis"
    assert res.image_bytes is not None and len(res.image_bytes) > 0
    for key in ("moisture", "clarity", "firmness", "undertone"):
        assert key in res.data


def test_fake_apply_makeup_produces_image() -> None:
    provider = FakeYouCamProvider()
    res = provider.apply_makeup(FIXTURE.read_bytes(), look="warm_romantic", undertone="warm")
    assert res.api_name == "ai_makeup_transfer"
    assert res.image_bytes is not None and len(res.image_bytes) > 0
    assert res.data["look"] == "warm_romantic"
    assert res.data["undertone"] == "warm"


def test_fake_change_hairstyle_produces_image() -> None:
    provider = FakeYouCamProvider()
    res = provider.change_hairstyle(FIXTURE.read_bytes(), style="soft_waves")
    assert res.api_name == "ai_hairstyle"
    assert res.image_bytes is not None and len(res.image_bytes) > 0
    assert res.data["style"] == "soft_waves"


def test_fake_call_dispatches_by_api_name() -> None:
    provider = FakeYouCamProvider()
    image = FIXTURE.read_bytes()
    skin = provider.call("skin_analysis", image, {})
    makeup = provider.call("ai_makeup_transfer", image, {"look": "everyday_glow"})
    hair = provider.call("ai_hairstyle", image, {"style": "loose_waves"})
    assert skin.api_name == "skin_analysis"
    assert makeup.api_name == "ai_makeup_transfer"
    assert hair.api_name == "ai_hairstyle"


def test_fake_call_unknown_api_passthrough() -> None:
    provider = FakeYouCamProvider()
    res = provider.call("brand_new_api", FIXTURE.read_bytes(), {"foo": "bar"})
    assert res.api_name == "brand_new_api"
    assert res.image_bytes is not None
    assert res.confidence < 1.0


def test_fake_skin_results_are_deterministic_for_same_input() -> None:
    provider = FakeYouCamProvider()
    a = provider.analyze_skin(FIXTURE.read_bytes())
    b = provider.analyze_skin(FIXTURE.read_bytes())
    assert a.data == b.data
