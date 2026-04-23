"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { User, Dumbbell, Salad, LineChart, ListChecks } from "lucide-react";
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

  return (
    <div className="grid md:grid-cols-[220px_1fr] gap-6 py-6">
      <aside className="glass-card p-3 h-max sticky top-24">
        <div className="px-2 pb-3 border-b border-[var(--border)]">
          <div className="text-xs text-muted">Привет,</div>
          <div className="display font-extrabold truncate">{user.full_name || user.email}</div>
        </div>
        <nav className="mt-3 space-y-1">
          {tabs.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-xl text-sm transition",
                  active
                    ? "bg-brand-gradient text-white"
                    : "hover:bg-black/5 dark:hover:bg-white/5 text-muted hover:text-inherit",
                )}
              >
                <Icon size={16} /> {label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <section>{children}</section>
    </div>
  );
}
