"use client";

import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

type Question = { id: number; title: string; body: string; is_approved: boolean };

export default function AdminForumPage() {
  const [items, setItems] = useState<Question[]>([]);

  async function load() { setItems(await api<Question[]>("/forum/questions")); }
  useEffect(() => { load(); }, []);

  async function remove(id: number) {
    await api(`/admin/forum/questions/${id}`, { method: "DELETE", auth: true });
    load();
  }

  return (
    <Card>
      <CardHeader><CardTitle>Модерация форума</CardTitle></CardHeader>
      <div className="space-y-2">
        {items.map((q) => (
          <div key={q.id} className="glass-card p-3 flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold">{q.title}</div>
              <div className="text-[11px] text-muted line-clamp-2">{q.body}</div>
            </div>
            <Button size="sm" variant="ghost" onClick={() => remove(q.id)}><Trash2 size={14} /></Button>
          </div>
        ))}
      </div>
    </Card>
  );
}
