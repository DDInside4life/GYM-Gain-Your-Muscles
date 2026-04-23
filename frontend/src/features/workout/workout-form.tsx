"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Brain, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input, Label, Select } from "@/components/ui/input";
import { aiApi } from "@/features/ai/api";
import type { AIWorkoutResponse } from "@/features/ai/types";
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

type Props = {
  onGenerated: (p: WorkoutPlan) => void;
  onAi?: (r: AIWorkoutResponse) => void;
  aiAvailable?: boolean;
};

export function WorkoutForm({ onGenerated, onAi, aiAvailable = false }: Props) {
  const router = useRouter();
  const [weight, setWeight] = useState(78);
  const [height, setHeight] = useState(178);
  const [age, setAge] = useState(28);
  const [experience, setExperience] = useState<Experience>("intermediate");
  const [goal, setGoal] = useState<Goal>("muscle_gain");
  const [days, setDays] = useState(4);
  const [equipment, setEquipment] = useState<Equipment[]>(["bodyweight", "dumbbell", "barbell", "machine"]);
  const [injuries, setInjuries] = useState<string[]>([]);
  const [aiMode, setAiMode] = useState<boolean>(aiAvailable);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [step, setStep] = useState(1);

  function toggleIn<T>(set: React.Dispatch<React.SetStateAction<T[]>>, v: T) {
    set((prev) => (prev.includes(v) ? prev.filter((x) => x !== v) : [...prev, v]));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    const payload = {
      weight_kg: weight, height_cm: height, age,
      experience, goal, days_per_week: days, equipment, injuries,
    };
    try {
      if (aiMode && aiAvailable) {
        const res = await aiApi.generateWorkout(payload);
        onGenerated(res.plan);
        onAi?.(res);
      } else {
        const plan = await workoutApi.generate(payload);
        onGenerated(plan);
      }
    } catch (err) {
      setError(String((err as Error).message));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="glass-card p-5 md:p-6 space-y-5">
      {aiAvailable && (
        <div className="flex items-center gap-3 p-3 rounded-xl border border-[var(--border)]">
          <Brain size={16} className="text-brand-500" />
          <div className="flex-1">
            <div className="text-sm font-semibold">AI-коуч</div>
            <div className="text-xs text-muted">
              LLM подбирает упражнения, объём и объясняет логику. Безопасность гарантируется правилами.
            </div>
          </div>
          <label className="inline-flex items-center gap-2 text-xs">
            <input type="checkbox" checked={aiMode} onChange={(e) => setAiMode(e.target.checked)} />
            {aiMode ? <Badge tone="brand">AI</Badge> : <Badge>Rules</Badge>}
          </label>
        </div>
      )}

      <div className="flex gap-2 text-xs">
        {[1, 2, 3, 4].map((n) => (
          <span
            key={n}
            className={`px-2 py-1 rounded-full ${n === step ? "bg-brand-gradient text-white" : "bg-black/5 dark:bg-white/10 text-muted"}`}
          >
            Шаг {n}
          </span>
        ))}
      </div>

      {step === 1 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <Label>Возраст</Label>
            <Input type="number" value={age} onChange={(e) => setAge(+e.target.value)} min={12} max={90} />
          </div>
          <div>
            <Label>Вес (кг)</Label>
            <Input type="number" value={weight} onChange={(e) => setWeight(+e.target.value)} min={30} max={250} />
          </div>
          <div>
            <Label>Рост (см)</Label>
            <Input type="number" value={height} onChange={(e) => setHeight(+e.target.value)} min={120} max={230} />
          </div>
        </div>
      )}

      {step === 2 && (
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
      )}

      {step === 3 && (
        <div className="space-y-4">
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
        </div>
      )}

      {step === 4 && (
        <div>
          <Label>Тренировок в неделю</Label>
          <Input type="number" value={days} onChange={(e) => setDays(+e.target.value)} min={2} max={6} />
        </div>
      )}

      {error && <p className="text-xs text-brand-500">{error}</p>}

      <div className="flex gap-2">
        {step > 1 && (
          <Button type="button" variant="outline" onClick={() => setStep((v) => v - 1)}>
            Назад
          </Button>
        )}
        {step < 4 ? (
          <Button type="button" onClick={() => setStep((v) => v + 1)}>
            Далее
          </Button>
        ) : (
          <Button type="submit" size="lg" disabled={loading}>
            <Sparkles size={16} />
            {loading ? "AI думает…" : aiMode && aiAvailable ? "AI: Сгенерировать план" : "Сгенерировать план"}
          </Button>
        )}
        <Button type="button" variant="ghost" onClick={() => router.push("/dashboard/workouts/plan")}>
          Сохранить программу
        </Button>
      </div>
    </form>
  );
}
