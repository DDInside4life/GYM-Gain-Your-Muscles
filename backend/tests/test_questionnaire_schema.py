from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.questionnaire import WorkoutQuestionnaireInput


def _payload(**overrides) -> dict:
    base = {
        "sex": "male",
        "age": 28,
        "height_cm": 178,
        "weight_kg": 78,
        "experience": "intermediate",
        "goal": "muscle_gain",
        "location": "gym",
        "equipment": ["BARBELL", "Dumbbell", "machine", " "],
        "injuries": ["Knee", " "],
        "days_per_week": 4,
        "available_days": ["MONDAY", "wed", "FRI", "Sun", "INVALID"],
        "notes": "",
    }
    base.update(overrides)
    return base


def test_questionnaire_normalizes_lists():
    model = WorkoutQuestionnaireInput.model_validate(_payload())
    assert "barbell" in model.equipment
    assert "dumbbell" in model.equipment
    assert "" not in model.equipment
    assert model.injuries == ["knee"]
    assert model.available_days == ["mon", "wed", "fri", "sun"]


def test_questionnaire_rejects_age_out_of_range():
    with pytest.raises(ValidationError):
        WorkoutQuestionnaireInput.model_validate(_payload(age=8))
    with pytest.raises(ValidationError):
        WorkoutQuestionnaireInput.model_validate(_payload(age=120))


def test_questionnaire_rejects_invalid_location():
    with pytest.raises(ValidationError):
        WorkoutQuestionnaireInput.model_validate(_payload(location="park"))


def test_questionnaire_rejects_too_few_days():
    with pytest.raises(ValidationError):
        WorkoutQuestionnaireInput.model_validate(_payload(days_per_week=1))


def test_questionnaire_rejects_extreme_weight():
    with pytest.raises(ValidationError):
        WorkoutQuestionnaireInput.model_validate(_payload(weight_kg=400))


def test_questionnaire_normalizes_session_duration():
    model = WorkoutQuestionnaireInput.model_validate(_payload(session_duration_min=70))
    assert model.session_duration_min in {60, 90}


def test_questionnaire_accepts_periodization_and_structure():
    model = WorkoutQuestionnaireInput.model_validate(_payload(
        periodization="dup",
        training_structure="upper_lower",
        cycle_length_weeks=6,
        priority_exercise_ids=[1, 2, 2, "3", -4, "abc"],
    ))
    assert model.periodization == "dup"
    assert model.training_structure == "upper_lower"
    assert model.cycle_length_weeks == 6
    assert model.priority_exercise_ids == [1, 2, 3]


def test_questionnaire_defaults_when_optional_missing():
    model = WorkoutQuestionnaireInput.model_validate(_payload())
    assert model.session_duration_min is None
    assert model.training_structure is None
    assert model.periodization is None
    assert model.cycle_length_weeks is None
    assert model.priority_exercise_ids == []


def test_questionnaire_rejects_invalid_cycle_length():
    with pytest.raises(ValidationError):
        WorkoutQuestionnaireInput.model_validate(_payload(cycle_length_weeks=2))
    with pytest.raises(ValidationError):
        WorkoutQuestionnaireInput.model_validate(_payload(cycle_length_weeks=20))
