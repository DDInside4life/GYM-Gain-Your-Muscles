"use client";

import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "ghost" | "outline" | "glass" | "soft";
type Size = "sm" | "md" | "lg";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
};

const variants: Record<Variant, string> = {
  primary:
    "text-white bg-brand-gradient dark:bg-neon-gradient shadow-glow-brand dark:shadow-glow hover:opacity-95 active:opacity-90",
  ghost:
    "bg-transparent hover:bg-black/5 dark:hover:bg-white/5 text-inherit",
  outline:
    "bg-transparent border border-[var(--border-strong)] hover:bg-black/5 dark:hover:bg-white/5",
  glass:
    "glass-card hover:bg-white/80 dark:hover:bg-white/10",
  soft:
    "bg-brand-500/10 text-brand-500 dark:bg-violet-500/15 dark:text-violet-300 hover:bg-brand-500/15 dark:hover:bg-violet-500/25",
};

const sizes: Record<Size, string> = {
  sm: "text-xs px-3 py-1.5 rounded-lg",
  md: "text-sm px-4 py-2.5 rounded-xl",
  lg: "text-base px-6 py-3.5 rounded-2xl",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 font-semibold transition-all duration-200 disabled:opacity-50 disabled:pointer-events-none focus:outline-none focus:ring-2 focus:ring-[var(--ring)]",
        variants[variant], sizes[size], className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";
