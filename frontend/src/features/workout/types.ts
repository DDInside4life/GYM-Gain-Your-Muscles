export type MuscleGroup =
  | "chest" | "back" | "legs" | "glutes" | "shoulders" | "biceps" | "triceps"
  | "core" | "calves" | "forearms" | "full_body" | "cardio";

export type Equipment =
  | "bodyweight" | "barbell" | "dumbbell" | "machine" | "cable" | "kettlebell" | "bands";

export type Experience = "beginner" | "intermediate" | "advanced";
export type Goal = "muscle_gain" | "fat_loss" | "strength" | "endurance" | "general";

export type Exercise = {
  id: number;
  slug: string;
  name_ru: string;
  name_en?: string | null;
  name: string;
  description: string;
  primary_muscle: MuscleGroup;
  secondary_muscles: string[];
  equipment: Equipment;
  category: "compound" | "isolation" | "cardio" | "mobility";
  difficulty: number;
  contraindications: string[];
  image_url: string | null;
  is_active: boolean;
};

export type WorkoutExercise = {
  id: number;
  position: number;
  sets: number;
  reps_min: number;
  reps_max: number;
  reps: string;
  weight_kg: number | null;
  rest_sec: number;
  notes: string;
  target_percent_1rm?: number | null;
  is_test_set?: boolean;
  test_instruction?: string;
  target_rir?: number | null;
  rpe_text?: string;
  exercise: Exercise;
};

export type WorkoutDay = {
  id: number;
  day_index: number;
  title: string;
  focus: string;
  is_rest: boolean;
  week_index: number;
  phase: "test" | "work";
  exercises: WorkoutExercise[];
};

export type WorkoutPlan = {
  id: number;
  name: string;
  week_number: number;
  month_index: number;
  cycle_week: number;
  phase: "test" | "work";
  split_type: string;
  is_active: boolean;
  days: WorkoutDay[];
  params: Record<string, unknown>;
};

export type WorkoutDayUpdate = {
  exercises: Array<{
    id?: number;
    exercise_id: number;
    sets: number;
    reps_min: number;
    reps_max: number;
    weight_kg: number | null;
    rest_sec: number;
    notes: string;
    target_percent_1rm?: number | null;
    is_test_set?: boolean;
    test_instruction?: string;
    target_rir?: number | null;
    rpe_text?: string;
  }>;
};

export type WorkoutResultInput = {
  workout_exercise_id: number;
  reps_completed: number;
  weight_kg: number;
};

export type GenerateInput = {
  weight_kg: number;
  height_cm: number;
  age: number;
  experience: Experience;
  goal: Goal;
  equipment: Equipment[];
  injuries: string[];
  days_per_week: number;
};

export type Difficulty = "very_easy" | "easy" | "ok" | "hard" | "very_hard";

export type FeedbackInput = {
  day_id: number;
  completed: boolean;
  difficulty: Difficulty;
  discomfort: string[];
  note: string;
};

export type WorkoutTemplateExercise = {
  id: number;
  position: number;
  sets: number;
  reps_min: number;
  reps_max: number;
  rest_sec: number;
  target_percent_1rm: number | null;
  notes: string;
  exercise_id: number;
  exercise_name: string;
  exercise_slug: string;
  muscle: string;
};

export type WorkoutTemplateDay = {
  id: number;
  day_index: number;
  title: string;
  focus: string;
  is_rest: boolean;
  exercises: WorkoutTemplateExercise[];
};

export type WorkoutTemplate = {
  id: number;
  slug: string;
  name: string;
  level: string;
  split_type: string;
  days_per_week: number;
  description: string;
  is_active: boolean;
  days: WorkoutTemplateDay[];
};
