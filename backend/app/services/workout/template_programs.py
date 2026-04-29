"""Template-based 4-week workout plans (no auto-weight, Russian copy).

Pipeline:

    selection criteria  ──▶  pick best template  ──▶  filter by equipment+injuries
                                                       ──▶  clone N weeks  ──▶  persist plan
                                                            │
                                                            └─ weight_kg=None on every exercise
                                                               (user fills working weight by hand)

Selection prefers templates that match the requested ``training_structure`` and is
closest to ``days_per_week``. The score is intentionally tiny and explicit to keep
the picker easy to reason about.

Equipment / injury filtering is applied while materializing the plan: any
exercise from the chosen template whose equipment is not in the user's
``equipment`` set, or whose contraindications collide with the user's
``injuries``, is silently dropped. If a day ends up empty after filtering it is
materialized as a rest day.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound
from app.models.exercise import Equipment, Exercise
from app.models.user import Goal, User
from app.models.workout import ProgramPhase, WorkoutDay, WorkoutExercise, WorkoutPlan
from app.models.workout_template import WorkoutTemplate
from app.repositories.template import WorkoutTemplateRepository
from app.repositories.workout import WorkoutPlanRepository
from app.schemas.template import TemplateGenerateWorkoutInput
from app.services.workout.filtering import resolve_contraindications

DEFAULT_WEEKS = 4
MIN_WEEKS = 1
MAX_WEEKS = 12

GOAL_TO_STRUCTURE: dict[Goal, str] = {
    Goal.strength:    "strength",
    Goal.muscle_gain: "hypertrophy",
    Goal.fat_loss:    "full_body",
    Goal.endurance:   "full_body",
    Goal.general:     "full_body",
}

STRUCTURE_ALIASES: dict[str, str] = {
    "split":          "ppl",
    "push_pull_legs": "ppl",
    "ppl":            "ppl",
    "full_body":      "full_body",
    "upper_lower":    "upper_lower",
    "half_split":     "upper_lower",
    "strength":       "strength",
    "hypertrophy":    "hypertrophy",
}


@dataclass(slots=True)
class TemplateSelectionCriteria:
    goal: Goal | None = None
    days_per_week: int | None = None
    training_structure: str | None = None
    equipment: frozenset[Equipment] = frozenset()
    injuries: tuple[str, ...] = ()


def _parse_equipment(values: Iterable[str] | None) -> frozenset[Equipment]:
    if not values:
        return frozenset()
    parsed: set[Equipment] = set()
    for raw in values:
        key = (str(raw) or "").strip().lower()
        if key in Equipment._value2member_map_:
            parsed.add(Equipment(key))
    return frozenset(parsed)


def _is_exercise_allowed(
    exercise: Exercise,
    *,
    equipment: frozenset[Equipment],
    contraindications: frozenset[str],
) -> bool:
    if not exercise.is_active:
        return False
    if equipment and exercise.equipment not in equipment:
        return False
    if contraindications and (contraindications & set(exercise.contraindications or [])):
        return False
    return True


def normalize_structure(value: str | None) -> str | None:
    if not value:
        return None
    return STRUCTURE_ALIASES.get(value.strip().lower())


def resolve_total_weeks(value: int | None) -> int:
    if value is None:
        return DEFAULT_WEEKS
    try:
        weeks = int(value)
    except (TypeError, ValueError):
        return DEFAULT_WEEKS
    return max(MIN_WEEKS, min(MAX_WEEKS, weeks))


class TemplatePicker:
    """Pure scoring of templates against selection criteria."""

    def __init__(self, templates: Iterable[WorkoutTemplate]) -> None:
        self._templates = [t for t in templates if t.is_active]

    def best(self, criteria: TemplateSelectionCriteria) -> WorkoutTemplate | None:
        if not self._templates:
            return None
        target_structure = normalize_structure(criteria.training_structure)
        if target_structure is None and criteria.goal is not None:
            target_structure = GOAL_TO_STRUCTURE.get(criteria.goal)
        target_days = criteria.days_per_week

        scored: list[tuple[float, int, WorkoutTemplate]] = []
        for template in self._templates:
            score = 0.0
            if target_structure and template.split_type == target_structure:
                score -= 100.0
            if target_days is not None:
                score += abs(template.days_per_week - target_days) * 5.0
            scored.append((score, template.id, template))
        scored.sort(key=lambda row: (row[0], row[1]))
        return scored[0][2]


class TemplateProgramService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.templates = WorkoutTemplateRepository(db)
        self.plans = WorkoutPlanRepository(db)

    async def list_templates(self) -> list[WorkoutTemplate]:
        return await self.templates.list_active()

    async def pick_template(self, criteria: TemplateSelectionCriteria) -> WorkoutTemplate:
        templates = await self.templates.list_active()
        picker = TemplatePicker(templates)
        chosen = picker.best(criteria)
        if chosen is None:
            raise NotFound("Шаблоны программ не найдены")
        return chosen

    async def apply_template(
        self,
        user: User,
        template_id: int,
        *,
        weeks: int | None = None,
        criteria: TemplateSelectionCriteria | None = None,
    ) -> tuple[WorkoutPlan, str]:
        template = await self.templates.get_with_days(template_id)
        if template is None:
            raise NotFound("Шаблон программы не найден")
        return await self._materialize(user, template, weeks=weeks, criteria=criteria)

    async def generate_for_criteria(
        self,
        user: User,
        criteria: TemplateSelectionCriteria,
        *,
        weeks: int | None = None,
    ) -> tuple[WorkoutPlan, str]:
        template = await self.pick_template(criteria)
        return await self._materialize(user, template, weeks=weeks, criteria=criteria)

    async def generate_from_template(
        self,
        user: User,
        payload: TemplateGenerateWorkoutInput,
    ) -> tuple[WorkoutPlan, str]:
        return await self.apply_template(user, payload.template_id)


def criteria_from(
    *,
    goal: str | Goal | None = None,
    days_per_week: int | None = None,
    training_structure: str | None = None,
    equipment: Iterable[str] | None = None,
    injuries: Iterable[str] | None = None,
) -> TemplateSelectionCriteria:
    parsed_goal: Goal | None
    if isinstance(goal, Goal):
        parsed_goal = goal
    elif isinstance(goal, str) and goal.strip():
        try:
            parsed_goal = Goal(goal.strip().lower())
        except ValueError:
            parsed_goal = None
    else:
        parsed_goal = None
    return TemplateSelectionCriteria(
        goal=parsed_goal,
        days_per_week=days_per_week,
        training_structure=training_structure,
        equipment=_parse_equipment(equipment),
        injuries=tuple(
            (str(i) or "").strip().lower()
            for i in (injuries or ())
            if str(i).strip()
        ),
    )

    async def _materialize(
        self,
        user: User,
        template: WorkoutTemplate,
        *,
        weeks: int | None,
        criteria: TemplateSelectionCriteria | None,
    ) -> tuple[WorkoutPlan, str]:
        total_weeks = resolve_total_weeks(weeks)
        prev = await self.plans.latest_for_user(user.id)
        next_month = (prev.month_index + 1) if prev else 1
        await self.plans.deactivate_all(user.id)

        equipment = criteria.equipment if criteria else frozenset()
        contraindications = (
            resolve_contraindications(criteria.injuries) if criteria else frozenset()
        )

        params: dict[str, object] = {
            "template_id": template.id,
            "template_slug": template.slug,
            "template_level": template.level,
            "source": "template",
            "days_per_week": template.days_per_week,
            "cycle_length_weeks": total_weeks,
        }
        if criteria is not None:
            if criteria.goal is not None:
                params["goal"] = criteria.goal.value
            if criteria.training_structure is not None:
                params["training_structure"] = criteria.training_structure
            if criteria.days_per_week is not None:
                params["requested_days_per_week"] = criteria.days_per_week
            if equipment:
                params["equipment"] = sorted(eq.value for eq in equipment)
            if criteria.injuries:
                params["injuries"] = sorted(set(criteria.injuries))

        plan = WorkoutPlan(
            user_id=user.id,
            name=f"Месяц {next_month} · {template.name}",
            week_number=(prev.week_number + total_weeks) if prev else total_weeks,
            month_index=next_month,
            cycle_week=1,
            phase=ProgramPhase.work,
            split_type=template.split_type,
            is_active=True,
            params=params,
        )
        self.db.add(plan)
        await self.db.flush()

        for week_index in range(1, total_weeks + 1):
            for tmpl_day in template.days:
                allowed_items = (
                    []
                    if tmpl_day.is_rest
                    else [
                        item
                        for item in tmpl_day.exercises
                        if _is_exercise_allowed(
                            item.exercise,
                            equipment=equipment,
                            contraindications=contraindications,
                        )
                    ]
                )
                day = WorkoutDay(
                    plan_id=plan.id,
                    day_index=(week_index - 1) * len(template.days) + tmpl_day.day_index,
                    title=tmpl_day.title,
                    focus=tmpl_day.focus,
                    is_rest=tmpl_day.is_rest or not allowed_items,
                    week_index=week_index,
                    phase=ProgramPhase.work,
                )
                self.db.add(day)
                await self.db.flush()
                for position, item in enumerate(allowed_items):
                    self.db.add(WorkoutExercise(
                        day_id=day.id,
                        exercise_id=item.exercise_id,
                        position=position,
                        sets=item.sets,
                        reps_min=item.reps_min,
                        reps_max=item.reps_max,
                        weight_kg=None,
                        rest_sec=item.rest_sec,
                        notes=item.notes,
                        target_percent_1rm=None,
                        is_test_set=False,
                        test_instruction="",
                        target_rir=None,
                        rpe_text="",
                    ))

        await self.db.commit()
        fresh = await self.plans.get_with_days(plan.id)
        assert fresh is not None
        return fresh, "template"
