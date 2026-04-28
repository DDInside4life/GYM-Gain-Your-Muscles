"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Calendar, CheckCircle2, Dumbbell, Plus, RefreshCcw, Sparkles } from "lucide-react";
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
      <button
        onClick={() => router.push("/dashboard/workouts/generate")}
        className="group relative w-full overflow-hidden rounded-2xl bg-brand-gradient dark:bg-neon-gradient p-5 md:p-6 text-white shadow-glow-brand dark:shadow-glow text-left"
      >
        <div className="absolute inset-0 grid-bg opacity-20" />
        <div className="relative flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-11 w-11 rounded-xl grid place-items-center bg-white/15 backdrop-blur-sm">
              <Sparkles size={20} />
            </div>
            <div>
              <div className="display font-extrabold text-lg md:text-xl">Сгенерировать новую тренировку</div>
              <div className="text-xs md:text-sm opacity-90 mt-0.5">Персональный план под цели и опыт</div>
            </div>
          </div>
          <ArrowRight size={22} className="shrink-0 group-hover:translate-x-1 transition-transform" />
        </div>
      </button>

      <div className="flex flex-wrap gap-2">
        <Link href="/dashboard/workouts/plan">
          <Button variant="outline" size="sm"><Calendar size={14} /> Просмотреть весь план</Button>
        </Link>
        <Link href="/dashboard/exercises">
          <Button variant="outline" size="sm"><Dumbbell size={14} /> Все упражнения</Button>
        </Link>
        {plan && (
          <Button variant="outline" size="sm" onClick={regenerate} disabled={progressing}>
            <RefreshCcw size={14} /> {progressing ? "Обновляем…" : "Следующий месяц"}
          </Button>
        )}
      </div>

      {plan ? (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <CheckCircle2 size={18} className="text-emerald-500" />
              <CardTitle>Активная программа</CardTitle>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="brand">Активная</Badge>
              <Badge tone="violet">Месяц {plan.month_index}</Badge>
              <Badge>Неделя {plan.cycle_week}</Badge>
            </div>
          </CardHeader>
          <div className="glass-card p-4 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-brand-gradient dark:bg-neon-gradient grid place-items-center text-2xl shadow-glow-brand dark:shadow-glow shrink-0">
              {GOAL_ICON[String(plan.params?.goal ?? "")] ?? "🏋️"}
            </div>
            <div className="min-w-0 flex-1">
              <div className="display font-bold truncate">{plan.name}</div>
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
            {templates.map((template) => {
              const isCurrent = Number(plan?.params?.template_id) === template.id;
              return (
                <div
                  key={template.id}
                  className={`glass-card p-4 hover-lift transition-all duration-300 ${
                    isCurrent ? "ring-1 ring-brand-500/70 dark:ring-accent-500/60" : ""
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="h-10 w-10 rounded-xl bg-violet-500/15 dark:bg-accent-500/20 grid place-items-center text-lg shrink-0">
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
                          {templateActionId === template.id ? "…" : "Сгенерировать"}
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
              );
            })}
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
              <div key={h.id} className="glass-card p-3 flex items-center gap-3 hover-lift">
                <div className="h-10 w-10 rounded-xl bg-brand-500/10 dark:bg-violet-500/15 grid place-items-center shrink-0">
                  <Dumbbell size={18} className="text-brand-500 dark:text-violet-300 opacity-90" />
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
