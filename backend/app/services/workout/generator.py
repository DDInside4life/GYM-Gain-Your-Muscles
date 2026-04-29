"""Monthly workout plan generator.

Orchestrates the small, single-responsibility modules:

    questionnaire → filtering → volume budget → split / recovery
                                    │
                                    ▼
                        load_progression (sets/reps/weight/RIR)
                                    │
                                    ▼
                              persistence (DB)

The generator deterministically builds 4 weeks: week 1 test, weeks 2-4 working.
"""
from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Equipment, Exercise, ExerciseCategory, MuscleGroup
from app.models.user import Experience, Goal, User
from app.models.workout import (
    Mesocycle, ProgramPhase, SetLog, WorkoutDay, WorkoutExercise, WorkoutPlan, WorkoutResult,
)
from app.repositories.exercise import ExerciseRepository
from app.repositories.workout import (
    MesocycleRepository,
    WorkoutPlanRepository,
    WorkoutResultRepository,
)
from app.schemas.questionnaire import WorkoutQuestionnaireInput
from app.schemas.workout import WorkoutGenerateInput
from app.services.workout.explanation import build_explanation
from app.services.workout.filtering import (
    FilterCriteria,
    filter_pool,
    resolve_contraindications,
)
from app.services.workout.swap_dictionary import suggest_swaps
from app.services.workout.load_progression import (
    LiftRecord,
    Prescription,
    build_test_prescription,
    build_test_week_easy_prescription,
    build_working_prescription,
    epley_one_rm,
)
from app.services.workout.periodization import Periodization, WeekModifier, week_modifier
from app.services.workout.recovery import (
    DAY_TO_INDEX,
    DayBlueprint,
    HEAVY_LOWER_PATTERNS,
    HEAVY_PUSH_PATTERNS,
    fatigue_cap,
    fatigue_score,
    normalize_available_days,
    space_heavy_days,
)
from app.services.workout.session_duration import (
    DEFAULT_DURATION_MIN,
    cap_for as session_cap_for,
    normalize_duration,
)
from app.services.workout.splits import SPLITS, normalize_structure, pick_split
from app.services.workout.volume import (
    ABSOLUTE_MAX_EXERCISES_PER_DAY,
    MIN_EXERCISES_PER_DAY,
    WeeklyMuscleBudget,
    goal_volume,
)


DEFAULT_TOTAL_WEEKS = 4
TOTAL_WEEKS = DEFAULT_TOTAL_WEEKS
TEST_WEEKS = {1}
MIN_TOTAL_WEEKS = 3
MAX_TOTAL_WEEKS = 12


def resolve_total_weeks(value: int | None) -> int:
    if value is None:
        return DEFAULT_TOTAL_WEEKS
    try:
        weeks = int(value)
    except (TypeError, ValueError):
        return DEFAULT_TOTAL_WEEKS
    return max(MIN_TOTAL_WEEKS, min(MAX_TOTAL_WEEKS, weeks))


@dataclass(slots=True)
class GenerationContext:
    user_id: int
    sex: str
    age: int
    height_cm: float
    weight_kg: float
    experience: Experience
    goal: Goal
    location: str
    equipment: frozenset[Equipment]
    contraindications: frozenset[str]
    days_per_week: int
    available_day_indices: list[int]
    notes: str
    questionnaire_id: int | None = None
    edit_history: dict | None = None
    session_duration_min: int = DEFAULT_DURATION_MIN
    training_structure: str | None = None
    periodization: str | None = None
    total_weeks: int = DEFAULT_TOTAL_WEEKS
    priority_exercise_ids: tuple[int, ...] = ()
    injuries: list[str] = field(default_factory=list)


@dataclass(slots=True)
class _GeneratedExercise:
    exercise: Exercise
    prescription: Prescription
    position: int


@dataclass(slots=True)
class _GeneratedDay:
    day_index: int
    title: str
    focus: str
    is_rest: bool
    week_index: int
    exercises: list[_GeneratedExercise] = field(default_factory=list)


def _seed(user_id: int, month: int) -> int:
    raw = f"{user_id}:{month}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _equipment_set(values: Iterable[str]) -> frozenset[Equipment]:
    parsed: set[Equipment] = set()
    for raw in values:
        key = (raw or "").strip().lower()
        if key in Equipment._value2member_map_:
            parsed.add(Equipment(key))
    if not parsed:
        parsed = {Equipment.bodyweight, Equipment.dumbbell, Equipment.barbell, Equipment.machine}
    return frozenset(parsed)


