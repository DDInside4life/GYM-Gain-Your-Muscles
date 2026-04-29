"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { workoutApi } from "@/features/workout/api";
import type { WorkoutDay, WorkoutPlan } from "@/features/workout/types";
import { SetRunner } from "@/components/dashboard/set-runner";

export default function WorkoutDayRunnerPage() {
  const { dayId } = useParams<{ dayId: string }>();
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    workoutApi.current().then(setPlan).finally(() => setLoading(false));
  }, []);

  const day: WorkoutDay | null = useMemo(() => {
    if (!plan) return null;
    return plan.days.find((d) => d.id === Number(dayId)) ?? null;
  }, [plan, dayId]);

  if (loading) return <div className="text-sm text-muted">Загрузка...</div>;
  if (!day) return <div className="text-sm text-muted">День не найден.</div>;

  return (
    <div className="space-y-4">
      <Link href="/dashboard/workouts/plan" className="text-sm text-muted hover:text-inherit">
        Назад к плану
      </Link>
      <Card>
        <CardHeader>
          <CardTitle>{day.title}</CardTitle>
          <div className="text-sm text-muted">
            Неделя {day.week_index} · {day.phase === "test" ? "Тестовая неделя" : "Рабочая неделя"}
          </div>
          {day.phase === "test" && (
            <div className="text-xs text-brand-500">
              Тестовая неделя: держите RIR 2 и не выходите в отказ.
            </div>
          )}
        </CardHeader>
      </Card>
      <div className="space-y-3">
        {day.exercises.map((ex) => (
          <SetRunner key={ex.id} exercise={ex} />
        ))}
      </div>
      <div className="flex justify-end">
        <Link href="/dashboard/workouts/plan/finalize-test">
          <Button variant="outline">Завершить тестовую неделю</Button>
        </Link>
      </div>
    </div>
  );
}
