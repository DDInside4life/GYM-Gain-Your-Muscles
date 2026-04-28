"""Russian explanation builder for generated programs."""
from __future__ import annotations

from app.models.user import Experience, Goal


GOAL_LABEL = {
    Goal.muscle_gain: "масса",
    Goal.fat_loss: "рельеф",
    Goal.strength: "сила",
    Goal.endurance: "выносливость",
    Goal.general: "поддержание",
}


EXPERIENCE_LABEL = {
    Experience.beginner: "новичок",
    Experience.intermediate: "средний уровень",
    Experience.advanced: "продвинутый уровень",
}


def build_explanation(
    *,
    goal: Goal,
    experience: Experience,
    days_per_week: int,
    split_key: str,
    location: str,
    has_previous_results: bool,
) -> list[str]:
    location_ru = "в зале" if location == "gym" else "дома"
    base = [
        f"Программа собрана под цель «{GOAL_LABEL[goal]}», {EXPERIENCE_LABEL[experience]}, "
        f"{days_per_week} тренировки в неделю {location_ru}.",
        f"Сплит: {_split_label(split_key)}. Подобран по частоте тренировок и опыту.",
        "Неделя 1 — тестовая: один рабочий подход с запасом 1–2 повтора.",
        "Недели 2–4 — рабочие: вес считается от 1ПМ, рассчитанного по тесту.",
        "Веса ограничены безопасным диапазоном для вашего опыта.",
        "На каждом упражнении указан целевой RIR и пояснение к интенсивности.",
    ]
    if has_previous_results:
        base.append("Учтены результаты прошлых тестов и логов сетов для уточнения весов.")
    else:
        base.append("Веса в первой неделе предварительные — после теста они будут уточнены.")
    return base


def _split_label(split_key: str) -> str:
    return {
        "full_body": "фулл-боди",
        "upper_lower": "верх/низ",
        "ppl": "тяни/толкай/ноги",
    }.get(split_key, split_key)
