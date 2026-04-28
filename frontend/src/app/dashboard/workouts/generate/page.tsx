"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowLeft,
  Calendar,
  Clock,
  Layers,
  Sparkles,
  Target,
  Timer,
  Wand2,
} from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Chip, OptionCard } from "@/components/ui/option-card";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-store";
import { questionnaireApi } from "@/features/questionnaire/api";
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
import type {
  QuestionnaireInput,
  Sex,
  TrainingLocation,
  WeekDay,
} from "@/features/questionnaire/types";
import type {
  Equipment,
  Exercise,
  Experience,
  Goal,
  Periodization,
  SessionDurationMin,
  TrainingStructure,
} from "@/features/workout/types";

const DEFAULT_FORM: QuestionnaireInput = {
  sex: "male",
  age: 28,
  height_cm: 178,
  weight_kg: 78,
  experience: "intermediate",
  goal: "muscle_gain",
  location: "gym",
  equipment: ["barbell", "dumbbell", "machine", "bodyweight"],
  injuries: [],
  days_per_week: 4,
  available_days: ["mon", "wed", "fri", "sat"],
  notes: "",
  session_duration_min: 60,
  training_structure: "upper_lower",
  periodization: "dup",
  cycle_length_weeks: 6,
  priority_exercise_ids: [],
};

function toggleInArray<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}

