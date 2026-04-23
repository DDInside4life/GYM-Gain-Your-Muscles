"use client";

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import type { WorkoutPlan } from "@/features/workout/types";

type Props = {
  plan: WorkoutPlan;
};

export function WorkoutViewer({ plan }: Props) {
  const [selectedWeek, setSelectedWeek] = useState(1);
  const currentDayIndex = useMemo(() => {
    const d = new Date().getDay();
    return d === 0 ? 6 : d - 1;
  }, []);
  const weeks = useMemo(() => Array.from(new Set(plan.days.map((d) => d.week_index))).sort((a, b) => a - b), [plan.days]);
  const visibleDays = useMemo(() => plan.days.filter((d) => d.week_index === selectedWeek), [plan.days, selectedWeek]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {weeks.map((week) => (
          <button
            key={week}
            className={`px-3 py-1 rounded-lg text-sm border ${selectedWeek === week ? "bg-brand-gradient text-white border-transparent" : "border-[var(--border)]"}`}
            onClick={() => setSelectedWeek(week)}
          >
            Week {week}
          </button>
        ))}
      </div>
      {visibleDays.map((day) => {
        const isToday = day.day_index % 7 === currentDayIndex;
        return (
          <div key={day.id} className={`glass-card p-4 ${isToday ? "ring-1 ring-brand-500/40" : ""}`}>
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="display font-bold">День {day.day_index + 1} · {day.title}</div>
                <div className="text-xs text-muted">Неделя {day.week_index} · {day.phase}</div>
              </div>
              <div className="flex gap-2 items-center">
                {isToday && <Badge tone="brand">Сегодня</Badge>}
                <Badge>{day.is_rest ? "Rest" : "Train"}</Badge>
              </div>
            </div>
            {!day.is_rest && (
              <div className="overflow-x-auto">
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
                      <tr key={ex.id} className="border-b border-[var(--border)]/60">
                        <td className="py-2">{ex.exercise.name_ru || ex.exercise.name}</td>
                        <td className="py-2">{ex.sets}</td>
                        <td className="py-2">{ex.reps}</td>
                        <td className="py-2">{ex.weight_kg ? `${ex.weight_kg} кг` : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {day.is_rest && <div className="mt-2 text-sm text-muted">Восстановление.</div>}
          </div>
        );
      })}
    </div>
  );
}
