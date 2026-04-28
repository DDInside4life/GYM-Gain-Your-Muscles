"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { FoodDraft, Meal } from "./types";
import { sanitizeNonNegativeNumericInput } from "./utils";

type MealCardProps = {
  meal: Meal;
  draft: FoodDraft;
  isExpanded: boolean;
  isSubmitting: boolean;
  deletingFoodId: number | null;
  formError: string | null;
  onToggle: () => void;
  onChangeDraft: (updater: (draft: FoodDraft) => FoodDraft) => void;
  onSubmitFood: () => void;
  onDeleteFood: (entryId: number) => void;
};

function NumericInput({
  value,
  placeholder,
  onChange,
}: {
  value: string;
  placeholder: string;
  onChange: (next: string) => void;
}) {
  return (
    <Input
      type="number"
      min="0"
      value={value}
      placeholder={placeholder}
      onChange={(e) => {
        const next = sanitizeNonNegativeNumericInput(e.target.value, true);
        if (next !== null) onChange(next);
      }}
    />
  );
}

function StatPill({ label, value, color }: { label: string; value: number | string; color: string }) {
  return (
    <div className="flex flex-col items-center min-w-[58px]">
      <span
        className="display font-extrabold text-base leading-none"
        style={{ color }}
      >
        {value}
      </span>
      <span className="text-[10px] text-muted uppercase tracking-wider mt-1">{label}</span>
    </div>
  );
}

export function MealCard({
  meal,
  draft,
  isExpanded,
  isSubmitting,
  deletingFoodId,
  formError,
  onToggle,
  onChangeDraft,
  onSubmitFood,
  onDeleteFood,
}: MealCardProps) {
  return (
    <motion.div layout className="glass-card p-4 hover-lift">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between text-left gap-4"
      >
        <div className="min-w-0">
          <p className="display text-base font-bold truncate">{meal.name}</p>
          <p className="text-xs text-muted">{meal.food_entries.length} {meal.food_entries.length === 1 ? "блюдо" : "блюд"}</p>
        </div>
        <div className="flex items-center gap-4 md:gap-6">
          <div className="hidden sm:flex items-center gap-4">
            <StatPill label="Ккал" value={meal.total_calories} color="#ff4533" />
            <StatPill label="Б" value={`${meal.total_protein} г`} color="#a855f7" />
            <StatPill label="Ж" value={`${meal.total_fat} г`} color="#ff8a7c" />
            <StatPill label="У" value={`${meal.total_carbs} г`} color="#c084fc" />
          </div>
          <ChevronDown
            size={16}
            className={`text-muted transition-transform shrink-0 ${isExpanded ? "rotate-180" : ""}`}
          />
        </div>
      </button>

      <div className="sm:hidden mt-3 grid grid-cols-4 gap-2 text-center">
        <StatPill label="Ккал" value={meal.total_calories} color="#ff4533" />
        <StatPill label="Б" value={`${meal.total_protein}г`} color="#a855f7" />
        <StatPill label="Ж" value={`${meal.total_fat}г`} color="#ff8a7c" />
        <StatPill label="У" value={`${meal.total_carbs}г`} color="#c084fc" />
      </div>

      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-4 space-y-3">
              {meal.food_entries.length === 0 ? (
                <p className="text-sm text-muted">Пока нет блюд.</p>
              ) : (
                meal.food_entries.map((entry) => (
                  <motion.div
                    key={entry.id}
                    layout
                    className="flex items-center justify-between gap-3 rounded-xl border border-[var(--border)] bg-white/40 dark:bg-white/[0.03] px-3 py-2"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-semibold truncate">{entry.name}</p>
                      <p className="text-xs text-muted">
                        {entry.grams} г · {entry.calories} ккал · Б {entry.calculated_protein} / Ж {entry.calculated_fat} / У {entry.calculated_carbs}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDeleteFood(entry.id)}
                      disabled={deletingFoodId === entry.id}
                      className="text-muted hover:text-red-500"
                    >
                      <Trash2 size={14} />
                    </Button>
                  </motion.div>
                ))
              )}

              <div className="grid grid-cols-2 gap-2 lg:grid-cols-6">
                <Input
                  value={draft.name}
                  placeholder="Название блюда"
                  onChange={(e) => onChangeDraft((prev) => ({ ...prev, name: e.target.value }))}
                  className="lg:col-span-2"
                />
                <NumericInput
                  value={draft.protein_per_100g}
                  placeholder="Б/100г"
                  onChange={(next) => onChangeDraft((prev) => ({ ...prev, protein_per_100g: next }))}
                />
                <NumericInput
                  value={draft.fat_per_100g}
                  placeholder="Ж/100г"
                  onChange={(next) => onChangeDraft((prev) => ({ ...prev, fat_per_100g: next }))}
                />
                <NumericInput
                  value={draft.carbs_per_100g}
                  placeholder="У/100г"
                  onChange={(next) => onChangeDraft((prev) => ({ ...prev, carbs_per_100g: next }))}
                />
                <NumericInput
                  value={draft.grams}
                  placeholder="Граммы"
                  onChange={(next) => onChangeDraft((prev) => ({ ...prev, grams: next }))}
                />
              </div>
              <Button onClick={onSubmitFood} disabled={isSubmitting} size="sm">
                <Plus size={14} />
                {isSubmitting ? "Добавляем…" : "Добавить блюдо"}
              </Button>
              {formError && <p className="text-xs text-red-400">{formError}</p>}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
