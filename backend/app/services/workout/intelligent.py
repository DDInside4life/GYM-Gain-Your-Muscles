from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, NotFound
from app.models.exercise import Exercise, ExerciseCategory, MuscleGroup
from app.models.user import Experience, Goal, User
from app.models.workout import Mesocycle, ProgramPhase, SetLog, WorkoutDay, WorkoutExercise, WorkoutPlan
from app.repositories.exercise import ExerciseRepository
from app.repositories.workout import MesocycleRepository, SetLogRepository, WorkoutPlanRepository, WorkoutResultRepository
from app.schemas.intelligent_training import GenerateProgramInput, ProgressPoint, StrengthProfileRead, WorkoutLogInput
from app.services.training_engine import TrainingEngine
from app.services.workout.rules import round_to_plate
from app.services.workout.splits import SPLITS

FOUR_WEEK_CYCLE = 4


@dataclass(slots=True)
class LogResult:
    updated: int
    next_weight_adjustment_pct: float
    weekly_volume: float


class IntelligentTrainingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.exercise_repo = ExerciseRepository(db)
        self.plan_repo = WorkoutPlanRepository(db)
        self.result_repo = WorkoutResultRepository(db)
        self.cycle_repo = MesocycleRepository(db)
        self.set_log_repo = SetLogRepository(db)
        self.training_engine = TrainingEngine()

    @staticmethod
    def _epley(weight_kg: float, reps: int) -> float:
        return round(weight_kg * (1 + reps / 30.0), 2)

    @staticmethod
    def _experience(value: str) -> Experience:
        return Experience(value)

    @staticmethod
    def _goal(value: str) -> Goal:
        mapping = {
            "hypertrophy": Goal.muscle_gain,
            "strength": Goal.strength,
            "recomposition": Goal.fat_loss,
        }
        return mapping[value]

    def _fallback_e1rm(self, user_weight: float, category: ExerciseCategory, muscle: MuscleGroup) -> float:
        base = 0.75 if category == ExerciseCategory.compound else 0.45
        muscle_mult = 1.0 if muscle in {MuscleGroup.back, MuscleGroup.legs, MuscleGroup.chest} else 0.65
        return round(user_weight * base * muscle_mult, 2)

    async def _strength_profile(self, payload: GenerateProgramInput, exercises: list[Exercise]) -> dict[int, StrengthProfileRead]:
        by_id = {entry.exercise_id: entry for entry in payload.initial_strength}
        profile: dict[int, StrengthProfileRead] = {}
        for ex in exercises:
            given = by_id.get(ex.id)
            if given is None:
                profile[ex.id] = StrengthProfileRead(
                    exercise_id=ex.id,
                    actual_1rm=None,
                    estimated_1rm=self._fallback_e1rm(payload.weight_kg, ex.category, ex.primary_muscle),
                )
                continue
            if given.one_rm is not None:
                profile[ex.id] = StrengthProfileRead(
                    exercise_id=ex.id,
                    actual_1rm=round(given.one_rm, 2),
                    estimated_1rm=round(given.one_rm, 2),
                )
                continue
            assert given.weight_kg is not None and given.reps is not None
            profile[ex.id] = StrengthProfileRead(
                exercise_id=ex.id,
                actual_1rm=None,
                estimated_1rm=self._epley(given.weight_kg, given.reps),
            )
        return profile

    async def generate_program(self, user: User, payload: GenerateProgramInput) -> tuple[WorkoutPlan, str, list[StrengthProfileRead]]:
        split_key = self.training_engine.choose_split(payload.training_days, self._experience(payload.training_experience))
        split_template = SPLITS[split_key][: payload.training_days]
        exercise_pool = await self.exercise_repo.list_filtered(active_only=True)
        if not exercise_pool:
            raise BadRequest("Exercise catalogue is empty")

        by_muscle: dict[MuscleGroup, list[Exercise]] = defaultdict(list)
        for ex in exercise_pool:
            by_muscle[ex.primary_muscle].append(ex)
        for values in by_muscle.values():
            values.sort(key=lambda item: (0 if item.category == ExerciseCategory.compound else 1, item.difficulty, item.id))

        prev = await self.plan_repo.latest_for_user(user.id)
        next_cycle = (prev.month_index + 1) if prev else 1
        await self.plan_repo.deactivate_all(user.id)
        await self.cycle_repo.deactivate_user_cycles(user.id)

        plan = WorkoutPlan(
            user_id=user.id,
            name=f"Mesocycle {next_cycle} · {split_key.replace('_', ' ').title()}",
            week_number=(prev.week_number + FOUR_WEEK_CYCLE) if prev else FOUR_WEEK_CYCLE,
            month_index=next_cycle,
            cycle_week=1,
            phase=ProgramPhase.work,
            split_type=split_key,
            is_active=True,
            params={
                "training_experience": payload.training_experience,
                "goal": payload.goal,
                "days_per_week": payload.training_days,
                "load_mode": payload.load_mode,
            },
        )
        self.db.add(plan)
        await self.db.flush()

        profile = await self._strength_profile(payload, exercise_pool)

        baseline_1rm = max((item.estimated_1rm for item in profile.values()), default=payload.weight_kg)
        weekly_targets = self.training_engine.build_targets(
            start_kpsh=payload.start_kpsh,
            start_weight=baseline_1rm * payload.start_intensity_pct,
            weeks=FOUR_WEEK_CYCLE,
            growth_step=payload.growth_step,
            drop_step=payload.drop_step,
            wave_length=payload.wave_length,
            load_mode=payload.load_mode,
        )
        plan.params["periodization"] = [
            {
                "week": item.week,
                "phase": item.phase,
                "kpsh": item.kpsh,
                "intensity": item.intensity,
                "tonnage": item.tonnage,
                "intensity_pct_1rm": item.intensity_pct_1rm,
            }
            for item in weekly_targets
        ]

        day_index = 0
        for week_index in range(1, FOUR_WEEK_CYCLE + 1):
            weekly_target = weekly_targets[week_index - 1]
            for day in range(7):
                if day < len(split_template):
                    template = split_template[day]
                    row = WorkoutDay(
                        plan_id=plan.id,
                        day_index=day_index,
                        title=f"W{week_index} · {template.title}",
                        focus=", ".join(m.value for m in template.muscles),
                        is_rest=False,
                        week_index=week_index,
                        phase=ProgramPhase.work,
                    )
                    self.db.add(row)
                    await self.db.flush()
                    used: set[int] = set()
                    position = 0
                    for muscle in template.muscles:
                        candidates = [ex for ex in by_muscle.get(muscle, []) if ex.id not in used]
                        if not candidates:
                            continue
                        primary = candidates[0]
                        used.add(primary.id)
                        is_compound = primary.category == ExerciseCategory.compound
                        reps_target = 5 if payload.goal == "strength" and is_compound else 8
                        if week_index == FOUR_WEEK_CYCLE:
                            reps_min = 3
                            reps_max = 5
                            sets = 3 if is_compound else 2
                        else:
                            if payload.goal == "strength":
                                reps_min = max(3, reps_target - 1)
                                reps_max = reps_target + 1
                            else:
                                reps_min = reps_target
                                reps_max = reps_target + 4
                            target_sets = round(max(4.0, min(28.0, weekly_target.kpsh)) / max(1, reps_target))
                            sets = max(2, min(6, target_sets + (1 if is_compound else 0)))

                        if payload.load_mode == "percent_1rm":
                            target_pct = 0.85 if week_index == FOUR_WEEK_CYCLE else weekly_target.intensity_pct_1rm
                        else:
                            target_pct = 0.0
                        e1rm = profile[primary.id].estimated_1rm
                        base_weight = e1rm * target_pct if payload.load_mode == "percent_1rm" else weekly_target.intensity
                        self.db.add(WorkoutExercise(
                            day_id=row.id,
                            exercise_id=primary.id,
                            position=position,
                            sets=sets,
                            reps_min=reps_min,
                            reps_max=reps_max,
                            weight_kg=round_to_plate(base_weight),
                            rest_sec=150 if is_compound else 90,
                            notes=f"KPSH {weekly_target.kpsh:.0f} · tonnage {weekly_target.tonnage:.0f}",
                            target_percent_1rm=target_pct if payload.load_mode == "percent_1rm" else None,
                            is_test_set=week_index == FOUR_WEEK_CYCLE,
                            test_instruction="Perform top set at 3-5RM to refresh e1RM" if week_index == FOUR_WEEK_CYCLE else "",
                        ))
                        position += 1
                        if position >= 6:
                            break
                else:
                    self.db.add(WorkoutDay(
                        plan_id=plan.id,
                        day_index=day_index,
                        title=f"W{week_index} · Rest",
                        focus="recovery",
                        is_rest=True,
                        week_index=week_index,
                        phase=ProgramPhase.work,
                    ))
                day_index += 1

        self.db.add(Mesocycle(
            user_id=user.id,
            plan_id=plan.id,
            cycle_number=next_cycle,
            start_date=date.today(),
            current_week=1,
            is_active=True,
            weekly_volume={},
        ))
        await self.db.commit()
        fresh = await self.plan_repo.get_with_days(plan.id)
        assert fresh is not None
        return fresh, split_key, list(profile.values())

    async def today_workout(self, user_id: int) -> tuple[WorkoutDay | None, Mesocycle]:
        cycle = await self.cycle_repo.active_for_user(user_id)
        if cycle is None:
            raise NotFound("No active mesocycle. Generate a program first.")
        plan = await self.plan_repo.get_with_days(cycle.plan_id)
        if plan is None:
            raise NotFound("Active plan not found")
        week = max(1, min(cycle.current_week, FOUR_WEEK_CYCLE))
        day_of_week = datetime.now(tz=UTC).weekday()
        target = next((d for d in plan.days if d.week_index == week and (d.day_index % 7) == day_of_week), None)
        return target, cycle

    async def log_workout(self, user: User, payload: WorkoutLogInput) -> LogResult:
        total_adjustment = 0.0
        updated = 0
        plan_id = 0
        current_week = 1
        for set_item in payload.sets:
            we = await self.db.get(WorkoutExercise, set_item.workout_exercise_id)
            if we is None:
                raise NotFound(f"Workout exercise {set_item.workout_exercise_id} not found")
            day = await self.db.get(WorkoutDay, we.day_id)
            if day is None:
                raise NotFound("Workout day not found")
            plan = await self.plan_repo.get(day.plan_id)
            if plan is None or plan.user_id != user.id:
                raise NotFound("Workout not found")
            plan_id = plan.id
            current_week = day.week_index

            exercise = await self.exercise_repo.get(we.exercise_id)
            if exercise is None:
                raise NotFound("Exercise not found")

            estimated = self._epley(set_item.completed_weight_kg, set_item.completed_reps)
            volume = round(set_item.completed_weight_kg * set_item.completed_reps, 2)

            self.db.add(SetLog(
                user_id=user.id,
                plan_id=plan.id,
                day_id=day.id,
                workout_exercise_id=we.id,
                exercise_id=exercise.id,
                week_index=day.week_index,
                set_index=set_item.set_index,
                planned_weight_kg=we.weight_kg,
                completed_reps=set_item.completed_reps,
                completed_weight_kg=set_item.completed_weight_kg,
                rir=set_item.rir,
                volume=volume,
                estimated_1rm=estimated,
            ))

            await self.result_repo.upsert(
                user_id=user.id,
                plan_id=plan.id,
                day_id=day.id,
                workout_exercise_id=we.id,
                exercise_id=exercise.id,
                week_index=day.week_index,
                reps_completed=set_item.completed_reps,
                weight_kg=set_item.completed_weight_kg,
                estimated_1rm=estimated,
            )

            adjustment = 0.0
            if set_item.rir > 3:
                adjustment = 0.05 if exercise.category == ExerciseCategory.compound else 0.025
            elif set_item.rir <= 1:
                adjustment = -0.05 if exercise.category == ExerciseCategory.compound else -0.025
            if adjustment != 0:
                await self._apply_future_adjustment(plan.id, day.day_index, exercise.id, adjustment)
            total_adjustment += adjustment
            updated += 1

        await self.db.flush()
        weekly_volume_map = await self.set_log_repo.weekly_volume(user.id, plan_id)
        current_week_volume = float(weekly_volume_map.get(current_week, 0.0))
        prev_week_volume = float(weekly_volume_map.get(max(1, current_week - 1), 0.0))
        if prev_week_volume > 0 and current_week_volume > prev_week_volume * 1.10:
            await self._reduce_remaining_week_volume(plan_id, current_week)

        cycle = await self.cycle_repo.active_for_user(user.id)
        if cycle is not None and cycle.plan_id == plan_id:
            cycle.weekly_volume = {str(k): round(v, 2) for k, v in weekly_volume_map.items()}
            cycle.current_week = min(FOUR_WEEK_CYCLE, max(cycle.current_week, current_week))

        await self.db.commit()
        average_adj = round((total_adjustment / updated) * 100, 2) if updated else 0.0
        return LogResult(updated=updated, next_weight_adjustment_pct=average_adj, weekly_volume=round(current_week_volume, 2))

    async def _apply_future_adjustment(self, plan_id: int, from_day_index: int, exercise_id: int, adjustment: float) -> None:
        stmt = (
            select(WorkoutExercise)
            .join(WorkoutDay, WorkoutDay.id == WorkoutExercise.day_id)
            .where(
                WorkoutDay.plan_id == plan_id,
                WorkoutDay.day_index > from_day_index,
                WorkoutExercise.exercise_id == exercise_id,
                WorkoutExercise.weight_kg.is_not(None),
            )
        )
        rows = await self.db.execute(stmt)
        for row in rows.scalars().all():
            assert row.weight_kg is not None
            row.weight_kg = round_to_plate(max(5.0, row.weight_kg * (1 + adjustment)))

    async def _reduce_remaining_week_volume(self, plan_id: int, week_index: int) -> None:
        stmt = (
            select(WorkoutExercise)
            .join(WorkoutDay, WorkoutDay.id == WorkoutExercise.day_id)
            .where(
                WorkoutDay.plan_id == plan_id,
                WorkoutDay.week_index == week_index,
                WorkoutDay.is_rest.is_(False),
            )
        )
        rows = await self.db.execute(stmt)
        for item in rows.scalars().all():
            if item.sets > 2:
                item.sets -= 1
                item.notes = "Volume cap applied (+10% weekly limit)"

    async def progress(self, user_id: int) -> tuple[dict[str, float], list[ProgressPoint], float]:
        cycle = await self.cycle_repo.active_for_user(user_id)
        if cycle is None:
            raise NotFound("No active mesocycle")
        volume = await self.set_log_repo.weekly_volume(user_id, cycle.plan_id)
        strength_rows = await self.set_log_repo.strength_timeline(user_id)
        strength = [
            ProgressPoint(
                at=row.created_at,
                exercise_id=row.exercise_id,
                estimated_1rm=row.estimated_1rm,
                volume=row.volume,
            )
            for row in strength_rows
        ]
        w1 = float(volume.get(1, 0.0))
        latest_week = max(volume.keys()) if volume else 1
        wl = float(volume.get(latest_week, 0.0))
        delta = 0.0 if w1 <= 0 else round(((wl - w1) / w1) * 100, 2)
        return {str(k): round(v, 2) for k, v in volume.items()}, strength, delta
