"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Calendar,
  Dumbbell,
  Flame,
  Plus,
  Salad,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth-store";
import { workoutApi } from "@/features/workout/api";
import { trainingApi } from "@/features/training/api";
import type { WorkoutPlan } from "@/features/workout/types";
import type { ProgressResponse } from "@/features/training/types";

const DAY_OF_WEEK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

export default function HomePage() {
  const user = useAuth((s) => s.user)!;
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [historyCount, setHistoryCount] = useState(0);

  useEffect(() => {
    Promise.allSettled([
      workoutApi.current(),
      workoutApi.history(),
      trainingApi.progress(),
    ]).then(([currentRes, historyRes, progressRes]) => {
      if (currentRes.status === "fulfilled") setPlan(currentRes.value);
      if (historyRes.status === "fulfilled") setHistoryCount(historyRes.value.length);
      if (progressRes.status === "fulfilled") setProgress(progressRes.value);
      setLoading(false);
    });
  }, []);

  const weeks = useMemo(
    () => (plan ? Array.from(new Set(plan.days.map((d) => d.week_index))).sort((a, b) => a - b) : []),
    [plan],
  );

  const currentWeek = useMemo(() => {
    if (!plan || weeks.length === 0) return 1;
    const fromParams = (plan.params as Record<string, unknown> | null)?.cycle_week;
    const value = typeof fromParams === "number" ? fromParams : 1;
    return weeks.includes(value) ? value : weeks[0];
  }, [plan, weeks]);

  const weekDays = useMemo(
    () => (plan ? plan.days.filter((d) => d.week_index === currentWeek) : []),
    [plan, currentWeek],
  );

  const totalVolumeKg = progress
    ? Object.values(progress.weekly_volume).reduce((acc, v) => acc + v, 0)
    : 0;
  const recentVolume = progress
    ? Object.entries(progress.weekly_volume)
        .sort((a, b) => Number(a[0]) - Number(b[0]))
        .slice(-5)
    : [];

  return (
    <div className="space-y-6 animate-fade-up">
      <div className="relative overflow-hidden rounded-3xl bg-brand-gradient dark:bg-neon-gradient p-6 md:p-8 text-white shadow-glow-brand dark:shadow-glow">
        <div className="absolute inset-0 grid-bg opacity-20" />
        <div className="relative">
          <div className="text-xs uppercase tracking-wider opacity-80">Главная</div>
          <h1 className="display font-extrabold text-2xl md:text-3xl mt-1">
            Привет, {user.full_name?.split(" ")[0] || user.email.split("@")[0]}
          </h1>
          <p className="text-sm md:text-base opacity-90 mt-1">
            {plan
              ? `Активная программа: ${plan.name}`
              : "Начните с генерации программы за 4 коротких шага"}
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-3">
              <span className="h-9 w-9 rounded-xl grid place-items-center bg-brand-500/10 text-brand-500 dark:bg-violet-500/15 dark:text-violet-300">
                <Sparkles size={18} />
              </span>
              <CardTitle>Быстрые действия</CardTitle>
            </div>
          </div>
        </CardHeader>
        <div className="grid sm:grid-cols-3 gap-3">
          <ActionCard
            href="/dashboard/workouts/plan"
            icon={<Dumbbell size={18} />}
            title="Открыть план"
            subtitle={plan ? `Месяц ${plan.month_index}` : "Создайте программу"}
            disabled={!plan}
          />
          <ActionCard
            href="/dashboard/workouts/generate"
            icon={<Plus size={18} />}
            title="Сгенерировать программу"
            subtitle="4 коротких вопроса"
          />
          <ActionCard
            href="/dashboard/nutrition"
            icon={<Salad size={18} />}
            title="Добавить приём пищи"
            subtitle="Питание и калории"
          />
        </div>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-3">
              <span className="h-9 w-9 rounded-xl grid place-items-center bg-brand-500/10 text-brand-500 dark:bg-violet-500/15 dark:text-violet-300">
                <Calendar size={18} />
              </span>
              <CardTitle>Текущий план</CardTitle>
            </div>
            {plan && (
              <Badge tone="brand">
                Неделя {currentWeek}
                {weeks.length > 1 && ` из ${weeks.length}`}
              </Badge>
            )}
          </div>
        </CardHeader>
        {loading ? (
          <div className="text-sm text-muted">Загрузка…</div>
        ) : !plan ? (
          <div className="text-sm text-muted">
            Активного плана нет. Сгенерируйте программу, чтобы увидеть тренировки на неделю.
          </div>
        ) : weekDays.length === 0 ? (
          <div className="text-sm text-muted">Тренировок на этой неделе нет.</div>
        ) : (
          <div className="grid sm:grid-cols-2 gap-3">
            {weekDays.map((day) => (
              <Link
                key={day.id}
                href="/dashboard/workouts/plan"
                className="glass-card p-4 hover-lift transition-transform"
              >
                <div className="flex items-center justify-between">
                  <div className="font-semibold">{day.title}</div>
                  <Badge>{day.is_rest ? "Отдых" : `${day.exercises.length} упр.`}</Badge>
                </div>
                {day.focus && (
                  <div className="text-[12px] text-muted mt-1">{day.focus}</div>
                )}
                <div className="text-[11px] text-muted mt-2">
                  {DAY_OF_WEEK[day.day_index % 7]} · день {day.day_index + 1}
                </div>
              </Link>
            ))}
          </div>
        )}
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-3">
              <span className="h-9 w-9 rounded-xl grid place-items-center bg-brand-500/10 text-brand-500 dark:bg-violet-500/15 dark:text-violet-300">
                <TrendingUp size={18} />
              </span>
              <CardTitle>Прогресс</CardTitle>
            </div>
            {progress && progress.volume_delta_pct !== 0 && (
              <Badge tone={progress.volume_delta_pct >= 0 ? "success" : "default"}>
                {progress.volume_delta_pct >= 0 ? "+" : ""}
                {progress.volume_delta_pct.toFixed(1)}%
              </Badge>
            )}
          </div>
        </CardHeader>
        <div className="grid sm:grid-cols-3 gap-3">
          <Stat
            icon={<Dumbbell size={18} />}
            value={historyCount}
            label="Программ создано"
          />
          <Stat
            icon={<Flame size={18} />}
            value={recentVolume.length}
            label="Активных недель"
          />
          <Stat
            icon={<TrendingUp size={18} />}
            value={`${(totalVolumeKg / 1000).toFixed(1)} т`}
            label="Общий объём"
          />
        </div>
        {recentVolume.length > 0 && (
          <div className="mt-4">
            <div className="text-xs text-muted mb-2">Объём по неделям</div>
            <VolumeChart data={recentVolume} />
          </div>
        )}
      </Card>
    </div>
  );
}

