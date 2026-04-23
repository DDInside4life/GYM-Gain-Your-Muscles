"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { Dumbbell, LineChart, ListChecks, Salad, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-store";

const tabs = [
  { href: "/dashboard", label: "Профиль", icon: User },
  { href: "/dashboard/workouts", label: "Тренировки", icon: Dumbbell },
  { href: "/dashboard/exercises", label: "Упражнения", icon: ListChecks },
  { href: "/dashboard/nutrition", label: "Питание", icon: Salad },
  { href: "/dashboard/progress", label: "Прогресс", icon: LineChart },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading } = useAuth();

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
    <div className="grid md:grid-cols-[240px_1fr] gap-6 py-6">
      <aside className="glass-card p-4 h-max sticky top-24">
        <div className="flex items-center gap-3 pb-4 border-b border-[var(--border)]">
          <div className="h-10 w-10 rounded-xl bg-brand-gradient grid place-items-center text-white display font-extrabold shrink-0">
            {initials}
          </div>
          <div className="min-w-0">
            <div className="display font-extrabold text-sm truncate">{user.full_name || user.email}</div>
            <div className="text-[11px] text-muted truncate">{user.experience ?? "Спортсмен"}</div>
          </div>
        </div>
        <nav className="mt-3 space-y-0.5">
          {tabs.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150",
                  active
                    ? "bg-brand-gradient text-white shadow-glow"
                    : "hover:bg-black/5 dark:hover:bg-white/5 text-muted hover:text-inherit",
                )}
              >
                <Icon size={16} className="shrink-0" />
                {label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <section>{children}</section>
    </div>
  );
}
