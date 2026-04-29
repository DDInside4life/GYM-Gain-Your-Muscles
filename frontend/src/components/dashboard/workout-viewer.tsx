"use client";

import { useEffect, useMemo, useState } from "react";
import { Save } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { workoutApi } from "@/features/workout/api";
import type { WorkoutPlan } from "@/features/workout/types";

type Props = {
  plan: WorkoutPlan;
  onChanged?: (plan: WorkoutPlan) => void;
};

const PHASE_LABEL: Record<string, string> = {
  test: "Тестовая",
  work: "Рабочая",
};

function formatRest(seconds: number): string {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m === 0) return `${s} сек`;
  if (s === 0) return `${m} мин`;
  return `${m} мин ${s} сек`;
}

export function WorkoutViewer({ plan, onChanged }: Props) {
  const weeks = useMemo(
    () => Array.from(new Set(plan.days.map((d) => d.week_index))).sort((a, b) => a - b),
    [plan.days],
  );
  const [selectedWeek, setSelectedWeek] = useState<number>(weeks[0] ?? 1);

  useEffect(() => {
    if (!weeks.includes(selectedWeek)) setSelectedWeek(weeks[0] ?? 1);
  }, [weeks, selectedWeek]);

  const visibleDays = useMemo(
    () => plan.days.filter((d) => d.week_index === selectedWeek),
    [plan.days, selectedWeek],
  );

  async function persistWeight(workoutExerciseId: number, raw: string) {
    const trimmed = raw.trim();
    const next = trimmed === "" ? null : Math.max(0, Math.min(700, Number.parseFloat(trimmed)));
    if (trimmed !== "" && Number.isNaN(next as number)) return;
    await workoutApi.setExerciseWeight(workoutExerciseId, next);
    if (onChanged) {
      onChanged({
        ...plan,
        days: plan.days.map((d) => ({
          ...d,
          exercises: d.exercises.map((ex) =>
            ex.id === workoutExerciseId ? { ...ex, weight_kg: next } : ex,
          ),
        })),
      });
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {weeks.map((week) => (
          <button
            key={week}
            type="button"
            className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
              selectedWeek === week
                ? "bg-brand-gradient dark:bg-neon-gradient text-white border-transparent shadow-glow-brand dark:shadow-glow"
                : "border-[var(--border)] hover:border-brand-500/40"
            }`}
            onClick={() => setSelectedWeek(week)}
          >
            Неделя {week}
          </button>
        ))}
      </div>

      {visibleDays.map((day) => (
        <div key={day.id} className="glass-card p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="display font-bold">{day.title}</div>
              {day.focus && (
                <div className="text-xs text-muted mt-0.5">{day.focus}</div>
              )}
            </div>
            <Badge>{day.is_rest ? "Отдых" : `Неделя ${day.week_index}`}</Badge>
          </div>
          {day.is_rest ? (
            <div className="text-sm text-muted">День восстановления.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-muted border-b border-[var(--border)]">
                    <th className="py-2">Упражнение</th>
                    <th className="py-2 w-[80px]">Подходы</th>
                    <th className="py-2 w-[100px]">Повторы</th>
                    <th className="py-2 w-[110px]">Отдых</th>
                    <th className="py-2 w-[140px]">Рабочий вес</th>
                  </tr>
                </thead>
                <tbody>
                  {day.exercises.map((ex) => (
                    <ExerciseRow
                      key={ex.id}
                      exerciseId={ex.id}
                      title={ex.exercise.name_ru || ex.exercise.name}
                      sets={ex.sets}
                      reps={ex.reps}
                      restSec={ex.rest_sec}
                      weightKg={ex.weight_kg}
                      notes={ex.notes}
                      onSave={persistWeight}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="text-[11px] text-muted mt-2">
            {PHASE_LABEL[day.phase] ?? day.phase}
          </div>
        </div>
      ))}
    </div>
  );
}

function ExerciseRow({
  exerciseId,
  title,
  sets,
  reps,
  restSec,
  weightKg,
  notes,
  onSave,
}: {
  exerciseId: number;
  title: string;
  sets: number;
  reps: string;
  restSec: number;
  weightKg: number | null;
  notes: string;
  onSave: (id: number, raw: string) => Promise<void>;
}) {
  const [draft, setDraft] = useState<string>(weightKg !== null ? String(weightKg) : "");
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  useEffect(() => {
    setDraft(weightKg !== null ? String(weightKg) : "");
  }, [weightKg]);

  async function commit() {
    if (saving) return;
    const baseline = weightKg !== null ? String(weightKg) : "";
    if (draft === baseline) return;
    setSaving(true);
    try {
      await onSave(exerciseId, draft);
      setSavedAt(Date.now());
    } finally {
      setSaving(false);
    }
  }

  return (
    <tr className="border-b border-[var(--border)]/60 align-top">
      <td className="py-2 pr-3">
        <div className="font-medium">{title}</div>
        {notes && <div className="text-[11px] text-muted mt-0.5">{notes}</div>}
      </td>
      <td className="py-2">{sets}</td>
      <td className="py-2">{reps}</td>
      <td className="py-2">{formatRest(restSec)}</td>
      <td className="py-2">
        <div className="flex items-center gap-1.5">
          <Input
            type="number"
            inputMode="decimal"
            min={0}
            max={700}
            step={0.5}
            placeholder="—"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={commit}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                (e.target as HTMLInputElement).blur();
              }
            }}
            className="h-9"
          />
          <span className="text-[11px] text-muted shrink-0">кг</span>
          {saving && <span className="text-[10px] text-muted">…</span>}
          {!saving && savedAt && Date.now() - savedAt < 1500 && (
            <Save size={12} className="text-emerald-500" />
          )}
        </div>
      </td>
    </tr>
  );
}
