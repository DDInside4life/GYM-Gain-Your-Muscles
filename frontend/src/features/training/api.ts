import { api } from "@/lib/api";
import type {
  GenerateProgramInput,
  GenerateProgramResponse,
  ProgressResponse,
  TodayWorkout,
  WeeklyWorkout,
  WorkoutLogInput,
  WorkoutLogResponse,
} from "./types";

export const trainingApi = {
  generateProgram: (payload: GenerateProgramInput) =>
    api<GenerateProgramResponse>("/generate-program", {
      method: "POST",
      body: JSON.stringify(payload),
      auth: true,
    }),
  todayWorkout: () => api<TodayWorkout>("/workout/today", { auth: true }),
  weeklyWorkout: () => api<WeeklyWorkout>("/workout/weekly", { auth: true }),
  logWorkout: (payload: WorkoutLogInput) =>
    api<WorkoutLogResponse>("/workout/log", {
      method: "POST",
      body: JSON.stringify(payload),
      auth: true,
    }),
  progress: () => api<ProgressResponse>("/progress", { auth: true }),
};