function ActionCard({
  href,
  icon,
  title,
  subtitle,
  disabled = false,
}: {
  href: string;
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  disabled?: boolean;
}) {
  if (disabled) {
    return (
      <div className="glass-card p-4 opacity-60 cursor-not-allowed">
        <div className="h-9 w-9 rounded-xl grid place-items-center bg-brand-500/10 text-brand-500 dark:bg-violet-500/15 dark:text-violet-300">
          {icon}
        </div>
        <div className="mt-3 font-semibold">{title}</div>
        <div className="text-[12px] text-muted mt-1">{subtitle}</div>
      </div>
    );
  }
  return (
    <Link href={href} className="glass-card p-4 hover-lift transition-transform">
      <div className="h-9 w-9 rounded-xl grid place-items-center bg-brand-500/10 text-brand-500 dark:bg-violet-500/15 dark:text-violet-300">
        {icon}
      </div>
      <div className="mt-3 font-semibold">{title}</div>
      <div className="text-[12px] text-muted mt-1">{subtitle}</div>
    </Link>
  );
}

function Stat({
  icon,
  value,
  label,
}: {
  icon: React.ReactNode;
  value: number | string;
  label: string;
}) {
  return (
    <div className="glass-card p-4 hover-lift">
      <div className="h-9 w-9 rounded-xl grid place-items-center bg-brand-500/10 text-brand-500 dark:bg-violet-500/15 dark:text-violet-300">
        {icon}
      </div>
      <div className="display font-extrabold text-2xl mt-3 leading-none">{value}</div>
      <div className="text-xs text-muted mt-1">{label}</div>
    </div>
  );
}

function VolumeChart({ data }: { data: Array<[string, number]> }) {
  const max = Math.max(...data.map(([, v]) => v), 1);
  return (
    <div className="grid grid-cols-5 gap-3 items-end h-[120px]">
      {data.map(([week, vol]) => {
        const heightPct = Math.max((vol / max) * 100, 8);
        return (
          <div key={week} className="flex flex-col items-center justify-end h-full">
            <div className="text-[10px] text-muted mb-1">{vol.toFixed(0)}</div>
            <div
              className="w-full max-w-[48px] rounded-t-lg bg-brand-gradient dark:bg-neon-gradient"
              style={{ height: `${heightPct}%` }}
            />
            <div className="text-[10px] text-muted mt-1">Нед. {week}</div>
          </div>
        );
      })}
    </div>
  );
}
