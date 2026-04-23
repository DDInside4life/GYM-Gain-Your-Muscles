"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Dumbbell } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { Exercise } from "@/features/workout/types";

const DIFFICULTY_LABEL: Record<number, string> = { 1: "Лёгкий", 2: "Средний", 3: "Сложный" };
const DIFFICULTY_TONE: Record<number, "brand" | "violet" | "default"> = { 1: "default", 2: "violet", 3: "brand" };

export default function ExerciseDetailsPage() {
  const params = useParams<{ id: string }>();
  const [exercise, setExercise] = useState<Exercise | null>(null);

  useEffect(() => {
    if (!params?.id) return;
    api<Exercise>(`/exercises/${params.id}`).then(setExercise);
  }, [params?.id]);

  if (!exercise) {
    return <div className="glass-card p-10 text-center text-muted animate-pulse">Загрузка упражнения…</div>;
  }

  return (
    <div className="space-y-4 animate-fade-up">
      <Link href="/dashboard/exercises" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-inherit transition">
        <ArrowLeft size={14} /> Назад к упражнениям
      </Link>

      <div className="glass-card overflow-hidden">
        <div className="h-56 md:h-72 bg-gradient-to-br from-violet-500/25 via-brand-500/15 to-purple-900/20 relative grid place-items-center">
          <div className="absolute inset-0 grid-bg opacity-25" />
          {exercise.image_url ? (
            <img src={exercise.image_url} alt={exercise.name_ru} className="h-full w-full object-cover" />
          ) : (
            <div className="flex flex-col items-center gap-3 opacity-40">
              <Dumbbell size={56} />
              <span className="text-sm">Фото появится в обновлении</span>
            </div>
          )}
        </div>

        <div className="p-5 md:p-6 space-y-4">
          <div>
            <h1 className="display text-2xl font-extrabold">{exercise.name_ru}</h1>
            {exercise.name_en && <p className="text-sm text-muted mt-1">{exercise.name_en}</p>}
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge tone="brand">{exercise.primary_muscle}</Badge>
            {exercise.equipment && <Badge>{exercise.equipment}</Badge>}
            {exercise.difficulty && (
              <Badge tone={DIFFICULTY_TONE[exercise.difficulty] ?? "default"}>
                {DIFFICULTY_LABEL[exercise.difficulty] ?? `Уровень ${exercise.difficulty}`}
              </Badge>
            )}
          </div>

          {exercise.description && (
            <p className="text-sm leading-relaxed">{exercise.description}</p>
          )}
        </div>
      </div>
    </div>
  );
}
