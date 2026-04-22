import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

type Tone = "default" | "brand" | "violet" | "success";

const tones: Record<Tone, string> = {
  default: "bg-black/5 dark:bg-white/10 text-inherit",
  brand: "bg-brand-500/15 text-brand-500",
  violet: "bg-violet-500/15 text-violet-500",
  success: "bg-emerald-500/15 text-emerald-500",
};

export function Badge({
  tone = "default",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
