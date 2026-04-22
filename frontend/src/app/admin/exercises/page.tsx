"use client";

import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Select } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { Equipment, Exercise, MuscleGroup } from "@/features/workout/types";

const MUSCLES: MuscleGroup[] = ["chest","back","legs","glutes","shoulders","biceps","triceps","core","calves","forearms","full_body","cardio"];
const EQUIPS: Equipment[] = ["bodyweight","barbell","dumbbell","machine","cable","kettlebell","bands"];

export default function AdminExercisesPage() {
  const [items, setItems] = useState<Exercise[]>([]);
  const [form, setForm] = useState({
    slug: "", name: "", description: "",
    primary_muscle: "chest" as MuscleGroup,
    equipment: "dumbbell" as Equipment,
    category: "compound" as "compound" | "isolation" | "cardio" | "mobility",
    difficulty: 2,
  });

  async function load() { setItems(await api<Exercise[]>("/exercises")); }
  useEffect(() => { load(); }, []);

  async function create() {
    await api("/exercises", {
      method: "POST",
      body: JSON.stringify({
        ...form,
        secondary_muscles: [],
        contraindications: [],
        is_active: true,
      }),
      auth: true,
    });
    setForm({ ...form, slug: "", name: "" });
    load();
  }

  async function remove(slug: string) {
    await api(`/exercises/${slug}`, { method: "DELETE", auth: true });
    load();
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Новое упражнение</CardTitle></CardHeader>
        <div className="grid md:grid-cols-3 gap-3">
          <div><Label>Slug</Label><Input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} /></div>
          <div><Label>Name</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
          <div>
            <Label>Muscle</Label>
            <Select value={form.primary_muscle} onChange={(e) => setForm({ ...form, primary_muscle: e.target.value as MuscleGroup })}>
              {MUSCLES.map((m) => <option key={m}>{m}</option>)}
            </Select>
          </div>
          <div>
            <Label>Equipment</Label>
            <Select value={form.equipment} onChange={(e) => setForm({ ...form, equipment: e.target.value as Equipment })}>
              {EQUIPS.map((m) => <option key={m}>{m}</option>)}
            </Select>
          </div>
          <div>
            <Label>Category</Label>
            <Select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value as never })}>
              <option value="compound">compound</option>
              <option value="isolation">isolation</option>
              <option value="cardio">cardio</option>
              <option value="mobility">mobility</option>
            </Select>
          </div>
          <div><Label>Difficulty</Label><Input type="number" min={1} max={5} value={form.difficulty} onChange={(e) => setForm({ ...form, difficulty: +e.target.value })} /></div>
        </div>
        <div className="mt-4"><Button onClick={create}>Создать</Button></div>
      </Card>

      <Card>
        <CardHeader><CardTitle>База упражнений · {items.length}</CardTitle></CardHeader>
        <div className="grid md:grid-cols-2 gap-2">
          {items.map((e) => (
            <div key={e.id} className="glass-card p-3 flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold">{e.name}</div>
                <div className="text-[11px] text-muted">{e.primary_muscle} · {e.equipment} · D{e.difficulty}</div>
              </div>
              <Button size="sm" variant="ghost" onClick={() => remove(e.slug)}><Trash2 size={14} /></Button>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
