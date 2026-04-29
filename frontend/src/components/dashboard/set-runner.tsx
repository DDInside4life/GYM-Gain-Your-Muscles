"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import type { WorkoutExercise } from "@/features/workout/types";
import { workoutApi } from "@/features/workout/api";
import { RestTimer } from "./rest-timer";

type Props = {
  exercise: WorkoutExercise;
  onLogged?: () => void;
};

export function SetRunner({ exercise, onLogged }: Props) {
  const [setIndex, setSetIndex] = useState(0);
  const [weight, setWeight] = useState(Number(exercise.weight_kg ?? 0));
  const [reps, setReps] = useState(exercise.reps_min);
  const [rir, setRir] = useState(Number(exercise.target_rir ?? 2));
  const [loading, setLoading] = useState(false);

  async function submitSet() {
    setLoading(true);
    try {
      await workoutApi.logSet({
        workout_exercise_id: exercise.id,
        set_index: setIndex,
        completed_reps: reps,
        completed_weight_kg: weight,
        rir,
      });
      setSetIndex((v) => v + 1);
      onLogged?.();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass-card p-3 space-y-2">
      <div className="text-sm font-semibold">{exercise.exercise.name}</div>
      <div className="text-xs text-muted">
        План: {exercise.sets}x{exercise.reps_min}-{exercise.reps_max}
        {exercise.is_test_set ? " · Тест" : ""}
      </div>
      {!!exercise.test_instruction && (
        <div className="text-xs text-brand-500">{exercise.test_instruction}</div>
      )}
      {!!exercise.explainability && (
        <details className="text-xs rounded-md border border-border/60 bg-muted/20 px-2 py-1">
          <summary className="cursor-pointer select-none text-muted-foreground">Почему такой вес?</summary>
          <div className="mt-1 space-y-1 text-muted-foreground">
            <div>{exercise.explainability.reason}</div>
            {exercise.explainability.target_percent_1rm != null && (
              <div>Цель: {(exercise.explainability.target_percent_1rm * 100).toFixed(0)}% от 1RM</div>
            )}
            {exercise.explainability.based_on_e1rm != null && (
              <div>База расчёта e1RM: {exercise.explainability.based_on_e1rm.toFixed(1)} кг</div>
            )}
          </div>
        </details>
      )}
      <div className="grid grid-cols-4 gap-2">
        <div>
          <Label>Сет</Label>
          <Input value={setIndex + 1} onChange={(e) => setSetIndex(Math.max(0, Number(e.target.value) - 1 || 0))} />
        </div>
        <div>
          <Label>Вес</Label>
          <Input inputMode="decimal" value={weight} onChange={(e) => setWeight(Number(e.target.value) || 0)} />
        </div>
        <div>
          <Label>Повторы</Label>
          <Input value={reps} onChange={(e) => setReps(Number(e.target.value) || 0)} />
        </div>
        <div>
          <Label>RIR</Label>
          <Input inputMode="decimal" value={rir} onChange={(e) => setRir(Number(e.target.value) || 0)} />
        </div>
      </div>
      <div className="flex items-center justify-between">
        <RestTimer initialSec={exercise.rest_sec} />
        <Button size="sm" onClick={submitSet} disabled={loading}>
          {loading ? "Сохранение..." : "Сохранить сет"}
        </Button>
      </div>
    </div>
  );
}
