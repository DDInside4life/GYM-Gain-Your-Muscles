"use client";

import { useEffect, useMemo, useState } from "react";
import { Input, Label, Select } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Exercise } from "@/features/workout/types";

const MUSCLE_OPTIONS = [
  { value: "", label: "Все" },
  { value: "chest", label: "Грудь" },
  { value: "back", label: "Спина" },
  { value: "legs", label: "Ноги" },
  { value: "glutes", label: "Ягодицы" },
  { value: "shoulders", label: "Плечи" },
  { value: "biceps", label: "Бицепс" },
  { value: "triceps", label: "Трицепс" },
  { value: "core", label: "Пресс" },
  { value: "calves", label: "Икры" },
  { value: "cardio", label: "Кардио" },
];

const EQUIPMENT_OPTIONS = [
  { value: "", label: "Все" },
  { value: "bodyweight", label: "Свой вес" },
  { value: "barbell", label: "Штанга" },
  { value: "dumbbell", label: "Гантели" },
  { value: "machine", label: "Тренажёр" },
  { value: "cable", label: "Блок" },
];

type Props = {
  onSelect: (exercise: Exercise) => void;
};

export function ExerciseSelector({ onSelect }: Props) {
  const [items, setItems] = useState<Exercise[]>([]);
  const [q, setQ] = useState("");
  const [muscle, setMuscle] = useState("");
  const [equipment, setEquipment] = useState("");

  useEffect(() => {
    const qs = new URLSearchParams();
    if (q) qs.set("q", q);
    if (muscle) qs.set("muscle", muscle);
    if (equipment) qs.append("equipment", equipment);
    api<Exercise[]>(`/exercises?${qs.toString()}`).then(setItems).catch(() => setItems([]));
  }, [q, muscle, equipment]);

  const filtered = useMemo(() => items.slice(0, 30), [items]);

  return (
    <div className="space-y-3">
      <div className="grid md:grid-cols-3 gap-2">
        <div>
          <Label>Поиск</Label>
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Жим, тяга…" />
        </div>
        <div>
          <Label>Мышца</Label>
          <Select value={muscle} onChange={(e) => setMuscle(e.target.value)}>
            {MUSCLE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </Select>
        </div>
        <div>
          <Label>Оборудование</Label>
          <Select value={equipment} onChange={(e) => setEquipment(e.target.value)}>
            {EQUIPMENT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </Select>
        </div>
      </div>
      <div className="max-h-72 overflow-auto space-y-2">
        {filtered.length === 0 && (
          <div className="text-sm text-muted text-center py-6">Упражнения не найдены</div>
        )}
        {filtered.map((it) => (
          <div key={it.id} className="glass-card p-3 flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold">{it.name_ru || it.name}</div>
              <div className="text-[11px] text-muted">{it.primary_muscle} · {it.equipment}</div>
            </div>
            <Button size="sm" onClick={() => onSelect(it)}>Добавить</Button>
          </div>
        ))}
      </div>
    </div>
  );
}
