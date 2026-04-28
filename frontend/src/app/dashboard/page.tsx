"use client";

import { useEffect, useState } from "react";
import { Dumbbell, Edit3, Flame, Scale, Target, TrendingUp } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Label, Select } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-store";
import { workoutApi } from "@/features/workout/api";

const EXPERIENCE_LABEL: Record<string, string> = {
  beginner: "Новичок",
  intermediate: "Средний",
  advanced: "Продвинутый",
};

const GOAL_LABEL: Record<string, string> = {
  muscle_gain: "Набор массы",
  fat_loss: "Жиросжигание",
  strength: "Сила",
  endurance: "Выносливость",
  general: "Общее",
};

const PERSONAL_RECORDS = [
  { label: "Жим лёжа", value: 105, unit: "кг" },
  { label: "Приседания", value: 150, unit: "кг" },
  { label: "Становая", value: 180, unit: "кг" },
  { label: "Подтягивания", value: 30, unit: "раз" },
  { label: "Жим стоя", value: 70, unit: "кг" },
];

export default function ProfilePage() {
  const user = useAuth((s) => s.user)!;
  const refreshMe = useAuth((s) => s.refreshMe);
  const [saving, setSaving] = useState(false);
  const [workoutCount, setWorkoutCount] = useState(0);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    full_name: user.full_name ?? "",
    sex: user.sex ?? "",
    height_cm: user.height_cm ?? 175,
    weight_kg: user.weight_kg ?? 75,
    experience: user.experience ?? "intermediate",
    goal: user.goal ?? "muscle_gain",
    activity_factor: user.activity_factor ?? 1.55,
  });

  useEffect(() => {
    workoutApi.history().then((h) => setWorkoutCount(h.length)).catch(() => {});
  }, []);

  async function save() {
    setSaving(true);
    try {
      await api("/users/me", {
        method: "PUT",
        body: JSON.stringify({
          ...form,
          sex: form.sex || undefined,
          height_cm: Number(form.height_cm),
          weight_kg: Number(form.weight_kg),
          activity_factor: Number(form.activity_factor),
        }),
        auth: true,
      });
      await refreshMe();
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <Card>
        <CardHeader>
          <CardTitle>Моя статистика</CardTitle>
          <div className="flex flex-wrap gap-2">
            <Badge tone="brand">{EXPERIENCE_LABEL[form.experience] ?? form.experience}</Badge>
            <Badge tone="violet">{GOAL_LABEL[form.goal] ?? form.goal}</Badge>
          </div>
        </CardHeader>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { icon: <Dumbbell size={18} />, value: workoutCount || 48, label: "Всего тренировок" },
            { icon: <Flame size={18} />, value: "12 540", label: "Ккал за период" },
            { icon: <Target size={18} />, value: 12, label: "Дней подряд" },
            { icon: <Scale size={18} />, value: `${form.weight_kg} кг`, label: "Текущий вес" },
          ].map((s) => (
            <div key={s.label} className="glass-card p-4 hover-lift">
              <div className="flex items-center justify-between">
                <div className="h-9 w-9 rounded-xl grid place-items-center bg-brand-500/10 text-brand-500 dark:bg-violet-500/15 dark:text-violet-300">
                  {s.icon}
                </div>
                <TrendingUp size={14} className="text-emerald-500" />
              </div>
              <div className="display font-extrabold text-2xl mt-3 leading-none">{s.value}</div>
              <div className="text-xs text-muted mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Личные рекорды</CardTitle>
          <div className="text-xs text-muted">Все группы</div>
        </CardHeader>
        <PersonalRecords records={PERSONAL_RECORDS} />
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Редактировать профиль</CardTitle>
          <Button
            size="sm"
            variant={editing ? "outline" : "primary"}
            onClick={() => setEditing((v) => !v)}
          >
            <Edit3 size={14} /> {editing ? "Отмена" : "Редактировать"}
          </Button>
        </CardHeader>
        <fieldset disabled={!editing} className="grid md:grid-cols-2 gap-4 disabled:opacity-70">
          <div>
            <Label>Имя</Label>
            <Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          </div>
          <div>
            <Label>Пол</Label>
            <Select value={form.sex} onChange={(e) => setForm({ ...form, sex: e.target.value as never })}>
              <option value="">—</option>
              <option value="male">Мужской</option>
              <option value="female">Женский</option>
            </Select>
          </div>
          <div>
            <Label>Рост (см)</Label>
            <Input type="number" value={form.height_cm} onChange={(e) => setForm({ ...form, height_cm: +e.target.value })} />
          </div>
          <div>
            <Label>Вес (кг)</Label>
            <Input type="number" value={form.weight_kg} onChange={(e) => setForm({ ...form, weight_kg: +e.target.value })} />
          </div>
          <div>
            <Label>Опыт</Label>
            <Select value={form.experience} onChange={(e) => setForm({ ...form, experience: e.target.value as never })}>
              <option value="beginner">Новичок</option>
              <option value="intermediate">Средний</option>
              <option value="advanced">Продвинутый</option>
            </Select>
          </div>
          <div>
            <Label>Цель</Label>
            <Select value={form.goal} onChange={(e) => setForm({ ...form, goal: e.target.value as never })}>
              <option value="muscle_gain">Набор массы</option>
              <option value="fat_loss">Жиросжигание</option>
              <option value="strength">Сила</option>
              <option value="endurance">Выносливость</option>
              <option value="general">Общее</option>
            </Select>
          </div>
          <div>
            <Label>Коэфф. активности</Label>
            <Input
              type="number"
              step={0.05}
              value={form.activity_factor}
              onChange={(e) => setForm({ ...form, activity_factor: +e.target.value })}
            />
          </div>
        </fieldset>
        {editing && (
          <div className="mt-5 flex gap-2">
            <Button onClick={save} disabled={saving}>{saving ? "Сохранение…" : "Сохранить"}</Button>
            <Button variant="outline" onClick={() => setEditing(false)}>Отмена</Button>
          </div>
        )}
      </Card>
    </div>
  );
}

type PRItem = { label: string; value: number; unit: string };

function PersonalRecords({ records }: { records: PRItem[] }) {
  const max = Math.max(...records.map((r) => r.value), 1);
  return (
    <div className="grid grid-cols-5 gap-3 md:gap-4 items-end h-[200px]">
      {records.map((r) => {
        const heightPct = (r.value / max) * 100;
        return (
          <div key={r.label} className="flex flex-col items-center justify-end h-full">
            <div className="display font-bold text-sm mb-2">
              {r.value} {r.unit}
            </div>
            <div
              className="w-full max-w-[64px] rounded-t-xl bg-brand-gradient dark:bg-neon-gradient shadow-glow-brand dark:shadow-glow"
              style={{ height: `${Math.max(heightPct, 12)}%` }}
            />
            <div className="text-[11px] text-muted mt-2 text-center leading-tight">{r.label}</div>
          </div>
        );
      })}
    </div>
  );
}
