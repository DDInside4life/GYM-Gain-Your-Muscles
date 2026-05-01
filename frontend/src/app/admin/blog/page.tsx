"use client";

import { useEffect, useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Select, Textarea } from "@/components/ui/input";
import { api } from "@/lib/api";

type Category = { id: number; slug: string; name: string };
type Post = {
  id: number;
  slug: string;
  title: string;
  excerpt: string;
  content_md: string;
  cover_url: string | null;
  is_published: boolean;
  category_id: number | null;
};

const EMPTY_FORM = {
  slug: "",
  title: "",
  excerpt: "",
  cover_url: "",
  content_md: "",
  category_id: "",
  is_published: true,
};

export default function AdminBlogPage() {
  const [items, setItems] = useState<Post[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [newCategory, setNewCategory] = useState({ slug: "", name: "" });
  const [editingSlug, setEditingSlug] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  async function load() {
    const [posts, cats] = await Promise.all([
      api<Post[]>("/blog/admin/posts", { auth: true }),
      api<Category[]>("/blog/categories"),
    ]);
    setItems(posts);
    setCategories(cats);
  }
  useEffect(() => { load(); }, []);

  async function create() {
    const payload = {
      ...form,
      cover_url: form.cover_url || null,
      category_id: form.category_id ? Number(form.category_id) : null,
    };
    await api("/blog/posts", {
      method: "POST",
      body: JSON.stringify(payload),
      auth: true,
    });
    setForm(EMPTY_FORM);
    setEditingSlug(null);
    await load();
  }

  async function update() {
    if (!editingSlug) return;
    const payload = {
      title: form.title,
      excerpt: form.excerpt,
      content_md: form.content_md,
      cover_url: form.cover_url || null,
      category_id: form.category_id ? Number(form.category_id) : null,
      is_published: form.is_published,
    };
    await api(`/blog/posts/${editingSlug}`, {
      method: "PUT",
      body: JSON.stringify(payload),
      auth: true,
    });
    setForm(EMPTY_FORM);
    setEditingSlug(null);
    await load();
  }

  function startEdit(post: Post) {
    setEditingSlug(post.slug);
    setForm({
      slug: post.slug,
      title: post.title,
      excerpt: post.excerpt,
      cover_url: post.cover_url ?? "",
      content_md: post.content_md,
      category_id: post.category_id ? String(post.category_id) : "",
      is_published: post.is_published,
    });
  }

  async function remove(slug: string) {
    await api(`/blog/posts/${slug}`, { method: "DELETE", auth: true });
    await load();
  }

  async function createCategory() {
    if (!newCategory.slug || !newCategory.name) return;
    await api("/blog/categories", {
      method: "POST",
      body: JSON.stringify(newCategory),
      auth: true,
    });
    setNewCategory({ slug: "", name: "" });
    await load();
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>{editingSlug ? "Редактирование статьи" : "Новая статья"}</CardTitle></CardHeader>
        <div className="space-y-3">
          <div><Label>Slug</Label><Input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} /></div>
          <div><Label>Title</Label><Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
          <div><Label>Excerpt</Label><Input value={form.excerpt} onChange={(e) => setForm({ ...form, excerpt: e.target.value })} /></div>
          <div><Label>Cover URL</Label><Input value={form.cover_url} onChange={(e) => setForm({ ...form, cover_url: e.target.value })} /></div>
          <div>
            <Label>Category</Label>
            <Select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
              <option value="">Без категории</option>
              {categories.map((cat) => <option key={cat.id} value={cat.id}>{cat.name}</option>)}
            </Select>
          </div>
          <label className="inline-flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.is_published}
              onChange={(e) => setForm({ ...form, is_published: e.target.checked })}
            />
            Опубликовано
          </label>
          <div><Label>Content (Markdown)</Label><Textarea rows={10} value={form.content_md} onChange={(e) => setForm({ ...form, content_md: e.target.value })} /></div>
          <div className="flex gap-2">
            {editingSlug ? (
              <>
                <Button onClick={update}>Сохранить</Button>
                <Button variant="outline" onClick={() => { setEditingSlug(null); setForm(EMPTY_FORM); }}>Отмена</Button>
              </>
            ) : (
              <Button onClick={create}>Создать статью</Button>
            )}
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader><CardTitle>Категории</CardTitle></CardHeader>
        <div className="grid md:grid-cols-3 gap-2">
          <Input placeholder="slug" value={newCategory.slug} onChange={(e) => setNewCategory({ ...newCategory, slug: e.target.value })} />
          <Input placeholder="name" value={newCategory.name} onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })} />
          <Button onClick={createCategory}>Добавить категорию</Button>
        </div>
      </Card>

      <Card>
        <CardHeader><CardTitle>Статьи · {items.length}</CardTitle></CardHeader>
        <div className="space-y-2">
          {items.map((p) => (
            <div key={p.id} className="glass-card p-3 flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold">{p.title}</div>
                <div className="text-[11px] text-muted">{p.slug} · {p.is_published ? "published" : "draft"}</div>
              </div>
              <div className="flex gap-1">
                <Button size="sm" variant="ghost" onClick={() => startEdit(p)}><Pencil size={14} /></Button>
                <Button size="sm" variant="ghost" onClick={() => remove(p.slug)}><Trash2 size={14} /></Button>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
