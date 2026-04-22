"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Label, Select } from "@/components/ui/input";
import { workoutApi } from "./api";
import type { Equipment, Experience, Goal, WorkoutPlan } from "./types";

const EQUIPMENT: { value: Equipment; label: string }[] = [
  { value: "bodyweight", label: "Своё тело" },
  { value: "dumbbell", label: "Гантели" },
  { value: "barbell", label: "Штанга" },
  { value: "machine", label: "Тренажёры" },
  { value: "cable", label: "Блоки" },
  { value: "kettlebell", label: "Гири" },
  { value: "bands", label: "Резинки" },
];

const INJURIES = ["knee", "back", "shoulder", "wrist", "elbow", "hip"];

export function WorkoutForm({ onGenerated }: { onGenerated: (p: WorkoutPlan) => void }) {
  const [weight, setWeight] = useState(78);
  const [height, setHeight] = useState(178);
  const [age, setAge] = useState(28);
  const [experience, setExperience] = useState<Experience>("intermediate");
  const [goal, setGoal] = useState<Goal>("muscle_gain");
  const [days, setDays] = useState(4);
  const [equipment, setEquipment] = useState<Equipment[]>(["bodyweight", "dumbbell", "barbell", "machine"]);
  const [injuries, setInjuries] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function toggleIn<T>(set: React.Dispatch<React.SetStateAction<T[]>>, v: T) {
    set((prev) => (prev.includes(v) ? prev.filter((x) => x !== v) : [...prev, v]));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const plan = await workoutApi.generate({
        weight_kg: weight, height_cm: height, age,
        experience, goal, days_per_week: days, equipment, injuries,
      });
      onGenerated(plan);
    } catch (err) {
      setError(String((err as Error).message));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="glass-card p-5 md:p-6 space-y-5">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <Label>Вес (кг)</Label>
          <Input type="number" value={weight} onChange={(e) => setWeight(+e.target.value)} min={30} max={250} />
        </div>
        <div>
          <Label>Рост (см)</Label>
          <Input type="number" value={height} onChange={(e) => setHeight(+e.target.value)} min={120} max={230} />
        </div>
        <div>
          <Label>Возраст</Label>
          <Input type="number" value={age} onChange={(e) => setAge(+e.target.value)} min={12} max={90} />
        </div>
        <div>
          <Label>Дней / неделю</Label>
          <Input type="number" value={days} onChange={(e) => setDays(+e.target.value)} min={2} max={6} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <Label>Опыт</Label>
          <Select value={experience} onChange={(e) => setExperience(e.target.value as Experience)}>
            <option value="beginner">Новичок</option>
            <option value="intermediate">Средний</option>
            <option value="advanced">Продвинутый</option>
          </Select>
        </div>
        <div>
          <Label>Цель</Label>
          <Select value={goal} onChange={(e) => setGoal(e.target.value as Goal)}>
            <option value="muscle_gain">Набор массы</option>
            <option value="fat_loss">Жиросжигание</option>
            <option value="strength">Сила</option>
            <option value="endurance">Выносливость</option>
            <option value="general">Общее</option>
          </Select>
        </div>
      </div>

      <div>
        <Label>Экипировка</Label>
        <div className="flex flex-wrap gap-2">
          {EQUIPMENT.map((eq) => (
            <button
              type="button"
              key={eq.value}
              onClick={() => toggleIn(setEquipment, eq.value)}
              className={`px-3 py-1.5 text-xs rounded-full border transition ${
                equipment.includes(eq.value)
                  ? "bg-brand-gradient text-white border-transparent"
                  : "border-[var(--border)] hover:bg-black/5 dark:hover:bg-white/10"
              }`}
            >
              {eq.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <Label>Ограничения / травмы</Label>
        <div className="flex flex-wrap gap-2">
          {INJURIES.map((inj) => (
            <button
              type="button"
              key={inj}
              onClick={() => toggleIn(setInjuries, inj)}
              className={`px-3 py-1.5 text-xs rounded-full border transition ${
                injuries.includes(inj)
                  ? "bg-brand-500/20 text-brand-500 border-brand-500/40"
                  : "border-[var(--border)] hover:bg-black/5 dark:hover:bg-white/10"
              }`}
            >
              {inj}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="text-xs text-brand-500">{error}</p>}

      <Button type="submit" size="lg" disabled={loading}>
        <Sparkles size={16} />
        {loading ? "Генерация…" : "Сгенерировать план"}
      </Button>
    </form>
  );
}
