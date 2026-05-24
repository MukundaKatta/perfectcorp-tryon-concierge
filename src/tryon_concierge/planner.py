"""Translate a ``LookSpec`` into an ordered list of ``YouCamTask`` calls.

The planner intentionally produces a deterministic ordering:

1. ``skin_analysis`` always runs first so downstream calls can use the
   detected undertone and skin condition.
2. ``ai_makeup_transfer`` runs next; the look name is derived from
   occasion + intensity so we get a stable, cache-friendly key.
3. ``ai_hairstyle`` runs only if ``hair_change_ok`` is set.
4. ``earrings_tryon`` runs only if ``jewelry_ok`` is set.
5. ``composite`` is always the final step; the concierge consumes this
   as the signal to stitch the gallery together.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .intent import LookSpec


@dataclass(frozen=True)
class YouCamTask:
    """One YouCam API call the planner wants the concierge to execute."""

    api_name: str
    params: dict[str, Any] = field(default_factory=dict)


_MAKEUP_LOOKS: dict[tuple[str, str], str] = {
    ("wedding_guest", "subtle"): "soft_romantic",
    ("wedding_guest", "natural"): "warm_romantic",
    ("wedding_guest", "bold"): "glam_romantic",
    ("office", "subtle"): "clean_office",
    ("office", "natural"): "office_polish",
    ("office", "bold"): "boardroom_power",
    ("date_night", "subtle"): "soft_date",
    ("date_night", "natural"): "warm_date",
    ("date_night", "bold"): "smokey_date",
    ("festival", "subtle"): "festival_dewy",
    ("festival", "natural"): "festival_glow",
    ("festival", "bold"): "festival_statement",
    ("interview", "subtle"): "interview_clean",
    ("interview", "natural"): "interview_polish",
    ("interview", "bold"): "interview_bold",
    ("brunch", "subtle"): "brunch_fresh",
    ("brunch", "natural"): "brunch_glow",
    ("brunch", "bold"): "brunch_bold",
    ("red_carpet", "subtle"): "carpet_soft",
    ("red_carpet", "natural"): "carpet_glow",
    ("red_carpet", "bold"): "carpet_statement",
    ("everyday", "subtle"): "everyday_bare",
    ("everyday", "natural"): "everyday_glow",
    ("everyday", "bold"): "everyday_bold",
}


_HAIR_PRESETS: dict[str, str] = {
    "wedding_guest": "soft_waves",
    "office": "sleek_low_bun",
    "date_night": "loose_waves",
    "festival": "boho_braids",
    "interview": "tucked_blunt",
    "brunch": "messy_lob",
    "red_carpet": "old_hollywood_waves",
    "everyday": "natural_blowout",
}


def _makeup_look_for(spec: LookSpec) -> str:
    return _MAKEUP_LOOKS.get((spec.occasion, spec.intensity), "everyday_glow")


def _hair_preset_for(spec: LookSpec) -> str:
    return _HAIR_PRESETS.get(spec.occasion, "natural_blowout")


def plan_tasks(spec: LookSpec) -> list[YouCamTask]:
    """Return the ordered task list for a ``LookSpec``."""

    tasks: list[YouCamTask] = []
    tasks.append(
        YouCamTask(
            api_name="skin_analysis",
            params={"undertone_hint": spec.undertone},
        )
    )
    tasks.append(
        YouCamTask(
            api_name="ai_makeup_transfer",
            params={
                "look": _makeup_look_for(spec),
                "undertone": spec.undertone,
                "intensity": spec.intensity,
            },
        )
    )
    if spec.hair_change_ok:
        tasks.append(
            YouCamTask(
                api_name="ai_hairstyle",
                params={
                    "style": _hair_preset_for(spec),
                    "occasion": spec.occasion,
                },
            )
        )
    if spec.jewelry_ok:
        tasks.append(
            YouCamTask(
                api_name="earrings_tryon",
                params={"style_family": spec.occasion},
            )
        )
    tasks.append(YouCamTask(api_name="composite", params={}))
    return tasks
