"use client";

import Link from "next/link";
import { ChevronRight, Dumbbell } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { motion } from "framer-motion";

type Item = { name: string; muscle: string; sets: string; reps: string };

const ITEMS: Item[] = [
  { name: "Жим штанги лёжа", muscle: "Грудь", sets: "4 подхода", reps: "8–12 повторений" },
  { name: "Подтягивания",   muscle: "Спина", sets: "4 подхода", reps: "6–10 повторений" },
  { name: "Приседания со штангой", muscle: "Ноги", sets: "4 подхода", reps: "8–12 повторений" },
  { name: "Жим гантелей сидя", muscle: "Плечи", sets: "3 подхода", reps: "10–12 повторений" },
];

export function ExerciseGrid({ items = ITEMS }: { items?: Item[] }) {
  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle>Рекомендовано для тебя</CardTitle>
        <Link href="/dashboard/workouts" className="text-xs text-brand-500 inline-flex items-center gap-1">
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
            className="glass-card p-3 overflow-hidden group"
          >
            <div className="relative h-36 rounded-xl bg-gradient-to-br from-violet-500/20 via-brand-500/10 to-transparent grid place-items-center overflow-hidden">
              <Dumbbell className="h-14 w-14 opacity-30 group-hover:scale-110 transition" />
              <span className="absolute top-2 left-2 text-[10px] px-2 py-0.5 rounded-full bg-black/40 text-white">
                {it.muscle}
              </span>
            </div>
            <div className="pt-3">
              <div className="display font-bold text-sm">{it.name}</div>
              <div className="text-[11px] text-muted mt-1">{it.sets}</div>
              <div className="text-[11px] text-muted">{it.reps}</div>
            </div>
          </motion.div>
        ))}
      </div>
    </Card>
  );
}
