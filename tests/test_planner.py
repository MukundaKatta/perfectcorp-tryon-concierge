from tryon_concierge.intent import LookSpec
from tryon_concierge.planner import YouCamTask, plan_tasks


def _spec(**overrides: object) -> LookSpec:
    base = dict(
        occasion="wedding_guest",
        undertone="warm",
        intensity="natural",
        hair_change_ok=True,
        jewelry_ok=False,
    )
    base.update(overrides)
    return LookSpec(**base)  # type: ignore[arg-type]


def test_plan_starts_with_skin_analysis_and_ends_with_composite() -> None:
    plan = plan_tasks(_spec())
    assert plan[0].api_name == "skin_analysis"
    assert plan[-1].api_name == "composite"


def test_plan_includes_hair_when_allowed() -> None:
    plan = plan_tasks(_spec(hair_change_ok=True))
    names = [t.api_name for t in plan]
    assert "ai_hairstyle" in names


def test_plan_skips_hair_when_disallowed() -> None:
    plan = plan_tasks(_spec(hair_change_ok=False))
    names = [t.api_name for t in plan]
    assert "ai_hairstyle" not in names


def test_plan_includes_earrings_when_jewelry_ok() -> None:
    plan = plan_tasks(_spec(jewelry_ok=True))
    names = [t.api_name for t in plan]
    assert "earrings_tryon" in names


def test_plan_makeup_look_varies_with_occasion_and_intensity() -> None:
    bold_carpet = plan_tasks(_spec(occasion="red_carpet", intensity="bold"))
    soft_office = plan_tasks(_spec(occasion="office", intensity="subtle"))
    look_bold = next(t for t in bold_carpet if t.api_name == "ai_makeup_transfer").params["look"]
    look_soft = next(t for t in soft_office if t.api_name == "ai_makeup_transfer").params["look"]
    assert look_bold == "carpet_statement"
    assert look_soft == "clean_office"


def test_plan_task_params_carry_undertone() -> None:
    plan = plan_tasks(_spec(undertone="olive"))
    makeup = next(t for t in plan if t.api_name == "ai_makeup_transfer")
    assert makeup.params["undertone"] == "olive"


def test_youcam_task_is_immutable_dataclass() -> None:
    t = YouCamTask(api_name="skin_analysis", params={"undertone_hint": "warm"})
    assert t.api_name == "skin_analysis"
    assert t.params["undertone_hint"] == "warm"
