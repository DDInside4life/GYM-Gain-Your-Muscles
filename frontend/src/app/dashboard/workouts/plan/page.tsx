"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Pencil } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { workoutApi } from "@/features/workout/api";
import { questionnaireApi } from "@/features/questionnaire/api";
import type { WorkoutPlan } from "@/features/workout/types";
import { WorkoutViewer } from "@/components/dashboard/workout-viewer";
import { EditableWorkout } from "@/components/dashboard/editable-workout";

export default function WorkoutPlanPage() {
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [hasQuestionnaire, setHasQuestionnaire] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  useEffect(() => {
    workoutApi
      .current()
      .then((p) => setPlan(p))
      .catch(() => setPlan(null))
      .finally(() => setLoading(false));
    questionnaireApi
      .latest()
      .then((row) => setHasQuestionnaire(Boolean(row)))
      .catch(() => {});
  }, []);

  async function regenerate() {
    setRegenerating(true);
    try {
      const next = hasQuestionnaire
        ? await questionnaireApi.regenerate()
        : await workoutApi.progress();
      setPlan(next);
    } finally {
      setRegenerating(false);
    }
  }

  if (loading) {
    return <div className="py-16 text-center text-muted">Загрузка…</div>;
  }

  if (!plan) {
    return (
      <div className="space-y-4">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 text-sm text-muted hover:text-inherit transition-colors"
        >
          <ArrowLeft size={14} /> На главную
        </Link>
        <Card>
          <CardHeader>
            <CardTitle>Активного плана нет</CardTitle>
          </CardHeader>
          <p className="text-sm text-muted">
            Сгенерируйте программу за 4 коротких шага — мы подберём готовый месячный план.
          </p>
          <div className="mt-3">
            <Link href="/dashboard/workouts/generate">
              <Button>Сгенерировать программу</Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-2 text-sm text-muted hover:text-inherit transition-colors"
      >
        <ArrowLeft size={14} /> На главную
      </Link>

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-3 w-full">
            <div>
              <CardTitle>{plan.name}</CardTitle>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <Badge tone="brand">Месяц {plan.month_index}</Badge>
                <Badge tone="violet">{plan.split_type}</Badge>
                <Badge>4 недели</Badge>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link href="/dashboard/workouts/history">
                <Button size="sm" variant="outline">История</Button>
              </Link>
              <Link href="/dashboard/workouts/plan/finalize-test">
                <Button size="sm" variant="outline">Финализировать тест</Button>
              </Link>
              <Button
                size="sm"
                variant={editing ? "soft" : "outline"}
                onClick={() => setEditing((v) => !v)}
              >
                <Pencil size={14} /> {editing ? "Готово" : "Редактировать"}
              </Button>
              <Button size="sm" variant="outline" onClick={regenerate} disabled={regenerating}>
                {regenerating ? "Генерация…" : "Новый месяц"}
              </Button>
            </div>
          </div>
        </CardHeader>

        {editing ? (
          <EditableWorkout plan={plan} onChanged={setPlan} />
        ) : (
          <div className="space-y-4">
            <WorkoutViewer plan={plan} onChanged={setPlan} />
            <div className="grid md:grid-cols-2 gap-2">
              {plan.days.filter((d) => !d.is_rest).map((day) => (
                <Link key={day.id} href={`/dashboard/workouts/plan/${day.id}`}>
                  <Button variant="outline" className="w-full justify-start">
                    Открыть тренировку: {day.title} (неделя {day.week_index})
                  </Button>
                </Link>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
