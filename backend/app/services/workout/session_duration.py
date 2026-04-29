"""Maps user-chosen session duration to per-day volume caps.

Also exposes ``pack_session`` which trims a day to fit a time budget by:
1. Pairing antagonist muscles as supersets.
2. Cutting isolation set counts.
3. Dropping isolation exercises entirely (never touching compound exercises).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from app.models.user import Experience
from app.services.workout.volume import (
    ABSOLUTE_MAX_EXERCISES_PER_DAY,
    MIN_EXERCISES_PER_DAY,
)


ALLOWED_DURATIONS: Final[tuple[int, ...]] = (45, 60, 90, 120, 150)
DEFAULT_DURATION_MIN: Final[int] = 60


@dataclass(frozen=True, slots=True)
class SessionShape:
    duration_min: int
    max_exercises: int
    accessory_bonus: int
    label: str


_BY_DURATION: Final[dict[int, SessionShape]] = {
    45: SessionShape(45, 4, 0, "Экспресс — 45 мин"),
    60: SessionShape(60, 5, 1, "Стандарт — 60 мин"),
    90: SessionShape(90, 6, 2, "Полный — 90 мин"),
    120: SessionShape(120, 7, 3, "Расширенный — 120 мин"),
    150: SessionShape(150, 7, 4, "Макс — 150 мин"),
}


def normalize_duration(value: int | None) -> int:
    if value is None:
        return DEFAULT_DURATION_MIN
    return min(ALLOWED_DURATIONS, key=lambda candidate: abs(candidate - int(value)))


def session_shape(duration_min: int | None) -> SessionShape:
    return _BY_DURATION[normalize_duration(duration_min)]


def cap_for(duration_min: int | None, experience: Experience, base_cap: int) -> int:
    """Final exercises-per-day cap honoring user duration choice and safety."""
    shape = session_shape(duration_min)
    cap = min(shape.max_exercises, base_cap)
    if experience == Experience.beginner:
        cap = min(cap, base_cap - 1) if base_cap > MIN_EXERCISES_PER_DAY else cap
    return max(MIN_EXERCISES_PER_DAY, min(cap, ABSOLUTE_MAX_EXERCISES_PER_DAY))


# ---------------------------------------------------------------------------
# pack_session — fit a day into a time budget
# ---------------------------------------------------------------------------

WARMUP_MIN: Final[int] = 8
SECS_PER_REP: Final[int] = 3
REST_COMPOUND_SEC: Final[int] = 120
REST_ISOLATION_SEC: Final[int] = 60
SUPERSET_REST_REDUCTION: Final[float] = 0.5

_ANTAGONIST_PAIRS: Final[list[tuple[str, str]]] = [
    ("push", "pull"),
    ("chest", "back"),
    ("quad", "hamstring"),
    ("bicep", "tricep"),
    ("anterior_delt", "posterior_delt"),
]


def _primary_category(exercise_dict: dict) -> str:
    return str(exercise_dict.get("category", "isolation"))


def _muscle_group(exercise_dict: dict) -> str:
    muscles = exercise_dict.get("primary_muscles", [])
    return str(muscles[0]) if muscles else ""


def _are_antagonists(g1: str, g2: str) -> bool:
    for a, b in _ANTAGONIST_PAIRS:
        if (a in g1 and b in g2) or (b in g1 and a in g2):
            return True
    return False


def _rest_sec(is_compound: bool, in_superset: bool) -> float:
    base = REST_COMPOUND_SEC if is_compound else REST_ISOLATION_SEC
    return base * (SUPERSET_REST_REDUCTION if in_superset else 1.0)


@dataclass(slots=True)
class PackedExercise:
    exercise_id: int
    sets: int
    reps_avg: float
    is_compound: bool
    superset_group: int | None = None
    muscle_group: str = ""


@dataclass(slots=True)
class PackResult:
    estimated_min: float
    superset_pairs_added: int
    isolation_sets_cut: int
    isolation_exercises_removed: int
    exercises: list[PackedExercise] = field(default_factory=list)


def _estimate_min(exercises: list[PackedExercise]) -> float:
    total_sec: float = WARMUP_MIN * 60
    for ex in exercises:
        in_superset = ex.superset_group is not None
        rest = _rest_sec(ex.is_compound, in_superset)
        time_per_set = ex.reps_avg * SECS_PER_REP + rest
        total_sec += ex.sets * time_per_set
    return round(total_sec / 60.0, 1)


def pack_session(
    exercises: list[dict],
    limit_min: int,
) -> PackResult:
    """Trim the exercise list to fit ``limit_min``.

    ``exercises`` is a list of plain dicts with keys:
        exercise_id, sets, reps_min, reps_max, category, primary_muscles
    (matching WorkoutExercise fields).

    Returns a ``PackResult`` with the (possibly modified) exercise list and
    a summary of changes applied.

    The input list is NOT mutated; a new list is built internally.
    """
    packed = [
        PackedExercise(
            exercise_id=ex["exercise_id"],
            sets=ex["sets"],
            reps_avg=(ex["reps_min"] + ex["reps_max"]) / 2.0,
            is_compound=_primary_category(ex) in {"compound"},
            superset_group=ex.get("superset_group"),
            muscle_group=_muscle_group(ex),
        )
        for ex in exercises
    ]

    superset_pairs = 0
    isolation_sets_cut = 0
    isolation_removed = 0

    if _estimate_min(packed) <= limit_min:
        return PackResult(_estimate_min(packed), 0, 0, 0, packed)

    # 1. Pair antagonists as supersets
    next_group = max((ex.superset_group or 0 for ex in packed), default=0) + 1
    used: set[int] = set()
    for i, ex_a in enumerate(packed):
        if i in used:
            continue
        for j, ex_b in enumerate(packed):
            if j <= i or j in used:
                continue
            if _are_antagonists(ex_a.muscle_group, ex_b.muscle_group):
                packed[i] = PackedExercise(
                    ex_a.exercise_id, ex_a.sets, ex_a.reps_avg,
                    ex_a.is_compound, next_group, ex_a.muscle_group
                )
                packed[j] = PackedExercise(
                    ex_b.exercise_id, ex_b.sets, ex_b.reps_avg,
                    ex_b.is_compound, next_group, ex_b.muscle_group
                )
                used.update({i, j})
                superset_pairs += 1
                next_group += 1
                break

    if _estimate_min(packed) <= limit_min:
        return PackResult(_estimate_min(packed), superset_pairs, 0, 0, packed)

    # 2. Cut isolation sets by 1 (down to minimum 1)
    for i, ex in enumerate(packed):
        if ex.is_compound:
            continue
        if ex.sets > 1:
            packed[i] = PackedExercise(
                ex.exercise_id, ex.sets - 1, ex.reps_avg,
                ex.is_compound, ex.superset_group, ex.muscle_group
            )
            isolation_sets_cut += 1

    if _estimate_min(packed) <= limit_min:
        return PackResult(_estimate_min(packed), superset_pairs, isolation_sets_cut, 0, packed)

    # 3. Remove isolation exercises from the end
    while len(packed) > 1 and _estimate_min(packed) > limit_min:
        for i in range(len(packed) - 1, -1, -1):
            if not packed[i].is_compound:
                packed.pop(i)
                isolation_removed += 1
                break
        else:
            break

    return PackResult(
        _estimate_min(packed),
        superset_pairs,
        isolation_sets_cut,
        isolation_removed,
        packed,
    )
