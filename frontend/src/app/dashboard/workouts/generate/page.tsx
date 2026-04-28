"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Label, Select } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { questionnaireApi } from "@/features/questionnaire/api";
import type {
  QuestionnaireInput,
  Sex,
  TrainingLocation,
  WeekDay,
} from "@/features/questionnaire/types";
import type { Equipment, Experience, Goal } from "@/features/workout/types";

const GOAL_OPTIONS: Array<{ value: Goal; label: string }> = [
  { value: "muscle_gain", label: "Масса" },
  { value: "fat_loss", label: "Рельеф" },
  { value: "strength", label: "Сила" },
  { value: "general", label: "Поддержание" },
];

const EXPERIENCE_OPTIONS: Array<{ value: Experience; label: string }> = [
  { value: "beginner", label: "Новичок" },
  { value: "intermediate", label: "Средний" },
  { value: "advanced", label: "Продвинутый" },
];

const LOCATION_OPTIONS: Array<{ value: TrainingLocation; label: string }> = [
  { value: "gym", label: "Зал" },
  { value: "home", label: "Дом" },
];

const SEX_OPTIONS: Array<{ value: Sex; label: string }> = [
  { value: "male", label: "Мужской" },
  { value: "female", label: "Женский" },
];

const EQUIPMENT_OPTIONS: Array<{ value: Equipment; label: string }> = [
  { value: "bodyweight", label: "Свой вес" },
  { value: "barbell", label: "Штанга" },
  { value: "dumbbell", label: "Гантели" },
  { value: "machine", label: "Тренажёр" },
  { value: "cable", label: "Блок" },
  { value: "kettlebell", label: "Гиря" },
  { value: "bands", label: "Резины" },
];

const INJURY_OPTIONS = [
  { value: "knee", label: "Колено" },
  { value: "back", label: "Спина" },
  { value: "shoulder", label: "Плечо" },
  { value: "wrist", label: "Запястье" },
  { value: "elbow", label: "Локоть" },
  { value: "hip", label: "Бедро" },
  { value: "ankle", label: "Голеностоп" },
  { value: "neck", label: "Шея" },
];

const WEEK_DAY_OPTIONS: Array<{ value: WeekDay; label: string }> = [
  { value: "mon", label: "Пн" },
  { value: "tue", label: "Вт" },
  { value: "wed", label: "Ср" },
  { value: "thu", label: "Чт" },
  { value: "fri", label: "Пт" },
  { value: "sat", label: "Сб" },
  { value: "sun", label: "Вс" },
];

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
};

function toggleInArray<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}

