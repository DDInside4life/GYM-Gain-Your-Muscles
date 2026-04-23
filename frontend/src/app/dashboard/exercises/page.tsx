"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Dumbbell, LayoutGrid, List, Search } from "lucide-react";
import { Input, Label, Select } from "@/components/ui/input";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { Exercise } from "@/features/workout/types";

const MUSCLE_GRADIENTS: Record<string, string> = {
  chest: "from-brand-500/30 to-brand-900/10",
  back: "from-violet-500/30 to-violet-900/10",
  legs: "from-brand-400/25 to-violet-500/10",
  glutes: "from-violet-400/25 to-brand-500/10",
  shoulders: "from-brand-300/25 to-violet-400/10",
  biceps: "from-violet-300/30 to-brand-400/10",
  triceps: "from-brand-400/30 to-violet-300/10",
  core: "from-violet-500/20 to-brand-300/10",
};

const DIFFICULTY_LABEL: Record<number, { label: string; tone: "brand" | "violet" | "default" }> = {
  1: { label: "Лёгкий", tone: "default" },
  2: { label: "Средний", tone: "violet" },
  3: { label: "Сложный", tone: "brand" },
};

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
    <div className="space-y-6 animate-fade-up">
      <Card>
        <CardHeader><CardTitle>Упражнения</CardTitle></CardHeader>
        <div className="grid md:grid-cols-3 gap-3 items-end">
          <div className="relative">
            <Label>Поиск</Label>
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
              <Input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Жим, приседания…"
                className="pl-8"
              />
            </div>
          </div>
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
            <Button variant={view === "grid" ? "primary" : "outline"} size="sm" onClick={() => setView("grid")}>
              <LayoutGrid size={14} /> Сетка
            </Button>
            <Button variant={view === "list" ? "primary" : "outline"} size="sm" onClick={() => setView("list")}>
              <List size={14} /> Список
            </Button>
          </div>
        </div>
      </Card>

      {items.length === 0 && (
        <div className="glass-card p-10 text-center text-muted">Упражнения не найдены</div>
      )}

      <div className={view === "grid" ? "grid sm:grid-cols-2 lg:grid-cols-3 gap-3" : "space-y-2"}>
        {items.map((it) =>
          view === "grid" ? (
            <Link
              key={it.id}
              href={`/dashboard/exercises/${it.id}`}
              className="glass-card p-0 block overflow-hidden group hover:shadow-glow transition-shadow duration-300"
            >
              <div className={`h-32 bg-gradient-to-br ${MUSCLE_GRADIENTS[it.primary_muscle] ?? "from-violet-500/20 to-brand-500/10"} grid place-items-center relative`}>
                <div className="absolute inset-0 grid-bg opacity-20" />
                {it.image_url ? (
                  <img src={it.image_url} alt={it.name_ru} className="h-full w-full object-cover opacity-80" />
                ) : (
                  <div className="h-14 w-14 rounded-full bg-white/5 border border-white/10 grid place-items-center group-hover:scale-110 transition-transform duration-300">
                    <Dumbbell size={24} className="opacity-40" />
                  </div>
                )}
                <span className="absolute top-2 left-2 text-[10px] px-2 py-0.5 rounded-full bg-black/50 text-white font-medium backdrop-blur-sm">
                  {it.primary_muscle}
                </span>
              </div>
              <div className="p-3">
                <div className="display font-bold text-sm leading-tight">{it.name_ru}</div>
                <div className="text-[11px] text-muted mt-1">{it.name_en ?? ""}</div>
                <div className="flex gap-2 mt-2">
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-500 font-medium">{it.equipment}</span>
                  {it.difficulty && (
                    <Badge tone={DIFFICULTY_LABEL[it.difficulty]?.tone ?? "default"}>
                      {DIFFICULTY_LABEL[it.difficulty]?.label ?? `d${it.difficulty}`}
                    </Badge>
                  )}
                </div>
              </div>
            </Link>
          ) : (
            <Link
              key={it.id}
              href={`/dashboard/exercises/${it.id}`}
              className="glass-card p-4 flex items-center gap-4 hover:shadow-glow transition-shadow duration-300"
            >
              <div className={`h-12 w-12 rounded-xl shrink-0 bg-gradient-to-br ${MUSCLE_GRADIENTS[it.primary_muscle] ?? "from-violet-500/20 to-brand-500/10"} grid place-items-center`}>
                {it.image_url ? (
                  <img src={it.image_url} alt={it.name_ru} className="h-full w-full object-cover rounded-xl" />
                ) : (
                  <Dumbbell size={20} className="opacity-40" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="display font-bold text-sm">{it.name_ru}</div>
                <div className="text-xs text-muted">{it.primary_muscle} · {it.equipment}</div>
              </div>
              {it.difficulty && (
                <Badge tone={DIFFICULTY_LABEL[it.difficulty]?.tone ?? "default"}>
                  {DIFFICULTY_LABEL[it.difficulty]?.label ?? `d${it.difficulty}`}
                </Badge>
              )}
            </Link>
          )
        )}
      </div>
    </div>
  );
}
