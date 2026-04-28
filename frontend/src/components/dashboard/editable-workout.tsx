"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { workoutApi } from "@/features/workout/api";
import type { Exercise, WorkoutDay, WorkoutPlan } from "@/features/workout/types";
import { ExerciseSelector } from "./exercise-selector";

type Props = {
  plan: WorkoutPlan;
  onChanged: (plan: WorkoutPlan) => void;
};

export function EditableWorkout({ plan, onChanged }: Props) {
  const [editingDay, setEditingDay] = useState<WorkoutDay | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>("");

  async function saveDay(day: WorkoutDay) {
    setSaving(true);
    setError("");
    try {
      const updated = await workoutApi.updateDay(plan.id, day.id, {
        exercises: day.exercises.map((e, idx) => ({
          id: e.id > 0 ? e.id : undefined,
          exercise_id: e.exercise.id,
          sets: e.sets,
          reps_min: e.reps_min,
          reps_max: e.reps_max,
          weight_kg: e.weight_kg,
          rest_sec: e.rest_sec,
          notes: e.notes,
          target_percent_1rm: e.target_percent_1rm ?? null,
          is_test_set: !!e.is_test_set,
          test_instruction: e.test_instruction ?? "",
          target_rir: e.target_rir ?? null,
          rpe_text: e.rpe_text ?? "",
        })).map((row, idx) => ({ ...row, position: idx })),
      });
      onChanged(updated);
      setEditingDay(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить день");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-3">
      {plan.days.filter((d) => !d.is_rest).map((day) => (
        <div key={day.id} className="glass-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="display font-bold">{day.title}</div>
              <div className="text-xs text-muted">
                Неделя {day.week_index} · {day.exercises.length} упр.
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setEditingDay({ ...day, exercises: [...day.exercises] })}
            >
              Редактировать
            </Button>
          </div>
        </div>
      ))}

      {editingDay && (
        <div className="fixed inset-0 bg-black/40 z-40 flex justify-end">
          <div className="w-full max-w-xl h-full overflow-auto bg-[var(--card)] p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="display font-bold">Редактирование: {editingDay.title}</div>
              <Button variant="ghost" onClick={() => setEditingDay(null)}>Закрыть</Button>
            </div>

            {editingDay.exercises.map((ex, idx) => (
              <div key={`${ex.id}-${idx}`} className="glass-card p-3 space-y-3">
                <div className="flex justify-between text-sm font-semibold">
                  <span>{ex.exercise.name_ru || ex.exercise.name}</span>
                  <button
                    type="button"
                    onClick={() => setEditingDay((d) =>
                      d ? ({ ...d, exercises: d.exercises.filter((_, i) => i !== idx) }) : d,
                    )}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <Label>Подходы</Label>
                    <Input
                      type="number" min={1} max={8} value={ex.sets}
                      onChange={(e) => setEditingDay((d) => {
                        if (!d) return d;
                        const copy = [...d.exercises];
                        copy[idx] = { ...copy[idx], sets: Number(e.target.value) };
                        return { ...d, exercises: copy };
                      })}
                    />
                  </div>
                  <div>
                    <Label>Повт. от</Label>
                    <Input
                      type="number" min={1} max={30} value={ex.reps_min}
                      onChange={(e) => setEditingDay((d) => {
                        if (!d) return d;
                        const copy = [...d.exercises];
                        copy[idx] = { ...copy[idx], reps_min: Number(e.target.value) };
                        return { ...d, exercises: copy };
                      })}
                    />
                  </div>
                  <div>
                    <Label>Повт. до</Label>
                    <Input
                      type="number" min={1} max={30} value={ex.reps_max}
                      onChange={(e) => setEditingDay((d) => {
                        if (!d) return d;
                        const copy = [...d.exercises];
                        copy[idx] = { ...copy[idx], reps_max: Number(e.target.value) };
                        return { ...d, exercises: copy };
                      })}
                    />
                  </div>
                  <div>
                    <Label>Вес, кг</Label>
                    <Input
                      type="number" min={0} value={ex.weight_kg ?? 0}
                      onChange={(e) => setEditingDay((d) => {
                        if (!d) return d;
                        const copy = [...d.exercises];
                        copy[idx] = { ...copy[idx], weight_kg: Number(e.target.value) || null };
                        return { ...d, exercises: copy };
                      })}
                    />
                  </div>
                  <div>
                    <Label>Отдых, сек</Label>
                    <Input
                      type="number" min={20} max={600} value={ex.rest_sec}
                      onChange={(e) => setEditingDay((d) => {
                        if (!d) return d;
                        const copy = [...d.exercises];
                        copy[idx] = { ...copy[idx], rest_sec: Number(e.target.value) };
                        return { ...d, exercises: copy };
                      })}
                    />
                  </div>
                  <div>
                    <Label>RIR</Label>
                    <Input
                      type="number" min={0} max={10} step={0.5}
                      value={ex.target_rir ?? 0}
                      onChange={(e) => setEditingDay((d) => {
                        if (!d) return d;
                        const copy = [...d.exercises];
                        copy[idx] = { ...copy[idx], target_rir: Number(e.target.value) };
                        return { ...d, exercises: copy };
                      })}
                    />
                  </div>
                </div>
              </div>
            ))}

            <div className="glass-card p-3">
              <div className="text-sm font-semibold mb-2 flex items-center gap-2">
                <Plus size={14} /> Добавить упражнение
              </div>
              <ExerciseSelector
                onSelect={(exercise: Exercise) => {
                  setEditingDay((d) =>
                    d
                      ? {
                          ...d,
                          exercises: [
                            ...d.exercises,
                            {
                              id: -Date.now(),
                              position: d.exercises.length,
                              sets: 3,
                              reps_min: 8,
                              reps_max: 12,
                              reps: "8-12",
                              weight_kg: null,
                              rest_sec: 90,
                              notes: "",
                              target_rir: 2,
                              rpe_text: "Контроль техники, RIR 2",
                              exercise,
                            },
                          ],
                        }
                      : d,
                  );
                }}
              />
            </div>

            {error && (
              <div className="glass-card p-3 text-sm text-red-400 border border-red-500/40">
                {error}
              </div>
            )}

            <div className="flex gap-2">
              <Button onClick={() => saveDay(editingDay)} disabled={saving}>
                {saving ? "Сохранение…" : "Сохранить день"}
              </Button>
              <Button variant="outline" onClick={() => setEditingDay(null)}>Отмена</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
