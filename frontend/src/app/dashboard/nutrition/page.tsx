"use client";

import { useEffect, useMemo, useState } from "react";
import { Plus, Salad, Sparkles } from "lucide-react";
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
    <div className="space-y-6 animate-fade-up">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Salad className="text-emerald-500" size={20} />
            <CardTitle>Сегодня</CardTitle>
          </div>
          <Input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="max-w-[180px]"
          />
        </CardHeader>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
          {[
            { label: "Калории", value: summary?.calories ?? 0, max: targets?.target_calories ?? 4000, color: "#ff4533", unit: "ккал", showPercent: true },
            { label: "Белки", value: summary?.protein ?? 0, max: targets?.protein.grams ?? 300, color: "#a855f7", unit: "г" },
            { label: "Жиры", value: summary?.fat ?? 0, max: targets?.fat.grams ?? 200, color: "#ff8a7c", unit: "г" },
            { label: "Углеводы", value: summary?.carbs ?? 0, max: targets?.carbs.grams ?? 500, color: "#c084fc", unit: "г" },
          ].map((it) => (
            <MacroRing key={it.label} {...it} />
          ))}
        </div>
      </Card>

      <CalorieCalculatorCard
        form={calculatorForm}
        targets={targets}
        loading={targetsLoading}
        error={targetsError}
        onChange={setCalculatorForm}
      />

      <Card>
        <CardHeader>
          <CardTitle>Приёмы пищи</CardTitle>
          <div className="text-xs text-muted">{meals.length} {meals.length === 1 ? "приём" : "приёма"}</div>
        </CardHeader>

        <div className="grid md:grid-cols-[1fr_auto] gap-3 items-end mb-4">
          <div>
            <Label>Название приёма пищи</Label>
            <Input
              value={mealName}
              onChange={(e) => setMealName(e.target.value)}
              placeholder="Завтрак / Обед / Ужин / Перекус"
            />
          </div>
          <div className="flex gap-2">
            <Button onClick={createMeal} disabled={creatingMeal || !mealName.trim()}>
              <Plus size={16} /> {creatingMeal ? "Создаём…" : "Добавить приём"}
            </Button>
            <Button variant="outline">
              <Sparkles size={16} /> Сгенерировать план
            </Button>
          </div>
        </div>

        {error && <p className="mb-3 text-sm text-red-400">{error}</p>}

        {loading ? (
          <p className="text-sm text-muted">Загрузка приёмов пищи…</p>
        ) : meals.length === 0 ? (
          <div className="glass-card p-10 text-center text-muted text-sm">
            На эту дату приёмов пищи нет. Добавьте первый приём.
          </div>
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
  showPercent = false,
}: {
  value: number;
  max: number;
  label: string;
  color: string;
  unit: string;
  showPercent?: boolean;
}) {
  const r = 42;
  const circ = 2 * Math.PI * r;
  const safeMax = max > 0 ? max : 1;
  const progress = Math.min(value / safeMax, 1);
  const offset = circ * (1 - progress);
  const percent = Math.round((value / safeMax) * 100);
  const displayValue = Math.round(value);

  return (
    <div className="glass-card p-4 flex flex-col items-center gap-2 hover-lift">
      <div className="text-xs font-semibold text-muted uppercase tracking-wider">{label}</div>
      <div className="relative">
        <svg width="112" height="112" viewBox="0 0 112 112">
          <circle cx="56" cy="56" r={r} fill="none" stroke="rgba(128,128,128,0.14)" strokeWidth="8" />
          <circle
            cx="56"
            cy="56"
            r={r}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform="rotate(-90 56 56)"
            style={{ filter: `drop-shadow(0 0 6px ${color}80)` }}
          />
          <text x="56" y="52" textAnchor="middle" fontSize="20" fontWeight="800" fill="currentColor" className="display">
            {displayValue}
          </text>
          <text x="56" y="70" textAnchor="middle" fontSize="11" fill="var(--muted)">
            {unit}
          </text>
        </svg>
      </div>
      {showPercent && (
        <span className="text-xs text-muted font-semibold">{percent}%</span>
      )}
    </div>
  );
}
