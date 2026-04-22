"use client";

import { useEffect, useState } from "react";
import { ChevronUp, RefreshCcw, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { WorkoutForm } from "@/features/workout/workout-form";
import { WorkoutFeedback } from "@/components/dashboard/workout-feedback";
import { workoutApi } from "@/features/workout/api";
import type { WorkoutPlan } from "@/features/workout/types";
import { FOCUS_LABEL } from "@/lib/constants";

export default function WorkoutsPage() {
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [progressing, setProgressing] = useState(false);
  const [activeFeedbackDay, setActiveFeedbackDay] = useState<number | null>(null);

  useEffect(() => {
    workoutApi.current().then(setPlan).catch(() => setPlan(null));
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

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>AI-генератор тренировок</CardTitle>
          <Zap className="text-brand-500" />
        </CardHeader>
        <WorkoutForm onGenerated={setPlan} />
      </Card>

      {plan && (
        <Card>
          <CardHeader>
            <CardTitle>{plan.name}</CardTitle>
            <div className="flex gap-2">
              <Badge tone="violet">Неделя {plan.week_number}</Badge>
              <Badge>{plan.split_type.replace("_", " ")}</Badge>
              <Button size="sm" variant="outline" onClick={progress} disabled={progressing}>
                <RefreshCcw size={14} /> Следующая неделя
              </Button>
            </div>
          </CardHeader>

          <div className="space-y-3">
            {plan.days.map((d) => (
              <div key={d.id} className="glass-card p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <div className="display font-bold">День {d.day_index + 1} · {d.title}</div>
                    <div className="text-xs text-muted">
                      {d.focus.split(", ").map((f) => FOCUS_LABEL[f] ?? f).join(" · ")}
                    </div>
                  </div>
                  {!d.is_rest && (
                    <Button size="sm" variant="ghost" onClick={() => setActiveFeedbackDay(
                      activeFeedbackDay === d.id ? null : d.id,
                    )}>
                      <ChevronUp size={14} className={activeFeedbackDay === d.id ? "" : "rotate-180"} />
                      Фидбек
                    </Button>
                  )}
                </div>

                {d.is_rest ? (
                  <div className="text-sm text-muted">Восстановление. Сон, растяжка, прогулка.</div>
                ) : (
                  <div className="grid md:grid-cols-2 gap-2">
                    {d.exercises.map((we) => (
                      <div key={we.id} className="flex items-center justify-between p-3 rounded-xl bg-black/5 dark:bg-white/5">
                        <div>
                          <div className="text-sm font-semibold">{we.exercise.name}</div>
                          <div className="text-[11px] text-muted">
                            {we.exercise.primary_muscle} · {we.exercise.equipment}
                          </div>
                        </div>
                        <div className="text-right text-xs">
                          <div className="font-semibold">{we.sets} × {we.reps}</div>
                          <div className="text-muted">{we.weight_kg ? `${we.weight_kg} кг` : "—"} · {we.rest_sec}с</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {activeFeedbackDay === d.id && (
                  <div className="mt-3">
                    <WorkoutFeedback dayId={d.id} onSubmitted={() => setActiveFeedbackDay(null)} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
