"use client";

import { useMemo } from "react";

export type WeightPoint = { recorded_at: string; weight_kg: number };

export function WeightChart({ data }: { data: WeightPoint[] }) {
  const { path, area, min, max, first, last } = useMemo(() => {
    if (!data.length) return { path: "", area: "", min: 0, max: 0, first: 0, last: 0 };
    const ys = data.map((d) => d.weight_kg);
    const min = Math.min(...ys) - 1;
    const max = Math.max(...ys) + 1;
    const W = 600, H = 160, P = 12;
    const sx = (i: number) => P + (i * (W - P * 2)) / Math.max(1, data.length - 1);
    const sy = (v: number) => H - P - ((v - min) / Math.max(0.01, max - min)) * (H - P * 2);
    const points = data.map((d, i) => [sx(i), sy(d.weight_kg)] as const);
    const path = points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x},${y}`).join(" ");
    const area = `${path} L${points[points.length - 1][0]},${H - P} L${points[0][0]},${H - P} Z`;
    return { path, area, min, max, first: data[0].weight_kg, last: data[data.length - 1].weight_kg };
  }, [data]);

  if (!data.length) {
    return <div className="glass-card p-6 text-sm text-muted">Пока нет данных. Добавь первую запись.</div>;
  }

  const delta = +(last - first).toFixed(1);

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-xs text-muted">Вес, кг</div>
          <div className="display text-2xl font-extrabold">{last.toFixed(1)}</div>
        </div>
        <div className={`text-xs font-semibold ${delta < 0 ? "text-emerald-500" : delta > 0 ? "text-brand-500" : "text-muted"}`}>
          {delta > 0 ? "+" : ""}{delta} кг
        </div>
      </div>
      <svg viewBox="0 0 600 160" className="w-full h-[160px]">
        <defs>
          <linearGradient id="grad" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.45" />
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={area} fill="url(#grad)" />
        <path d={path} fill="none" stroke="#8b5cf6" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
      </svg>
      <div className="flex justify-between text-[10px] text-muted mt-1">
        <span>min {min.toFixed(1)}</span>
        <span>max {max.toFixed(1)}</span>
      </div>
    </div>
  );
}