export default function GenerateWorkoutPage() {
  const router = useRouter();
  const [form, setForm] = useState<QuestionnaireInput>(DEFAULT_FORM);
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
        });
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  const setField = <K extends keyof QuestionnaireInput>(key: K, value: QuestionnaireInput[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

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
      <Card>
        <CardHeader>
          <CardTitle>Анкета для генерации тренировки</CardTitle>
        </CardHeader>
        <p className="text-sm text-muted -mt-2">
          Заполните анкету — получите месячную программу: тестовая неделя + три рабочие недели,
          с расчётом весов, периодизацией и подсказками по RIR.
        </p>

        <form onSubmit={onSubmit} className="space-y-6">
          <Section title="Параметры тела">
            <div className="grid md:grid-cols-3 gap-3">
              <div>
                <Label>Пол</Label>
                <Select
                  value={form.sex}
                  onChange={(e) => setField("sex", e.target.value as Sex)}
                >
                  {SEX_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </Select>
              </div>
              <div>
                <Label>Возраст</Label>
                <Input
                  type="number" min={12} max={90}
                  value={form.age}
                  onChange={(e) => setField("age", Number(e.target.value))}
                />
              </div>
              <div>
                <Label>Рост, см</Label>
                <Input
                  type="number" min={120} max={230}
                  value={form.height_cm}
                  onChange={(e) => setField("height_cm", Number(e.target.value))}
                />
              </div>
              <div>
                <Label>Вес, кг</Label>
                <Input
                  type="number" min={30} max={250}
                  value={form.weight_kg}
                  onChange={(e) => setField("weight_kg", Number(e.target.value))}
                />
              </div>
              <div>
                <Label>Уровень подготовки</Label>
                <Select
                  value={form.experience}
                  onChange={(e) => setField("experience", e.target.value as Experience)}
                >
                  {EXPERIENCE_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </Select>
              </div>
              <div>
                <Label>Цель</Label>
                <Select
                  value={form.goal}
                  onChange={(e) => setField("goal", e.target.value as Goal)}
                >
                  {GOAL_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </Select>
              </div>
            </div>
          </Section>

          <Section title="Где и когда тренируетесь">
            <div className="grid md:grid-cols-2 gap-3">
              <div>
                <Label>Место тренировок</Label>
                <Select
                  value={form.location}
                  onChange={(e) => setField("location", e.target.value as TrainingLocation)}
                >
                  {LOCATION_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </Select>
              </div>
              <div>
                <Label>Тренировок в неделю</Label>
                <Input
                  type="number" min={2} max={6}
                  value={form.days_per_week}
                  onChange={(e) => setField("days_per_week", Math.max(2, Math.min(6, Number(e.target.value))))}
                />
              </div>
            </div>
            <div className="mt-3">
              <Label>Доступные дни недели</Label>
              <div className="flex flex-wrap gap-2 mt-1">
                {WEEK_DAY_OPTIONS.map((d) => {
                  const active = form.available_days.includes(d.value);
                  return (
                    <button
                      key={d.value}
                      type="button"
                      onClick={() => setField("available_days", toggleInArray(form.available_days, d.value))}
                      className={`px-3 py-1.5 rounded-lg text-sm border transition ${
                        active
                          ? "bg-brand-gradient text-white border-transparent"
                          : "border-[var(--border)] hover:border-brand-500/60"
                      }`}
                    >
                      {d.label}
                    </button>
                  );
                })}
              </div>
              <p className="text-xs text-muted mt-1">
                Выберите минимум {form.days_per_week} дн. — тяжёлые сессии будут разнесены на 48 часов.
              </p>
            </div>
          </Section>

          <Section title="Инвентарь">
            <div className="flex flex-wrap gap-2">
              {EQUIPMENT_OPTIONS.map((eq) => {
                const active = form.equipment.includes(eq.value);
                return (
                  <button
                    key={eq.value}
                    type="button"
                    onClick={() => setField("equipment", toggleInArray(form.equipment, eq.value))}
                    className={`px-3 py-1.5 rounded-lg text-sm border transition ${
                      active
                        ? "bg-violet-500/20 border-violet-500/60"
                        : "border-[var(--border)] hover:border-violet-500/40"
                    }`}
                  >
                    {eq.label}
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-muted mt-2">
              Если ничего не выбрано — используется свободный набор для дома.
            </p>
          </Section>

          <Section title="Ограничения по здоровью">
            <div className="flex flex-wrap gap-2">
              {INJURY_OPTIONS.map((inj) => {
                const active = form.injuries.includes(inj.value);
                return (
                  <button
                    key={inj.value}
                    type="button"
                    onClick={() => setField("injuries", toggleInArray(form.injuries, inj.value))}
                    className={`px-3 py-1.5 rounded-lg text-sm border transition ${
                      active
                        ? "bg-red-500/20 border-red-500/60"
                        : "border-[var(--border)] hover:border-red-500/40"
                    }`}
                  >
                    {inj.label}
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-muted mt-2">
              Упражнения с риском для отмеченных зон будут автоматически исключены.
            </p>
          </Section>

          <Section title="Дополнительные пожелания">
            <textarea
              className="w-full bg-[var(--card)] border border-[var(--border)] rounded-lg p-3 text-sm focus:border-brand-500/60 focus:outline-none"
              rows={3}
              maxLength={500}
              placeholder="Например: акцент на ноги, ограничение по времени и т.д."
              value={form.notes}
              onChange={(e) => setField("notes", e.target.value)}
            />
          </Section>

          {error && (
            <div className="glass-card p-3 text-sm text-red-400 border border-red-500/40">
              {error}
            </div>
          )}
          {success && (
            <div className="glass-card p-3 text-sm text-emerald-400 border border-emerald-500/40">
              {success}
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <Button type="submit" disabled={loading}>
              {loading ? "Генерация…" : "Сгенерировать тренировку"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => router.push("/dashboard/workouts")}
            >
              Отмена
            </Button>
          </div>
        </form>
      </Card>

      <Card>
        <CardHeader><CardTitle>Что вы получите</CardTitle></CardHeader>
        <ul className="text-sm space-y-2">
          <li><Badge tone="brand">Неделя 1</Badge> Тестовая: один рабочий подход на основные упражнения, без отказа.</li>
          <li><Badge tone="violet">Недели 2–4</Badge> Рабочие подходы с расчётом веса от 1ПМ и контролем объёма.</li>
          <li><Badge>Безопасность</Badge> Веса ограничены диапазоном для вашего опыта, упражнения отфильтрованы по травмам.</li>
          <li><Badge>RIR</Badge> Каждое рабочее упражнение содержит целевой RIR и пояснение.</li>
        </ul>
      </Card>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="glass-card p-4 space-y-3">
      <div className="display font-bold text-sm uppercase tracking-wide text-muted">{title}</div>
      {children}
    </div>
  );
}
