"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Input, Label, Select } from "@/components/ui/input";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { trainingApi } from "@/features/training/api";
import type { GenerateProgramResponse, TrainingExperience, TrainingGoal } from "@/features/training/types";

export default function GenerateWorkoutPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [response, setResponse] = useState<GenerateProgramResponse | null>(null);
  const [form, setForm] = useState({
    weight_kg: 78,
    height_cm: 178,
    training_experience: "intermediate" as TrainingExperience,
    goal: "hypertrophy" as TrainingGoal,
    training_days: 4,
    bench_1rm: 80,
    load_mode: "percent_1rm" as "percent_1rm" | "absolute",
    start_kpsh: 24,
    growth_step: 0.08,
    drop_step: 0.15,
  });

  const strengthPayload = useMemo(
    () => [{ exercise_id: 1, one_rm: Number(form.bench_1rm) }],
    [form.bench_1rm],
  );

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const generated = await trainingApi.generateProgram({
        training_experience: form.training_experience,
        goal: form.goal,
        training_days: Number(form.training_days),
        weight_kg: Number(form.weight_kg),
        height_cm: Number(form.height_cm),
        initial_strength: strengthPayload,
        load_mode: form.load_mode,
        start_kpsh: Number(form.start_kpsh),
        growth_step: Number(form.growth_step),
        drop_step: Number(form.drop_step),
      });
      setResponse(generated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate program");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Генерация программы</CardTitle></CardHeader>
        <form onSubmit={onSubmit} className="glass-card p-5 md:p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <Label>Вес (кг)</Label>
              <Input type="number" value={form.weight_kg} min={30} max={250} onChange={(e) => setForm((v) => ({ ...v, weight_kg: +e.target.value }))} />
            </div>
            <div>
              <Label>Рост (см, опционально)</Label>
              <Input type="number" value={form.height_cm} min={120} max={230} onChange={(e) => setForm((v) => ({ ...v, height_cm: +e.target.value }))} />
            </div>
            <div>
              <Label>Опыт</Label>
              <Select value={form.training_experience} onChange={(e) => setForm((v) => ({ ...v, training_experience: e.target.value as TrainingExperience }))}>
                <option value="beginner">Новичок</option>
                <option value="intermediate">Средний</option>
                <option value="advanced">Продвинутый</option>
              </Select>
            </div>
            <div>
              <Label>Цель</Label>
              <Select value={form.goal} onChange={(e) => setForm((v) => ({ ...v, goal: e.target.value as TrainingGoal }))}>
                <option value="hypertrophy">Гипертрофия</option>
                <option value="strength">Сила</option>
                <option value="recomposition">Рекомпозиция</option>
              </Select>
            </div>
            <div>
              <Label>Тренировок в неделю (3-6)</Label>
              <Input type="number" value={form.training_days} min={3} max={6} onChange={(e) => setForm((v) => ({ ...v, training_days: +e.target.value }))} />
            </div>
            <div>
              <Label>Базовый 1RM жим лежа (кг)</Label>
              <Input type="number" value={form.bench_1rm} min={10} max={400} onChange={(e) => setForm((v) => ({ ...v, bench_1rm: +e.target.value }))} />
            </div>
            <div>
              <Label>Режим нагрузки</Label>
              <Select value={form.load_mode} onChange={(e) => setForm((v) => ({ ...v, load_mode: e.target.value as "percent_1rm" | "absolute" }))}>
                <option value="percent_1rm">% от 1RM</option>
                <option value="absolute">Абсолютный вес</option>
              </Select>
            </div>
            <div>
              <Label>Стартовый KPSH</Label>
              <Input type="number" value={form.start_kpsh} min={8} max={80} onChange={(e) => setForm((v) => ({ ...v, start_kpsh: +e.target.value }))} />
            </div>
            <div>
              <Label>Шаг роста</Label>
              <Input type="number" step="0.01" value={form.growth_step} min={0.01} max={0.25} onChange={(e) => setForm((v) => ({ ...v, growth_step: +e.target.value }))} />
            </div>
            <div>
              <Label>Deload шаг</Label>
              <Input type="number" step="0.01" value={form.drop_step} min={0.05} max={0.35} onChange={(e) => setForm((v) => ({ ...v, drop_step: +e.target.value }))} />
            </div>
          </div>
          {error && <p className="text-xs text-brand-500">{error}</p>}
          <Button type="submit" disabled={loading}>
            {loading ? "Генерация..." : "Generate Workout"}
          </Button>
        </form>
      </Card>

      {response && (
        <Card>
          <CardHeader><CardTitle>{response.plan.name}</CardTitle></CardHeader>
          <div className="space-y-2">
            {response.plan.days.slice(0, 7).map((d) => (
              <div key={d.id} className="glass-card p-3 text-sm">
                День {d.day_index + 1} · {d.title} · {d.is_rest ? "Rest" : `${d.exercises.length} exercises`}
              </div>
            ))}
            <div className="flex gap-2">
              <Button onClick={() => router.push("/dashboard/workouts/plan")}>Сохранить программу</Button>
              <Button variant="outline" onClick={() => router.push("/dashboard/workouts")}>К тренировкам</Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
