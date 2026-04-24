import { api } from "@/lib/api";
import type {
  FeedbackInput,
  GenerateInput,
  WorkoutDayUpdate,
  WorkoutPlan,
  WorkoutResultInput,
  WorkoutTemplate,
} from "./types";

export const workoutApi = {
  current: () => api<WorkoutPlan | null>("/workouts/current", { auth: true }),
  history: () => api<WorkoutPlan[]>("/workouts/history", { auth: true }),
  predefined: () => api<Array<{ id: number; slug: string; name: string; days_per_week: number; level: string; split_type: string; description: string }>>("/workouts/predefined", { auth: true }),
  templates: () => api<WorkoutTemplate[]>("/templates", { auth: true }),
  applyTemplate: (templateId: number) =>
    api<{ plan: WorkoutPlan; source: string; template_id: number }>(
      "/templates/apply",
      { method: "POST", body: JSON.stringify({ template_id: templateId }), auth: true },
    ),
  generateFromTemplate: (templateId: number, age = 28, aiAdapt = true) =>
    api<WorkoutPlan>(
      "/workouts/generate-from-template",
      { method: "POST", body: JSON.stringify({ template_id: templateId, age, ai_adapt: aiAdapt }), auth: true },
    ),
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
