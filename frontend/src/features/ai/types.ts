import type { GenerateInput, WorkoutPlan } from "@/features/workout/types";

export type AIExplanation = {
  headline: string;
  bullets: string[];
  warnings: string[];
  next_steps: string[];
  source: "llm" | "fallback";
};

export type AIWorkoutResponse = {
  plan: WorkoutPlan;
  source: "llm" | "fallback";
  rationale: string;
  explanation: AIExplanation;
  warnings: string[];
  latency_ms: number;
  model: string | null;
};

export type AIProgressionResponse = {
  plan: WorkoutPlan;
  source: "llm" | "fallback";
  strategy: string;
  rationale: string;
  explanation: AIExplanation;
  warnings: string[];
  latency_ms: number;
  model: string | null;
};

export type AIStatus = { enabled: boolean; provider: string; model: string };

export type { GenerateInput };

export type AINutritionInput = {
  weight_kg: number;
  height_cm: number;
  age: number;
  sex: "male" | "female";
  activity_factor: number;
  goal: "muscle_gain" | "fat_loss" | "strength" | "endurance" | "general";
};

export type AINutritionResponse = {
  plan: {
    id: number;
    calories: number;
    protein_g: number;
    fat_g: number;
    carbs_g: number;
    bmr: number;
    tdee: number;
    goal_label: string;
    meals: {
      id: number;
      position: number;
      title: string;
      calories: number;
      protein_g: number;
      fat_g: number;
      carbs_g: number;
      items: { name: string; amount_g: number }[];
    }[];
  };
  source: "llm" | "fallback";
  rationale: string;
  explanation: AIExplanation;
  warnings: string[];
  latency_ms: number;
  model: string | null;
};
