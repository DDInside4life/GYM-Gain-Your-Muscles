"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ChevronRight, CircleCheck, Coffee, Dumbbell, Heart } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { WEEK } from "@/lib/constants";
import { workoutApi } from "@/features/workout/api";
import type { WeekProgress, WorkoutDay, WorkoutPlan } from "@/features/workout/types";

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
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [weeklyProgress, setWeeklyProgress] = useState<WeekProgress[]>([]);

  useEffect(() => {
    workoutApi.current().then(setPlan).catch(() => setPlan(null));
  }, []);

  useEffect(() => {
    if (!plan) {
      setWeeklyProgress([]);
      return;
    }
    workoutApi.planProgress(plan.id).then(setWeeklyProgress).catch(() => setWeeklyProgress([]));
  }, [plan]);

  const normalizedToday = useMemo(() => {
    const jsDay = new Date().getDay();
    return jsDay === 0 ? 6 : jsDay - 1; // Mon=0..Sun=6
  }, []);

  const effectiveDays = useMemo(() => {
    if (!plan) return days;

    const weeks = Array.from(new Set(plan.days.map((d) => d.week_index))).sort((a, b) => a - b);
    const inProgress = weeklyProgress.find((w) => w.week_status === "in_progress");
    const upcoming = weeklyProgress.find((w) => w.week_status === "upcoming");
    const currentWeek = inProgress?.week_index
      ?? upcoming?.week_index
      ?? (weeks.includes(plan.cycle_week) ? plan.cycle_week : weeks[0] ?? 1);

    const weekDays = plan.days.filter((d) => d.week_index === currentWeek);
    const weekStatus = weeklyProgress.find((w) => w.week_index === currentWeek)?.week_status ?? "upcoming";
    const byDow = new Map<number, WorkoutDay>();
    for (const d of weekDays) byDow.set(d.day_index % 7, d);

    return WEEK.map((w, idx) => {
      const d = byDow.get(idx);
      if (!d) return { label: w, focus: "—", icon: <Dumbbell size={18} /> };
      const isRest = d.is_rest;
      const focus = isRest ? "Отдых" : (d.focus || `${d.exercises.length} упр.`);
      const icon = isRest
        ? <Coffee size={18} />
        : focus.toLowerCase().includes("кардио")
        ? <Heart size={18} />
        : <Dumbbell size={18} />;
      const isToday = idx === normalizedToday;
      return {
        label: w,
        focus,
        icon,
        active: isToday,
        done: !isRest && !isToday && (weekStatus === "complete" || (weekStatus === "in_progress" && idx < normalizedToday)),
      };
    });
  }, [days, normalizedToday, plan, weeklyProgress]);

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle>План на эту неделю</CardTitle>
        <Link href="/dashboard/workouts/plan" className="text-xs font-semibold text-brand-500 dark:text-violet-300 inline-flex items-center gap-1 hover:underline">
          Просмотреть весь план <ChevronRight size={14} />
        </Link>
      </CardHeader>

      <div className="grid grid-cols-3 md:grid-cols-7 gap-2 md:gap-3">
        {WEEK.map((w, idx) => {
          const d = effectiveDays[idx] ?? { label: w, focus: "—", icon: <Dumbbell size={18} /> };
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
