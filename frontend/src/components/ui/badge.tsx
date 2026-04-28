import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

type Tone = "default" | "brand" | "violet" | "success" | "neon";

const tones: Record<Tone, string> = {
  default: "bg-black/5 dark:bg-white/10 text-inherit",
  brand: "bg-brand-500/15 text-brand-500",
  violet: "bg-violet-500/15 text-violet-500 dark:text-violet-300",
  success: "bg-emerald-500/15 text-emerald-500",
  neon: "bg-gradient-to-r from-accent-500/20 to-pink-500/20 text-accent-500 dark:text-accent-400 border border-accent-500/20",
};

export function Badge({
  tone = "default",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium tracking-wide",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
