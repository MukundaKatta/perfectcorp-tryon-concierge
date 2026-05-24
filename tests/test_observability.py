from tryon_concierge.observability import CallRecord, Observability, _percentile, load_rates


def test_load_rates_returns_known_keys() -> None:
    rates = load_rates()
    assert "skin_analysis" in rates
    assert "ai_makeup_transfer" in rates
    assert isinstance(rates["_meta"], dict)


def test_unit_cost_uses_rates_when_known() -> None:
    obs = Observability()
    assert obs.unit_cost("skin_analysis") >= 1
    assert obs.unit_cost("ai_makeup_transfer") >= 1


def test_unit_cost_falls_back_when_unknown() -> None:
    obs = Observability()
    assert obs.unit_cost("totally_new_api") == obs.fallback_unit_cost


def test_record_and_summary_basic_math() -> None:
    obs = Observability()
    obs.record("skin_analysis", latency_ms=10.0, confidence=0.9)
    obs.record("ai_makeup_transfer", latency_ms=20.0, confidence=0.8)
    obs.record("ai_hairstyle", latency_ms=30.0, confidence=0.7)
    summary = obs.summary()
    assert summary["total_calls"] == 3
    assert summary["ok_calls"] == 3
    assert summary["failed_calls"] == 0
    assert summary["total_units"] >= 3
    assert summary["p50_latency_ms"] == 20.0
    assert summary["p95_latency_ms"] >= 28.0


def test_failed_call_charges_zero_units() -> None:
    obs = Observability()
    obs.record("ai_makeup_transfer", latency_ms=5.0, confidence=0.0, ok=False, error="boom")
    assert obs.records[0].units == 0
    summary = obs.summary()
    assert summary["failed_calls"] == 1


def test_as_table_rows_shape() -> None:
    obs = Observability()
    obs.record("skin_analysis", latency_ms=10.0, confidence=0.9)
    rows = obs.as_table_rows()
    assert len(rows) == 1
    assert rows[0][0] == "skin_analysis"
    assert rows[0][1] == "ok"
    assert rows[0][3] >= 1


def test_percentile_helper_handles_edges() -> None:
    assert _percentile([], 50.0) == 0.0
    assert _percentile([7.0], 95.0) == 7.0
    assert _percentile([1.0, 2.0, 3.0, 4.0], 50.0) == 2.5
