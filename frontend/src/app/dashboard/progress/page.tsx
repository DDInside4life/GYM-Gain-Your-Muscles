"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label } from "@/components/ui/input";
import { WeightChart, type WeightPoint } from "@/components/dashboard/weight-chart";
import { api } from "@/lib/api";

export default function ProgressPage() {
  const [data, setData] = useState<WeightPoint[]>([]);
  const [weight, setWeight] = useState(75);
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today);

  async function load() {
    const items = await api<{ recorded_at: string; weight_kg: number }[]>("/users/me/weights", { auth: true });
    setData(items);
  }

  useEffect(() => { load(); }, []);

  async function add() {
    await api("/users/me/weights", {
      method: "POST",
      body: JSON.stringify({ weight_kg: weight, recorded_at: date }),
      auth: true,
    });
    await load();
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Прогресс веса</CardTitle>
        </CardHeader>
        <WeightChart data={data} />
      </Card>

      <Card>
        <CardHeader><CardTitle>Добавить запись</CardTitle></CardHeader>
        <div className="grid md:grid-cols-3 gap-3">
          <div>
            <Label>Вес (кг)</Label>
            <Input type="number" step={0.1} value={weight} onChange={(e) => setWeight(+e.target.value)} />
          </div>
          <div>
            <Label>Дата</Label>
            <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
          <div className="flex items-end">
            <Button onClick={add}>Добавить</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
