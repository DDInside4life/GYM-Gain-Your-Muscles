import { api } from "@/lib/api";
import type {
  FeedbackInput, GenerateInput, WorkoutDayUpdate, WorkoutPlan, WorkoutResultInput,
} from "./types";

export const workoutApi = {
  current: () => api<WorkoutPlan | null>("/workouts/current", { auth: true }),
  history: () => api<WorkoutPlan[]>("/workouts/history", { auth: true }),
  predefined: () => api<Array<{ id: string; name: string; days_per_week: number; goal: string }>>("/workouts/predefined", { auth: true }),
  generate: (payload: GenerateInput) =>
    api<WorkoutPlan>("/workouts/generate", { method: "POST", body: JSON.stringify(payload), auth: true }),
  progress: () => api<WorkoutPlan>("/workouts/progress", { method: "POST", auth: true }),
  get: (planId: number) => api<WorkoutPlan>(`/workouts/${planId}`, { auth: true }),
  select: (planId: number) => api<WorkoutPlan>(`/workouts/${planId}/select`, { method: "POST", auth: true }),
  updateDay: (planId: number, dayId: number, payload: WorkoutDayUpdate) =>
    api<WorkoutPlan>(`/workouts/${planId}/days/${dayId}`, { method: "PUT", body: JSON.stringify(payload), auth: true }),
  submitResult: (payload: WorkoutResultInput) =>
    api("/workouts/results", { method: "POST", body: JSON.stringify(payload), auth: true }),
  feedback: (payload: FeedbackInput) =>
    api<unknown>("/workouts/feedback", { method: "POST", body: JSON.stringify(payload), auth: true }),
};
