import { api } from "@/lib/api";
import type { FeedbackInput, GenerateInput, WorkoutPlan } from "./types";

export const workoutApi = {
  current: () => api<WorkoutPlan | null>("/workouts/current", { auth: true }),
  history: () => api<WorkoutPlan[]>("/workouts/history", { auth: true }),
  generate: (payload: GenerateInput) =>
    api<WorkoutPlan>("/workouts/generate", { method: "POST", body: JSON.stringify(payload), auth: true }),
  progress: () => api<WorkoutPlan>("/workouts/progress", { method: "POST", auth: true }),
  feedback: (payload: FeedbackInput) =>
    api<unknown>("/workouts/feedback", { method: "POST", body: JSON.stringify(payload), auth: true }),
};