export default function GenerateWorkoutPage() {
  const router = useRouter();
  const user = useAuth((s) => s.user);

  const [form, setForm] = useState<QuestionnaireInput>(DEFAULT_FORM);
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [exerciseQuery, setExerciseQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    questionnaireApi
      .latest()
      .then((latest) => {
        if (cancelled || !latest) return;
        setForm({
          sex: latest.sex,
          age: latest.age,
          height_cm: latest.height_cm,
          weight_kg: latest.weight_kg,
          experience: latest.experience,
          goal: latest.goal,
          location: latest.location,
          equipment: latest.equipment as Equipment[],
          injuries: latest.injuries,
          days_per_week: latest.days_per_week,
          available_days: latest.available_days as WeekDay[],
          notes: latest.notes ?? "",
          session_duration_min: (latest.session_duration_min ?? 60) as SessionDurationMin,
          training_structure: (latest.training_structure ?? "upper_lower") as TrainingStructure,
          periodization: (latest.periodization ?? "dup") as Periodization,
          cycle_length_weeks: latest.cycle_length_weeks ?? 6,
          priority_exercise_ids: latest.priority_exercise_ids ?? [],
        });
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    api<Exercise[]>("/exercises").then(setExercises).catch(() => {});
  }, []);

  useEffect(() => {
    if (!user) return;
    setForm((prev) => ({
      ...prev,
      sex: prev.sex || (user.sex ?? "male"),
      height_cm: prev.height_cm || (user.height_cm ?? 178),
      weight_kg: prev.weight_kg || (user.weight_kg ?? 78),
      experience: (user.experience as Experience) ?? prev.experience,
      goal: (user.goal as Goal) ?? prev.goal,
      injuries:
        prev.injuries.length > 0 ? prev.injuries : user.global_restrictions ?? prev.injuries,
      priority_exercise_ids:
        prev.priority_exercise_ids && prev.priority_exercise_ids.length > 0
          ? prev.priority_exercise_ids
          : user.priority_exercise_ids ?? [],
    }));
  }, [user]);

  const setField = <K extends keyof QuestionnaireInput>(key: K, value: QuestionnaireInput[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const filteredExercises = useMemo(() => {
    const query = exerciseQuery.trim().toLowerCase();
    const list = query
      ? exercises.filter((ex) => (ex.name_ru || ex.name).toLowerCase().includes(query))
      : exercises;
    return list.slice(0, 60);
  }, [exerciseQuery, exercises]);

  const priorityIds = form.priority_exercise_ids ?? [];

  function togglePriorityExercise(id: number) {
    setForm((prev) => {
      const list = prev.priority_exercise_ids ?? [];
      const has = list.includes(id);
      const next = has ? list.filter((eid) => eid !== id) : [...list, id].slice(0, 24);
      return { ...prev, priority_exercise_ids: next };
    });
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setSuccess("");
    if (form.available_days.length < form.days_per_week) {
      setError(
        `Выберите минимум ${form.days_per_week} ${
          form.days_per_week === 1 ? "день" : "дня"
        } недели для тренировок`,
      );
      return;
    }
    if (form.equipment.length === 0) {
      setError("Выберите хотя бы один тип инвентаря");
      return;
    }
    setLoading(true);
    try {
      const saved = await questionnaireApi.create(form);
      const plan = await questionnaireApi.generate(saved.id);
      setSuccess(`Программа «${plan.name}» успешно создана.`);
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
        <div className="relative flex items-start gap-4">
          <div className="h-12 w-12 rounded-2xl bg-white/15 backdrop-blur-sm grid place-items-center shrink-0">
            <Wand2 size={24} />
          </div>
          <div>
            <h1 className="display font-extrabold text-2xl md:text-3xl leading-tight">
              Конструктор тренировки
            </h1>
            <p className="text-sm md:text-base opacity-90 mt-1 max-w-2xl">
              Соберите цикл по своим параметрам: длительность сессии, структура,
              периодизация и приоритетные упражнения.
            </p>
          </div>
        </div>
      </div>

      <form onSubmit={onSubmit} className="space-y-6">
        <Section
          title="Базовые параметры"
          subtitle="Берётся из профиля при первом открытии — корректируйте при необходимости"
          icon={<Activity size={18} />}
        >
          <div className="grid md:grid-cols-2 gap-3">
            <SubGroup label="Пол">
              <div className="grid grid-cols-2 gap-2.5">
                {SEX_OPTIONS.map((option) => (
                  <OptionCard
                    key={option.value}
                    active={form.sex === option.value}
                    title={option.label}
                    onClick={() => setField("sex", option.value as Sex)}
                    size="sm"
                  />
                ))}
              </div>
            </SubGroup>
            <SubGroup label="Место">
              <div className="grid grid-cols-2 gap-2.5">
                {LOCATION_OPTIONS.map((option) => (
                  <OptionCard
                    key={option.value}
                    active={form.location === option.value}
                    title={option.label}
                    onClick={() => setField("location", option.value as TrainingLocation)}
                    size="sm"
                  />
                ))}
              </div>
            </SubGroup>
          </div>
          <div className="grid md:grid-cols-3 gap-3 mt-3">
            <NumberField
              label="Возраст"
              value={form.age}
              min={12}
              max={90}
              onChange={(value) => setField("age", value)}
            />
            <NumberField
              label="Рост, см"
              value={form.height_cm}
              min={120}
              max={230}
              onChange={(value) => setField("height_cm", value)}
            />
            <NumberField
              label="Вес тела, кг"
              value={form.weight_kg}
              min={30}
              max={250}
              onChange={(value) => setField("weight_kg", value)}
            />
          </div>
        </Section>

        <Section
          title="Уровень подготовки"
          subtitle="Влияет на объём, прогрессию и сложность"
          icon={<Target size={18} />}
        >
          <div className="grid md:grid-cols-3 gap-3">
            {EXPERIENCE_OPTIONS.map((option) => (
              <OptionCard
                key={option.value}
                active={form.experience === option.value}
                title={option.label}
                description={option.description}
                onClick={() => setField("experience", option.value as Experience)}
              />
            ))}
          </div>
        </Section>

        <Section
          title="Цель тренировок"
          subtitle="Определяет повторения, отдых, интенсивность"
          icon={<Sparkles size={18} />}
        >
          <div className="grid md:grid-cols-2 gap-3">
            {GOAL_OPTIONS.map((option) => (
              <OptionCard
                key={option.value}
                active={form.goal === option.value}
                title={`${option.icon} ${option.label}`}
                description={option.description}
                onClick={() => setField("goal", option.value as Goal)}
              />
            ))}
          </div>
        </Section>

        <Section
          title="Длительность одной тренировки"
          subtitle="Влияет на количество упражнений и аксессуаров за день"
          icon={<Timer size={18} />}
        >
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {SESSION_DURATION_OPTIONS.map((option) => (
              <OptionCard
                key={option.value}
                active={form.session_duration_min === option.value}
                title={option.label}
                subtitle={option.subtitle}
                description={option.description}
                onClick={() => setField("session_duration_min", option.value)}
              />
            ))}
          </div>
        </Section>

        <Section
          title="Структура тренировок"
          subtitle="Базовый сплит: фулбади, полусплит, верх/низ или сплит"
          icon={<Layers size={18} />}
        >
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
        </Section>

        <Section
          title="Дни в неделю и расписание"
          subtitle="Тяжёлые дни автоматически разносятся минимум на 48 часов"
          icon={<Calendar size={18} />}
        >
          <Label>Дней в неделю</Label>
          <div className="grid grid-cols-5 gap-2.5">
            {DAYS_PER_WEEK_OPTIONS.map((option) => (
              <OptionCard
                key={option.value}
                active={form.days_per_week === option.value}
                title={option.label}
                subtitle={option.description}
                onClick={() => setField("days_per_week", option.value)}
                size="sm"
              />
            ))}
          </div>
          <div className="mt-4">
            <Label>Доступные дни недели</Label>
            <div className="flex flex-wrap gap-2">
              {WEEK_DAY_OPTIONS.map((d) => {
                const active = form.available_days.includes(d.value);
                return (
                  <Chip
                    key={d.value}
                    active={active}
                    onClick={() => setField("available_days", toggleInArray(form.available_days, d.value))}
                  >
                    {d.label}
                  </Chip>
                );
              })}
            </div>
            <p className="text-xs text-muted mt-2">
              Выберите минимум {form.days_per_week} дн. — расписание определит дни тяжёлой нагрузки.
            </p>
          </div>
        </Section>

        <Section
          title="Периодизация"
          subtitle="Как меняется нагрузка от недели к неделе"
          icon={<Sparkles size={18} />}
        >
          <div className="grid md:grid-cols-2 gap-3">
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
        </Section>

        <Section
          title="Длина цикла"
          subtitle="Определяет сколько недель программы будет сгенерировано"
          icon={<Clock size={18} />}
        >
          <div className="grid md:grid-cols-3 gap-3">
            {CYCLE_LENGTH_OPTIONS.map((option) => (
              <OptionCard
                key={option.value}
                active={form.cycle_length_weeks === option.value}
                title={option.label}
                subtitle={option.subtitle}
                description={option.description}
                onClick={() => setField("cycle_length_weeks", option.value)}
              />
            ))}
          </div>
        </Section>

        <Section
          title="Инвентарь"
          subtitle="Только то, что есть в зале или дома"
          icon={<Layers size={18} />}
        >
          <div className="flex flex-wrap gap-2">
            {EQUIPMENT_OPTIONS.map((eq) => (
              <Chip
                key={eq.value}
                tone="violet"
                active={form.equipment.includes(eq.value)}
                onClick={() => setField("equipment", toggleInArray(form.equipment, eq.value))}
              >
                {eq.label}
              </Chip>
            ))}
          </div>
        </Section>

        <Section
          title="Ограничения по здоровью"
          subtitle="Не подбираются упражнения с риском для отмеченных зон"
          icon={<Activity size={18} />}
        >
          <div className="flex flex-wrap gap-2">
            {RESTRICTION_OPTIONS.map((restriction) => (
              <Chip
                key={restriction.value}
                tone="danger"
                active={form.injuries.includes(restriction.value)}
                onClick={() => setField("injuries", toggleInArray(form.injuries, restriction.value))}
              >
                {restriction.label}
              </Chip>
            ))}
          </div>
          <p className="text-xs text-muted mt-2">
            По умолчанию подтягиваются ограничения из профиля.
          </p>
        </Section>

        <Section
          title="Приоритетные упражнения"
          subtitle={`Выбрано ${priorityIds.length} из 24`}
          icon={<Sparkles size={18} />}
        >
          <Input
            placeholder="Поиск по названию…"
            value={exerciseQuery}
            onChange={(e) => setExerciseQuery(e.target.value)}
          />
          {exercises.length === 0 ? (
            <div className="text-sm text-muted text-center py-6">Загрузка упражнений…</div>
          ) : (
            <div className="mt-3 max-h-[280px] overflow-y-auto pr-1 grid sm:grid-cols-2 gap-2">
              {filteredExercises.map((ex) => (
                <Chip
                  key={ex.id}
                  tone="violet"
                  active={priorityIds.includes(ex.id)}
                  onClick={() => togglePriorityExercise(ex.id)}
                  className="justify-start truncate text-left"
                >
                  <span className="truncate">{ex.name_ru || ex.name}</span>
                </Chip>
              ))}
            </div>
          )}
        </Section>

        <Section title="Дополнительные пожелания" icon={<Sparkles size={18} />}>
          <textarea
            className="w-full bg-[var(--card)] border border-[var(--border)] rounded-xl p-3 text-sm focus:border-brand-500/60 focus:outline-none"
            rows={3}
            maxLength={500}
            placeholder="Например: акцент на ноги, ограничение по времени и т.д."
            value={form.notes}
            onChange={(e) => setField("notes", e.target.value)}
          />
        </Section>

        {error && (
          <Card className="border border-red-500/40">
            <span className="text-sm text-red-400">{error}</span>
          </Card>
        )}
        {success && (
          <Card className="border border-emerald-500/40">
            <span className="text-sm text-emerald-400">{success}</span>
          </Card>
        )}

        <div className="sticky bottom-3 z-10">
          <div className="glass-card-strong p-3 flex flex-wrap items-center gap-3">
            <div className="flex flex-wrap items-center gap-2 flex-1 min-w-[200px]">
              <Badge tone="brand">Дней: {form.days_per_week}</Badge>
              <Badge tone="violet">{form.session_duration_min} мин</Badge>
              <Badge>{form.cycle_length_weeks} нед.</Badge>
              {priorityIds.length > 0 && <Badge>{priorityIds.length} приоритет.</Badge>}
            </div>
            <Button type="submit" disabled={loading}>
              <Wand2 size={14} /> {loading ? "Генерация…" : "Сгенерировать тренировку"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => router.push("/dashboard/workouts")}
            >
              Отмена
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}

function Section({
  title,
  subtitle,
  icon,
  children,
}: {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          {icon && (
            <span className="h-9 w-9 rounded-xl grid place-items-center bg-brand-500/10 text-brand-500 dark:bg-violet-500/15 dark:text-violet-300">
              {icon}
            </span>
          )}
          <div>
            <CardTitle>{title}</CardTitle>
            {subtitle && <p className="text-xs text-muted mt-0.5">{subtitle}</p>}
          </div>
        </div>
      </CardHeader>
      {children}
    </Card>
  );
}

function SubGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function NumberField({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
}) {
  return (
    <div>
      <Label>{label}</Label>
      <Input
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={(e) =>
          onChange(Math.max(min, Math.min(max, Number(e.target.value) || min)))
        }
      />
    </div>
  );
}
