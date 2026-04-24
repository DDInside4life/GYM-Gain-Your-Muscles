"use client";

import { useEffect, useMemo, useState } from "react";
import { Plus, Salad } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label } from "@/components/ui/input";
import { nutritionApi } from "@/features/nutrition/api";
import { CalorieCalculatorCard } from "@/features/nutrition/calorie-calculator";
import { MealCard } from "@/features/nutrition/meal-card";
import type { CalculatorFormState } from "@/features/nutrition/calorie-calculator";
import type { FoodDraft, Meal, NutritionDailySummary, NutritionTargets } from "@/features/nutrition/types";
import { parseNonNegativeNumber, parsePositiveNumber } from "@/features/nutrition/utils";

const emptyFoodDraft: FoodDraft = {
  name: "",
  protein_per_100g: "",
  fat_per_100g: "",
  carbs_per_100g: "",
  grams: "",
};

export default function NutritionPage() {
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);
  const [selectedDate, setSelectedDate] = useState(today);
  const [summary, setSummary] = useState<NutritionDailySummary | null>(null);
  const [meals, setMeals] = useState<Meal[]>([]);
  const [mealName, setMealName] = useState("");
  const [foodDrafts, setFoodDrafts] = useState<Record<number, FoodDraft>>({});
  const [mealFormErrors, setMealFormErrors] = useState<Record<number, string | null>>({});
  const [expandedMeals, setExpandedMeals] = useState<Record<number, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [creatingMeal, setCreatingMeal] = useState(false);
  const [addingFoodMealId, setAddingFoodMealId] = useState<number | null>(null);
  const [deletingFoodId, setDeletingFoodId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [targets, setTargets] = useState<NutritionTargets | null>(null);
  const [targetsLoading, setTargetsLoading] = useState(false);
  const [targetsError, setTargetsError] = useState<string | null>(null);
  const [calculatorForm, setCalculatorForm] = useState<CalculatorFormState>({
    sex: "male",
    age: "28",
    weight_kg: "75",
    height_cm: "175",
    activity: "moderate",
    goal: "maintain",
  });

  function setMealDraft(mealId: number, updater: (current: FoodDraft) => FoodDraft) {
    setFoodDrafts((prev) => {
      const current = prev[mealId] ?? emptyFoodDraft;
      return { ...prev, [mealId]: updater(current) };
    });
  }

  async function loadData(date: string) {
    setLoading(true);
    setError(null);
    try {
      const [loadedMeals, loadedSummary] = await Promise.all([
        nutritionApi.getMealsByDate(date),
        nutritionApi.getDailySummary(date),
      ]);
      setMeals(loadedMeals);
      setSummary(loadedSummary);
      setExpandedMeals((prev) =>
        loadedMeals.reduce<Record<number, boolean>>((acc, meal) => {
          acc[meal.id] = prev[meal.id] ?? true;
          return acc;
        }, {}),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить данные питания.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData(selectedDate);
  }, [selectedDate]);

  useEffect(() => {
    const age = parsePositiveNumber(calculatorForm.age);
    const weight = parsePositiveNumber(calculatorForm.weight_kg);
    const height = parsePositiveNumber(calculatorForm.height_cm);
    if (!age || !weight || !height) {
      setTargets(null);
      setTargetsError("Введите корректные данные для расчета.");
      return;
    }

    const timeout = window.setTimeout(async () => {
      setTargetsLoading(true);
      setTargetsError(null);
      try {
        const result = await nutritionApi.calculateTargets({
          sex: calculatorForm.sex,
          age,
          weight_kg: weight,
          height_cm: height,
          activity: calculatorForm.activity,
          goal: calculatorForm.goal,
        });
        setTargets(result);
      } catch (e) {
        setTargetsError(e instanceof Error ? e.message : "Не удалось рассчитать цели.");
      } finally {
        setTargetsLoading(false);
      }
    }, 250);

    return () => window.clearTimeout(timeout);
  }, [calculatorForm]);

  async function refreshSummary() {
    const freshSummary = await nutritionApi.getDailySummary(selectedDate);
    setSummary(freshSummary);
  }

  async function createMeal() {
    if (!mealName.trim()) return;
    setCreatingMeal(true);
    setError(null);
    try {
      const created = await nutritionApi.createMeal({
        date: selectedDate,
        name: mealName.trim(),
      });
      setMeals((prev) => [...prev, created]);
      setMealName("");
      setExpandedMeals((prev) => ({ ...prev, [created.id]: true }));
      await refreshSummary();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать прием пищи.");
    } finally {
      setCreatingMeal(false);
    }
  }

  async function addFood(mealId: number) {
    const draft = foodDrafts[mealId] ?? emptyFoodDraft;
    const protein = parseNonNegativeNumber(draft.protein_per_100g);
    const fat = parseNonNegativeNumber(draft.fat_per_100g);
    const carbs = parseNonNegativeNumber(draft.carbs_per_100g);
    const grams = parsePositiveNumber(draft.grams);

    if (!draft.name.trim()) {
      setMealFormErrors((prev) => ({ ...prev, [mealId]: "Введите название блюда." }));
      return;
    }
    if (protein === null || fat === null || carbs === null || grams === null) {
      setMealFormErrors((prev) => ({ ...prev, [mealId]: "Укажите корректные неотрицательные значения. Граммы должны быть больше 0." }));
      return;
    }

    setAddingFoodMealId(mealId);
    setError(null);
    setMealFormErrors((prev) => ({ ...prev, [mealId]: null }));
    try {
      await nutritionApi.createFoodEntry({
        meal_id: mealId,
        name: draft.name.trim(),
        protein_per_100g: protein,
        fat_per_100g: fat,
        carbs_per_100g: carbs,
        grams,
      });
      setFoodDrafts((prev) => ({ ...prev, [mealId]: emptyFoodDraft }));
      await loadData(selectedDate);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось добавить блюдо.");
    } finally {
      setAddingFoodMealId(null);
    }
  }

  async function deleteFood(entryId: number) {
    setDeletingFoodId(entryId);
    setError(null);
    try {
      await nutritionApi.deleteFoodEntry(entryId);
      await loadData(selectedDate);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось удалить блюдо.");
    } finally {
      setDeletingFoodId(null);
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Питание</CardTitle>
          <Salad className="text-emerald-500" />
        </CardHeader>
        <div className="grid md:grid-cols-[220px_1fr_auto] gap-3 items-end">
          <div>
            <Label>Дата</Label>
            <Input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} />
          </div>
          <div>
            <Label>Прием пищи</Label>
            <Input
              value={mealName}
              onChange={(e) => setMealName(e.target.value)}
              placeholder="Завтрак / Обед / Ужин / Перекус"
            />
          </div>
          <Button onClick={createMeal} disabled={creatingMeal || !mealName.trim()} variant="glass">
            <Plus size={16} /> {creatingMeal ? "Создаем..." : "Добавить прием пищи"}
          </Button>
        </div>
        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
      </Card>

      <CalorieCalculatorCard
        form={calculatorForm}
        targets={targets}
        loading={targetsLoading}
        error={targetsError}
        onChange={setCalculatorForm}
      />

      <Card>
        <CardHeader><CardTitle>Сводка за день</CardTitle></CardHeader>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 justify-items-center py-2">
          {[
            { label: "Калории", value: summary?.calories ?? 0, max: targets?.target_calories ?? 4000, color: "#ff4533", unit: "ккал" },
            { label: "Белки", value: summary?.protein ?? 0, max: targets?.protein.grams ?? 300, color: "#8b5cf6", unit: "г" },
            { label: "Жиры", value: summary?.fat ?? 0, max: targets?.fat.grams ?? 200, color: "#ff5f4c", unit: "г" },
            { label: "Углеводы", value: summary?.carbs ?? 0, max: targets?.carbs.grams ?? 500, color: "#a78bfa", unit: "г" },
          ].map((it) => (
            <MacroRing key={it.label} {...it} />
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader><CardTitle>Приемы пищи</CardTitle></CardHeader>
        {loading ? (
          <p className="text-sm text-muted">Загрузка приемов пищи...</p>
        ) : meals.length === 0 ? (
          <p className="text-sm text-muted">На эту дату приемов пищи нет.</p>
        ) : (
          <div className="space-y-3">
            {meals.map((meal) => (
              <MealCard
                key={meal.id}
                meal={meal}
                draft={foodDrafts[meal.id] ?? emptyFoodDraft}
                isExpanded={expandedMeals[meal.id] ?? true}
                isSubmitting={addingFoodMealId === meal.id}
                deletingFoodId={deletingFoodId}
                formError={mealFormErrors[meal.id] ?? null}
                onToggle={() => setExpandedMeals((prev) => ({ ...prev, [meal.id]: !(prev[meal.id] ?? true) }))}
                onChangeDraft={(updater) => setMealDraft(meal.id, updater)}
                onSubmitFood={() => addFood(meal.id)}
                onDeleteFood={deleteFood}
              />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function MacroRing({
  value,
  max,
  label,
  color,
  unit,
}: {
  value: number;
  max: number;
  label: string;
  color: string;
  unit: string;
}) {
  const r = 38;
  const circ = 2 * Math.PI * r;
  const safeMax = max > 0 ? max : 1;
  const progress = Math.min(value / safeMax, 1);
  const offset = circ * (1 - progress);
  const percent = Math.round((value / safeMax) * 100);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative">
        <svg width="96" height="96" viewBox="0 0 96 96">
          <circle cx="48" cy="48" r={r} fill="none" stroke="rgba(128,128,128,0.12)" strokeWidth="7" />
          <circle
            cx="48" cy="48" r={r}
            fill="none"
            stroke={color}
            strokeWidth="7"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform="rotate(-90 48 48)"
          />
          <text x="48" y="44" textAnchor="middle" fontSize="15" fontWeight="bold" fill="currentColor">
            {value}
          </text>
          <text x="48" y="60" textAnchor="middle" fontSize="10" fill="var(--muted)">
            {unit}
          </text>
        </svg>
      </div>
      <span className="text-xs text-muted font-medium">{label} ({percent}%)</span>
    </div>
  );
}
