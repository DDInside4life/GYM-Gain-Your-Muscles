"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Wand2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Chip, OptionCard } from "@/components/ui/option-card";
import { Input, Label } from "@/components/ui/input";
import {
  CYCLE_LENGTH_OPTIONS,
  DAYS_PER_WEEK_OPTIONS,
  EQUIPMENT_OPTIONS,
  EXPERIENCE_OPTIONS,
  GOAL_OPTIONS,
  LOCATION_OPTIONS,
  PERIODIZATION_OPTIONS,
  RESTRICTION_OPTIONS,
  SESSION_DURATION_OPTIONS,
  SEX_OPTIONS,
  TRAINING_STRUCTURE_OPTIONS,
  WEEK_DAY_OPTIONS,
} from "@/features/workout/constants";
import { workoutApi } from "@/features/workout/api";
import type { Equipment, QuestionnaireInput, SessionDurationMin, Sex } from "@/features/workout/types";

type FormState = QuestionnaireInput & { priority_text: string };

const DEFAULT_FORM: FormState = {
  sex: "male",
  age: 28,
  height_cm: 178,
  weight_kg: 75,
  experience: "intermediate",
  goal: "muscle_gain",
  location: "gym",
  equipment: ["barbell", "dumbbell", "machine", "bodyweight"],
  injuries: [],
  days_per_week: 4,
  available_days: ["mon", "tue", "thu", "sat"],
  notes: "",
  session_duration_min: 60,
  training_structure: "upper_lower",
  periodization: "dup",
  cycle_length_weeks: 6,
  priority_exercise_ids: [],
  priority_text: "",
};

function toggle<T>(list: readonly T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}

function parsePriorityIds(value: string): number[] {
  return value
    .split(",")
    .map((v) => Number(v.trim()))
    .filter((v) => Number.isFinite(v) && v > 0);
}

