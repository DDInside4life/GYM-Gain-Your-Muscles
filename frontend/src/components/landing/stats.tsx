"use client";

import { Activity, Clock, Scale, Target } from "lucide-react";

const items = [
  { icon: <Activity size={18} />, value: "28", label: "Тренировок" },
  { icon: <Clock size={18} />, value: "152", label: "Часов тренировок" },
  { icon: <Scale size={18} />, value: "12.4 кг", label: "Прогресс веса" },
  { icon: <Target size={18} />, value: "97%", label: "Выполнено целей" },
];

export function Stats() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
      {items.map((it) => (
        <div key={it.label} className="glass-card p-4 flex items-center gap-4">
          <div className="h-10 w-10 grid place-items-center rounded-xl bg-brand-gradient text-white">
            {it.icon}
          </div>
          <div>
            <div className="display font-extrabold text-xl">{it.value}</div>
            <div className="text-xs text-muted">{it.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
