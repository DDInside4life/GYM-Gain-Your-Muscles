"use client";

import { useEffect, useMemo, useState } from "react";
import { Activity, Save, Target } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Chip, OptionCard } from "@/components/ui/option-card";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-store";
import {
  EXPERIENCE_OPTIONS,
  GOAL_OPTIONS,
  RESTRICTION_OPTIONS,
  SEX_OPTIONS,
} from "@/features/workout/constants";
import type { Experience, Exercise, Goal } from "@/features/workout/types";

type ProfileForm = {
  full_name: string;
  avatar_url: string;
  sex: "" | "male" | "female";
  height_cm: number;
  weight_kg: number;
  experience: Experience;
  goal: Goal;
  activity_factor: number;
  global_restrictions: string[];
  priority_exercise_ids: number[];
};

export default function ProfilePage() {
  const user = useAuth((s) => s.user)!;
  const refreshMe = useAuth((s) => s.refreshMe);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [error, setError] = useState<string>("");
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [exerciseQuery, setExerciseQuery] = useState("");

  const [form, setForm] = useState<ProfileForm>({
    full_name: user.full_name ?? "",
    avatar_url: user.avatar_url ?? "",
    sex: user.sex ?? "",
    height_cm: user.height_cm ?? 175,
    weight_kg: user.weight_kg ?? 75,
    experience: (user.experience as Experience) ?? "intermediate",
    goal: (user.goal as Goal) ?? "muscle_gain",
    activity_factor: user.activity_factor ?? 1.55,
    global_restrictions: user.global_restrictions ?? [],
    priority_exercise_ids: user.priority_exercise_ids ?? [],
  });

  useEffect(() => {
    api<Exercise[]>("/exercises").then(setExercises).catch(() => {});
  }, []);

  useEffect(() => {
    setForm((prev) => ({
      ...prev,
      full_name: user.full_name ?? prev.full_name,
      avatar_url: user.avatar_url ?? prev.avatar_url,
      sex: (user.sex ?? prev.sex) as ProfileForm["sex"],
      height_cm: user.height_cm ?? prev.height_cm,
      weight_kg: user.weight_kg ?? prev.weight_kg,
      experience: (user.experience as Experience) ?? prev.experience,
      goal: (user.goal as Goal) ?? prev.goal,
      activity_factor: user.activity_factor ?? prev.activity_factor,
      global_restrictions: user.global_restrictions ?? prev.global_restrictions,
      priority_exercise_ids: user.priority_exercise_ids ?? prev.priority_exercise_ids,
    }));
  }, [user]);

  const filteredExercises = useMemo(() => {
    const query = exerciseQuery.trim().toLowerCase();
    if (!query) return exercises.slice(0, 60);
    return exercises
      .filter((ex) => (ex.name_ru || ex.name).toLowerCase().includes(query))
      .slice(0, 60);
  }, [exerciseQuery, exercises]);

  const setField = <K extends keyof ProfileForm>(key: K, value: ProfileForm[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  function toggleRestriction(value: string) {
    setForm((prev) => {
      const has = prev.global_restrictions.includes(value);
      return {
        ...prev,
        global_restrictions: has
          ? prev.global_restrictions.filter((r) => r !== value)
          : [...prev.global_restrictions, value],
      };
    });
  }

  function togglePriorityExercise(id: number) {
    setForm((prev) => {
      const has = prev.priority_exercise_ids.includes(id);
      const next = has
        ? prev.priority_exercise_ids.filter((eid) => eid !== id)
        : [...prev.priority_exercise_ids, id].slice(0, 24);
      return { ...prev, priority_exercise_ids: next };
    });
  }

  async function save() {
    setSaving(true);
    setError("");
    try {
      await api("/users/me", {
        method: "PUT",
        body: JSON.stringify({
          full_name: form.full_name || undefined,
          avatar_url: form.avatar_url || undefined,
          sex: form.sex || undefined,
          height_cm: Number(form.height_cm),
          weight_kg: Number(form.weight_kg),
          experience: form.experience,
          goal: form.goal,
          activity_factor: Number(form.activity_factor),
          global_restrictions: form.global_restrictions,
          priority_exercise_ids: form.priority_exercise_ids,
        }),
        auth: true,
      });
      await refreshMe();
      setSavedAt(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить профиль");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <Card>
        <CardHeader>
          <CardTitle>Личные данные</CardTitle>
          <span className="text-xs text-muted">Используется для подбора программ и расчёта калорий</span>
        </CardHeader>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <Label>Имя</Label>
            <Input value={form.full_name} onChange={(e) => setField("full_name", e.target.value)} />
          </div>
          <div>
            <Label>Фото профиля (URL)</Label>
            <Input
              placeholder="https://..."
              value={form.avatar_url}
              onChange={(e) => setField("avatar_url", e.target.value)}
            />
          </div>
          <div>
            <Label>Коэффициент активности</Label>
            <Input
              type="number"
              step={0.05}
              min={1.2}
              max={2.4}
              value={form.activity_factor}
              onChange={(e) => setField("activity_factor", Number(e.target.value))}
            />
          </div>
          <div>
            <Label>Рост (см)</Label>
            <Input
              type="number"
              min={120}
              max={230}
              value={form.height_cm}
              onChange={(e) => setField("height_cm", Number(e.target.value))}
            />
          </div>
          <div>
            <Label>Вес тела (кг)</Label>
            <Input
              type="number"
              min={30}
              max={250}
              value={form.weight_kg}
              onChange={(e) => setField("weight_kg", Number(e.target.value))}
            />
          </div>
        </div>

        <div className="mt-5">
          <Label>Пол</Label>
          <div className="grid grid-cols-2 gap-3">
            {SEX_OPTIONS.map((option) => (
              <OptionCard
                key={option.value}
                active={form.sex === option.value}
                title={option.label}
                onClick={() => setField("sex", option.value)}
                size="sm"
              />
            ))}
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Опыт тренировок</CardTitle>
          <span className="text-xs text-muted">Влияет на подбор шаблона программы</span>
        </CardHeader>
        <div className="grid md:grid-cols-3 gap-3">
          {EXPERIENCE_OPTIONS.map((option) => (
            <OptionCard
              key={option.value}
              active={form.experience === option.value}
              title={option.label}
              description={option.description}
              icon={<Activity size={18} />}
              onClick={() => setField("experience", option.value)}
            />
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Цель тренировок</CardTitle>
          <span className="text-xs text-muted">Используется для подбора шаблона программы</span>
        </CardHeader>
        <div className="grid md:grid-cols-2 gap-3">
          {GOAL_OPTIONS.map((option) => (
            <OptionCard
              key={option.value}
              active={form.goal === option.value}
              title={`${option.icon} ${option.label}`}
              description={option.description}
              onClick={() => setField("goal", option.value)}
            />
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Ограничения по здоровью</CardTitle>
          <span className="text-xs text-muted">Эти зоны будут учитываться при подборе программы</span>
        </CardHeader>
        <div className="flex flex-wrap gap-2">
          {RESTRICTION_OPTIONS.map((restriction) => (
            <Chip
              key={restriction.value}
              tone="danger"
              active={form.global_restrictions.includes(restriction.value)}
              onClick={() => toggleRestriction(restriction.value)}
            >
              {restriction.label}
            </Chip>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Приоритетные упражнения</CardTitle>
          <Badge>{form.priority_exercise_ids.length} / 24</Badge>
        </CardHeader>
        <p className="text-sm text-muted -mt-2">
          Подбираются в первую очередь при генерации, если совпадают со структурой программы.
        </p>
        <div className="mt-3">
          <Input
            placeholder="Поиск по названию…"
            value={exerciseQuery}
            onChange={(e) => setExerciseQuery(e.target.value)}
          />
        </div>
        {exercises.length === 0 ? (
          <div className="text-sm text-muted text-center py-6">Загрузка упражнений…</div>
        ) : (
          <div className="mt-3 max-h-[320px] overflow-y-auto pr-1 grid sm:grid-cols-2 gap-2">
            {filteredExercises.map((ex) => {
              const active = form.priority_exercise_ids.includes(ex.id);
              return (
                <Chip
                  key={ex.id}
                  tone="violet"
                  active={active}
                  onClick={() => togglePriorityExercise(ex.id)}
                  className="justify-start truncate text-left"
                >
                  <span className="truncate">{ex.name_ru || ex.name}</span>
                </Chip>
              );
            })}
          </div>
        )}
      </Card>

      <div className="sticky bottom-3 z-10">
        <div className="glass-card-strong p-3 flex flex-wrap items-center gap-3">
          <div className="flex-1 min-w-[180px] text-sm">
            {error ? (
              <span className="text-red-400">{error}</span>
            ) : savedAt ? (
              <span className="text-emerald-400">
                Сохранено в {savedAt.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}
              </span>
            ) : (
              <span className="text-muted">Изменения применятся к новым программам</span>
            )}
          </div>
          <Button onClick={save} disabled={saving}>
            <Save size={14} /> {saving ? "Сохранение…" : "Сохранить профиль"}
          </Button>
        </div>
      </div>
    </div>
  );
}
