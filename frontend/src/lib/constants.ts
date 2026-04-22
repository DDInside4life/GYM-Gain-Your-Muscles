export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost/api";

export const WEEK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"] as const;

export const FOCUS_LABEL: Record<string, string> = {
  chest: "Грудь",
  back: "Спина",
  legs: "Ноги",
  glutes: "Ягодицы",
  shoulders: "Плечи",
  biceps: "Бицепс",
  triceps: "Трицепс",
  core: "Пресс",
  calves: "Икры",
  forearms: "Предплечья",
  full_body: "Всё тело",
  cardio: "Кардио",
  recovery: "Отдых",
};
