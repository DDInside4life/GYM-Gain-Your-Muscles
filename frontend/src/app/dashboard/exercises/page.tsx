"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Input, Label, Select } from "@/components/ui/input";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Exercise } from "@/features/workout/types";

export default function DashboardExercisesPage() {
  const [q, setQ] = useState("");
  const [muscle, setMuscle] = useState("");
  const [view, setView] = useState<"grid" | "list">("grid");
  const [items, setItems] = useState<Exercise[]>([]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (muscle) params.set("muscle", muscle);
    api<Exercise[]>(`/exercises?${params.toString()}`).then(setItems);
  }, [q, muscle]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Упражнения</CardTitle></CardHeader>
        <div className="grid md:grid-cols-3 gap-3 items-end">
          <div><Label>Поиск</Label><Input value={q} onChange={(e) => setQ(e.target.value)} /></div>
          <div>
            <Label>Мышечная группа</Label>
            <Select value={muscle} onChange={(e) => setMuscle(e.target.value)}>
              <option value="">Все</option>
              <option value="chest">Грудь</option>
              <option value="back">Спина</option>
              <option value="legs">Ноги</option>
              <option value="glutes">Ягодицы</option>
              <option value="shoulders">Плечи</option>
              <option value="biceps">Бицепс</option>
              <option value="triceps">Трицепс</option>
              <option value="core">Пресс</option>
            </Select>
          </div>
          <div className="flex gap-2">
            <Button variant={view === "grid" ? "primary" : "outline"} onClick={() => setView("grid")}>Сетка</Button>
            <Button variant={view === "list" ? "primary" : "outline"} onClick={() => setView("list")}>Список</Button>
          </div>
        </div>
      </Card>

      <div className={view === "grid" ? "grid md:grid-cols-2 gap-3" : "space-y-2"}>
        {items.map((it) => (
          <Link key={it.id} href={`/dashboard/exercises/${it.id}`} className="glass-card p-4 block">
            <div className="display font-bold">{it.name_ru}</div>
            <div className="text-xs text-muted">{it.primary_muscle} · {it.equipment} · d{it.difficulty}</div>
            <p className="text-sm mt-2">{it.description}</p>
            <div className="text-[11px] text-muted mt-2">{it.name_en ?? ""}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
