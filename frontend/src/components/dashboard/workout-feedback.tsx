"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea, Label } from "@/components/ui/input";
import { workoutApi } from "@/features/workout/api";
import type { Difficulty } from "@/features/workout/types";

const DIFFICULTIES: { value: Difficulty; label: string }[] = [
  { value: "very_easy", label: "Очень легко" },
  { value: "easy", label: "Легко" },
  { value: "ok", label: "Норм" },
  { value: "hard", label: "Тяжело" },
  { value: "very_hard", label: "Очень тяжело" },
];

const DISCOMFORTS = ["knee", "back", "shoulder", "wrist", "elbow"];

export function WorkoutFeedback({ dayId, onSubmitted }: { dayId: number; onSubmitted?: () => void }) {
  const [completed, setCompleted] = useState(true);
  const [difficulty, setDifficulty] = useState<Difficulty>("ok");
  const [discomfort, setDiscomfort] = useState<string[]>([]);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function submit() {
    setSaving(true);
    try {
      await workoutApi.feedback({ day_id: dayId, completed, difficulty, discomfort, note });
      setSaved(true);
      onSubmitted?.();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="glass-card p-4 space-y-3 animate-fade-up">
      <div className="flex items-center gap-2">
        <label className="inline-flex items-center gap-2 text-sm">
          <input type="checkbox" checked={completed} onChange={(e) => setCompleted(e.target.checked)} />
          Выполнено
        </label>
      </div>

      <div className="flex flex-wrap gap-2">
        {DIFFICULTIES.map((d) => (
          <button
            key={d.value}
            onClick={() => setDifficulty(d.value)}
            className={`px-3 py-1.5 text-xs rounded-full border transition ${
              difficulty === d.value
                ? "bg-brand-gradient text-white border-transparent"
                : "border-[var(--border)]"
            }`}
          >
            {d.label}
          </button>
        ))}
      </div>

      <div>
        <Label>Дискомфорт</Label>
        <div className="flex flex-wrap gap-2">
          {DISCOMFORTS.map((d) => (
            <button
              key={d}
              onClick={() =>
                setDiscomfort((arr) => (arr.includes(d) ? arr.filter((x) => x !== d) : [...arr, d]))
              }
              className={`px-3 py-1.5 text-xs rounded-full border transition ${
                discomfort.includes(d)
                  ? "bg-brand-500/20 text-brand-500 border-brand-500/40"
                  : "border-[var(--border)]"
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      <div>
        <Label>Заметка</Label>
        <Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Как прошла тренировка?" />
      </div>

      <Button onClick={submit} disabled={saving}>
        {saved ? "Сохранено" : saving ? "Сохранение…" : "Сохранить фидбек"}
      </Button>
    </div>
  );
}
