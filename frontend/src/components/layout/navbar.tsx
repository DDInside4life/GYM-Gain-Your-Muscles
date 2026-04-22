"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Dumbbell, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useAuth } from "@/lib/auth-store";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Главная" },
  { href: "/dashboard", label: "Профиль" },
  { href: "/dashboard/workouts", label: "Тренировки" },
  { href: "/blog", label: "Блог" },
  { href: "/dashboard/nutrition", label: "Питание" },
  { href: "/faq", label: "FAQ" },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);

  return (
    <header className="sticky top-4 z-50 px-4">
      <nav className="glass-card mx-auto max-w-6xl flex items-center gap-2 px-4 py-2.5">
        <Link href="/" className="flex items-center gap-2 pr-2">
          <div className="h-8 w-8 rounded-lg bg-brand-gradient grid place-items-center">
            <Dumbbell size={16} className="text-white" />
          </div>
          <span className="display font-extrabold text-lg">GYM</span>
        </Link>

        <ul className="hidden md:flex items-center gap-1 ml-2">
          {links.map((l) => {
            const active = pathname === l.href || (l.href !== "/" && pathname.startsWith(l.href));
            return (
              <li key={l.href}>
                <Link
                  href={l.href}
                  className={cn(
                    "px-3 py-1.5 text-sm rounded-lg transition",
                    active
                      ? "text-brand-500 dark:text-violet-400"
                      : "text-muted hover:text-inherit hover:bg-black/5 dark:hover:bg-white/5",
                  )}
                >
                  {l.label}
                </Link>
              </li>
            );
          })}
        </ul>

        <div className="ml-auto flex items-center gap-2">
          <ThemeToggle />
          {user ? (
            <>
              {user.is_admin && (
                <Link href="/admin">
                  <Button variant="outline" size="sm">Admin</Button>
                </Link>
              )}
              <Button variant="ghost" size="sm" onClick={() => { logout(); router.push("/"); }}>
                <LogOut size={14} /> Выйти
              </Button>
            </>
          ) : (
            <>
              <Link href="/sign-up"><Button variant="primary" size="sm">Sign up</Button></Link>
              <Link href="/sign-in"><Button variant="ghost" size="sm">Sign in</Button></Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
