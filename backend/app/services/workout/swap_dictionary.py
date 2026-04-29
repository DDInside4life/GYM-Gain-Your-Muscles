"""Injury-safe exercise substitutions.

Keys are (movement_archetype, injury_keyword) tuples; values are ordered
lists of substitute archetypes (first = most preferred).

The generator calls ``suggest_swaps(exercise, injuries)`` before falling back
to a random filtered pick; this gives clinically safer choices for common
injury patterns.

Six injury categories covered per the requirement:
  knees, back, shoulder, elbow, varicose_veins, hypertension
"""
from __future__ import annotations

from typing import Final

SWAPS: Final[dict[tuple[str, str], list[str]]] = {
    # ---- Knees ----
    ("squat", "knee"): ["leg_press", "goblet_squat", "step_up", "leg_extension"],
    ("lunge", "knee"): ["leg_press", "step_up", "seated_leg_curl"],
    ("leg_press", "knee"): ["seated_leg_curl", "hip_thrust", "glute_bridge"],
    # ---- Lower back / spine ----
    ("deadlift", "back"): ["hip_thrust", "cable_pull_through", "glute_bridge", "back_extension"],
    ("bent_over_row", "back"): ["seated_cable_row", "chest_supported_row", "lat_pulldown"],
    ("squat", "back"): ["leg_press", "goblet_squat", "hack_squat"],
    ("good_morning", "back"): ["hip_thrust", "glute_bridge"],
    # ---- Shoulders ----
    ("overhead_press", "shoulder"): ["landmine_press", "lateral_raise", "cable_lateral_raise"],
    ("upright_row", "shoulder"): ["face_pull", "band_pull_apart", "lateral_raise"],
    ("bench_press", "shoulder"): ["db_floor_press", "cable_crossover", "machine_chest_press"],
    ("dip", "shoulder"): ["machine_chest_press", "cable_crossover", "db_floor_press"],
    # ---- Elbows ----
    ("barbell_curl", "elbow"): ["hammer_curl", "cable_curl", "reverse_curl"],
    ("skull_crusher", "elbow"): ["cable_pushdown", "overhead_tricep_cable", "band_pushdown"],
    ("close_grip_bench", "elbow"): ["cable_pushdown", "machine_tricep_press"],
    # ---- Varicose veins (avoid prolonged standing under load) ----
    ("barbell_squat", "varicose"): ["leg_press", "hack_squat", "leg_extension"],
    ("standing_calf_raise", "varicose"): ["seated_calf_raise"],
    ("deadlift", "varicose"): ["seated_leg_curl", "hip_thrust", "glute_bridge"],
    # ---- Hypertension (avoid isometric heavy grips & Valsalva) ----
    ("heavy_deadlift", "hypertension"): ["hip_thrust", "glute_bridge", "cable_pull_through"],
    ("heavy_squat", "hypertension"): ["leg_press", "hack_squat"],
    ("overhead_press", "hypertension"): ["lateral_raise", "cable_lateral_raise", "face_pull"],
}

_INJURY_KEYWORDS: Final[dict[str, list[str]]] = {
    "knee":        ["knee", "колено", "колени", "коленях"],
    "back":        ["back", "спина", "спину", "поясниц", "lumbar", "позвоноч"],
    "shoulder":    ["shoulder", "плечо", "плеча", "плечи", "rotator"],
    "elbow":       ["elbow", "локоть", "локтя", "локти", "tendinitis"],
    "varicose":    ["varicose", "варикоз", "вена", "вены", "veins"],
    "hypertension":["hypertension", "гипертони", "давлени", "артериальн"],
}


def _canonical_injury(injury: str) -> str | None:
    lower = injury.lower()
    for canonical, keywords in _INJURY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return canonical
    return None


def suggest_swaps(archetype: str, injuries: list[str]) -> list[str]:
    """Return ordered list of substitute archetypes for a given exercise archetype and injury list.

    Returns an empty list if no known swap exists.
    """
    canonical_injuries = {_canonical_injury(inj) for inj in injuries} - {None}
    candidates: list[str] = []
    for inj in canonical_injuries:
        key = (archetype, inj)  # type: ignore[arg-type]
        candidates.extend(SWAPS.get(key, []))
    seen: set[str] = set()
    deduped: list[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            deduped.append(c)
    return deduped
