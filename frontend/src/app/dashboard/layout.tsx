"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { Dumbbell, Home, LineChart, ListChecks, LogOut, Salad, Settings, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-store";

const tabs = [
  { href: "/dashboard", label: "Главная", icon: Home },
  { href: "/dashboard/workouts", label: "Тренировки", icon: Dumbbell },
  { href: "/dashboard/exercises", label: "Упражнения", icon: ListChecks },
  { href: "/dashboard/nutrition", label: "Питание", icon: Salad },
  { href: "/dashboard/progress", label: "Прогресс", icon: LineChart },
  { href: "/dashboard/profile", label: "Профиль", icon: User },
];

const EXPERIENCE_LABEL: Record<string, string> = {
  beginner: "Beginner",
  intermediate: "Intermediate",
  advanced: "Advanced",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading, logout } = useAuth();

  useEffect(() => {
    if (!loading && !user) router.push("/sign-in");
  }, [user, loading, router]);

  if (!user) {
    return <div className="py-16 text-center text-muted">Загрузка…</div>;
  }

  const initials = (user.full_name || user.email)
    .split(" ")
    .slice(0, 2)
    .map((w: string) => w[0]?.toUpperCase() ?? "")
    .join("");

  return (
    <div className="grid md:grid-cols-[260px_1fr] gap-6 py-6">
      <aside className="glass-card p-5 h-max sticky top-24">
        <div className="flex flex-col items-center text-center pb-5 border-b border-[var(--border)]">
          <div className="relative">
            <div className="h-20 w-20 rounded-2xl bg-brand-gradient dark:bg-neon-gradient grid place-items-center text-white display font-extrabold text-2xl shadow-glow-brand dark:shadow-glow">
              {initials}
            </div>
            <span className="absolute -bottom-1 -right-1 h-5 w-5 rounded-full bg-emerald-500 border-2 border-[var(--bg)]" />
          </div>
          <div className="mt-3 min-w-0 w-full">
            <div className="display font-extrabold text-base truncate">
              {user.full_name || user.email.split("@")[0]}
            </div>
            <div className="mt-1 inline-flex items-center gap-1 text-[10px] uppercase tracking-wider text-muted">
              {EXPERIENCE_LABEL[user.experience ?? "intermediate"] ?? "Athlete"}
            </div>
          </div>
        </div>

        <nav className="mt-4 space-y-1">
          {tabs.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150",
                  active
                    ? "bg-brand-gradient dark:bg-neon-gradient text-white shadow-glow-brand dark:shadow-glow"
                    : "hover:bg-black/5 dark:hover:bg-white/5 text-muted hover:text-inherit",
                )}
              >
                <Icon size={16} className="shrink-0" />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-5 pt-4 border-t border-[var(--border)] space-y-1.5">
          <Button variant="outline" size="sm" className="w-full justify-start">
            <Settings size={14} /> Настройки
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start"
            onClick={() => { logout(); router.push("/"); }}
          >
            <LogOut size={14} /> Выйти
          </Button>
        </div>
      </aside>
      <section>{children}</section>
    </div>
  );
}
