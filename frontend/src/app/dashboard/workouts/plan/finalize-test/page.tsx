"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { workoutApi } from "@/features/workout/api";
import type { WorkoutPlan } from "@/features/workout/types";

export default function FinalizeTestWeekPage() {
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [updated, setUpdated] = useState(0);

  useEffect(() => {
    workoutApi.current().then(setPlan);
  }, []);

  async function finalize() {
    if (!plan) return;
    setLoading(true);
    try {
      const res = await workoutApi.finalizeTestWeek(plan.id);
      setUpdated(res.updated_exercises);
      setDone(true);
    } finally {
      setLoading(false);
    }
  }

  if (!plan) return <div className="text-sm text-muted">Нет активного плана.</div>;

  return (
    <div className="space-y-4">
      <Link href="/dashboard/workouts/plan" className="text-sm text-muted hover:text-inherit">
        Назад к плану
      </Link>
      <Card>
        <CardHeader>
          <CardTitle>Завершение тестовой недели</CardTitle>
          <p className="text-sm text-muted">
            После завершения веса в неделях 2..N будут пересчитаны по e1RM из ваших сетов.
          </p>
          {done && <p className="text-sm text-emerald-500">Пересчитано упражнений: {updated}</p>}
        </CardHeader>
      </Card>
      <Button onClick={finalize} disabled={loading}>
        {loading ? "Пересчитываем..." : "Пересчитать рабочие веса"}
      </Button>
    </div>
  );
}
