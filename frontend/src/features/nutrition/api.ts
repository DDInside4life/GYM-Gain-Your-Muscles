import { api } from "@/lib/api";
import type {
  CreateFoodEntryInput,
  CreateMealInput,
  FoodEntry,
  Meal,
  NutritionDailySummary,
  NutritionTargets,
  NutritionTargetsInput,
} from "./types";

export const nutritionApi = {
  getMealsByDate: (date: string) => api<Meal[]>(`/meals?date=${encodeURIComponent(date)}`, { auth: true }),
  createMeal: (payload: CreateMealInput) =>
    api<Meal>("/meals", { method: "POST", body: JSON.stringify(payload), auth: true }),
  createFoodEntry: (payload: CreateFoodEntryInput) =>
    api<FoodEntry>("/food-entries", { method: "POST", body: JSON.stringify(payload), auth: true }),
  deleteFoodEntry: (entryId: number) => api<void>(`/food-entries/${entryId}`, { method: "DELETE", auth: true }),
  getDailySummary: (date: string) =>
    api<NutritionDailySummary>(`/nutrition/daily-summary?date=${encodeURIComponent(date)}`, { auth: true }),
  calculateTargets: (payload: NutritionTargetsInput) =>
    api<NutritionTargets>("/nutrition/targets", { method: "POST", body: JSON.stringify(payload), auth: true }),
};
