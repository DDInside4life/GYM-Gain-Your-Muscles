import { api } from "@/lib/api";
import type {
  AIExplanation,
  AINutritionInput,
  AINutritionResponse,
  AIProgressionResponse,
  AIStatus,
  AIWorkoutResponse,
  GenerateInput,
} from "./types";

export const aiApi = {
  status: () => api<AIStatus>("/ai/status"),
  generateWorkout: (payload: GenerateInput) =>
    api<AIWorkoutResponse>("/ai/workouts/generate", {
      method: "POST",
      body: JSON.stringify(payload),
      auth: true,
    }),
  progressWorkout: () =>
    api<AIProgressionResponse>("/ai/workouts/progress", {
      method: "POST",
      auth: true,
    }),
  generateNutrition: (payload: AINutritionInput) =>
    api<AINutritionResponse>("/ai/nutrition/generate", {
      method: "POST",
      body: JSON.stringify(payload),
      auth: true,
    }),
  planExplanation: (planId: number) =>
    api<AIExplanation>(`/ai/plans/${planId}/explanation`, { auth: true }),
};
