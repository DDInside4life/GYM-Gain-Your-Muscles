from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Equipment, Exercise, ExerciseCategory, MuscleGroup
from app.models.user import Experience, Goal, User
from app.models.workout import WorkoutDay, WorkoutExercise, WorkoutPlan
from app.repositories.exercise import ExerciseRepository
from app.repositories.workout import WorkoutPlanRepository
from app.schemas.workout import WorkoutGenerateInput
from app.services.workout.rules import (
    DEFAULT_EQUIPMENT, EXPERIENCE_INTENSITY_MOD, EXPERIENCE_VOLUME_MOD,
    GOAL_INTENSITY_MOD, GOAL_SCHEME, clamp_sets, resolve_injury_contras, round_to_plate,
)
from app.services.workout.splits import SPLITS, pick_split

MIN_PER_DAY, MAX_PER_DAY = 4, 6

MUSCLE_LOAD_FACTOR: dict[MuscleGroup, float] = {
    MuscleGroup.legs: 1.20,
    MuscleGroup.back: 1.00,
    MuscleGroup.chest: 0.90,
    MuscleGroup.glutes: 1.00,
    MuscleGroup.calves: 0.80,
    MuscleGroup.full_body: 0.60,
    MuscleGroup.shoulders: 0.50,
    MuscleGroup.triceps: 0.30,
    MuscleGroup.biceps: 0.25,
    MuscleGroup.forearms: 0.25,
    MuscleGroup.core: 0.20,
    MuscleGroup.cardio: 0.00,
}


@dataclass(slots=True)
class GeneratedExercise:
    exercise: Exercise
    sets: int
    reps_min: int
    reps_max: int
    rest: int
    notes: str = ""
    weight_kg: float | None = None


@dataclass(slots=True)
class GeneratedDay:
    day_index: int
    title: str
    focus: str
    is_rest: bool
    exercises: list[GeneratedExercise] = field(default_factory=list)


