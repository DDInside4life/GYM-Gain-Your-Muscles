"use client";

import { forwardRef, type InputHTMLAttributes, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const base =
  "w-full rounded-xl px-4 py-2.5 text-sm bg-white/70 dark:bg-white/[0.04] border border-[var(--border)] outline-none transition placeholder:text-muted focus:border-[var(--border-strong)] focus:ring-2 focus:ring-[var(--ring)]";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => <input ref={ref} className={cn(base, className)} {...props} />,
);
Input.displayName = "Input";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => <textarea ref={ref} className={cn(base, "min-h-[96px]", className)} {...props} />,
);
Textarea.displayName = "Textarea";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <select ref={ref} className={cn(base, "appearance-none pr-8 bg-no-repeat bg-[length:14px] bg-[position:right_12px_center]", className)} {...props}>
      {children}
    </select>
  ),
);
Select.displayName = "Select";

export function Label({ children, className }: { children: React.ReactNode; className?: string }) {
  return <label className={cn("text-xs font-medium text-muted mb-1.5 block", className)}>{children}</label>;
}
