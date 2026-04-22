"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Label, Select } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-store";

export default function ProfilePage() {
  const user = useAuth((s) => s.user)!;
  const refreshMe = useAuth((s) => s.refreshMe);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    full_name: user.full_name ?? "",
    sex: user.sex ?? "",
    height_cm: user.height_cm ?? 175,
    weight_kg: user.weight_kg ?? 75,
    experience: user.experience ?? "intermediate",
    goal: user.goal ?? "muscle_gain",
    activity_factor: user.activity_factor ?? 1.55,
  });

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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Профиль</CardTitle>
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
  );
}
