"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { workoutApi } from "@/features/workout/api";
import { trainingApi } from "@/features/training/api";
import type { ProgressResponse, TodayWorkout, WeeklyWorkout, WorkoutSetLogInput } from "@/features/training/types";
import type { WorkoutPlan } from "@/features/workout/types";
import { WorkoutViewer } from "@/components/dashboard/workout-viewer";
import { EditableWorkout } from "@/components/dashboard/editable-workout";

export default function WorkoutPlanPage() {
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [reps, setReps] = useState<Record<number, number>>({});
  const [weights, setWeights] = useState<Record<number, number>>({});
  const [rirs, setRirs] = useState<Record<number, number>>({});
  const [today, setToday] = useState<TodayWorkout | null>(null);
  const [weekly, setWeekly] = useState<WeeklyWorkout | null>(null);
  const [progress, setProgress] = useState<ProgressResponse | null>(null);

  useEffect(() => {
    workoutApi.current().then(setPlan);
    trainingApi.todayWorkout().then(setToday).catch(() => setToday(null));
    trainingApi.weeklyWorkout().then(setWeekly).catch(() => setWeekly(null));
    trainingApi.progress().then(setProgress).catch(() => setProgress(null));
  }, []);

  const testExercises = useMemo(() => {
    if (!plan) return [];
    return plan.days.flatMap((d) => d.exercises.map((e) => ({ day: d, e }))).filter((x) => x.e.is_test_set);
  }, [plan]);

  if (!plan) return <div className="glass-card p-6">Нет активного плана.</div>;

  async function submitDayLog() {
    if (!today?.day) return;
    const sets: WorkoutSetLogInput[] = [];
    for (const ex of today.day.exercises) {
      const repsVal = reps[ex.id];
      const weightVal = weights[ex.id] ?? ex.weight_kg ?? 0;
      const rirVal = rirs[ex.id];
      if (!repsVal || !weightVal || rirVal === undefined) continue;
      sets.push({
        workout_exercise_id: ex.id,
        set_index: 1,
        completed_reps: repsVal,
        completed_weight_kg: weightVal,
        rir: rirVal,
      });
    }
    if (!sets.length) return;
    await trainingApi.logWorkout({ sets });
    const updatedProgress = await trainingApi.progress();
    setProgress(updatedProgress);
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Workout Today</CardTitle></CardHeader>
        {today?.day ? (
          <div className="space-y-2">
            <div className="text-sm text-muted">Week {today.week_index} · {today.phase}</div>
            <div className="glass-card p-3 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-muted border-b border-[var(--border)]">
                    <th className="py-2">Упражнение</th>
                    <th className="py-2">Подходы</th>
                    <th className="py-2">Повторы</th>
                    <th className="py-2">Вес</th>
                    <th className="py-2">RIR</th>
                  </tr>
                </thead>
                <tbody>
                  {today.day.exercises.map((e) => (
                    <tr key={e.id} className="border-b border-[var(--border)]/50">
                      <td className="py-2">{e.exercise.name_ru || e.exercise.name}</td>
                      <td className="py-2">{e.sets}</td>
                      <td className="py-2"><Input type="number" placeholder={e.reps} value={reps[e.id] ?? ""} onChange={(ev) => setReps((p) => ({ ...p, [e.id]: +ev.target.value }))} /></td>
                      <td className="py-2"><Input type="number" placeholder="kg" value={weights[e.id] ?? e.weight_kg ?? ""} onChange={(ev) => setWeights((p) => ({ ...p, [e.id]: +ev.target.value }))} /></td>
                      <td className="py-2"><Input type="number" placeholder="RIR" min={0} max={10} value={rirs[e.id] ?? ""} onChange={(ev) => setRirs((p) => ({ ...p, [e.id]: +ev.target.value }))} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Button onClick={submitDayLog}>Log Workout</Button>
          </div>
        ) : (
          <div className="glass-card p-4 text-sm text-muted">Сегодня запланирован отдых или нет активного дня.</div>
        )}
      </Card>

      <Card>
        <CardHeader><CardTitle>Полный план · {plan.name}</CardTitle></CardHeader>
        <WorkoutViewer plan={plan} />
      </Card>

      {weekly && (
        <Card>
          <CardHeader><CardTitle>План на неделю {weekly.week_index}</CardTitle></CardHeader>
          <div className="space-y-3">
            {weekly.days.map((day) => (
              <div key={day.id} className="glass-card p-3 overflow-x-auto">
                <div className="font-semibold mb-2">{day.title}</div>
                {day.is_rest ? (
                  <div className="text-sm text-muted">Восстановление</div>
                ) : (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-muted border-b border-[var(--border)]">
                        <th className="py-2">Упражнение</th>
                        <th className="py-2">Подходы</th>
                        <th className="py-2">Повторы</th>
                        <th className="py-2">Вес</th>
                      </tr>
                    </thead>
                    <tbody>
                      {day.exercises.map((ex) => (
                        <tr key={ex.id} className="border-b border-[var(--border)]/50">
                          <td className="py-2">{ex.exercise.name_ru || ex.exercise.name}</td>
                          <td className="py-2">{ex.sets}</td>
                          <td className="py-2">{ex.reps}</td>
                          <td className="py-2">{ex.weight_kg ? `${ex.weight_kg} кг` : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Редактирование программы</CardTitle></CardHeader>
        <EditableWorkout plan={plan} onChanged={setPlan} />
      </Card>

      {testExercises.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Результаты тестовой недели</CardTitle></CardHeader>
          <div className="space-y-2">
            {testExercises.map(({ day, e }) => (
              <div key={e.id} className="glass-card p-3 grid md:grid-cols-[1fr_120px_120px_140px] gap-2 items-center">
                <div className="text-sm">{day.title}: {e.exercise.name}</div>
                <Input type="number" placeholder="reps" value={reps[e.id] ?? ""} onChange={(ev) => setReps((p) => ({ ...p, [e.id]: +ev.target.value }))} />
                <Input type="number" placeholder="kg" value={weights[e.id] ?? e.weight_kg ?? ""} onChange={(ev) => setWeights((p) => ({ ...p, [e.id]: +ev.target.value }))} />
                <Button size="sm" onClick={() => workoutApi.submitResult({
                  workout_exercise_id: e.id,
                  reps_completed: reps[e.id] ?? 0,
                  weight_kg: weights[e.id] ?? e.weight_kg ?? 0,
                })}>
                  Сохранить тест
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {progress && (
        <Card>
          <CardHeader><CardTitle>Progress</CardTitle></CardHeader>
          <div className="grid md:grid-cols-2 gap-3">
            <div className="glass-card p-3">
              <div className="text-xs text-muted">Weekly volume</div>
              {Object.entries(progress.weekly_volume).map(([week, vol]) => (
                <div key={week} className="text-sm">Week {week}: {vol.toFixed(1)} kg</div>
              ))}
            </div>
            <div className="glass-card p-3">
              <div className="text-xs text-muted">Strength trend ({progress.volume_delta_pct}%)</div>
              <div className="text-sm">{progress.strength.slice(-5).map((p) => p.estimated_1rm.toFixed(1)).join(" → ") || "No logs yet"}</div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
