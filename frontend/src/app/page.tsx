import { Hero } from "@/components/landing/hero";
import { WeekPlan } from "@/components/landing/week-plan";
import { ExerciseGrid } from "@/components/landing/exercise-grid";
import { Stats } from "@/components/landing/stats";

export default function HomePage() {
  return (
    <div className="space-y-2 animate-fade-up pb-10">
      <Hero />
      <WeekPlan />
      <ExerciseGrid />
      <Stats />
    </div>
  );
}