def _user_priority_ids(user: User) -> list[int]:
    raw = getattr(user, "priority_exercise_ids", None) or []
    return [int(pid) for pid in raw if isinstance(pid, (int, float)) and int(pid) > 0]


def _user_restrictions(user: User) -> list[str]:
    raw = getattr(user, "global_restrictions", None) or []
    return [str(token).strip().lower() for token in raw if str(token).strip()]


def _merge_priority(*sources: list[int] | tuple[int, ...]) -> tuple[int, ...]:
    seen: list[int] = []
    for source in sources:
        for pid in source or ():
            if pid and pid not in seen:
                seen.append(int(pid))
    return tuple(seen)


def context_from_questionnaire(
    user: User,
    payload: WorkoutQuestionnaireInput,
    *,
    questionnaire_id: int | None = None,
    edit_history: dict | None = None,
) -> GenerationContext:
    combined_injuries = list(payload.injuries) + _user_restrictions(user)
    return GenerationContext(
        user_id=user.id,
        sex=payload.sex.value,
        age=payload.age,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        experience=payload.experience,
        goal=payload.goal,
        location=payload.location,
        equipment=_equipment_set(payload.equipment),
        contraindications=resolve_contraindications(combined_injuries),
        days_per_week=payload.days_per_week,
        available_day_indices=normalize_available_days(payload.available_days, payload.days_per_week),
        notes=payload.notes,
        questionnaire_id=questionnaire_id,
        edit_history=edit_history,
        session_duration_min=normalize_duration(payload.session_duration_min),
        training_structure=normalize_structure(payload.training_structure),
        periodization=payload.periodization,
        total_weeks=resolve_total_weeks(payload.cycle_length_weeks),
        priority_exercise_ids=_merge_priority(payload.priority_exercise_ids, _user_priority_ids(user)),
        injuries=combined_injuries,
    )


def context_from_legacy(user: User, payload: WorkoutGenerateInput) -> GenerationContext:
    combined_injuries = list(payload.injuries) + _user_restrictions(user)
    return GenerationContext(
        user_id=user.id,
        sex=getattr(user.sex, "value", "male") if user.sex else "male",
        age=payload.age,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        experience=payload.experience,
        goal=payload.goal,
        location="gym",
        equipment=_equipment_set(payload.equipment),
        contraindications=resolve_contraindications(combined_injuries),
        days_per_week=payload.days_per_week,
        available_day_indices=normalize_available_days((), payload.days_per_week),
        notes="",
        session_duration_min=normalize_duration(payload.session_duration_min),
        training_structure=normalize_structure(payload.training_structure),
        periodization=payload.periodization,
        total_weeks=resolve_total_weeks(payload.cycle_length_weeks),
        priority_exercise_ids=_merge_priority(payload.priority_exercise_ids, _user_priority_ids(user)),
        injuries=combined_injuries,
    )


