import { api } from "@/lib/api";
import type { WorkoutPlan } from "@/features/workout/types";
import type { Questionnaire, QuestionnaireInput } from "./types";

export const questionnaireApi = {
  create: (payload: QuestionnaireInput) =>
    api<Questionnaire>("/workouts/questionnaires", {
      method: "POST",
      body: JSON.stringify(payload),
      auth: true,
    }),
  latest: () =>
    api<Questionnaire | null>("/workouts/questionnaires/latest", { auth: true }),
  list: () =>
    api<Questionnaire[]>("/workouts/questionnaires", { auth: true }),
  generate: (questionnaireId: number) =>
    api<WorkoutPlan>(`/workouts/questionnaires/${questionnaireId}/generate`, {
      method: "POST",
      auth: true,
    }),
  generateInline: (payload: QuestionnaireInput) =>
    api<WorkoutPlan>("/workouts/generate-from-questionnaire", {
      method: "POST",
      body: JSON.stringify(payload),
      auth: true,
    }),
  regenerate: () =>
    api<WorkoutPlan>("/workouts/regenerate", { method: "POST", auth: true }),
};