class WorkoutGenerator:
    """Deterministic per-user weekly plan generator."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.exercises = ExerciseRepository(db)
        self.plans = WorkoutPlanRepository(db)

    @staticmethod
    def _seed(user_id: int, week: int) -> int:
        raw = f"{user_id}:{week}".encode()
        return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")

    @staticmethod
    def _parse_equipment(values: list[str]) -> frozenset[Equipment]:
        valid = {v for v in values if v in Equipment._value2member_map_}
        return frozenset(Equipment(v) for v in valid) or DEFAULT_EQUIPMENT

    @staticmethod
    def _is_safe(ex: Exercise, contras: frozenset[str]) -> bool:
        return not (contras & set(ex.contraindications))

    def _pick_for_muscle(
        self,
        muscle: MuscleGroup,
        pool: list[Exercise],
        equipment: frozenset[Equipment],
        contras: frozenset[str],
        experience: Experience,
        goal: Goal,
        used: set[int],
        rng: random.Random,
    ) -> list[Exercise]:
        candidates = [
            ex for ex in pool
            if ex.primary_muscle == muscle
            and ex.equipment in equipment
            and ex.id not in used
            and self._is_safe(ex, contras)
        ]
        if experience == Experience.beginner:
            beginner = [c for c in candidates if c.difficulty <= 3]
            if beginner:
                candidates = beginner

        candidates.sort(key=lambda e: (
            0 if e.category == ExerciseCategory.compound else 1,
            e.difficulty,
            e.id,  # deterministic tiebreak
        ))
        want = 2 if goal in (Goal.strength, Goal.muscle_gain) else 1
        # deterministic tiny shuffle among same-rank candidates to add variety
        rng.shuffle(candidates[:4])
        return candidates[:want]

    def _fill_to_min(
        self,
        current: list[Exercise],
        pool: list[Exercise],
        equipment: frozenset[Equipment],
        contras: frozenset[str],
        used: set[int],
    ) -> list[Exercise]:
        if len(current) >= MIN_PER_DAY:
            return current
        filler = [
            ex for ex in pool
            if ex.equipment in equipment and ex.id not in used and self._is_safe(ex, contras)
        ]
        filler.sort(key=lambda e: (e.difficulty, e.id))
        for ex in filler:
            if len(current) >= MIN_PER_DAY:
                break
            current.append(ex)
            used.add(ex.id)
        return current

    def _estimate_weight(
        self,
        user: User,
        ex: Exercise,
        experience: Experience,
        goal: Goal,
    ) -> float | None:
        if ex.equipment == Equipment.bodyweight or ex.category == ExerciseCategory.cardio:
            return None
        bw = user.weight_kg or 75.0
        raw = (
            bw
            * EXPERIENCE_INTENSITY_MOD[experience]
            * GOAL_INTENSITY_MOD[goal]
            * MUSCLE_LOAD_FACTOR.get(ex.primary_muscle, 0.6)
        )
        return round_to_plate(raw)

    def _build_day(
        self,
        *,
        day_index: int,
        template_title: str,
        muscles: tuple[MuscleGroup, ...],
        pool: list[Exercise],
        equipment: frozenset[Equipment],
        contras: frozenset[str],
        user: User,
        experience: Experience,
        goal: Goal,
        rng: random.Random,
    ) -> GeneratedDay:
        scheme = GOAL_SCHEME[goal]
        target_sets = clamp_sets(round(scheme.sets * EXPERIENCE_VOLUME_MOD[experience]))

        chosen: list[Exercise] = []
        used: set[int] = set()
        for muscle in muscles:
            for ex in self._pick_for_muscle(muscle, pool, equipment, contras, experience, goal, used, rng):
                if len(chosen) >= MAX_PER_DAY:
                    break
                chosen.append(ex)
                used.add(ex.id)
            if len(chosen) >= MAX_PER_DAY:
                break

        chosen = self._fill_to_min(chosen, pool, equipment, contras, used)

        exercises = [
            GeneratedExercise(
                exercise=ex,
                sets=target_sets,
                reps_min=scheme.reps_min,
                reps_max=scheme.reps_max,
                rest=scheme.rest_sec,
                notes=f"RPE ~{scheme.rpe}",
                weight_kg=self._estimate_weight(user, ex, experience, goal),
            )
            for ex in chosen[:MAX_PER_DAY]
        ]
        return GeneratedDay(
            day_index=day_index,
            title=template_title,
            focus=", ".join(m.value for m in muscles),
            is_rest=False,
            exercises=exercises,
        )

    async def generate(self, user: User, payload: WorkoutGenerateInput) -> WorkoutPlan:
        split_key = pick_split(payload.days_per_week, payload.experience)
        template = SPLITS[split_key][: payload.days_per_week]
        equipment = self._parse_equipment(payload.equipment)
        contras = resolve_injury_contras(payload.injuries)

        pool = await self.exercises.list_filtered(active_only=True)
        if not pool:
            raise ValueError("Exercise catalogue is empty; seed data missing")

        prev = await self.plans.latest_for_user(user.id)
        next_week = (prev.week_number + 1) if prev else 1
        rng = random.Random(self._seed(user.id, next_week))

        days: list[GeneratedDay] = []
        for i in range(7):
            if i < len(template):
                tmpl = template[i]
                days.append(self._build_day(
                    day_index=i,
                    template_title=tmpl.title,
                    muscles=tmpl.muscles,
                    pool=pool,
                    equipment=equipment,
                    contras=contras,
                    user=user,
                    experience=payload.experience,
                    goal=payload.goal,
                    rng=rng,
                ))
            else:
                days.append(GeneratedDay(i, "Rest", "recovery", True))

        await self.plans.deactivate_all(user.id)

        scheme = GOAL_SCHEME[payload.goal]
        plan = WorkoutPlan(
            user_id=user.id,
            name=f"Week {next_week} · {split_key.replace('_', ' ').title()}",
            week_number=next_week,
            split_type=split_key,
            is_active=True,
            params={
                "goal": payload.goal.value,
                "experience": payload.experience.value,
                "days_per_week": payload.days_per_week,
                "equipment": sorted(e.value for e in equipment),
                "injuries": payload.injuries,
                "scheme": {
                    "sets": scheme.sets, "reps_min": scheme.reps_min, "reps_max": scheme.reps_max,
                    "rest_sec": scheme.rest_sec, "rpe": scheme.rpe,
                },
            },
        )
        self.db.add(plan)
        await self.db.flush()

        for gd in days:
            day_row = WorkoutDay(
                plan_id=plan.id, day_index=gd.day_index,
                title=gd.title, focus=gd.focus, is_rest=gd.is_rest,
            )
            self.db.add(day_row)
            await self.db.flush()
            for pos, ge in enumerate(gd.exercises):
                self.db.add(WorkoutExercise(
                    day_id=day_row.id,
                    exercise_id=ge.exercise.id,
                    position=pos,
                    sets=ge.sets,
                    reps_min=ge.reps_min,
                    reps_max=ge.reps_max,
                    weight_kg=ge.weight_kg,
                    rest_sec=ge.rest,
                    notes=ge.notes,
                ))

        await self.db.commit()
        fresh = await self.plans.get_with_days(plan.id)
        assert fresh is not None
        return fresh
