import { api } from "@/lib/api";
import type {
  FeedbackInput,
  FinalizeTestWeekRead,
  GenerateInput,
  QuestionnaireInput,
  SetLogInput,
  SetLogRead,
  WeekProgress,
  WorkoutDayUpdate,
  WorkoutExercise,
  WorkoutPlan,
  WorkoutResultInput,
  WorkoutTemplate,
} from "./types";

export const workoutApi = {
  current: () => api<WorkoutPlan | null>("/workouts/current", { auth: true }),
  history: () => api<WorkoutPlan[]>("/workouts/history", { auth: true }),
  predefined: () => api<Array<{ id: number; slug: string; name: string; days_per_week: number; level: string; split_type: string; description: string }>>("/workouts/predefined", { auth: true }),
  templates: () => api<WorkoutTemplate[]>("/templates", { auth: true }),
  generate: (payload: GenerateInput) =>
    api<WorkoutPlan>("/workouts/generate", { method: "POST", body: JSON.stringify(payload), auth: true }),
  generateFromQuestionnaire: (payload: QuestionnaireInput) =>
    api<WorkoutPlan>("/workouts/generate-from-questionnaire", { method: "POST", body: JSON.stringify(payload), auth: true }),
  setExerciseWeight: (workoutExerciseId: number, weightKg: number | null) =>
    api<WorkoutExercise>(`/workouts/exercises/${workoutExerciseId}/weight`, {
      method: "PATCH",
      body: JSON.stringify({ weight_kg: weightKg }),
      auth: true,
    }),
  progress: () => api<WorkoutPlan>("/workouts/progress", { method: "POST", auth: true }),
  regenerate: () => api<WorkoutPlan>("/workouts/regenerate", { method: "POST", auth: true }),
  get: (planId: number) => api<WorkoutPlan>(`/workouts/${planId}`, { auth: true }),
  select: (planId: number) => api<WorkoutPlan>(`/workouts/${planId}/select`, { method: "POST", auth: true }),
  updateDay: (planId: number, dayId: number, payload: WorkoutDayUpdate) =>
    api<WorkoutPlan>(`/workouts/${planId}/days/${dayId}`, { method: "PUT", body: JSON.stringify(payload), auth: true }),
  submitResult: (payload: WorkoutResultInput) =>
    api("/workouts/results", { method: "POST", body: JSON.stringify(payload), auth: true }),
  feedback: (payload: FeedbackInput) =>
    api<unknown>("/workouts/feedback", { method: "POST", body: JSON.stringify(payload), auth: true }),
  logSet: (payload: SetLogInput) =>
    api<SetLogRead>("/workouts/sets", { method: "POST", body: JSON.stringify(payload), auth: true }),
  deleteSetLog: (logId: number) =>
    api<void>(`/workouts/sets/${logId}`, { method: "DELETE", auth: true }),
  planProgress: (planId: number) =>
    api<WeekProgress[]>(`/workouts/${planId}/progress`, { auth: true }),
  finalizeTestWeek: (planId: number) =>
    api<FinalizeTestWeekRead>(`/workouts/${planId}/finalize-test-week`, { method: "POST", auth: true }),
};
