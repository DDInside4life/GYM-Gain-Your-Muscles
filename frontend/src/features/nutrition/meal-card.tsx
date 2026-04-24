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
    <motion.div layout className="rounded-2xl border border-[var(--border)] bg-white/40 p-4 dark:bg-white/5">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between text-left"
      >
        <div>
          <p className="text-base font-semibold">{meal.name}</p>
          <p className="text-xs text-muted">{meal.food_entries.length} блюд</p>
        </div>
        <ChevronDown size={16} className={`transition-transform ${isExpanded ? "rotate-180" : ""}`} />
      </button>

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
                    className="flex items-center justify-between gap-3 rounded-xl border border-[var(--border)] px-3 py-2"
                  >
                    <div>
                      <p className="text-sm font-medium">{entry.name}</p>
                      <p className="text-xs text-muted">
                        {entry.grams} г | {entry.calories} ккал | Б {entry.calculated_protein} / Ж {entry.calculated_fat} / У {entry.calculated_carbs}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => onDeleteFood(entry.id)}
                      disabled={deletingFoodId === entry.id}
                    >
                      <Trash2 size={14} />
                    </Button>
                  </motion.div>
                ))
              )}
              <div className="rounded-xl border border-[var(--border)] bg-white/20 px-3 py-2 text-xs dark:bg-white/5">
                Итого: {meal.total_calories} ккал | Б {meal.total_protein} г | Ж {meal.total_fat} г | У {meal.total_carbs} г
              </div>

              <div className="grid grid-cols-2 gap-2 lg:grid-cols-6">
                <Input
                  value={draft.name}
                  placeholder="Название блюда"
                  onChange={(e) => onChangeDraft((prev) => ({ ...prev, name: e.target.value }))}
                />
                <NumericInput
                  value={draft.protein_per_100g}
                  placeholder="Белки/100г"
                  onChange={(next) => onChangeDraft((prev) => ({ ...prev, protein_per_100g: next }))}
                />
                <NumericInput
                  value={draft.fat_per_100g}
                  placeholder="Жиры/100г"
                  onChange={(next) => onChangeDraft((prev) => ({ ...prev, fat_per_100g: next }))}
                />
                <NumericInput
                  value={draft.carbs_per_100g}
                  placeholder="Углеводы/100г"
                  onChange={(next) => onChangeDraft((prev) => ({ ...prev, carbs_per_100g: next }))}
                />
                <NumericInput
                  value={draft.grams}
                  placeholder="Граммы"
                  onChange={(next) => onChangeDraft((prev) => ({ ...prev, grams: next }))}
                />
                <Button onClick={onSubmitFood} disabled={isSubmitting}>
                  <Plus size={14} />
                  {isSubmitting ? "Добавляем..." : "Добавить блюдо"}
                </Button>
              </div>
              {formError && <p className="text-xs text-red-400">{formError}</p>}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
