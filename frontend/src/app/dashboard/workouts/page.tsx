"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Calendar, CheckCircle2, Dumbbell, Plus, RefreshCcw, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input, Label, Select } from "@/components/ui/input";
import { workoutApi } from "@/features/workout/api";
import { trainingApi } from "@/features/training/api";
import type { WorkoutPlan } from "@/features/workout/types";

const GOAL_ICON: Record<string, string> = {
  hypertrophy: "💪", strength: "🏋️", recomposition: "⚡",
  muscle_gain: "💪", fat_loss: "🔥", endurance: "🏃", general: "🎯",
};

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
    try { setPlan(await workoutApi.progress()); }
    finally { setProgressing(false); }
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
    <div className="space-y-6 animate-fade-up">
      <div className="glass-card p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-brand-500" />
            <h2 className="display font-extrabold text-xl">Тренировочные программы</h2>
          </div>
          <p className="text-sm text-muted mt-1">Генерируй, выбирай и прогрессируй</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => setModalOpen(true)}>
            <Plus size={16} /> Сгенерировать тренировку
          </Button>
          <Link href="/dashboard/workouts/plan">
            <Button variant="outline"><Calendar size={16} /> Весь план</Button>
          </Link>
        </div>
      </div>

      {modalOpen && (
        <Card>
          <CardHeader>
            <CardTitle>Параметры генерации</CardTitle>
            <button onClick={() => setModalOpen(false)} className="text-muted hover:text-inherit transition">
              <X size={18} />
            </button>
          </CardHeader>
          <div className="grid md:grid-cols-3 gap-3">
            <div>
              <Label>Цель</Label>
              <Select value={form.goal} onChange={(e) => setForm((p) => ({ ...p, goal: e.target.value }))}>
                <option value="hypertrophy">Гипертрофия</option>
                <option value="strength">Сила</option>
                <option value="recomposition">Рекомпозиция</option>
              </Select>
            </div>
            <div>
              <Label>Опыт</Label>
              <Select value={form.training_experience} onChange={(e) => setForm((p) => ({ ...p, training_experience: e.target.value }))}>
                <option value="beginner">Новичок</option>
                <option value="intermediate">Средний</option>
                <option value="advanced">Продвинутый</option>
              </Select>
            </div>
            <div><Label>Дней/неделю</Label><Input type="number" min={3} max={6} value={form.training_days} onChange={(e) => setForm((p) => ({ ...p, training_days: +e.target.value }))} /></div>
            <div><Label>Вес, кг</Label><Input type="number" value={form.weight_kg} onChange={(e) => setForm((p) => ({ ...p, weight_kg: +e.target.value }))} /></div>
            <div><Label>Рост, см</Label><Input type="number" value={form.height_cm} onChange={(e) => setForm((p) => ({ ...p, height_cm: +e.target.value }))} /></div>
            <div><Label>1RM жима лёжа</Label><Input type="number" value={form.bench_1rm} onChange={(e) => setForm((p) => ({ ...p, bench_1rm: +e.target.value }))} /></div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button onClick={generateProgram} disabled={generating}>
              {generating ? "Генерация…" : "Создать программу"}
            </Button>
            <Button variant="outline" onClick={() => setModalOpen(false)}>Отмена</Button>
          </div>
        </Card>
      )}

      {plan && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <CheckCircle2 size={18} className="text-brand-500" />
              <CardTitle>Активная программа</CardTitle>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="brand">Активная</Badge>
              <Badge>Месяц {plan.month_index}</Badge>
              <Badge>Неделя {plan.cycle_week}</Badge>
              <Button size="sm" variant="outline" onClick={progress} disabled={progressing}>
                <RefreshCcw size={14} /> {progressing ? "…" : "Следующая неделя"}
              </Button>
            </div>
          </CardHeader>
          <div className="glass-card p-4 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-brand-gradient grid place-items-center text-2xl shrink-0">
              {GOAL_ICON[plan.split_type] ?? "🏋️"}
            </div>
            <div>
              <div className="display font-bold">{plan.name}</div>
              <div className="text-sm text-muted">{plan.days.length} дней · {plan.split_type}</div>
            </div>
          </div>
        </Card>
      )}

      {predefined.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Готовые программы</CardTitle></CardHeader>
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
            {predefined.map((p) => (
              <div key={p.id} className="glass-card p-4 group hover:shadow-glow transition-shadow duration-300">
                <div className="flex items-start gap-3">
                  <div className="h-10 w-10 rounded-xl bg-violet-500/15 grid place-items-center text-lg shrink-0">
                    {GOAL_ICON[p.goal] ?? "🏋️"}
                  </div>
                  <div>
                    <div className="font-semibold text-sm leading-tight">{p.name}</div>
                    <div className="text-xs text-muted mt-1">{p.days_per_week} дней/нед · {p.goal}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>История программ</CardTitle></CardHeader>
        {history.length === 0 ? (
          <div className="text-sm text-muted text-center py-6">Программ пока нет. Создайте свою первую!</div>
        ) : (
          <div className="space-y-2">
            {history.map((h) => (
              <div key={h.id} className="glass-card p-3 flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-brand-500/10 grid place-items-center text-lg shrink-0">
                  <Dumbbell size={18} className="text-brand-500 opacity-70" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-sm truncate">{h.name}</div>
                  <div className="text-xs text-muted">Месяц {h.month_index} · {h.split_type}</div>
                </div>
                <Button size="sm" variant="outline" onClick={async () => setPlan(await workoutApi.select(h.id))}>
                  Выбрать
                </Button>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
