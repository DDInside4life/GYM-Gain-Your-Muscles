"use client";

import { useState } from "react";
import { Flame, Salad } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Select } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-store";

type NutritionPlan = {
  id: number;
  calories: number;
  protein_g: number;
  fat_g: number;
  carbs_g: number;
  bmr: number;
  tdee: number;
  goal_label: string;
  meals: {
    id: number; title: string; calories: number;
    protein_g: number; fat_g: number; carbs_g: number;
    items: { name: string; amount_g: number }[];
  }[];
};

export default function NutritionPage() {
  const user = useAuth((s) => s.user)!;
  const [form, setForm] = useState({
    weight_kg: user.weight_kg ?? 75,
    height_cm: user.height_cm ?? 175,
    age: 28,
    sex: user.sex ?? "male",
    activity_factor: user.activity_factor ?? 1.55,
    goal: user.goal ?? "muscle_gain",
  });
  const [plan, setPlan] = useState<NutritionPlan | null>(null);
  const [loading, setLoading] = useState(false);

  async function generate() {
    setLoading(true);
    try {
      const p = await api<NutritionPlan>("/nutrition/generate", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          weight_kg: Number(form.weight_kg),
          height_cm: Number(form.height_cm),
          age: Number(form.age),
          activity_factor: Number(form.activity_factor),
        }),
        auth: true,
      });
      setPlan(p);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Питание</CardTitle>
          <Salad className="text-emerald-500" />
        </CardHeader>
        <div className="grid md:grid-cols-3 gap-3">
          <div>
            <Label>Вес (кг)</Label>
            <Input type="number" value={form.weight_kg} onChange={(e) => setForm({ ...form, weight_kg: +e.target.value })} />
          </div>
          <div>
            <Label>Рост (см)</Label>
            <Input type="number" value={form.height_cm} onChange={(e) => setForm({ ...form, height_cm: +e.target.value })} />
          </div>
          <div>
            <Label>Возраст</Label>
            <Input type="number" value={form.age} onChange={(e) => setForm({ ...form, age: +e.target.value })} />
          </div>
          <div>
            <Label>Пол</Label>
            <Select value={form.sex as string} onChange={(e) => setForm({ ...form, sex: e.target.value as never })}>
              <option value="male">Мужской</option>
              <option value="female">Женский</option>
            </Select>
          </div>
          <div>
            <Label>Активность</Label>
            <Select value={String(form.activity_factor)} onChange={(e) => setForm({ ...form, activity_factor: +e.target.value })}>
              <option value="1.2">Сидячий (1.2)</option>
              <option value="1.375">Лёгкая (1.375)</option>
              <option value="1.55">Умеренная (1.55)</option>
              <option value="1.725">Высокая (1.725)</option>
              <option value="1.9">Очень высокая (1.9)</option>
            </Select>
          </div>
          <div>
            <Label>Цель</Label>
            <Select value={form.goal as string} onChange={(e) => setForm({ ...form, goal: e.target.value as never })}>
              <option value="muscle_gain">Набор массы</option>
              <option value="fat_loss">Жиросжигание</option>
              <option value="strength">Сила</option>
              <option value="endurance">Выносливость</option>
              <option value="general">Общее</option>
            </Select>
          </div>
        </div>
        <div className="mt-5">
          <Button onClick={generate} disabled={loading}><Flame size={16} /> {loading ? "…" : "Рассчитать"}</Button>
        </div>
      </Card>

      {plan && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: "Калории", v: plan.calories, c: "brand" as const },
              { label: "Белки, г", v: plan.protein_g, c: "violet" as const },
              { label: "Жиры, г", v: plan.fat_g, c: "brand" as const },
              { label: "Углеводы, г", v: plan.carbs_g, c: "violet" as const },
            ].map((it) => (
              <div key={it.label} className="glass-card p-4">
                <div className="text-xs text-muted">{it.label}</div>
                <div className={`display text-2xl font-extrabold ${it.c === "brand" ? "text-brand-500" : "text-violet-500"}`}>
                  {it.v}
                </div>
              </div>
            ))}
          </div>

          <Card>
            <CardHeader><CardTitle>План приёмов пищи</CardTitle></CardHeader>
            <div className="grid md:grid-cols-2 gap-3">
              {plan.meals.map((m) => (
                <div key={m.id} className="glass-card p-4">
                  <div className="flex items-center justify-between">
                    <div className="display font-bold">{m.title}</div>
                    <div className="text-xs text-muted">{m.calories} ккал</div>
                  </div>
                  <div className="text-[11px] text-muted mt-1">
                    Б {m.protein_g} · Ж {m.fat_g} · У {m.carbs_g}
                  </div>
                  <ul className="mt-3 text-sm space-y-1">
                    {m.items.map((i) => (
                      <li key={i.name} className="flex justify-between border-b border-[var(--border)] py-1">
                        <span>{i.name}</span><span className="text-muted">{i.amount_g} г</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
