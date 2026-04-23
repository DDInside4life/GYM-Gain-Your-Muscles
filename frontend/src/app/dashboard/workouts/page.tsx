"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { RefreshCcw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input, Label, Select } from "@/components/ui/input";
import { workoutApi } from "@/features/workout/api";
import { trainingApi } from "@/features/training/api";
import type { WorkoutPlan } from "@/features/workout/types";

export default function WorkoutsPage() {
  const router = useRouter();
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [history, setHistory] = useState<WorkoutPlan[]>([]);
  const [predefined, setPredefined] = useState<Array<{ id: string; name: string; days_per_week: number; goal: string }>>([]);
  const [progressing, setProgressing] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [form, setForm] = useState({
    training_experience: "intermediate",
    goal: "hypertrophy",
    training_days: 4,
    weight_kg: 78,
    height_cm: 178,
    bench_1rm: 80,
  });

  useEffect(() => {
    workoutApi.current().then(setPlan).catch(() => setPlan(null));
    workoutApi.history().then(setHistory).catch(() => setHistory([]));
    workoutApi.predefined().then(setPredefined).catch(() => setPredefined([]));
  }, []);

  async function progress() {
    setProgressing(true);
    try {
      const next = await workoutApi.progress();
      setPlan(next);
    } finally {
      setProgressing(false);
    }
  }

  async function generateProgram() {
    setGenerating(true);
    try {
      await trainingApi.generateProgram({
        training_experience: form.training_experience as "beginner" | "intermediate" | "advanced",
        goal: form.goal as "hypertrophy" | "strength" | "recomposition",
        training_days: form.training_days,
        weight_kg: form.weight_kg,
        height_cm: form.height_cm,
        initial_strength: [{ exercise_id: 1, one_rm: form.bench_1rm }],
      });
      setModalOpen(false);
      router.push("/dashboard/workouts/plan");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Тренировочные программы</CardTitle>
          <Sparkles className="text-brand-500" />
        </CardHeader>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => setModalOpen(true)}>Сгенерировать тренировку</Button>
          <Link href="/dashboard/workouts/plan"><Button variant="outline">Просмотреть весь план</Button></Link>
          <Link href="/dashboard/exercises"><Button variant="outline">Смотреть все упражнения</Button></Link>
        </div>
      </Card>
      {modalOpen && (
        <Card>
          <CardHeader><CardTitle>Параметры генерации</CardTitle></CardHeader>
          <div className="grid md:grid-cols-3 gap-3">
            <div><Label>Цель</Label><Select value={form.goal} onChange={(e) => setForm((p) => ({ ...p, goal: e.target.value }))}><option value="hypertrophy">Гипертрофия</option><option value="strength">Сила</option><option value="recomposition">Рекомпозиция</option></Select></div>
            <div><Label>Опыт</Label><Select value={form.training_experience} onChange={(e) => setForm((p) => ({ ...p, training_experience: e.target.value }))}><option value="beginner">Новичок</option><option value="intermediate">Средний</option><option value="advanced">Продвинутый</option></Select></div>
            <div><Label>Дней</Label><Input type="number" min={3} max={6} value={form.training_days} onChange={(e) => setForm((p) => ({ ...p, training_days: +e.target.value }))} /></div>
            <div><Label>Вес, кг</Label><Input type="number" value={form.weight_kg} onChange={(e) => setForm((p) => ({ ...p, weight_kg: +e.target.value }))} /></div>
            <div><Label>Рост, см</Label><Input type="number" value={form.height_cm} onChange={(e) => setForm((p) => ({ ...p, height_cm: +e.target.value }))} /></div>
            <div><Label>1RM жима</Label><Input type="number" value={form.bench_1rm} onChange={(e) => setForm((p) => ({ ...p, bench_1rm: +e.target.value }))} /></div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button onClick={generateProgram} disabled={generating}>{generating ? "Генерация..." : "Создать"}</Button>
            <Button variant="outline" onClick={() => setModalOpen(false)}>Отмена</Button>
          </div>
        </Card>
      )}

      {plan && (
        <Card>
          <CardHeader>
            <CardTitle>Текущая выбранная программа</CardTitle>
            <div className="flex gap-2">
              <Badge tone="brand">Активная</Badge>
              <Badge>Month {plan.month_index}</Badge>
              <Badge>Week {plan.cycle_week}</Badge>
              <Button size="sm" variant="outline" onClick={progress} disabled={progressing}>
                <RefreshCcw size={14} /> {progressing ? "…" : "Следующая неделя"}
              </Button>
            </div>
          </CardHeader>
          <div className="glass-card p-4">
            <div className="display font-bold">{plan.name}</div>
            <div className="text-sm text-muted mt-1">{plan.days.length} дней в программе</div>
          </div>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Предопределенные программы</CardTitle></CardHeader>
        <div className="grid md:grid-cols-3 gap-2">
          {predefined.map((p) => (
            <div key={p.id} className="glass-card p-3">
              <div className="font-semibold">{p.name}</div>
              <div className="text-xs text-muted">{p.days_per_week} days · {p.goal}</div>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader><CardTitle>Ваши программы</CardTitle></CardHeader>
        <div className="space-y-2">
          {history.map((h) => (
            <div key={h.id} className="glass-card p-3 flex items-center justify-between">
              <div>
                <div className="font-semibold">{h.name}</div>
                <div className="text-xs text-muted">Month {h.month_index} · {h.split_type}</div>
              </div>
              <Button size="sm" variant="outline" onClick={async () => setPlan(await workoutApi.select(h.id))}>
                Выбрать
              </Button>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
