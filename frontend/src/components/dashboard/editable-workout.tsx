"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

  async function saveDay(day: WorkoutDay) {
    setSaving(true);
    try {
      const updated = await workoutApi.updateDay(plan.id, day.id, {
        exercises: day.exercises.map((e) => ({
          id: e.id,
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
        })),
      });
      onChanged(updated);
      setEditingDay(null);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-3">
      {plan.days.filter((d) => !d.is_rest).map((day) => (
        <div key={day.id} className="glass-card p-4">
          <div className="flex items-center justify-between">
            <div className="display font-bold">{day.title}</div>
            <Button size="sm" variant="outline" onClick={() => setEditingDay({ ...day, exercises: [...day.exercises] })}>
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
              <div key={ex.id} className="glass-card p-3 space-y-2">
                <div className="flex justify-between text-sm font-semibold">
                  <span>{ex.exercise.name}</span>
                  <button onClick={() => setEditingDay((d) => d ? ({ ...d, exercises: d.exercises.filter((_, i) => i !== idx) }) : d)}>
                    <Trash2 size={14} />
                  </button>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <Input type="number" value={ex.sets} onChange={(e) => setEditingDay((d) => {
                    if (!d) return d;
                    const copy = [...d.exercises];
                    copy[idx] = { ...copy[idx], sets: +e.target.value };
                    return { ...d, exercises: copy };
                  })} />
                  <Input type="number" value={ex.reps_min} onChange={(e) => setEditingDay((d) => {
                    if (!d) return d;
                    const copy = [...d.exercises];
                    copy[idx] = { ...copy[idx], reps_min: +e.target.value };
                    return { ...d, exercises: copy };
                  })} />
                  <Input type="number" value={ex.weight_kg ?? 0} onChange={(e) => setEditingDay((d) => {
                    if (!d) return d;
                    const copy = [...d.exercises];
                    copy[idx] = { ...copy[idx], weight_kg: +e.target.value };
                    return { ...d, exercises: copy };
                  })} />
                </div>
              </div>
            ))}

            <div className="glass-card p-3">
              <div className="text-sm font-semibold mb-2 flex items-center gap-2"><Plus size={14} /> Добавить упражнение</div>
              <ExerciseSelector onSelect={(exercise: Exercise) => {
                setEditingDay((d) => d ? ({
                  ...d,
                  exercises: [...d.exercises, {
                    id: Date.now(),
                    position: d.exercises.length,
                    sets: 3,
                    reps_min: 8,
                    reps_max: 12,
                    reps: "8-12",
                    weight_kg: null,
                    rest_sec: 90,
                    notes: "",
                    exercise,
                  }],
                }) : d);
              }} />
            </div>

            <Button onClick={() => saveDay(editingDay)} disabled={saving}>{saving ? "Сохранение..." : "Сохранить день"}</Button>
          </div>
        </div>
      )}
    </div>
  );
}
