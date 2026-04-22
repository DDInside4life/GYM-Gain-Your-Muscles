"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { BarChart3, BookOpen, Dumbbell, MessagesSquare } from "lucide-react";
import { useAuth } from "@/lib/auth-store";
import { cn } from "@/lib/utils";

const tabs = [
  { href: "/admin", label: "Обзор", icon: BarChart3 },
  { href: "/admin/exercises", label: "Упражнения", icon: Dumbbell },
  { href: "/admin/blog", label: "Блог", icon: BookOpen },
  { href: "/admin/forum", label: "Форум", icon: MessagesSquare },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (loading) return;
    if (!user) router.push("/sign-in");
    else if (!user.is_admin) router.push("/");
  }, [user, loading, router]);

  if (!user?.is_admin) return <div className="py-10 text-center text-muted">Проверка прав…</div>;

  return (
    <div className="grid md:grid-cols-[220px_1fr] gap-6 py-6">
      <aside className="glass-card p-3 h-max sticky top-24">
        <div className="px-2 pb-3 border-b border-[var(--border)] display font-extrabold">Admin</div>
        <nav className="mt-3 space-y-1">
          {tabs.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link key={href} href={href} className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-xl text-sm transition",
                active ? "bg-brand-gradient text-white" : "hover:bg-black/5 dark:hover:bg-white/5 text-muted hover:text-inherit",
              )}>
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
