"""Unit tests for the template picker — pure scoring, no DB."""
from __future__ import annotations

from dataclasses import dataclass

from app.models.user import Goal
from app.services.workout.template_programs import (
    TemplatePicker,
    TemplateSelectionCriteria,
    normalize_structure,
    resolve_total_weeks,
)


@dataclass
class FakeTemplate:
    id: int
    slug: str
    split_type: str
    days_per_week: int
    is_active: bool = True


def _seed() -> list[FakeTemplate]:
    return [
        FakeTemplate(1, "full-body-3", "full_body", 3),
        FakeTemplate(2, "upper-lower-4", "upper_lower", 4),
        FakeTemplate(3, "push-pull-legs-6", "ppl", 6),
        FakeTemplate(4, "strength-3-4", "strength", 3),
        FakeTemplate(5, "hypertrophy-5", "hypertrophy", 5),
    ]


def test_normalize_structure_aliases() -> None:
    assert normalize_structure("Split") == "ppl"
    assert normalize_structure("push_pull_legs") == "ppl"
    assert normalize_structure("Half_Split") == "upper_lower"
    assert normalize_structure("FULL_BODY") == "full_body"
    assert normalize_structure(None) is None
    assert normalize_structure("nonsense") is None


def test_resolve_total_weeks_clamps() -> None:
    assert resolve_total_weeks(None) == 4
    assert resolve_total_weeks(0) == 1
    assert resolve_total_weeks(99) == 12
    assert resolve_total_weeks("garbage") == 4
    assert resolve_total_weeks(6) == 6


def test_picker_prefers_matching_structure_over_days() -> None:
    picker = TemplatePicker(_seed())
    chosen = picker.best(TemplateSelectionCriteria(
        goal=Goal.muscle_gain, days_per_week=4, training_structure="upper_lower",
    ))
    assert chosen is not None and chosen.slug == "upper-lower-4"


def test_picker_falls_back_to_goal_when_structure_missing() -> None:
    picker = TemplatePicker(_seed())
    chosen = picker.best(TemplateSelectionCriteria(
        goal=Goal.muscle_gain, days_per_week=5, training_structure=None,
    ))
    assert chosen is not None and chosen.slug == "hypertrophy-5"


def test_picker_strength_goal_picks_strength_template() -> None:
    picker = TemplatePicker(_seed())
    chosen = picker.best(TemplateSelectionCriteria(
        goal=Goal.strength, days_per_week=3, training_structure=None,
    ))
    assert chosen is not None and chosen.slug == "strength-3-4"


def test_picker_full_body_for_general_goal() -> None:
    picker = TemplatePicker(_seed())
    chosen = picker.best(TemplateSelectionCriteria(
        goal=Goal.general, days_per_week=3,
    ))
    assert chosen is not None and chosen.slug == "full-body-3"


def test_picker_split_alias_picks_ppl() -> None:
    picker = TemplatePicker(_seed())
    chosen = picker.best(TemplateSelectionCriteria(
        goal=Goal.muscle_gain, days_per_week=6, training_structure="split",
    ))
    assert chosen is not None and chosen.slug == "push-pull-legs-6"


def test_picker_returns_none_when_no_templates() -> None:
    picker = TemplatePicker([])
    assert picker.best(TemplateSelectionCriteria(goal=Goal.general)) is None


def test_picker_inactive_templates_ignored() -> None:
    pool = _seed()
    pool[1].is_active = False
    picker = TemplatePicker(pool)
    chosen = picker.best(TemplateSelectionCriteria(
        days_per_week=4, training_structure="upper_lower",
    ))
    assert chosen is not None
    assert chosen.slug != "upper-lower-4"


def test_picker_picks_closest_days_when_no_structure_or_goal() -> None:
    picker = TemplatePicker(_seed())
    chosen = picker.best(TemplateSelectionCriteria(days_per_week=5))
    assert chosen is not None and chosen.days_per_week == 5
