"""Per-call latency + cost rollup.

Costs are looked up in ``rates.json``; unknown api names fall back to
``fallback_unit_cost`` so a new API does not break the report. The
rollup is intentionally tiny: the goal is to surface the same numbers a
production observability dashboard would (calls, units, latency p50/p95)
without pulling in heavyweight deps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping
import json


_DEFAULT_RATES_PATH = Path(__file__).parent / "rates.json"


def load_rates(path: str | Path | None = None) -> dict[str, Any]:
    """Read ``rates.json`` from the package or an override path."""

    p = Path(path) if path else _DEFAULT_RATES_PATH
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


@dataclass(frozen=True)
class CallRecord:
    """One YouCam API call as observed by the concierge."""

    api_name: str
    latency_ms: float
    units: int
    confidence: float
    ok: bool = True
    error: str | None = None


@dataclass
class Observability:
    """Collector + summarizer."""

    rates: Mapping[str, Any] = field(default_factory=load_rates)
    records: list[CallRecord] = field(default_factory=list)

    @property
    def fallback_unit_cost(self) -> int:
        meta = self.rates.get("_meta", {}) if isinstance(self.rates, Mapping) else {}
        try:
            return int(meta.get("fallback_unit_cost", 1))
        except (TypeError, ValueError):
            return 1

    def unit_cost(self, api_name: str) -> int:
        value = self.rates.get(api_name) if isinstance(self.rates, Mapping) else None
        if isinstance(value, (int, float)):
            return int(value)
        return self.fallback_unit_cost

    def record(
        self,
        api_name: str,
        latency_ms: float,
        confidence: float = 1.0,
        ok: bool = True,
        error: str | None = None,
    ) -> CallRecord:
        units = self.unit_cost(api_name) if ok else 0
        rec = CallRecord(
            api_name=api_name,
            latency_ms=float(latency_ms),
            units=units,
            confidence=float(confidence),
            ok=ok,
            error=error,
        )
        self.records.append(rec)
        return rec

    def summary(self) -> dict[str, Any]:
        latencies = [r.latency_ms for r in self.records]
        units = sum(r.units for r in self.records)
        ok_calls = sum(1 for r in self.records if r.ok)
        return {
            "total_calls": len(self.records),
            "ok_calls": ok_calls,
            "failed_calls": len(self.records) - ok_calls,
            "total_units": units,
            "p50_latency_ms": _percentile(latencies, 50.0),
            "p95_latency_ms": _percentile(latencies, 95.0),
            "by_api": _by_api(self.records),
        }

    def as_table_rows(self) -> list[list[Any]]:
        """Return rows suitable for a Gradio dataframe.

        Columns: api, status, latency_ms, units, confidence.
        """

        rows: list[list[Any]] = []
        for r in self.records:
            rows.append(
                [
                    r.api_name,
                    "ok" if r.ok else f"error: {r.error or 'unknown'}",
                    round(r.latency_ms, 2),
                    r.units,
                    round(r.confidence, 2),
                ]
            )
        return rows


def _percentile(values: Iterable[float], pct: float) -> float:
    sorted_values = sorted(float(v) for v in values)
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * (pct / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = k - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def _by_api(records: list[CallRecord]) -> dict[str, dict[str, Any]]:
    by: dict[str, dict[str, Any]] = {}
    for r in records:
        slot = by.setdefault(
            r.api_name,
            {"calls": 0, "units": 0, "total_latency_ms": 0.0, "ok": 0, "failed": 0},
        )
        slot["calls"] += 1
        slot["units"] += r.units
        slot["total_latency_ms"] += r.latency_ms
        if r.ok:
            slot["ok"] += 1
        else:
            slot["failed"] += 1
    for name, slot in by.items():
        calls = slot["calls"] or 1
        slot["avg_latency_ms"] = round(slot["total_latency_ms"] / calls, 2)
    return by
