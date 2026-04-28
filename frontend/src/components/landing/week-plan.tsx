"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ChevronRight, CircleCheck, Coffee, Dumbbell, Heart } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { WEEK } from "@/lib/constants";

type DayCard = { label: string; focus: string; icon: React.ReactNode; done?: boolean; active?: boolean };

const DEFAULT: DayCard[] = [
  { label: "Пн", focus: "Грудь", icon: <Dumbbell size={18} />, done: true },
  { label: "Вт", focus: "Спина", icon: <Dumbbell size={18} />, done: true },
  { label: "Ср", focus: "Ноги", icon: <Dumbbell size={18} />, active: true },
  { label: "Чт", focus: "Плечи", icon: <Dumbbell size={18} /> },
  { label: "Пт", focus: "Руки", icon: <Dumbbell size={18} /> },
  { label: "Сб", focus: "Кардио", icon: <Heart size={18} /> },
  { label: "Вс", focus: "Отдых", icon: <Coffee size={18} /> },
];

export function WeekPlan({ days = DEFAULT }: { days?: DayCard[] }) {
  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle>План на эту неделю</CardTitle>
        <Link href="/dashboard/workouts" className="text-xs font-semibold text-brand-500 dark:text-violet-300 inline-flex items-center gap-1 hover:underline">
          Просмотреть весь план <ChevronRight size={14} />
        </Link>
      </CardHeader>

      <div className="grid grid-cols-3 md:grid-cols-7 gap-2 md:gap-3">
        {WEEK.map((w, idx) => {
          const d = days[idx] ?? { label: w, focus: "—", icon: <Dumbbell size={18} /> };
          return (
            <motion.div
              key={w}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className={`glass-card p-3 md:p-4 hover-lift ${
                d.active
                  ? "ring-2 ring-brand-500/60 dark:ring-accent-500/70 shadow-glow-brand dark:shadow-glow"
                  : ""
              }`}
            >
              <div className="text-xs font-semibold">{w}</div>
              <div className="text-[11px] text-muted mb-3">{d.focus}</div>
              <div
                className={`h-9 w-9 rounded-xl grid place-items-center ${
                  d.active
                    ? "bg-brand-gradient dark:bg-neon-gradient text-white"
                    : d.done
                      ? "bg-emerald-500/15 text-emerald-500"
                      : "bg-black/5 dark:bg-white/[0.06] text-muted"
                }`}
              >
                {d.done ? <CircleCheck size={18} /> : d.icon}
              </div>
            </motion.div>
          );
        })}
      </div>
    </Card>
  );
}
