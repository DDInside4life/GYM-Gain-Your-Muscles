"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronDown, Search } from "lucide-react";
import { cn } from "@/lib/utils";

const STATIC_FAQ = [
  { q: "Как часто менять программу?", a: "Оптимально каждые 8–12 недель. Если прогресс остановился или упражнения стали слишком лёгкими — сигнал к смене программы." },
  { q: "Нужен ли кардио?", a: "Кардио улучшает работу сердца и ускоряет восстановление. 2–3 лёгких сессии в неделю достаточно для большинства целей." },
  { q: "Сколько отдыхать между подходами?", a: "Для силы: 3–5 минут. Для гипертрофии: 1–3 минуты. Для выносливости: менее 1 минуты." },
  { q: "Как понять, что перетренировался?", a: "Падение результатов, хроническая усталость, плохой сон, раздражительность. Возьми 1–2 дня полного отдыха." },
  { q: "Можно ли тренироваться каждый день?", a: "Можно, если чередовать группы мышц. Каждая мышца должна отдыхать минимум 48 часов." },
  { q: "Как правильно питаться для набора массы?", a: "Профицит калорий 300–500 ккал, 1.6–2.2 г белка на кг веса, достаточно углеводов для энергии." },
];

export default function FaqPage() {
  const [openStatic, setOpenStatic] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  useEffect(() => {
    setOpenStatic(null);
  }, [search]);

  const filteredStatic = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return STATIC_FAQ.map((it, idx) => ({ ...it, idx }));
    return STATIC_FAQ
      .map((it, idx) => ({ ...it, idx }))
      .filter((it) => it.q.toLowerCase().includes(q) || it.a.toLowerCase().includes(q));
  }, [search]);

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
    </div>
  );
}