class WorkoutGenerator:
    """Persists a 4-week monthly plan from a generation context."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.exercises = ExerciseRepository(db)
        self.plans = WorkoutPlanRepository(db)
        self.results = WorkoutResultRepository(db)
        self.mesocycles = MesocycleRepository(db)

    async def generate(
        self,
        user: User,
        payload: WorkoutGenerateInput | WorkoutQuestionnaireInput,
        *,
        questionnaire_id: int | None = None,
    ) -> WorkoutPlan:
        if isinstance(payload, WorkoutQuestionnaireInput):
            ctx = context_from_questionnaire(user, payload, questionnaire_id=questionnaire_id)
        else:
            ctx = context_from_legacy(user, payload)
        return await self.generate_from_context(user, ctx)

    async def generate_from_context(self, user: User, ctx: GenerationContext) -> WorkoutPlan:
        pool = await self.exercises.list_filtered(active_only=True)
        if not pool:
            raise ValueError("Каталог упражнений пуст: запустите сидер")

        filtered = filter_pool(
            pool,
            FilterCriteria(
                location=ctx.location,
                equipment=ctx.equipment,
                contraindications=ctx.contraindications,
                experience=ctx.experience,
            ),
        )
        if len(filtered) < MIN_EXERCISES_PER_DAY:
            filtered = filter_pool(
                pool,
                FilterCriteria(
                    location=ctx.location,
                    equipment=frozenset(),
                    contraindications=ctx.contraindications,
                    experience=ctx.experience,
                ),
            )
        if not filtered:
            raise ValueError("После фильтрации не осталось безопасных упражнений")

        prev = await self.plans.latest_for_user(user.id)
        next_month = (prev.month_index + 1) if prev else 1
        rng = random.Random(_seed(user.id, next_month))

        split_key = pick_split(ctx.days_per_week, ctx.experience, ctx.training_structure)
        templates = SPLITS[split_key][: ctx.days_per_week]

        blueprints = [
            DayBlueprint(
                title=tmpl.title,
                focus=", ".join(m.value for m in tmpl.muscles),
                is_rest=False,
                primary_muscles=tmpl.muscles,
                heavy_compound=any(m in {MuscleGroup.legs, MuscleGroup.back, MuscleGroup.chest, MuscleGroup.shoulders} for m in tmpl.muscles),
            )
            for tmpl in templates
        ]
        slots = space_heavy_days(blueprints, ctx.available_day_indices)

        records = await self._lift_records(user.id)
        edit_history = ctx.edit_history or {}
        avoid_ids = set(edit_history.get("avoid_exercise_ids") or [])
        prefer_ids: set[int] = set(edit_history.get("prefer_exercise_ids") or [])
        prefer_ids |= set(ctx.priority_exercise_ids)

        total_weeks = max(MIN_TOTAL_WEEKS, min(MAX_TOTAL_WEEKS, ctx.total_weeks))
        days: list[_GeneratedDay] = []
        for week_index in range(1, total_weeks + 1):
            weekly_budget = WeeklyMuscleBudget.for_experience(ctx.experience)
            modifier = week_modifier(ctx.periodization, week_index, total_weeks)
            for day_of_week in range(7):
                if day_of_week in slots:
                    template_idx = slots.index(day_of_week)
                    template = templates[template_idx]
                    used_archetypes: set[str] = set()
                    day = await self._build_day(
                        absolute_index=week_index * 100 + day_of_week,
                        day_index=(week_index - 1) * 7 + day_of_week,
                        week_index=week_index,
                        title=template.title,
                        focus=", ".join(m.value for m in template.muscles),
                        muscles=template.muscles,
                        pool=filtered,
                        ctx=ctx,
                        rng=rng,
                        records=records,
                        weekly_budget=weekly_budget,
                        used_archetypes=used_archetypes,
                        avoid_ids=avoid_ids,
                        prefer_ids=prefer_ids,
                        modifier=modifier,
                        is_test_week=(week_index in TEST_WEEKS),
                    )
                    days.append(day)
                else:
                    days.append(_GeneratedDay(
                        day_index=(week_index - 1) * 7 + day_of_week,
                        title="Отдых",
                        focus="восстановление",
                        is_rest=True,
                        week_index=week_index,
                    ))

        await self.plans.deactivate_all(user.id)

        explanation = build_explanation(
            goal=ctx.goal,
            experience=ctx.experience,
            days_per_week=ctx.days_per_week,
            split_key=split_key,
            location=ctx.location,
            has_previous_results=any(r.estimated_1rm for r in records.values()),
        )

        plan = WorkoutPlan(
            user_id=user.id,
            name=f"Месяц {next_month} · {self._split_name_ru(split_key)}",
            week_number=(prev.week_number + total_weeks) if prev else total_weeks,
            month_index=next_month,
            cycle_week=1,
            phase=ProgramPhase.test,
            split_type=split_key,
            is_active=True,
            params={
                "goal": ctx.goal.value,
                "experience": ctx.experience.value,
                "location": ctx.location,
                "days_per_week": ctx.days_per_week,
                "available_days": [list(DAY_TO_INDEX.keys())[idx] for idx in ctx.available_day_indices],
                "equipment": sorted(e.value for e in ctx.equipment),
                "injuries": sorted(ctx.contraindications),
                "questionnaire_id": ctx.questionnaire_id,
                "explanation_ru": explanation,
                "method": "test_week+intensity_volume_blend+double_progression",
                "user_edits": edit_history,
                "session_duration_min": ctx.session_duration_min,
                "training_structure": ctx.training_structure or split_key,
                "periodization": ctx.periodization,
                "cycle_length_weeks": total_weeks,
                "priority_exercise_ids": list(ctx.priority_exercise_ids),
                "global_restrictions": sorted(_user_restrictions(user)),
            },
        )
        self.db.add(plan)
        await self.db.flush()

        for gd in days:
            day_row = WorkoutDay(
                plan_id=plan.id,
                day_index=gd.day_index,
                title=gd.title,
                focus=gd.focus,
                is_rest=gd.is_rest,
                week_index=gd.week_index,
                phase=ProgramPhase.test if gd.week_index == 1 else ProgramPhase.work,
            )
            self.db.add(day_row)
            await self.db.flush()
            for ge in gd.exercises:
                self.db.add(WorkoutExercise(
                    day_id=day_row.id,
                    exercise_id=ge.exercise.id,
                    position=ge.position,
                    sets=ge.prescription.sets,
                    reps_min=ge.prescription.reps_min,
                    reps_max=ge.prescription.reps_max,
                    weight_kg=ge.prescription.weight_kg,
                    rest_sec=ge.prescription.rest_sec,
                    notes=ge.prescription.notes,
                    target_percent_1rm=ge.prescription.target_percent_1rm,
                    is_test_set=ge.prescription.is_test_set,
                    test_instruction=ge.prescription.test_instruction,
                    target_rir=ge.prescription.target_rir,
                    rpe_text=ge.prescription.rpe_text,
                ))

        await self._reset_mesocycle(user.id, plan.id, prev)

        await self.db.commit()
        fresh = await self.plans.get_with_days(plan.id)
        assert fresh is not None
        return fresh

    async def _reset_mesocycle(
        self,
        user_id: int,
        plan_id: int,
        previous_plan: WorkoutPlan | None,
    ) -> Mesocycle:
        """Deactivate any open mesocycle and start a fresh one for the new plan."""
        prev_active = await self.mesocycles.active_for_user(user_id)
        await self.mesocycles.deactivate_user_cycles(user_id)
        next_cycle_number = (prev_active.cycle_number + 1) if prev_active else 1
        meso = Mesocycle(
            user_id=user_id,
            plan_id=plan_id,
            cycle_number=next_cycle_number,
            current_week=1,
            is_active=True,
            weekly_volume={},
        )
        self.db.add(meso)
        await self.db.flush()
        return meso

    async def _build_day(
        self,
        *,
        absolute_index: int,
        day_index: int,
        week_index: int,
        title: str,
        focus: str,
        muscles: tuple[MuscleGroup, ...],
        pool: list[Exercise],
        ctx: GenerationContext,
        rng: random.Random,
        records: dict[int, LiftRecord],
        weekly_budget: WeeklyMuscleBudget,
        used_archetypes: set[str],
        avoid_ids: set[int],
        prefer_ids: set[int],
        modifier: WeekModifier,
        is_test_week: bool,
    ) -> _GeneratedDay:
        cfg = goal_volume(ctx.goal)
        max_per_day = session_cap_for(
            ctx.session_duration_min, ctx.experience, cfg.max_exercises_per_day,
        )
        chosen: list[Exercise] = []
        used_ids: set[int] = set()

        for muscle in muscles:
            if len(chosen) >= max_per_day:
                break
            for ex in self._pick_for_muscle(
                muscle=muscle,
                pool=pool,
                week_index=week_index,
                is_test_week=is_test_week,
                ctx=ctx,
                used_ids=used_ids,
                used_archetypes=used_archetypes,
                weekly_budget=weekly_budget,
                rng=rng,
                avoid_ids=avoid_ids,
                prefer_ids=prefer_ids,
            ):
                if len(chosen) >= max_per_day:
                    break
                chosen.append(ex)
                used_ids.add(ex.id)
                used_archetypes.add(ex.movement_archetype)
                weekly_budget.add(ex.primary_muscle, sets_for(ex, ctx.goal))

        chosen = self._fill_to_min(
            chosen, pool, ctx, used_ids, used_archetypes, weekly_budget, max_per_day,
        )

        day_fatigue = 0
        cap = fatigue_cap(ctx.experience)

        gd = _GeneratedDay(
            day_index=day_index,
            title=f"Неделя {week_index} · {self._title_ru(title)}",
            focus=self._focus_ru(focus),
            is_rest=False,
            week_index=week_index,
        )

        for position, ex in enumerate(chosen):
            cost = fatigue_score(muscles, ex.category)
            if day_fatigue + cost > cap and len(gd.exercises) >= MIN_EXERCISES_PER_DAY:
                break
            day_fatigue += cost

            record = records.get(ex.id, LiftRecord())
            e1rm = record.estimated_1rm
            if is_test_week:
                prescription = (
                    build_test_prescription(ex, ctx.experience, ctx.goal, prev_e1rm=e1rm)
                    if ex.suitable_for_test
                    else build_test_week_easy_prescription(
                        ex, ctx.experience, ctx.goal, prev_e1rm=e1rm,
                    )
                )
            else:
                prescription = build_working_prescription(
                    ex, ctx.experience, ctx.goal, week_index, e1rm,
                )
                prescription = _apply_modifier(prescription, modifier)
            gd.exercises.append(_GeneratedExercise(
                exercise=ex,
                prescription=prescription,
                position=position,
            ))
        return gd

    def _pick_for_muscle(
        self,
        *,
        muscle: MuscleGroup,
        pool: list[Exercise],
        week_index: int,
        is_test_week: bool,
        ctx: GenerationContext,
        used_ids: set[int],
        used_archetypes: set[str],
        weekly_budget: WeeklyMuscleBudget,
        rng: random.Random,
        avoid_ids: set[int],
        prefer_ids: set[int],
    ) -> list[Exercise]:
        def _build_candidates(exercises: list[Exercise]) -> list[Exercise]:
            result = [
                ex for ex in exercises
                if ex.primary_muscle == muscle
                and ex.id not in used_ids
                and ex.id not in avoid_ids
                and (ex.movement_archetype not in used_archetypes or ex.category != ExerciseCategory.compound)
            ]
            if is_test_week:
                result = sorted(result, key=lambda e: (0 if e.suitable_for_test else 1))
            result.sort(key=lambda e: (
                0 if e.id in prefer_ids else 1,
                0 if e.category == ExerciseCategory.compound else 1,
                e.difficulty,
                e.id,
            ))
            return result

        candidates = _build_candidates(pool)

        if not candidates and ctx.injuries:
            source_archetypes = {
                ex.movement_archetype for ex in pool if ex.primary_muscle == muscle
            }
            swap_archetypes: set[str] = set()
            for archetype in source_archetypes:
                swap_archetypes.update(suggest_swaps(archetype, ctx.injuries))
            if swap_archetypes:
                swap_pool = [
                    ex for ex in pool
                    if ex.primary_muscle == muscle and ex.movement_archetype in swap_archetypes
                ]
                candidates = _build_candidates(swap_pool)

        affordable = [c for c in candidates if weekly_budget.can_add(muscle, sets_for(c, ctx.goal))]
        if not affordable and candidates:
            affordable = candidates[:1]

        if affordable:
            preferred = [c for c in affordable if c.id in prefer_ids]
            others = [c for c in affordable if c.id not in prefer_ids]
            head = others[: min(4, len(others))]
            tail = others[len(head):]
            rng.shuffle(head)
            affordable = preferred + head + tail

        want = 2 if ctx.goal in (Goal.muscle_gain, Goal.strength) else 1
        return affordable[:want]

    def _fill_to_min(
        self,
        chosen: list[Exercise],
        pool: list[Exercise],
        ctx: GenerationContext,
        used_ids: set[int],
        used_archetypes: set[str],
        weekly_budget: WeeklyMuscleBudget,
        max_per_day: int,
    ) -> list[Exercise]:
        target = max(MIN_EXERCISES_PER_DAY, min(max_per_day, ABSOLUTE_MAX_EXERCISES_PER_DAY))
        if len(chosen) >= target:
            return chosen[:target]
        candidates = [
            ex for ex in pool
            if ex.id not in used_ids
            and weekly_budget.can_add(ex.primary_muscle, sets_for(ex, ctx.goal))
        ]
        candidates.sort(key=lambda e: (e.difficulty, e.id))
        for ex in candidates:
            if len(chosen) >= target:
                break
            chosen.append(ex)
            used_ids.add(ex.id)
            used_archetypes.add(ex.movement_archetype)
            weekly_budget.add(ex.primary_muscle, sets_for(ex, ctx.goal))
        return chosen[:target]

    async def _lift_records(self, user_id: int) -> dict[int, LiftRecord]:
        result_stmt = (
            select(WorkoutResult)
            .where(WorkoutResult.user_id == user_id)
            .order_by(desc(WorkoutResult.created_at))
        )
        rows = (await self.db.execute(result_stmt)).scalars().all()
        records: dict[int, LiftRecord] = {}
        for row in rows:
            if row.exercise_id in records:
                continue
            records[row.exercise_id] = LiftRecord(
                estimated_1rm=row.estimated_1rm,
                last_weight=row.weight_kg,
                last_reps_completed=row.reps_completed,
            )

        log_stmt = (
            select(SetLog)
            .where(SetLog.user_id == user_id)
            .order_by(desc(SetLog.created_at))
            .limit(200)
        )
        log_rows = (await self.db.execute(log_stmt)).scalars().all()
        agg: dict[int, list[SetLog]] = defaultdict(list)
        for row in log_rows:
            agg[row.exercise_id].append(row)
        for exercise_id, sets in agg.items():
            valid = [s for s in sets if s.rir is not None and 0.5 <= s.rir <= 5 and 3 <= s.completed_reps <= 15]
            if not valid:
                continue
            best_e1rm = max(epley_one_rm(s.completed_weight_kg, s.completed_reps) for s in valid)
            last = sets[0]
            existing = records.get(exercise_id)
            base_e1rm = existing.estimated_1rm if existing and existing.estimated_1rm else None
            records[exercise_id] = LiftRecord(
                estimated_1rm=max(base_e1rm or 0.0, best_e1rm) or best_e1rm,
                last_weight=last.completed_weight_kg,
                last_reps_completed=last.completed_reps,
                last_rir=last.rir,
                successful_streak=sum(1 for s in valid if s.rir >= 1.0),
            )
        return records

    @staticmethod
    def _split_name_ru(split_key: str) -> str:
        return {
            "full_body": "Фулбади",
            "half_split": "Полусплит",
            "upper_lower": "Верх/Низ",
            "split": "Сплит",
            "ppl": "Тяни/Толкай/Ноги",
        }.get(split_key, split_key)

    @staticmethod
    def _title_ru(title: str) -> str:
        mapping = {
            "Full A": "Фулл A", "Full B": "Фулл B", "Full C": "Фулл C",
            "Half A": "Сплит A", "Half B": "Сплит B", "Half C": "Сплит C", "Half D": "Сплит D",
            "Upper A": "Верх A", "Upper B": "Верх B",
            "Lower A": "Низ A", "Lower B": "Низ B",
            "Push": "Толкающий", "Pull": "Тянущий", "Legs": "Ноги",
        }
        return mapping.get(title, title)

    @staticmethod
    def _focus_ru(focus: str) -> str:
        mapping = {
            "legs": "ноги", "chest": "грудь", "back": "спина", "shoulders": "плечи",
            "biceps": "бицепс", "triceps": "трицепс", "core": "пресс",
            "glutes": "ягодицы", "calves": "икры", "forearms": "предплечья",
            "full_body": "всё тело", "cardio": "кардио",
        }
        parts = [mapping.get(p.strip(), p.strip()) for p in focus.split(",")]
        return ", ".join(p for p in parts if p)


def sets_for(exercise: Exercise, goal: Goal) -> int:
    cfg = goal_volume(goal)
    return cfg.sets_per_compound if exercise.category == ExerciseCategory.compound else cfg.sets_per_isolation


def _apply_modifier(prescription: Prescription, modifier: WeekModifier) -> Prescription:
    """Apply a periodization week-modifier to a working prescription.

    - ``intensity`` scales target_percent_1rm and weight_kg
    - ``volume`` scales the sets count (clamped to ≥1, ≤8)
    """
    if modifier.intensity == 1.0 and modifier.volume == 1.0:
        return prescription
    new_sets = max(1, min(8, round(prescription.sets * modifier.volume)))
    new_pct = (
        round(prescription.target_percent_1rm * modifier.intensity, 4)
        if prescription.target_percent_1rm is not None else None
    )
    new_weight = (
        round(prescription.weight_kg * modifier.intensity, 1)
        if prescription.weight_kg is not None else None
    )
    return Prescription(
        sets=new_sets,
        reps_min=prescription.reps_min,
        reps_max=prescription.reps_max,
        rest_sec=prescription.rest_sec,
        weight_kg=new_weight,
        target_percent_1rm=new_pct,
        target_rir=prescription.target_rir,
        rpe_text=prescription.rpe_text,
        is_test_set=prescription.is_test_set,
        test_instruction=prescription.test_instruction,
        notes=(
            f"{prescription.notes} · {modifier.label}".strip(" ·")
            if modifier.label else prescription.notes
        ),
    )
