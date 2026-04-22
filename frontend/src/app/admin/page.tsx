"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

type Analytics = Record<string, number>;

export default function AdminDashboard() {
  const [data, setData] = useState<Analytics | null>(null);
  useEffect(() => {
    api<Analytics>("/admin/analytics", { auth: true }).then(setData).catch(() => setData({}));
  }, []);
  return (
    <Card>
      <CardHeader><CardTitle>Аналитика</CardTitle></CardHeader>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {Object.entries(data ?? {}).map(([k, v]) => (
          <div key={k} className="glass-card p-4">
            <div className="text-xs text-muted">{k}</div>
            <div className="display text-2xl font-extrabold">{v}</div>
          </div>
        ))}
      </div>
    </Card>
  );
}
