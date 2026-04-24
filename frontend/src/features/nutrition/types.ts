export type NutritionDailySummary = {
  date: string;
  protein: number;
  fat: number;
  carbs: number;
  calories: number;
};

export type FoodEntry = {
  id: number;
  meal_id: number;
  name: string;
  protein_per_100g: number;
  fat_per_100g: number;
  carbs_per_100g: number;
  grams: number;
  calculated_protein: number;
  calculated_fat: number;
  calculated_carbs: number;
  calories: number;
  created_at: string;
  updated_at: string;
};

export type Meal = {
  id: number;
  user_id: number;
  date: string;
  name: string;
  food_entries: FoodEntry[];
  total_protein: number;
  total_fat: number;
  total_carbs: number;
  total_calories: number;
  created_at: string;
  updated_at: string;
};

export type CreateMealInput = {
  date: string;
  name: string;
};

export type CreateFoodEntryInput = {
  meal_id: number;
  name: string;
  protein_per_100g: number;
  fat_per_100g: number;
  carbs_per_100g: number;
  grams: number;
};

export type FoodDraft = {
  name: string;
  protein_per_100g: string;
  fat_per_100g: string;
  carbs_per_100g: string;
  grams: string;
};

export type NutritionCalculatorGoal = "cut" | "maintain" | "bulk";
export type NutritionCalculatorActivity = "sedentary" | "light" | "moderate" | "active" | "very_active";
export type NutritionCalculatorSex = "male" | "female";

export type NutritionTargetsInput = {
  sex: NutritionCalculatorSex;
  age: number;
  weight_kg: number;
  height_cm: number;
  activity: NutritionCalculatorActivity;
  goal: NutritionCalculatorGoal;
};

export type MacroTarget = {
  grams: number;
  kcal: number;
};

export type NutritionTargets = {
  bmr: number;
  tdee: number;
  target_calories: number;
  goal: NutritionCalculatorGoal;
  protein: MacroTarget;
  fat: MacroTarget;
  carbs: MacroTarget;
};
