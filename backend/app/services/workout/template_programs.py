from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agents.config import ai_settings
from app.core.exceptions import NotFound
from app.models.exercise import Equipment, ExerciseCategory
from app.models.user import Experience, Goal, User
from app.models.workout import ProgramPhase, WorkoutDay, WorkoutExercise, WorkoutPlan
from app.repositories.template import WorkoutTemplateRepository
from app.repositories.workout import WorkoutPlanRepository, WorkoutResultRepository
from app.schemas.template import TemplateGenerateWorkoutInput
from app.services.workout.rules import round_to_plate

EXPERIENCE_SCALE: dict[Experience, float] = {
    Experience.beginner: 0.9,
    Experience.intermediate: 1.0,
    Experience.advanced: 1.1,
}

GOAL_PERCENT: dict[Goal, float] = {
    Goal.strength: 0.82,
    Goal.muscle_gain: 0.72,
    Goal.fat_loss: 0.65,
    Goal.endurance: 0.6,
    Goal.general: 0.68,
}


class TemplateProgramService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.templates = WorkoutTemplateRepository(db)
        self.plans = WorkoutPlanRepository(db)
        self.results = WorkoutResultRepository(db)

    async def list_templates(self):
        return await self.templates.list_active()

    async def apply_template(self, user: User, template_id: int, *, ai_adapt: bool = False) -> tuple[WorkoutPlan, str]:
        template = await self.templates.get_with_days(template_id)
        if template is None:
            raise NotFound("Template not found")

        prev = await self.plans.latest_for_user(user.id)
        next_month = (prev.month_index + 1) if prev else 1
        next_week = (prev.week_number + 1) if prev else 1
        await self.plans.deactivate_all(user.id)

        experience = user.experience or Experience.intermediate
        goal = user.goal or Goal.general

        source = "template_rules"
        if ai_adapt and ai_settings.is_ready:
            source = "template_ai_adapted"

        plan = WorkoutPlan(
            user_id=user.id,
            name=f"{template.name} · Month {next_month}",
            week_number=next_week,
            month_index=next_month,
            cycle_week=1,
            phase=ProgramPhase.work,
            split_type=template.split_type,
            is_active=True,
            params={
                "template_id": template.id,
                "template_slug": template.slug,
                "template_level": template.level,
                "source": source,
                "goal": goal.value,
                "experience": experience.value,
                "days_per_week": template.days_per_week,
            },
        )
        self.db.add(plan)
        await self.db.flush()

        for day in template.days:
            row = WorkoutDay(
                plan_id=plan.id,
                day_index=day.day_index,
                title=day.title,
                focus=day.focus,
                is_rest=day.is_rest,
                week_index=1,
                phase=ProgramPhase.work,
            )
            self.db.add(row)
            await self.db.flush()
            if day.is_rest:
                continue

            for item in day.exercises:
                sets = self._adjust_sets(item.sets, experience, ai_adapt)
                reps_min, reps_max = self._adjust_reps(item.reps_min, item.reps_max, goal, ai_adapt)
                weight = await self._estimate_working_weight(
                    user=user,
                    exercise_id=item.exercise_id,
                    fallback_percent=item.target_percent_1rm or GOAL_PERCENT[goal],
                    experience=experience,
                )
                self.db.add(WorkoutExercise(
                    day_id=row.id,
                    exercise_id=item.exercise_id,
                    position=item.position,
                    sets=sets,
                    reps_min=reps_min,
                    reps_max=reps_max,
                    weight_kg=weight,
                    rest_sec=item.rest_sec,
                    notes=item.notes,
                    target_percent_1rm=item.target_percent_1rm or GOAL_PERCENT[goal],
                    is_test_set=False,
                    test_instruction="",
                ))

        await self.db.commit()
        fresh = await self.plans.get_with_days(plan.id)
        assert fresh is not None
        return fresh, source

    async def generate_from_template(
        self,
        user: User,
        payload: TemplateGenerateWorkoutInput,
    ) -> tuple[WorkoutPlan, str]:
        return await self.apply_template(user, payload.template_id, ai_adapt=payload.ai_adapt)

    @staticmethod
    def _adjust_sets(sets: int, experience: Experience, ai_adapt: bool) -> int:
        scale = EXPERIENCE_SCALE[experience]
        if ai_adapt:
            scale += 0.05 if experience == Experience.advanced else 0.0
        return max(2, min(6, round(sets * scale)))

    @staticmethod
    def _adjust_reps(reps_min: int, reps_max: int, goal: Goal, ai_adapt: bool) -> tuple[int, int]:
        if goal == Goal.strength:
            return max(3, reps_min - 2), max(5, reps_max - 3)
        if goal == Goal.endurance:
            return min(20, reps_min + 3), min(25, reps_max + 4)
        if ai_adapt and goal == Goal.muscle_gain:
            return max(6, reps_min), min(15, reps_max + 1)
        return reps_min, reps_max

    async def _estimate_working_weight(
        self,
        *,
        user: User,
        exercise_id: int,
        fallback_percent: float,
        experience: Experience,
    ) -> float | None:
        latest = await self.results.by_exercise_latest(user.id, exercise_id)
        if latest is not None:
            return round_to_plate(latest.estimated_1rm * fallback_percent)

        from app.repositories.exercise import ExerciseRepository

        exercise = await ExerciseRepository(self.db).get(exercise_id)
        if exercise is None:
            return None
        if exercise.equipment == Equipment.bodyweight or exercise.category == ExerciseCategory.cardio:
            return None
        base = float(user.weight_kg or 75.0)
        mult = 0.55 if experience == Experience.beginner else (0.65 if experience == Experience.intermediate else 0.75)
        return round_to_plate(base * mult * fallback_percent)
