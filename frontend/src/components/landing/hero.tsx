"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Flame, Sparkles, TrendingUp, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

const HERO_STATS = [
  { label: "Тренировок", value: "28" },
  { label: "Выполнено целей", value: "97%" },
];

export function Hero() {
  return (
    <section className="relative overflow-hidden rounded-3xl mt-6 glass-card">
      <div className="absolute inset-0 -z-10 grid-bg opacity-40" />
      <div className="absolute -top-24 right-0 -z-10 h-96 w-96 rounded-full bg-violet-500/30 blur-3xl" />
      <div className="absolute -bottom-24 -left-16 -z-10 h-80 w-80 rounded-full bg-brand-500/25 blur-3xl" />

      <div className="grid md:grid-cols-2 items-center gap-8 p-6 md:p-10">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="space-y-6"
        >
          <span className="inline-flex items-center gap-2 glass-card px-3 py-1 text-xs">
            <Sparkles size={14} className="text-violet-500" />
            Умные тренировки для реальных результатов
          </span>

          <h1 className="display text-4xl md:text-6xl font-extrabold leading-[1.05]">
            Тренировки,
            <br />
            <span className="bg-brand-gradient bg-clip-text text-transparent">созданные для тебя</span>
          </h1>

          <p className="text-muted max-w-lg">
            Персонализируй план, отслеживай прогресс и достигай новых вершин вместе с GYM.
          </p>

          <div className="flex flex-wrap items-center gap-3">
            <Link href="/dashboard/workouts">
              <Button size="lg">
                Сгенерировать тренировку <ArrowRight size={18} />
              </Button>
            </Link>
            <div className="flex items-center gap-3 ml-1">
              <div className="flex -space-x-2">
                {["#ff5f4c", "#8b5cf6", "#22c55e", "#eab308"].map((c, i) => (
                  <div key={i} className="h-8 w-8 rounded-full border-2 border-[var(--bg)]" style={{ background: c }} />
                ))}
              </div>
              <div>
                <div className="font-bold">10K+</div>
                <div className="text-xs text-muted">довольных атлетов</div>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7 }}
          className="relative aspect-[4/5] rounded-2xl overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-violet-500/25 via-brand-500/15 to-purple-900/20" />
          <div className="absolute inset-0 grid-bg opacity-30" />

          <div className="relative h-full w-full flex flex-col items-center justify-center gap-4 p-6">
            <div className="display text-[7rem] leading-none font-black opacity-[0.07] select-none absolute">GYM</div>

            <div className="relative flex flex-col items-center gap-3 w-full">
              <div className="h-28 w-28 rounded-full bg-brand-gradient/20 border-2 border-brand-500/30 flex items-center justify-center">
                <div className="h-20 w-20 rounded-full bg-brand-gradient/40 border border-brand-400/40 flex items-center justify-center">
                  <Zap size={32} className="text-brand-400" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 w-full mt-2">
                {HERO_STATS.map((s) => (
                  <div key={s.label} className="glass-card p-3 text-center">
                    <div className="display text-xl font-extrabold text-brand-500">{s.value}</div>
                    <div className="text-[10px] text-muted mt-0.5">{s.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="absolute bottom-4 right-4 glass-card px-4 py-3 flex items-center gap-3">
            <Flame className="text-brand-500 shrink-0" />
            <div>
              <div className="text-xs text-muted">Серия побед</div>
              <div className="display text-2xl font-extrabold">12</div>
              <div className="text-[10px] text-muted">дней подряд</div>
            </div>
          </div>

          <div className="absolute top-4 left-4 glass-card px-3 py-2 flex items-center gap-2">
            <TrendingUp size={14} className="text-violet-400" />
            <div className="text-xs font-semibold">+12.4 кг прогресс</div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