export default function GenerateWorkoutPage() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const setField = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    if (form.equipment.length === 0) {
      setError("Выберите хотя бы один тип инвентаря");
      return;
    }
    if (form.available_days.length === 0) {
      setError("Выберите доступные дни");
      return;
    }
    setLoading(true);
    try {
      const payload: QuestionnaireInput = {
        sex: form.sex,
        age: form.age,
        height_cm: form.height_cm,
        weight_kg: form.weight_kg,
        experience: form.experience,
        goal: form.goal,
        location: form.location,
        equipment: form.equipment,
        injuries: form.injuries,
        days_per_week: form.days_per_week,
        available_days: form.available_days,
        notes: form.notes,
        session_duration_min: form.session_duration_min,
        training_structure: form.training_structure,
        periodization: form.periodization,
        cycle_length_weeks: form.cycle_length_weeks,
        priority_exercise_ids: parsePriorityIds(form.priority_text),
      };
      await workoutApi.generateFromQuestionnaire(payload);
      router.push("/dashboard/workouts/plan");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сгенерировать программу");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <button
        onClick={() => router.push("/dashboard/workouts")}
        className="inline-flex items-center gap-2 text-sm text-muted hover:text-inherit transition-colors"
      >
        <ArrowLeft size={14} /> К программам
      </button>

      <div className="relative overflow-hidden rounded-3xl bg-brand-gradient dark:bg-neon-gradient p-6 md:p-8 text-white shadow-glow-brand dark:shadow-glow">
        <div className="absolute inset-0 grid-bg opacity-20" />
        <div className="relative">
          <h1 className="display font-extrabold text-2xl md:text-3xl leading-tight">
            Полная анкета тренировок
          </h1>
          <p className="text-sm md:text-base opacity-90 mt-1 max-w-2xl">
            Первая неделя тестовая, дальше рабочие недели с авторасчётом веса и прогрессией.
          </p>
        </div>
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        <Accordion title="Профиль">
          <div className="grid md:grid-cols-2 gap-3">
            <div>
              <Label>Пол</Label>
              <div className="flex gap-2 mt-2">
                {SEX_OPTIONS.map((s) => (
                  <Chip
                    key={s.value}
                    active={form.sex === s.value}
                    onClick={() => setField("sex", s.value as Sex)}
                  >
                    {s.label}
                  </Chip>
                ))}
              </div>
            </div>
            <div>
              <Label>Локация</Label>
              <div className="flex gap-2 mt-2">
                {LOCATION_OPTIONS.map((l) => (
                  <Chip
                    key={l.value}
                    active={form.location === l.value}
                    onClick={() => setField("location", l.value)}
                  >
                    {l.label}
                  </Chip>
                ))}
              </div>
            </div>
          </div>
          <div className="grid sm:grid-cols-3 gap-3 mt-3">
            <div>
              <Label>Возраст</Label>
              <Input type="number" min={12} max={90} value={form.age} onChange={(e) => setField("age", Number(e.target.value) || 0)} />
            </div>
            <div>
              <Label>Рост, см</Label>
              <Input type="number" min={120} max={230} value={form.height_cm} onChange={(e) => setField("height_cm", Number(e.target.value) || 0)} />
            </div>
            <div>
              <Label>Вес, кг</Label>
              <Input type="number" step={0.5} min={30} max={300} value={form.weight_kg} onChange={(e) => setField("weight_kg", Number(e.target.value) || 0)} />
            </div>
          </div>
          <div className="grid md:grid-cols-3 gap-3 mt-3">
            {EXPERIENCE_OPTIONS.map((option) => (
              <OptionCard
                key={option.value}
                active={form.experience === option.value}
                title={option.label}
                description={option.description}
                onClick={() => setField("experience", option.value)}
              />
            ))}
          </div>
        </Accordion>

        <Accordion title="Цели и расписание">
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
          <div className="grid md:grid-cols-5 gap-2 mt-3">
            {DAYS_PER_WEEK_OPTIONS.map((d) => (
              <OptionCard
                key={d.value}
                active={form.days_per_week === d.value}
                title={String(d.value)}
                description={d.description}
                onClick={() => setField("days_per_week", d.value)}
                size="sm"
              />
            ))}
          </div>
          <div className="mt-3">
            <Label>Доступные дни</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {WEEK_DAY_OPTIONS.map((d) => (
                <Chip
                  key={d.value}
                  active={form.available_days.includes(d.value)}
                  onClick={() => setField("available_days", toggle(form.available_days, d.value))}
                >
                  {d.label}
                </Chip>
              ))}
            </div>
          </div>
        </Accordion>

        <Accordion title="Параметры тренировки">
          <div className="grid md:grid-cols-2 gap-3">
            {TRAINING_STRUCTURE_OPTIONS.map((option) => (
              <OptionCard
                key={option.value}
                active={form.training_structure === option.value}
                title={option.label}
                description={option.description}
                onClick={() => setField("training_structure", option.value)}
              />
            ))}
          </div>
          <div className="grid md:grid-cols-2 gap-3 mt-3">
            {PERIODIZATION_OPTIONS.map((option) => (
              <OptionCard
                key={option.value}
                active={form.periodization === option.value}
                title={option.label}
                description={option.description}
                onClick={() => setField("periodization", option.value)}
              />
            ))}
          </div>
          <div className="grid md:grid-cols-3 gap-3 mt-3">
            {SESSION_DURATION_OPTIONS.map((option) => (
              <OptionCard
                key={option.value}
                active={form.session_duration_min === option.value}
                title={option.label}
                description={option.description}
                onClick={() => setField("session_duration_min", option.value as SessionDurationMin)}
                size="sm"
              />
            ))}
          </div>
          <div className="grid md:grid-cols-3 gap-3 mt-3">
            {CYCLE_LENGTH_OPTIONS.map((option) => (
              <OptionCard
                key={option.value}
                active={form.cycle_length_weeks === option.value}
                title={option.subtitle}
                description={option.description}
                onClick={() => setField("cycle_length_weeks", option.value)}
                size="sm"
              />
            ))}
          </div>
        </Accordion>

        <Accordion title="Ограничения и приоритеты">
          <div>
            <Label>Инвентарь</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {EQUIPMENT_OPTIONS.map((eq) => (
                <Chip
                  key={eq.value}
                  tone="violet"
                  active={form.equipment.includes(eq.value as Equipment)}
                  onClick={() => setField("equipment", toggle(form.equipment, eq.value as Equipment))}
                >
                  {eq.label}
                </Chip>
              ))}
            </div>
          </div>
          <div className="mt-3">
            <Label>Травмы / ограничения</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {RESTRICTION_OPTIONS.map((inj) => (
                <Chip
                  key={inj.value}
                  tone="warning"
                  active={form.injuries.includes(inj.value)}
                  onClick={() => setField("injuries", toggle(form.injuries, inj.value))}
                >
                  {inj.label}
                </Chip>
              ))}
            </div>
          </div>
          <div className="mt-3">
            <Label>ID приоритетных упражнений (через запятую)</Label>
            <Input
              value={form.priority_text}
              onChange={(e) => setField("priority_text", e.target.value)}
              placeholder="например: 101, 205, 330"
            />
          </div>
          <div className="mt-3">
            <Label>Заметки</Label>
            <Input value={form.notes} onChange={(e) => setField("notes", e.target.value)} placeholder="Комментарий по ограничениям или предпочтениям" />
          </div>
        </Accordion>

        {error && <Card className="border border-red-500/40 p-3 text-sm text-red-400">{error}</Card>}

        <div className="sticky bottom-3 z-10">
          <div className="glass-card-strong p-3 flex flex-wrap items-center gap-3">
            <div className="text-sm text-muted flex-1 min-w-[200px]">
              {form.cycle_length_weeks} недель · {form.days_per_week} тренировок/нед · тестовая неделя №1
            </div>
            <Button type="submit" disabled={loading}>
              <Wand2 size={14} /> {loading ? "Генерация…" : "Сгенерировать программу"}
            </Button>
            <Button type="button" variant="outline" onClick={() => router.push("/dashboard/workouts")}>
              Отмена
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}

function Accordion({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <details className="glass-card p-4" open>
      <summary className="cursor-pointer font-semibold">{title}</summary>
      <div className="mt-3">{children}</div>
    </details>
  );
}
