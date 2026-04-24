from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.nutrition import NutritionPlan, PlanMeal
from app.models.user import Goal, Sex, User
from app.schemas.nutrition import NutritionCalculatorActivity, NutritionCalculatorGoal, NutritionInput, NutritionTargetsInput


MEAL_TEMPLATES = [
    ("Breakfast", 0.25, [
        {"name": "Oats", "amount_g": 70},
        {"name": "Eggs", "amount_g": 120},
        {"name": "Berries", "amount_g": 100},
    ]),
    ("Lunch", 0.35, [
        {"name": "Chicken breast", "amount_g": 180},
        {"name": "Rice", "amount_g": 150},
        {"name": "Vegetables", "amount_g": 200},
    ]),
    ("Snack", 0.15, [
        {"name": "Greek yogurt", "amount_g": 200},
        {"name": "Nuts", "amount_g": 30},
    ]),
    ("Dinner", 0.25, [
        {"name": "Salmon", "amount_g": 180},
        {"name": "Potatoes", "amount_g": 200},
        {"name": "Salad", "amount_g": 150},
    ]),
]


class NutritionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def mifflin_st_jeor(weight_kg: float, height_cm: float, age: int, sex: Sex) -> int:
        base = 10 * weight_kg + 6.25 * height_cm - 5 * age
        return int(round(base + (5 if sex == Sex.male else -161)))

    @staticmethod
    def _round(value: float) -> float:
        return round(value, 2)

    @staticmethod
    def activity_factor(activity: NutritionCalculatorActivity) -> float:
        return {
            NutritionCalculatorActivity.sedentary: 1.2,
            NutritionCalculatorActivity.light: 1.375,
            NutritionCalculatorActivity.moderate: 1.55,
            NutritionCalculatorActivity.active: 1.725,
            NutritionCalculatorActivity.very_active: 1.9,
        }[activity]

    @staticmethod
    def goal_multiplier(goal: NutritionCalculatorGoal) -> float:
        return {
            NutritionCalculatorGoal.cut: 0.82,
            NutritionCalculatorGoal.maintain: 1.0,
            NutritionCalculatorGoal.bulk: 1.12,
        }[goal]

    @staticmethod
    def protein_per_kg(goal: NutritionCalculatorGoal) -> float:
        return {
            NutritionCalculatorGoal.cut: 2.2,
            NutritionCalculatorGoal.maintain: 1.8,
            NutritionCalculatorGoal.bulk: 2.0,
        }[goal]

    @staticmethod
    def fat_per_kg(goal: NutritionCalculatorGoal) -> float:
        return {
            NutritionCalculatorGoal.cut: 0.8,
            NutritionCalculatorGoal.maintain: 0.9,
            NutritionCalculatorGoal.bulk: 1.0,
        }[goal]

    @dataclass(slots=True)
    class MacroTarget:
        grams: float
        kcal: float

    @dataclass(slots=True)
    class NutritionTargets:
        bmr: float
        tdee: float
        target_calories: float
        goal: NutritionCalculatorGoal
        protein: "NutritionService.MacroTarget"
        fat: "NutritionService.MacroTarget"
        carbs: "NutritionService.MacroTarget"

    def calculate_targets(self, payload: NutritionTargetsInput) -> "NutritionTargets":
        bmr = float(self.mifflin_st_jeor(payload.weight_kg, payload.height_cm, payload.age, payload.sex))
        tdee = self._round(bmr * self.activity_factor(payload.activity))
        target_calories = self._round(tdee * self.goal_multiplier(payload.goal))

        protein_g = self._round(payload.weight_kg * self.protein_per_kg(payload.goal))
        fat_g = self._round(payload.weight_kg * self.fat_per_kg(payload.goal))
        protein_kcal = self._round(protein_g * 4.0)
        fat_kcal = self._round(fat_g * 9.0)
        carbs_kcal = self._round(max(0.0, target_calories - protein_kcal - fat_kcal))
        carbs_g = self._round(carbs_kcal / 4.0)

        return NutritionService.NutritionTargets(
            bmr=bmr,
            tdee=tdee,
            target_calories=target_calories,
            goal=payload.goal,
            protein=NutritionService.MacroTarget(grams=protein_g, kcal=protein_kcal),
            fat=NutritionService.MacroTarget(grams=fat_g, kcal=fat_kcal),
            carbs=NutritionService.MacroTarget(grams=carbs_g, kcal=carbs_kcal),
        )

    @staticmethod
    def macro_split(calories: int, goal: Goal, weight_kg: float) -> tuple[int, int, int]:
        protein_per_kg = {
            Goal.muscle_gain: 2.0, Goal.fat_loss: 2.2, Goal.strength: 2.0,
            Goal.endurance: 1.6, Goal.general: 1.8,
        }[goal]
        fat_ratio = {
            Goal.muscle_gain: 0.25, Goal.fat_loss: 0.30, Goal.strength: 0.30,
            Goal.endurance: 0.25, Goal.general: 0.30,
        }[goal]
        protein_g = int(round(protein_per_kg * weight_kg))
        fat_g = int(round((calories * fat_ratio) / 9))
        carbs_cal = max(0, calories - (protein_g * 4 + fat_g * 9))
        carbs_g = int(round(carbs_cal / 4))
        return protein_g, fat_g, carbs_g

    @staticmethod
    def adjust_for_goal(tdee: int, goal: Goal) -> tuple[int, str]:
        delta_map = {
            Goal.muscle_gain: (+300, "lean_bulk"),
            Goal.fat_loss: (-450, "cut"),
            Goal.strength: (+150, "performance"),
            Goal.endurance: (+100, "endurance"),
            Goal.general: (0, "maintenance"),
        }
        delta, label = delta_map[goal]
        return tdee + delta, label

    async def generate_for(self, user: User, payload: NutritionInput) -> NutritionPlan:
        bmr = self.mifflin_st_jeor(payload.weight_kg, payload.height_cm, payload.age, payload.sex)
        tdee = int(round(bmr * payload.activity_factor))
        calories, label = self.adjust_for_goal(tdee, payload.goal)
        protein_g, fat_g, carbs_g = self.macro_split(calories, payload.goal, payload.weight_kg)

        plan = NutritionPlan(
            user_id=user.id,
            calories=calories, protein_g=protein_g, fat_g=fat_g, carbs_g=carbs_g,
            bmr=bmr, tdee=tdee, goal_label=label,
        )
        self.db.add(plan)
        await self.db.flush()

        for idx, (title, ratio, items) in enumerate(MEAL_TEMPLATES):
            self.db.add(PlanMeal(
                plan_id=plan.id,
                position=idx,
                title=title,
                calories=int(calories * ratio),
                protein_g=round(protein_g * ratio, 1),
                fat_g=round(fat_g * ratio, 1),
                carbs_g=round(carbs_g * ratio, 1),
                items=items,
            ))
        await self.db.commit()
        await self.db.refresh(plan, ["meals"])
        return plan
