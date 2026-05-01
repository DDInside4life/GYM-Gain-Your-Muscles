"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Trash2 } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { workoutApi } from "@/features/workout/api";
import type { WorkoutPlan } from "@/features/workout/types";
import { E1rmChart } from "@/components/dashboard/e1rm-chart";

export default function WorkoutsHistoryPage() {
  const [plans, setPlans] = useState<WorkoutPlan[]>([]);
  const [progress, setProgress] = useState<Record<number, number[]>>({});

  useEffect(() => {
    workoutApi.history().then(async (rows) => {
      setPlans(rows);
      const byPlan: Record<number, number[]> = {};
      for (const p of rows) {
        try {
          const weeks = await workoutApi.planProgress(p.id);
          const values = weeks.map((w) => {
            const vals = Object.values(w.top_e1rm_per_exercise);
            if (vals.length === 0) return 0;
            return Math.max(...vals);
          });
          byPlan[p.id] = values;
        } catch {
          byPlan[p.id] = [];
        }
      }
      setProgress(byPlan);
    });
  }, []);

  const sorted = useMemo(
    () => [...plans].sort((a, b) => b.id - a.id),
    [plans],
  );

  async function clearHistory() {
    await workoutApi.clearHistory();
    setPlans([]);
    setProgress({});
  }

  return (
    <div className="space-y-4">
      <Link href="/dashboard/workouts" className="text-sm text-muted hover:text-inherit">
        Назад к тренировкам
      </Link>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <CardTitle>История мезоциклов</CardTitle>
            <Button size="sm" variant="outline" onClick={clearHistory} disabled={sorted.length === 0}>
              <Trash2 size={14} /> Очистить историю
            </Button>
          </div>
        </CardHeader>
      </Card>
      {sorted.map((plan) => (
        <Card key={plan.id}>
          <CardHeader>
            <div className="font-semibold">{plan.name}</div>
            <div className="text-xs text-muted">
              Месяц {plan.month_index} · {plan.split_type}
            </div>
            <E1rmChart values={(progress[plan.id] ?? []).filter((v) => v > 0)} />
          </CardHeader>
        </Card>
      ))}
    </div>
  );
}
