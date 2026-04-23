"use client";

import { AlertTriangle, CheckCircle2, Sparkles, Target } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { AIExplanation } from "@/features/ai/types";

type Props = {
  explanation: AIExplanation;
  rationale?: string;
  latencyMs?: number;
  model?: string | null;
};

export function AIExplanationBlock({ explanation, rationale, latencyMs, model }: Props) {
  const { headline, bullets, warnings, next_steps, source } = explanation;

  return (
    <div className="glass-card p-4 space-y-3 animate-fade-up">
      <div className="flex items-center gap-2">
        <Sparkles size={16} className="text-brand-500" />
        <div className="display font-bold">Почему такой план?</div>
        <div className="ml-auto flex items-center gap-2">
          <Badge tone={source === "llm" ? "brand" : "default"}>
            {source === "llm" ? "AI" : "Rule-based"}
          </Badge>
          {model && source === "llm" && <span className="text-[10px] text-muted">{model}</span>}
          {typeof latencyMs === "number" && latencyMs > 0 && (
            <span className="text-[10px] text-muted">{latencyMs} мс</span>
          )}
        </div>
      </div>

      {headline && <p className="text-sm font-medium">{headline}</p>}
      {rationale && <p className="text-xs text-muted">{rationale}</p>}

      {bullets.length > 0 && (
        <ul className="space-y-1.5">
          {bullets.map((b, i) => (
            <li key={i} className="flex gap-2 text-sm">
              <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-emerald-500" />
              <span>{b}</span>
            </li>
          ))}
        </ul>
      )}

      {warnings.length > 0 && (
        <div className="pt-2 border-t border-[var(--border)] space-y-1.5">
          {warnings.map((w, i) => (
            <div key={i} className="flex gap-2 text-xs text-amber-500">
              <AlertTriangle size={13} className="mt-0.5 shrink-0" />
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}

      {next_steps.length > 0 && (
        <div className="pt-2 border-t border-[var(--border)]">
          <div className="flex items-center gap-1.5 text-xs font-semibold mb-1.5">
            <Target size={12} /> Дальше
          </div>
          <ul className="space-y-1">
            {next_steps.map((n, i) => (
              <li key={i} className="text-xs text-muted">· {n}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
