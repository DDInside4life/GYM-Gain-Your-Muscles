"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Flame, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Hero() {
  return (
    <section className="relative overflow-hidden rounded-3xl mt-6">
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
          className="relative aspect-square md:aspect-[4/5] glass-card p-4"
        >
          <div className="absolute inset-0 rounded-2xl bg-[radial-gradient(400px_200px_at_50%_100%,rgba(139,92,246,0.35),transparent)]" />
          <div className="relative h-full w-full rounded-2xl overflow-hidden bg-gradient-to-br from-violet-500/20 via-brand-500/10 to-transparent grid place-items-center">
            <div className="display text-[10rem] leading-none font-black opacity-10 select-none">GYM</div>
            <div className="absolute bottom-4 right-4 glass-card px-4 py-3 flex items-center gap-3">
              <Flame className="text-brand-500" />
              <div>
                <div className="text-xs text-muted">Серия побед</div>
                <div className="display text-2xl font-extrabold">12</div>
                <div className="text-[10px] text-muted">дней подряд</div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
