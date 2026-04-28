"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronDown, MessageSquare, Search, Send, ThumbsUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea, Label } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-store";
import { cn } from "@/lib/utils";

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

const STATIC_FAQ = [
  { q: "Как часто менять программу?", a: "Оптимально каждые 8–12 недель. Если прогресс остановился или упражнения стали слишком лёгкими — сигнал к смене программы." },
  { q: "Нужен ли кардио?", a: "Кардио улучшает работу сердца и ускоряет восстановление. 2–3 лёгких сессии в неделю достаточно для большинства целей." },
  { q: "Сколько отдыхать между подходами?", a: "Для силы: 3–5 минут. Для гипертрофии: 1–3 минуты. Для выносливости: менее 1 минуты." },
  { q: "Как понять, что перетренировался?", a: "Падение результатов, хроническая усталость, плохой сон, раздражительность. Возьми 1–2 дня полного отдыха." },
  { q: "Можно ли тренироваться каждый день?", a: "Можно, если чередовать группы мышц. Каждая мышца должна отдыхать минимум 48 часов." },
  { q: "Как правильно питаться для набора массы?", a: "Профицит калорий 300–500 ккал, 1.6–2.2 г белка на кг веса, достаточно углеводов для энергии." },
];

export default function FaqPage() {
  const user = useAuth((s) => s.user);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [openId, setOpenId] = useState<number | null>(null);
  const [openStatic, setOpenStatic] = useState<number | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [search, setSearch] = useState("");

  async function loadList() {
    setQuestions(await api<Question[]>("/forum/questions"));
  }
  useEffect(() => { loadList(); }, []);

  async function openQuestion(id: number) {
    if (openId === id) { setOpenId(null); return; }
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
    if (openId === id) openQuestion(id);
    loadList();
  }

  const filteredStatic = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return STATIC_FAQ.map((it, idx) => ({ ...it, idx }));
    return STATIC_FAQ
      .map((it, idx) => ({ ...it, idx }))
      .filter((it) => it.q.toLowerCase().includes(q) || it.a.toLowerCase().includes(q));
  }, [search]);

  const filteredQuestions = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return questions;
    return questions.filter(
      (it) => it.title.toLowerCase().includes(q) || (it.body ?? "").toLowerCase().includes(q),
    );
  }, [search, questions]);

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
            <ReplyForm questionId={detail!.id} parentId={c.id} onPosted={() => openQuestion(detail!.id)} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-8 py-8 animate-fade-up">
      <div className="text-center space-y-4">
        <h1 className="display text-3xl md:text-5xl font-extrabold tracking-tight">
          <span className="gradient-text">FAQ</span>
        </h1>
        <p className="text-muted">Ответы на частые вопросы о тренировках, питании и восстановлении.</p>
        <div className="relative max-w-xl mx-auto">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
          <input
            type="search"
            placeholder="Поиск по вопросам…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-2xl pl-11 pr-4 py-3 text-sm bg-white/70 dark:bg-white/[0.04] border border-[var(--border)] outline-none transition placeholder:text-muted focus:border-[var(--border-strong)] focus:ring-2 focus:ring-[var(--ring)]"
          />
        </div>
      </div>

      <div className="space-y-2">
        {filteredStatic.length === 0 ? (
          <div className="glass-card p-8 text-center text-muted text-sm">Ничего не найдено по запросу.</div>
        ) : (
          filteredStatic.map((item) => (
            <div
              key={item.idx}
              className={cn(
                "glass-card overflow-hidden transition-all duration-200",
                openStatic === item.idx && "shadow-glow-brand dark:shadow-glow",
              )}
            >
              <button
                className="w-full flex items-center justify-between p-4 md:px-5 text-left gap-4"
                onClick={() => setOpenStatic(openStatic === item.idx ? null : item.idx)}
              >
                <span className="font-semibold text-sm md:text-base">{item.q}</span>
                <ChevronDown
                  size={18}
                  className={cn(
                    "text-muted shrink-0 transition-transform duration-200",
                    openStatic === item.idx && "rotate-180 text-brand-500 dark:text-violet-300",
                  )}
                />
              </button>
              {openStatic === item.idx && (
                <div className="px-4 md:px-5 pb-5 text-sm text-muted leading-relaxed border-t border-[var(--border)] pt-3">
                  {item.a}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Форум</CardTitle>
          <MessageSquare className="text-violet-500 dark:text-violet-300" size={18} />
        </CardHeader>

        {user && (
          <form onSubmit={ask} className="glass-card p-4 space-y-3 mb-5">
            <div>
              <Label>Вопрос</Label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} required minLength={3} placeholder="Ваш вопрос…" />
            </div>
            <div>
              <Label>Подробности</Label>
              <Textarea value={body} onChange={(e) => setBody(e.target.value)} placeholder="Опишите вопрос подробнее…" />
            </div>
            <Button type="submit" size="sm"><Send size={14} /> Опубликовать</Button>
          </form>
        )}

        <div className="space-y-2">
          {filteredQuestions.length === 0 && (
            <p className="text-sm text-muted text-center py-6">
              {search ? "По запросу ничего не найдено." : "Вопросов пока нет. Будьте первым!"}
            </p>
          )}
          {filteredQuestions.map((q) => (
            <div key={q.id} className="glass-card overflow-hidden">
              <div className="p-4 flex items-start justify-between gap-4">
                <button onClick={() => openQuestion(q.id)} className="text-left flex-1 min-w-0">
                  <div className="display font-bold text-sm">{q.title}</div>
                  <div className="text-xs text-muted mt-1 line-clamp-2">{q.body}</div>
                </button>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => reactQ(q.id, "like")}
                    className="inline-flex items-center gap-1 text-xs glass-card px-2 py-1 hover:text-brand-500 dark:hover:text-violet-300 transition"
                  >
                    <ThumbsUp size={12} /> {q.reactions?.like ?? 0}
                  </button>
                  <ChevronDown
                    size={14}
                    className={cn("text-muted transition-transform duration-200 cursor-pointer", openId === q.id && "rotate-180")}
                    onClick={() => openQuestion(q.id)}
                  />
                </div>
              </div>

              {openId === q.id && detail && (
                <div className="border-t border-[var(--border)] px-4 py-3 space-y-3">
                  <Tree comments={detail.comments} />
                  {user && <ReplyForm questionId={detail.id} parentId={null} onPosted={() => openQuestion(detail.id)} />}
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
      <button onClick={() => setOpen(true)} className="text-xs text-brand-500 dark:text-violet-300 mt-2 hover:underline">
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
