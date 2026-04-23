"use client";

import { useEffect, useState } from "react";
import { Dumbbell, Flame, Scale, Target } from "lucide-react";
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

export default function ProfilePage() {
  const user = useAuth((s) => s.user)!;
  const refreshMe = useAuth((s) => s.refreshMe);
  const [saving, setSaving] = useState(false);
  const [workoutCount, setWorkoutCount] = useState(0);
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
    } finally {
      setSaving(false);
    }
  }

  const initials = (user.full_name || user.email)
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");

  return (
    <div className="space-y-6 animate-fade-up">
      <div className="glass-card p-5 flex flex-col sm:flex-row items-start sm:items-center gap-5">
        <div className="h-16 w-16 rounded-2xl bg-brand-gradient grid place-items-center text-white display font-extrabold text-2xl shrink-0">
          {initials}
        </div>
        <div className="flex-1 min-w-0">
          <div className="display font-extrabold text-xl truncate">{user.full_name || user.email}</div>
          <div className="text-sm text-muted mt-0.5 truncate">{user.email}</div>
          <div className="flex flex-wrap gap-2 mt-2">
            <Badge tone="brand">{EXPERIENCE_LABEL[form.experience] ?? form.experience}</Badge>
            <Badge>{GOAL_LABEL[form.goal] ?? form.goal}</Badge>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { icon: <Dumbbell size={18} />, value: workoutCount, label: "Тренировок", color: "brand" },
          { icon: <Scale size={18} />, value: `${form.weight_kg} кг`, label: "Текущий вес", color: "violet" },
          { icon: <Flame size={18} />, value: `${form.height_cm} см`, label: "Рост", color: "brand" },
          { icon: <Target size={18} />, value: String(form.activity_factor), label: "Коэфф. активности", color: "violet" },
        ].map((s) => (
          <div key={s.label} className="glass-card p-4 flex items-center gap-3">
            <div className={`h-9 w-9 rounded-xl grid place-items-center shrink-0 ${s.color === "brand" ? "bg-brand-gradient text-white" : "bg-violet-500/15 text-violet-400"}`}>
              {s.icon}
            </div>
            <div className="min-w-0">
              <div className="display font-extrabold text-lg leading-none">{s.value}</div>
              <div className="text-[11px] text-muted mt-0.5">{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Редактировать профиль</CardTitle>
        </CardHeader>
        <div className="grid md:grid-cols-2 gap-4">
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
              type="number" step={0.05}
              value={form.activity_factor}
              onChange={(e) => setForm({ ...form, activity_factor: +e.target.value })}
            />
          </div>
        </div>
        <div className="mt-5">
          <Button onClick={save} disabled={saving}>{saving ? "Сохранение…" : "Сохранить"}</Button>
        </div>
      </Card>
    </div>
  );
}
