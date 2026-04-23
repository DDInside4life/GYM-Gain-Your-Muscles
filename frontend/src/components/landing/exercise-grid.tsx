"use client";

import Link from "next/link";
import { ChevronRight, Dumbbell } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { motion } from "framer-motion";

type Item = { name: string; muscle: string; sets: string; reps: string; gradient?: string };

const ITEMS: Item[] = [
  { name: "Жим штанги лёжа", muscle: "Грудь", sets: "4 подхода", reps: "8–12 повторений", gradient: "from-brand-500/30 to-brand-900/10" },
  { name: "Подтягивания", muscle: "Спина", sets: "4 подхода", reps: "6–10 повторений", gradient: "from-violet-500/30 to-violet-900/10" },
  { name: "Приседания со штангой", muscle: "Ноги", sets: "4 подхода", reps: "8–12 повторений", gradient: "from-brand-400/25 to-violet-500/10" },
  { name: "Жим гантелей сидя", muscle: "Плечи", sets: "3 подхода", reps: "10–12 повторений", gradient: "from-violet-400/25 to-brand-500/10" },
];

export function ExerciseGrid({ items = ITEMS }: { items?: Item[] }) {
  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle>Рекомендовано для тебя</CardTitle>
        <Link href="/dashboard/exercises" className="text-xs text-brand-500 inline-flex items-center gap-1 hover:underline">
          Смотреть все упражнения <ChevronRight size={14} />
        </Link>
      </CardHeader>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {items.map((it, idx) => (
          <motion.div
            key={it.name}
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: idx * 0.05 }}
            className="glass-card p-3 overflow-hidden group cursor-pointer hover:shadow-glow transition-shadow duration-300"
          >
            <div className={`relative h-36 rounded-xl bg-gradient-to-br ${it.gradient ?? "from-violet-500/20 via-brand-500/10 to-transparent"} grid place-items-center overflow-hidden`}>
              <div className="absolute inset-0 grid-bg opacity-20" />
              <div className="h-16 w-16 rounded-full bg-white/5 border border-white/10 grid place-items-center group-hover:scale-110 transition-transform duration-300">
                <Dumbbell className="h-8 w-8 opacity-50" />
              </div>
              <span className="absolute top-2 left-2 text-[10px] px-2 py-0.5 rounded-full bg-black/50 text-white font-medium backdrop-blur-sm">
                {it.muscle}
              </span>
            </div>
            <div className="pt-3">
              <div className="display font-bold text-sm leading-tight">{it.name}</div>
              <div className="flex gap-2 mt-2">
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-500 font-medium">{it.sets}</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-400 font-medium">{it.reps}</span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </Card>
  );
}
