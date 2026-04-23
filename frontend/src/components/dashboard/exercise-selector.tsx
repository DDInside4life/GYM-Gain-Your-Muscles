"use client";

import { useEffect, useMemo, useState } from "react";
import { Input, Label, Select } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Exercise } from "@/features/workout/types";

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
    api<Exercise[]>(`/exercises?${qs.toString()}`).then(setItems);
  }, [q, muscle, equipment]);

  const filtered = useMemo(() => items.slice(0, 30), [items]);

  return (
    <div className="space-y-3">
      <div className="grid md:grid-cols-3 gap-2">
        <div><Label>Поиск</Label><Input value={q} onChange={(e) => setQ(e.target.value)} /></div>
        <div>
          <Label>Мышца</Label>
          <Select value={muscle} onChange={(e) => setMuscle(e.target.value)}>
            <option value="">all</option>
            <option value="chest">chest</option><option value="back">back</option><option value="legs">legs</option>
            <option value="shoulders">shoulders</option><option value="core">core</option>
          </Select>
        </div>
        <div>
          <Label>Оборудование</Label>
          <Select value={equipment} onChange={(e) => setEquipment(e.target.value)}>
            <option value="">all</option>
            <option value="bodyweight">bodyweight</option><option value="dumbbell">dumbbell</option>
            <option value="barbell">barbell</option><option value="machine">machine</option>
            <option value="cable">cable</option>
          </Select>
        </div>
      </div>
      <div className="max-h-72 overflow-auto space-y-2">
        {filtered.map((it) => (
          <div key={it.id} className="glass-card p-3 flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold">{it.name}</div>
              <div className="text-[11px] text-muted">{it.primary_muscle} · {it.equipment}</div>
            </div>
            <Button size="sm" onClick={() => onSelect(it)}>Добавить</Button>
          </div>
        ))}
      </div>
    </div>
  );
}
