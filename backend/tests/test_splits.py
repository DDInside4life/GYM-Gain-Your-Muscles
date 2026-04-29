from __future__ import annotations

from app.models.user import Experience
from app.services.workout.splits import SPLITS, normalize_structure, pick_split


def test_split_keys_present():
    assert "full_body" in SPLITS
    assert "half_split" in SPLITS
    assert "upper_lower" in SPLITS
    assert "split" in SPLITS


def test_pick_split_default_for_beginner():
    assert pick_split(3, Experience.beginner) == "full_body"


def test_pick_split_intermediate_4_days_default_upper_lower():
    assert pick_split(4, Experience.intermediate) == "upper_lower"


def test_pick_split_advanced_5_days_default_split():
    assert pick_split(5, Experience.advanced) == "split"


def test_pick_split_honors_user_choice_when_feasible():
    assert pick_split(4, Experience.intermediate, "split") == "split"
    assert pick_split(3, Experience.intermediate, "half_split") == "half_split"


def test_pick_split_falls_back_when_choice_infeasible():
    assert pick_split(2, Experience.beginner, "split") == "upper_lower"
    assert pick_split(2, Experience.beginner, "half_split") == "full_body"


def test_normalize_structure_aliases():
    assert normalize_structure("PPL") == "split"
    assert normalize_structure("full_body") == "full_body"
    assert normalize_structure("garbage") is None
    assert normalize_structure(None) is None
