"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { Exercise } from "@/features/workout/types";

export default function ExerciseDetailsPage() {
  const params = useParams<{ id: string }>();
  const [exercise, setExercise] = useState<Exercise | null>(null);

  useEffect(() => {
    if (!params?.id) return;
    api<Exercise>(`/exercises/${params.id}`).then(setExercise);
  }, [params?.id]);

  if (!exercise) {
    return <div className="glass-card p-6">Загрузка упражнения...</div>;
  }

  return (
    <Card>
      <CardHeader><CardTitle>{exercise.name_ru}</CardTitle></CardHeader>
      <div className="glass-card p-5 md:p-6 space-y-3">
        <div className="text-sm text-muted">{exercise.name_en ?? "English name will be added later."}</div>
        <div className="text-sm">{exercise.description || "Описание пока не добавлено."}</div>
        <div className="text-sm"><b>Мышечная группа:</b> {exercise.primary_muscle}</div>
        <div className="rounded-xl border border-[var(--border)] p-8 text-center text-sm text-muted">
          {exercise.image_url ? (
            <img src={exercise.image_url} alt={exercise.name_ru} className="mx-auto rounded-lg max-h-72 object-cover" />
          ) : (
            "Изображение появится в следующем обновлении"
          )}
        </div>
      </div>
    </Card>
  );
}
