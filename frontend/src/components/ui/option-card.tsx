"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

type OptionCardProps = {
  active: boolean;
  onClick?: () => void;
  title: string;
  subtitle?: string;
  description?: string;
  icon?: ReactNode;
  badge?: ReactNode;
  disabled?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
};

const SIZE: Record<NonNullable<OptionCardProps["size"]>, string> = {
  sm: "p-3 gap-2",
  md: "p-4 gap-3",
  lg: "p-5 gap-3",
};

export function OptionCard({
  active,
  onClick,
  title,
  subtitle,
  description,
  icon,
  badge,
  disabled,
  size = "md",
  className,
}: OptionCardProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "group relative w-full overflow-hidden text-left rounded-2xl border transition-all duration-200",
        "bg-[var(--card)] backdrop-blur-xl",
        SIZE[size],
        active
          ? "border-transparent ring-2 ring-[var(--ring)] shadow-glass dark:shadow-glow"
          : "border-[var(--border)] hover:border-[var(--border-strong)] hover:-translate-y-0.5",
        disabled && "opacity-50 pointer-events-none",
        "flex flex-col",
        className,
      )}
    >
      {active && (
        <span className="absolute inset-0 -z-10 opacity-90 bg-brand-gradient/15 dark:bg-neon-gradient/20" />
      )}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          {icon && (
            <span
              className={cn(
                "h-9 w-9 rounded-xl grid place-items-center shrink-0 transition-colors",
                active
                  ? "bg-brand-gradient dark:bg-neon-gradient text-white shadow-glow-brand dark:shadow-glow"
                  : "bg-brand-500/10 text-brand-500 dark:bg-violet-500/15 dark:text-violet-300",
              )}
            >
              {icon}
            </span>
          )}
          <div className="min-w-0">
            <div className="display font-bold text-sm md:text-base leading-tight truncate">{title}</div>
            {subtitle && <div className="text-[11px] text-muted mt-0.5">{subtitle}</div>}
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {badge}
          <span
            className={cn(
              "h-5 w-5 rounded-full grid place-items-center border transition-all",
              active
                ? "bg-brand-gradient dark:bg-neon-gradient text-white border-transparent"
                : "border-[var(--border-strong)] text-transparent",
            )}
          >
            <Check size={12} strokeWidth={3} />
          </span>
        </div>
      </div>
      {description && (
        <p className="text-xs leading-relaxed text-muted">
          {description}
        </p>
      )}
    </button>
  );
}

type ChipProps = {
  active: boolean;
  onClick?: () => void;
  children: ReactNode;
  tone?: "default" | "brand" | "violet" | "danger" | "warning";
  className?: string;
  disabled?: boolean;
};

const CHIP_ACTIVE: Record<NonNullable<ChipProps["tone"]>, string> = {
  default: "bg-brand-gradient dark:bg-neon-gradient text-white border-transparent",
  brand: "bg-brand-gradient text-white border-transparent",
  violet: "bg-violet-500/85 text-white border-transparent",
  danger: "bg-red-500/85 text-white border-transparent",
  warning: "bg-amber-500/85 text-white border-transparent",
};

const CHIP_HOVER: Record<NonNullable<ChipProps["tone"]>, string> = {
  default: "hover:border-brand-500/60",
  brand: "hover:border-brand-500/60",
  violet: "hover:border-violet-500/60",
  danger: "hover:border-red-500/60",
  warning: "hover:border-amber-500/60",
};

export function Chip({ active, onClick, children, tone = "default", className, disabled }: ChipProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "px-3 py-1.5 rounded-lg text-sm border transition-colors",
        active ? CHIP_ACTIVE[tone] : `border-[var(--border)] ${CHIP_HOVER[tone]}`,
        disabled && "opacity-40 pointer-events-none",
        className,
      )}
    >
      {children}
    </button>
  );
}
