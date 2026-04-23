import type { WorkoutDay, WorkoutPlan } from "@/features/workout/types";

export type TrainingExperience = "beginner" | "intermediate" | "advanced";
export type TrainingGoal = "hypertrophy" | "strength" | "recomposition";

export type InitialStrength = {
  exercise_id: number;
  one_rm?: number;
  weight_kg?: number;
  reps?: number;
};

export type GenerateProgramInput = {
  training_experience: TrainingExperience;
  goal: TrainingGoal;
  training_days: number;
  weight_kg: number;
  height_cm?: number;
  initial_strength: InitialStrength[];
  load_mode?: "percent_1rm" | "absolute";
  start_kpsh?: number;
  start_intensity_pct?: number;
  growth_step?: number;
  drop_step?: number;
  wave_length?: number;
};

export type StrengthProfile = {
  exercise_id: number;
  actual_1rm: number | null;
  estimated_1rm: number;
};

export type GenerateProgramResponse = {
  plan: WorkoutPlan;
  split: string;
  mesocycle_weeks: number;
  strength_profile: StrengthProfile[];
};

export type TodayWorkout = {
  date: string;
  day: WorkoutDay | null;
  week_index: number;
  phase: string;
  mesocycle_number: number;
};

export type WeeklyWorkout = {
  week_index: number;
  days: WorkoutDay[];
};

export type WorkoutSetLogInput = {
  workout_exercise_id: number;
  set_index: number;
  completed_reps: number;
  completed_weight_kg: number;
  rir: number;
};

export type WorkoutLogInput = {
  sets: WorkoutSetLogInput[];
};

export type WorkoutLogResponse = {
  updated: number;
  next_weight_adjustment_pct: number;
  weekly_volume: number;
};

export type ProgressPoint = {
  at: string;
  exercise_id: number;
  estimated_1rm: number;
  volume: number;
};

export type ProgressResponse = {
  weekly_volume: Record<string, number>;
  strength: ProgressPoint[];
  volume_delta_pct: number;
};
