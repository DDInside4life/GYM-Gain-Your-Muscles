"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/components/providers/theme-provider";

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      onClick={toggle}
      aria-label="Toggle theme"
      className="h-9 w-9 inline-flex items-center justify-center rounded-full border border-[var(--border)] bg-white/40 dark:bg-white/[0.04] hover:bg-white/80 dark:hover:bg-white/10 transition"
    >
      {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  );
}
