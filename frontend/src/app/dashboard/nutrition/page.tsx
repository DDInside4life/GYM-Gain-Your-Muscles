"use client";

import { useState } from "react";
import { Brain, Flame, Salad } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Select } from "@/components/ui/input";
import { AIExplanationBlock } from "@/components/dashboard/ai-explanation";
import { aiApi } from "@/features/ai/api";
import { useAiStatus } from "@/features/ai/use-ai-workout";
import type { AIExplanation } from "@/features/ai/types";
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
  const [explanation, setExplanation] = useState<AIExplanation | null>(null);
  const [loading, setLoading] = useState(false);
  const aiStatus = useAiStatus();
  const aiAvailable = !!aiStatus?.enabled;
  const [aiMode, setAiMode] = useState<boolean>(false);

  async function generate() {
    setLoading(true);
    const payload = {
      ...form,
      weight_kg: Number(form.weight_kg),
      height_cm: Number(form.height_cm),
      age: Number(form.age),
      activity_factor: Number(form.activity_factor),
    };
    try {
      if (aiMode && aiAvailable) {
        const res = await aiApi.generateNutrition(payload as never);
        setPlan(res.plan as unknown as NutritionPlan);
        setExplanation(res.explanation);
      } else {
        const p = await api<NutritionPlan>("/nutrition/generate", {
          method: "POST",
          body: JSON.stringify(payload),
          auth: true,
        });
        setPlan(p);
        setExplanation(null);
      }
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
        {aiAvailable && (
          <div className="mt-4 flex items-center gap-3 p-3 rounded-xl border border-[var(--border)]">
            <Brain size={16} className="text-brand-500" />
            <div className="flex-1">
              <div className="text-sm font-semibold">AI-нутрициолог</div>
              <div className="text-xs text-muted">
                Калории и макросы рассчитываются детерминированно; LLM персонализирует приёмы пищи.
              </div>
            </div>
            <label className="inline-flex items-center gap-2 text-xs">
              <input type="checkbox" checked={aiMode} onChange={(e) => setAiMode(e.target.checked)} />
              {aiMode ? <Badge tone="brand">AI</Badge> : <Badge>Rules</Badge>}
            </label>
          </div>
        )}
        <div className="mt-5">
          <Button onClick={generate} disabled={loading}><Flame size={16} /> {loading ? "…" : "Рассчитать"}</Button>
        </div>
      </Card>

      {explanation && <AIExplanationBlock explanation={explanation} />}

      {plan && (
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Сегодня</CardTitle></CardHeader>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 justify-items-center py-2">
              {[
                { label: "Калории", value: plan.calories, max: 3000, color: "#ff4533", unit: "ккал" },
                { label: "Белки", value: plan.protein_g, max: 250, color: "#8b5cf6", unit: "г" },
                { label: "Жиры", value: plan.fat_g, max: 150, color: "#ff5f4c", unit: "г" },
                { label: "Углеводы", value: plan.carbs_g, max: 400, color: "#a78bfa", unit: "г" },
              ].map((it) => (
                <MacroRing key={it.label} {...it} />
              ))}
            </div>
            <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 justify-center text-xs text-muted">
              <span>БМР: {plan.bmr} ккал</span>
              <span>ТДЕЕ: {plan.tdee} ккал</span>
              <span>{plan.goal_label}</span>
            </div>
          </Card>

          <Card>
            <CardHeader><CardTitle>Приёмы пищи</CardTitle></CardHeader>
            <div className="space-y-3">
              {plan.meals.map((m) => (
                <div key={m.id} className="glass-card p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="display font-bold">{m.title}</div>
                    <div className="text-xs text-muted font-semibold">{m.calories} ккал</div>
                  </div>
                  <div className="flex gap-4 text-[11px] text-muted mb-3">
                    <span>Б <span className="font-semibold text-violet-400">{m.protein_g}</span> г</span>
                    <span>Ж <span className="font-semibold text-brand-400">{m.fat_g}</span> г</span>
                    <span>У <span className="font-semibold text-violet-300">{m.carbs_g}</span> г</span>
                  </div>
                  <ul className="text-sm space-y-1">
                    {m.items.map((i) => (
                      <li key={i.name} className="flex justify-between border-b border-[var(--border)] py-1.5">
                        <span>{i.name}</span>
                        <span className="text-muted">{i.amount_g} г</span>
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

function MacroRing({
  value,
  max,
  label,
  color,
  unit,
}: {
  value: number;
  max: number;
  label: string;
  color: string;
  unit: string;
}) {
  const r = 38;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - Math.min(value / max, 1));

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative">
        <svg width="96" height="96" viewBox="0 0 96 96">
          <circle cx="48" cy="48" r={r} fill="none" stroke="rgba(128,128,128,0.12)" strokeWidth="7" />
          <circle
            cx="48" cy="48" r={r}
            fill="none"
            stroke={color}
            strokeWidth="7"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform="rotate(-90 48 48)"
          />
          <text x="48" y="44" textAnchor="middle" fontSize="15" fontWeight="bold" fill="currentColor">
            {value}
          </text>
          <text x="48" y="60" textAnchor="middle" fontSize="10" fill="var(--muted)">
            {unit}
          </text>
        </svg>
      </div>
      <span className="text-xs text-muted font-medium">{label}</span>
    </div>
  );
}
