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
import type { WorkoutPlan, WorkoutTemplate } from "@/features/workout/types";

const GOAL_ICON: Record<string, string> = {
  hypertrophy: "💪", strength: "🏋️", recomposition: "⚡",
  muscle_gain: "💪", fat_loss: "🔥", endurance: "🏃", general: "🎯",
};

export default function WorkoutsPage() {
  const router = useRouter();
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [history, setHistory] = useState<WorkoutPlan[]>([]);
  const [templates, setTemplates] = useState<WorkoutTemplate[]>([]);
  const [progressing, setProgressing] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [expandedTemplateId, setExpandedTemplateId] = useState<number | null>(null);
  const [templateActionId, setTemplateActionId] = useState<number | null>(null);
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
    workoutApi.templates().then(setTemplates).catch(() => setTemplates([]));
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

  async function applyTemplate(templateId: number) {
    setTemplateActionId(templateId);
    try {
      const result = await workoutApi.applyTemplate(templateId);
      setPlan(result.plan);
      setHistory((prev) => [result.plan, ...prev.filter((p) => p.id !== result.plan.id)]);
    } finally {
      setTemplateActionId(null);
    }
  }

  async function generateFromTemplate(templateId: number) {
    setTemplateActionId(templateId);
    try {
      const result = await workoutApi.generateFromTemplate(templateId, 28, true);
      setPlan(result);
      setHistory((prev) => [result, ...prev.filter((p) => p.id !== result.id)]);
    } finally {
      setTemplateActionId(null);
    }
  }

  const aiPrograms = history.filter((item) => {
    const source = String(item.params?.source ?? "");
    return source.includes("llm") || source.includes("ai") || source.includes("template_ai_adapted");
  });

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

      {aiPrograms.length > 0 && (
        <Card>
          <CardHeader><CardTitle>AI программы</CardTitle></CardHeader>
          <div className="space-y-2">
            {aiPrograms.map((h) => (
              <div key={h.id} className="glass-card p-3 flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-violet-500/15 grid place-items-center text-lg shrink-0">🤖</div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-sm truncate">{h.name}</div>
                  <div className="text-xs text-muted">
                    Месяц {h.month_index} · {h.split_type} · {String(h.params?.source ?? "ai")}
                  </div>
                </div>
                <Button size="sm" variant="outline" onClick={async () => setPlan(await workoutApi.select(h.id))}>
                  Выбрать
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {templates.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Предопределенные программы</CardTitle></CardHeader>
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
            {templates.map((template) => (
              <div key={template.id} className={`glass-card p-4 group hover:shadow-glow transition-all duration-300 ${plan?.params?.template_id === template.id ? "ring-1 ring-brand-500/70" : ""}`}>
                <div className="flex items-start gap-3">
                  <div className="h-10 w-10 rounded-xl bg-violet-500/15 grid place-items-center text-lg shrink-0">
                    {GOAL_ICON[template.split_type] ?? "🏋️"}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="font-semibold text-sm leading-tight">{template.name}</div>
                    <div className="text-xs text-muted mt-1">{template.days_per_week} дней/нед · {template.level}</div>
                    <div className="text-xs text-muted mt-1 line-clamp-2">{template.description}</div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setExpandedTemplateId((prev) => (prev === template.id ? null : template.id))}
                      >
                        View
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={templateActionId === template.id}
                        onClick={() => applyTemplate(template.id)}
                      >
                        {templateActionId === template.id ? "..." : "Select"}
                      </Button>
                      <Button
                        size="sm"
                        disabled={templateActionId === template.id}
                        onClick={() => generateFromTemplate(template.id)}
                      >
                        {templateActionId === template.id ? "..." : "Generate based on this"}
                      </Button>
                    </div>
                  </div>
                </div>
                {expandedTemplateId === template.id && (
                  <div className="mt-3 pt-3 border-t border-[var(--border)] space-y-2">
                    {template.days.map((day) => (
                      <div key={day.id} className="text-xs">
                        <div className="font-semibold">{day.title}</div>
                        <div className="text-muted">{day.exercises.map((e) => e.exercise_name).join(", ")}</div>
                      </div>
                    ))}
                  </div>
                )}
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
