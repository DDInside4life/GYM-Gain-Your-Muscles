"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Calendar, CheckCircle2, Dumbbell, Plus, RefreshCcw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { workoutApi } from "@/features/workout/api";
import { questionnaireApi } from "@/features/questionnaire/api";
import type { WorkoutPlan, WorkoutTemplate } from "@/features/workout/types";

const SPLIT_LABEL: Record<string, string> = {
  full_body: "Фулл-боди",
  upper_lower: "Верх/Низ",
  ppl: "Тяни/Толкай/Ноги",
};

const GOAL_ICON: Record<string, string> = {
  hypertrophy: "💪",
  strength: "🏋️",
  recomposition: "⚡",
  muscle_gain: "💪",
  fat_loss: "🔥",
  endurance: "🏃",
  general: "🎯",
};

export default function WorkoutsPage() {
  const router = useRouter();
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [history, setHistory] = useState<WorkoutPlan[]>([]);
  const [templates, setTemplates] = useState<WorkoutTemplate[]>([]);
  const [hasQuestionnaire, setHasQuestionnaire] = useState(false);
  const [progressing, setProgressing] = useState(false);
  const [expandedTemplateId, setExpandedTemplateId] = useState<number | null>(null);
  const [templateActionId, setTemplateActionId] = useState<number | null>(null);

  useEffect(() => {
    workoutApi.current().then(setPlan).catch(() => setPlan(null));
    workoutApi.history().then(setHistory).catch(() => setHistory([]));
    workoutApi.templates().then(setTemplates).catch(() => setTemplates([]));
    questionnaireApi
      .latest()
      .then((row) => setHasQuestionnaire(Boolean(row)))
      .catch(() => setHasQuestionnaire(false));
  }, []);

  async function regenerate() {
    setProgressing(true);
    try {
      const next = hasQuestionnaire ? await questionnaireApi.regenerate() : await workoutApi.progress();
      setPlan(next);
      setHistory((prev) => [next, ...prev.filter((p) => p.id !== next.id)]);
    } finally {
      setProgressing(false);
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

  return (
    <div className="space-y-6 animate-fade-up">
      <div className="glass-card p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-brand-500" />
            <h2 className="display font-extrabold text-xl">Тренировочные программы</h2>
          </div>
          <p className="text-sm text-muted mt-1">
            Сгенерируйте персональный месячный план или выберите готовый шаблон.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => router.push("/dashboard/workouts/generate")}>
            <Plus size={16} /> Сгенерировать тренировку
          </Button>
          <Link href="/dashboard/workouts/plan">
            <Button variant="outline"><Calendar size={16} /> Просмотреть весь план</Button>
          </Link>
          <Link href="/dashboard/exercises">
            <Button variant="outline"><Dumbbell size={16} /> Смотреть все упражнения</Button>
          </Link>
        </div>
      </div>

      {plan ? (
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
              <Button size="sm" variant="outline" onClick={regenerate} disabled={progressing}>
                <RefreshCcw size={14} /> {progressing ? "…" : "Следующий месяц"}
              </Button>
            </div>
          </CardHeader>
          <div className="glass-card p-4 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-brand-gradient grid place-items-center text-2xl shrink-0">
              {GOAL_ICON[String(plan.params?.goal ?? "")] ?? "🏋️"}
            </div>
            <div>
              <div className="display font-bold">{plan.name}</div>
              <div className="text-sm text-muted">
                {plan.days.length} дней · {SPLIT_LABEL[plan.split_type] ?? plan.split_type}
              </div>
            </div>
          </div>
        </Card>
      ) : (
        <Card>
          <CardHeader><CardTitle>Программа ещё не создана</CardTitle></CardHeader>
          <p className="text-sm text-muted">
            Заполните анкету — система соберёт месячный план с тестовой неделей и тремя рабочими.
          </p>
          <div className="mt-3">
            <Button onClick={() => router.push("/dashboard/workouts/generate")}>
              <Plus size={16} /> Заполнить анкету
            </Button>
          </div>
        </Card>
      )}

      {templates.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Готовые шаблоны</CardTitle></CardHeader>
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
            {templates.map((template) => (
              <div
                key={template.id}
                className={`glass-card p-4 group hover:shadow-glow transition-all duration-300 ${
                  Number(plan?.params?.template_id) === template.id ? "ring-1 ring-brand-500/70" : ""
                }`}
              >
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
                        Подробнее
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={templateActionId === template.id}
                        onClick={() => applyTemplate(template.id)}
                      >
                        {templateActionId === template.id ? "…" : "Выбрать"}
                      </Button>
                      <Button
                        size="sm"
                        disabled={templateActionId === template.id}
                        onClick={() => generateFromTemplate(template.id)}
                      >
                        {templateActionId === template.id ? "…" : "Сгенерировать на основе"}
                      </Button>
                    </div>
                  </div>
                </div>
                {expandedTemplateId === template.id && (
                  <div className="mt-3 pt-3 border-t border-[var(--border)] space-y-2">
                    {template.days.map((day) => (
                      <div key={day.id} className="text-xs">
                        <div className="font-semibold">{day.title}</div>
                        <div className="text-muted">
                          {day.exercises.map((e) => e.exercise_name).join(", ")}
                        </div>
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
          <div className="text-sm text-muted text-center py-6">
            Программ пока нет. Создайте свою первую через анкету.
          </div>
        ) : (
          <div className="space-y-2">
            {history.map((h) => (
              <div key={h.id} className="glass-card p-3 flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-brand-500/10 grid place-items-center text-lg shrink-0">
                  <Dumbbell size={18} className="text-brand-500 opacity-70" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-sm truncate">{h.name}</div>
                  <div className="text-xs text-muted">
                    Месяц {h.month_index} · {SPLIT_LABEL[h.split_type] ?? h.split_type}
                  </div>
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
