"use client";

import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Textarea } from "@/components/ui/input";
import { api } from "@/lib/api";

type Post = { id: number; slug: string; title: string; excerpt: string; is_published: boolean };

export default function AdminBlogPage() {
  const [items, setItems] = useState<Post[]>([]);
  const [form, setForm] = useState({ slug: "", title: "", excerpt: "", content_md: "" });

  async function load() { setItems(await api<Post[]>("/blog/posts")); }
  useEffect(() => { load(); }, []);

  async function create() {
    await api("/blog/posts", {
      method: "POST",
      body: JSON.stringify({ ...form, is_published: true }),
      auth: true,
    });
    setForm({ slug: "", title: "", excerpt: "", content_md: "" });
    load();
  }

  async function remove(slug: string) {
    await api(`/blog/posts/${slug}`, { method: "DELETE", auth: true });
    load();
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Новая статья</CardTitle></CardHeader>
        <div className="space-y-3">
          <div><Label>Slug</Label><Input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} /></div>
          <div><Label>Title</Label><Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
          <div><Label>Excerpt</Label><Input value={form.excerpt} onChange={(e) => setForm({ ...form, excerpt: e.target.value })} /></div>
          <div><Label>Content (Markdown)</Label><Textarea rows={10} value={form.content_md} onChange={(e) => setForm({ ...form, content_md: e.target.value })} /></div>
          <Button onClick={create}>Опубликовать</Button>
        </div>
      </Card>

      <Card>
        <CardHeader><CardTitle>Статьи · {items.length}</CardTitle></CardHeader>
        <div className="space-y-2">
          {items.map((p) => (
            <div key={p.id} className="glass-card p-3 flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold">{p.title}</div>
                <div className="text-[11px] text-muted">{p.slug}</div>
              </div>
              <Button size="sm" variant="ghost" onClick={() => remove(p.slug)}><Trash2 size={14} /></Button>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
