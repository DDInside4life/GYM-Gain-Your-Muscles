"use client";

import { useEffect, useState } from "react";
import { MessageSquare, Send, ThumbsUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea, Label } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-store";

type Question = {
  id: number; title: string; body: string;
  tags: string[]; reactions: Record<string, number>;
  created_at: string;
};

type Comment = {
  id: number; parent_id: number | null;
  body: string; reactions: Record<string, number>;
  created_at: string;
};

type Detail = Question & { comments: Comment[] };

export default function FaqPage() {
  const user = useAuth((s) => s.user);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [openId, setOpenId] = useState<number | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");

  async function loadList() {
    setQuestions(await api<Question[]>("/forum/questions"));
  }
  useEffect(() => { loadList(); }, []);

  async function open(id: number) {
    setOpenId(id);
    setDetail(await api<Detail>(`/forum/questions/${id}`));
  }

  async function ask(e: React.FormEvent) {
    e.preventDefault();
    if (!user) return;
    await api("/forum/questions", {
      method: "POST",
      body: JSON.stringify({ title, body, tags: [] }),
      auth: true,
    });
    setTitle(""); setBody("");
    loadList();
  }

  async function reactQ(id: number, r: string) {
    await api(`/forum/questions/${id}/react`, {
      method: "POST",
      body: JSON.stringify({ reaction: r }),
    });
    if (openId === id) open(id);
    loadList();
  }

  function Tree({ comments, parent = null }: { comments: Comment[]; parent?: number | null }) {
    const items = comments.filter((c) => c.parent_id === parent);
    return (
      <div className={parent ? "ml-5 border-l border-[var(--border)] pl-3 mt-2" : "space-y-2"}>
        {items.map((c) => (
          <div key={c.id} className="glass-card p-3">
            <p className="text-sm">{c.body}</p>
            <div className="text-[11px] text-muted mt-1">
              {new Date(c.created_at).toLocaleDateString()}
            </div>
            <Tree comments={comments} parent={c.id} />
            <ReplyForm questionId={detail!.id} parentId={c.id} onPosted={() => open(detail!.id)} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6 py-6">
      <Card>
        <CardHeader>
          <CardTitle>FAQ / Форум</CardTitle>
          <MessageSquare className="text-violet-500" />
        </CardHeader>

        {user && (
          <form onSubmit={ask} className="glass-card p-4 space-y-3 mb-5">
            <div>
              <Label>Вопрос</Label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} required minLength={3} />
            </div>
            <div>
              <Label>Подробности</Label>
              <Textarea value={body} onChange={(e) => setBody(e.target.value)} />
            </div>
            <Button type="submit"><Send size={14} /> Опубликовать</Button>
          </form>
        )}

        <div className="space-y-3">
          {questions.map((q) => (
            <div key={q.id} className="glass-card p-4">
              <div className="flex items-start justify-between gap-4">
                <button onClick={() => open(q.id)} className="text-left">
                  <div className="display font-bold">{q.title}</div>
                  <div className="text-xs text-muted mt-1 line-clamp-2">{q.body}</div>
                </button>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => reactQ(q.id, "like")}
                    className="inline-flex items-center gap-1 text-xs glass-card px-2 py-1"
                  >
                    <ThumbsUp size={12} /> {q.reactions?.like ?? 0}
                  </button>
                </div>
              </div>

              {openId === q.id && detail && (
                <div className="mt-4 space-y-3">
                  <p className="text-sm">{detail.body}</p>
                  <Tree comments={detail.comments} />
                  {user && <ReplyForm questionId={detail.id} parentId={null} onPosted={() => open(detail.id)} />}
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function ReplyForm({ questionId, parentId, onPosted }: { questionId: number; parentId: number | null; onPosted: () => void }) {
  const [body, setBody] = useState("");
  const [open, setOpen] = useState(false);
  const user = useAuth((s) => s.user);
  if (!user) return null;

  async function send() {
    if (!body.trim()) return;
    await api(`/forum/questions/${questionId}/comments`, {
      method: "POST",
      body: JSON.stringify({ body, parent_id: parentId }),
      auth: true,
    });
    setBody(""); setOpen(false);
    onPosted();
  }

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="text-xs text-brand-500 mt-2">
        Ответить
      </button>
    );
  }

  return (
    <div className="mt-2 space-y-2">
      <Textarea value={body} onChange={(e) => setBody(e.target.value)} placeholder="Ваш ответ…" />
      <div className="flex gap-2">
        <Button size="sm" onClick={send}>Отправить</Button>
        <Button size="sm" variant="ghost" onClick={() => setOpen(false)}>Отмена</Button>
      </div>
    </div>
  );
}
