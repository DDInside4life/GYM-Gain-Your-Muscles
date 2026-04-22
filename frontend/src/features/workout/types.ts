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
  reps: string;
  weight_kg: number | null;
  rest_sec: number;
  notes: string;
  exercise: Exercise;
};

export type WorkoutDay = {
  id: number;
  day_index: number;
  title: string;
  focus: string;
  is_rest: boolean;
  exercises: WorkoutExercise[];
};

export type WorkoutPlan = {
  id: number;
  name: string;
  week_number: number;
  split_type: string;
  is_active: boolean;
  days: WorkoutDay[];
  params: Record<string, unknown>;
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
