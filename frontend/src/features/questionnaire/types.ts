import type {
  Equipment,
  Experience,
  Goal,
  Periodization,
  SessionDurationMin,
  TrainingStructure,
  WorkoutPlan,
} from "@/features/workout/types";

export type Sex = "male" | "female";
export type TrainingLocation = "gym" | "home";
export type WeekDay = "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun";

export type QuestionnaireInput = {
  sex: Sex;
  age: number;
  height_cm: number;
  weight_kg: number;
  experience: Experience;
  goal: Goal;
  location: TrainingLocation;
  equipment: Equipment[];
  injuries: string[];
  days_per_week: number;
  available_days: WeekDay[];
  notes?: string;
  session_duration_min?: SessionDurationMin | null;
  training_structure?: TrainingStructure | null;
  periodization?: Periodization | null;
  cycle_length_weeks?: number | null;
  priority_exercise_ids?: number[];
};

export type Questionnaire = QuestionnaireInput & {
  id: number;
  user_id: number;
  config: Record<string, unknown>;
  plan_id: number | null;
  created_at: string;
  updated_at: string;
  priority_exercise_ids: number[];
  session_duration_min: SessionDurationMin | null;
  training_structure: TrainingStructure | null;
  periodization: Periodization | null;
  cycle_length_weeks: number | null;
};

export type QuestionnaireGenerateResponse = WorkoutPlan;
