from tryon_concierge.intent import (
    FakeLLM,
    IntentParser,
    LookSpec,
    _coerce_json,
)


def test_fake_llm_wedding_warm_subtle() -> None:
    parser = IntentParser(FakeLLM())
    spec = parser.parse("warm wedding guest look, subtle, olive skin")
    assert isinstance(spec, LookSpec)
    assert spec.occasion == "wedding_guest"
    assert spec.undertone == "olive"
    assert spec.intensity == "subtle"
    assert spec.hair_change_ok is True
    assert spec.jewelry_ok is False


def test_fake_llm_bold_date_night_with_jewelry() -> None:
    parser = IntentParser(FakeLLM())
    spec = parser.parse("bold smokey date night look with statement earrings")
    assert spec.occasion == "date_night"
    assert spec.intensity == "bold"
    assert spec.jewelry_ok is True


def test_fake_llm_keep_hair_flag() -> None:
    parser = IntentParser(FakeLLM())
    spec = parser.parse("everyday glow, keep my hair as is")
    assert spec.hair_change_ok is False


def test_intent_parser_handles_extra_chatter_around_json() -> None:
    class Wrapped:
        def complete(self, prompt: str) -> str:  # noqa: ARG002
            return (
                "Sure thing! Here is the JSON: ```json\n"
                "{\"occasion\": \"office\", \"undertone\": \"cool\", "
                "\"intensity\": \"natural\", \"hair_change_ok\": false, "
                "\"jewelry_ok\": false}\n"
                "```\nAsk if you want more."
            )

    parser = IntentParser(Wrapped())
    spec = parser.parse("polished office look")
    assert spec.occasion == "office"
    assert spec.undertone == "cool"
    assert spec.hair_change_ok is False


def test_intent_parser_falls_back_to_safe_defaults_when_unknown_values() -> None:
    class Garbage:
        def complete(self, prompt: str) -> str:  # noqa: ARG002
            return "{\"occasion\": \"moon_landing\", \"undertone\": \"banana\", \"intensity\": \"loud\"}"

    parser = IntentParser(Garbage())
    spec = parser.parse("???")
    assert spec.occasion == "everyday"
    assert spec.undertone == "neutral"
    assert spec.intensity == "natural"


def test_coerce_json_returns_empty_dict_on_garbage() -> None:
    assert _coerce_json("not json at all") == {}
    assert _coerce_json("") == {}


def test_lookspec_to_dict_roundtrip() -> None:
    spec = LookSpec(
        occasion="brunch",
        undertone="warm",
        intensity="natural",
        hair_change_ok=True,
        jewelry_ok=False,
    )
    d = spec.to_dict()
    assert d["occasion"] == "brunch"
    assert d["hair_change_ok"] is True
