"use client";

import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Select } from "@/components/ui/input";
import type { NutritionCalculatorActivity, NutritionCalculatorGoal, NutritionCalculatorSex, NutritionTargets } from "./types";
import { sanitizeNonNegativeNumericInput } from "./utils";

export type CalculatorFormState = {
  sex: NutritionCalculatorSex;
  age: string;
  weight_kg: string;
  height_cm: string;
  activity: NutritionCalculatorActivity;
  goal: NutritionCalculatorGoal;
};

type CalorieCardProps = { title: string; value: number; tone: "base" | "cut" | "bulk"; suffix?: string };

function CalorieCard({ title, value, tone, suffix = "ккал" }: CalorieCardProps) {
  const toneClass =
    tone === "cut"
      ? "text-red-500 dark:text-red-400"
      : tone === "bulk"
        ? "text-emerald-500 dark:text-emerald-400"
        : "text-violet-500 dark:text-violet-300";
  return (
    <div className="rounded-xl border border-[var(--border)] bg-white/40 dark:bg-white/[0.03] p-3">
      <p className="text-xs text-muted">{title}</p>
      <p className={`display text-xl font-extrabold mt-1 ${toneClass}`}>
        {value} <span className="text-xs font-medium opacity-70">{suffix}</span>
      </p>
    </div>
  );
}

type Props = {
  form: CalculatorFormState;
  targets: NutritionTargets | null;
  loading: boolean;
  error: string | null;
  onChange: (next: CalculatorFormState) => void;
};

export function CalorieCalculatorCard({ form, targets, loading, error, onChange }: Props) {
  function updateNumericField(field: "age" | "weight_kg" | "height_cm", raw: string) {
    const next = sanitizeNonNegativeNumericInput(raw, true);
    if (next === null) return;
    onChange({ ...form, [field]: next });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Калькулятор калорий и БЖУ</CardTitle>
        <span className="text-xs text-muted">{loading ? "Пересчёт…" : "Авто-расчёт"}</span>
      </CardHeader>
      <div className="grid gap-3 md:grid-cols-5">
        <div>
          <Label>Пол</Label>
          <Select value={form.sex} onChange={(e) => onChange({ ...form, sex: e.target.value as NutritionCalculatorSex })}>
            <option value="male">Мужской</option>
            <option value="female">Женский</option>
          </Select>
        </div>
        <div>
          <Label>Возраст</Label>
          <Input
            type="number"
            min="0"
            value={form.age}
            onChange={(e) => updateNumericField("age", e.target.value)}
            placeholder="Возраст"
          />
        </div>
        <div>
          <Label>Вес (кг)</Label>
          <Input
            type="number"
            min="0"
            value={form.weight_kg}
            onChange={(e) => updateNumericField("weight_kg", e.target.value)}
            placeholder="Вес"
          />
        </div>
        <div>
          <Label>Рост (см)</Label>
          <Input
            type="number"
            min="0"
            value={form.height_cm}
            onChange={(e) => updateNumericField("height_cm", e.target.value)}
            placeholder="Рост"
          />
        </div>
        <div>
          <Label>Активность</Label>
          <Select
            value={form.activity}
            onChange={(e) => onChange({ ...form, activity: e.target.value as NutritionCalculatorActivity })}
          >
            <option value="sedentary">Сидячий (1.2)</option>
            <option value="light">Лёгкая (1.375)</option>
            <option value="moderate">Умеренная (1.55)</option>
            <option value="active">Высокая (1.725)</option>
            <option value="very_active">Очень высокая (1.9)</option>
          </Select>
        </div>
      </div>

      <div className="mt-3">
        <Label>Цель</Label>
        <Select value={form.goal} onChange={(e) => onChange({ ...form, goal: e.target.value as NutritionCalculatorGoal })}>
          <option value="maintain">Поддержание</option>
          <option value="bulk">Масса</option>
          <option value="cut">Сушка</option>
        </Select>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <CalorieCard title="BMR" value={Math.round(targets?.bmr ?? 0)} tone="base" />
        <CalorieCard title="TDEE" value={Math.round(targets?.tdee ?? 0)} tone="base" />
        <CalorieCard title="Целевые калории" value={Math.round(targets?.target_calories ?? 0)} tone={form.goal === "cut" ? "cut" : form.goal === "bulk" ? "bulk" : "base"} />
      </div>

      <div className="mt-3 grid gap-3 md:grid-cols-3">
        <CalorieCard title={`Белки · ${Math.round(targets?.protein.grams ?? 0)} г`} value={Math.round(targets?.protein.kcal ?? 0)} tone="base" />
        <CalorieCard title={`Жиры · ${Math.round(targets?.fat.grams ?? 0)} г`} value={Math.round(targets?.fat.kcal ?? 0)} tone="base" />
        <CalorieCard title={`Углеводы · ${Math.round(targets?.carbs.grams ?? 0)} г`} value={Math.round(targets?.carbs.kcal ?? 0)} tone="base" />
      </div>

      {error && <div className="mt-3 text-xs text-red-400">{error}</div>}
    </Card>
  );
}
