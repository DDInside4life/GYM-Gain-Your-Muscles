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
