import type {
  Equipment,
  Experience,
  Goal,
  Periodization,
  SessionDurationMin,
  TrainingStructure,
} from "./types";
import type { Sex, TrainingLocation, WeekDay } from "@/features/questionnaire/types";

export const SEX_OPTIONS: ReadonlyArray<{ value: Sex; label: string }> = [
  { value: "male", label: "Мужской" },
  { value: "female", label: "Женский" },
];

export const EXPERIENCE_OPTIONS: ReadonlyArray<{
  value: Experience;
  label: string;
  description: string;
}> = [
  {
    value: "beginner",
    label: "Новичок",
    description: "Меньший объём, упор на технику, более длительное восстановление.",
  },
  {
    value: "intermediate",
    label: "Средний",
    description: "Сбалансированный объём и прогрессия, базовые сплиты.",
  },
  {
    value: "advanced",
    label: "Продвинутый",
    description: "Высокий объём, агрессивная периодизация, точечная работа.",
  },
];

export const GOAL_OPTIONS: ReadonlyArray<{
  value: Goal;
  label: string;
  description: string;
  icon: string;
}> = [
  {
    value: "strength",
    label: "Сила",
    description: "85–95% 1ПМ, 1–5 повторений, длинный отдых, акцент на ЦНС и топ-сеты.",
    icon: "🏋️",
  },
  {
    value: "muscle_gain",
    label: "Гипертрофия / Масса",
    description: "60–80% 1ПМ, 6–12 повторов, умеренный отдых, приоритет объёма.",
    icon: "💪",
  },
  {
    value: "fat_loss",
    label: "Рельеф / Выносливость",
    description: "Высокие повторения, короткий отдых, плотный темп и метаболическая работа.",
    icon: "🔥",
  },
  {
    value: "general",
    label: "Поддержание",
    description: "Сбалансированная нагрузка, умеренный объём, стабильные веса.",
    icon: "🎯",
  },
];

export const LOCATION_OPTIONS: ReadonlyArray<{ value: TrainingLocation; label: string }> = [
  { value: "gym", label: "Зал" },
  { value: "home", label: "Дом" },
];

export const EQUIPMENT_OPTIONS: ReadonlyArray<{ value: Equipment; label: string }> = [
  { value: "bodyweight", label: "Свой вес" },
  { value: "barbell", label: "Штанга" },
  { value: "dumbbell", label: "Гантели" },
  { value: "machine", label: "Тренажёр" },
  { value: "cable", label: "Блок" },
  { value: "kettlebell", label: "Гиря" },
  { value: "bands", label: "Резины" },
];

export const RESTRICTION_OPTIONS: ReadonlyArray<{ value: string; label: string }> = [
  { value: "back", label: "Спина" },
  { value: "knees", label: "Колени" },
  { value: "shoulders", label: "Плечи" },
  { value: "elbows", label: "Локти" },
  { value: "wrists", label: "Запястья" },
  { value: "varicose_veins", label: "Варикоз" },
  { value: "blood_pressure", label: "Давление" },
];

export const WEEK_DAY_OPTIONS: ReadonlyArray<{ value: WeekDay; label: string }> = [
  { value: "mon", label: "Пн" },
  { value: "tue", label: "Вт" },
  { value: "wed", label: "Ср" },
  { value: "thu", label: "Чт" },
  { value: "fri", label: "Пт" },
  { value: "sat", label: "Сб" },
  { value: "sun", label: "Вс" },
];

export const SESSION_DURATION_OPTIONS: ReadonlyArray<{
  value: SessionDurationMin;
  label: string;
  subtitle: string;
  description: string;
}> = [
  {
    value: 45,
    label: "45 мин",
    subtitle: "Экспресс",
    description: "Только базовые движения, без аксессуаров.",
  },
  {
    value: 60,
    label: "60 мин",
    subtitle: "Стандарт",
    description: "Сбалансированная сессия: 1–2 базовых + аксессуары.",
  },
  {
    value: 90,
    label: "90 мин",
    subtitle: "Полный",
    description: "Расширенный объём с дополнительными изоляциями.",
  },
  {
    value: 120,
    label: "120 мин",
    subtitle: "Расширенный",
    description: "Большой объём с акцессуарной работой и пампом.",
  },
  {
    value: 150,
    label: "150 мин",
    subtitle: "Макс",
    description: "Только для продвинутых при достаточном восстановлении.",
  },
];

export const TRAINING_STRUCTURE_OPTIONS: ReadonlyArray<{
  value: TrainingStructure;
  label: string;
  description: string;
}> = [
  {
    value: "full_body",
    label: "Фулбади",
    description: "Все мышцы за тренировку. Подходит для новичков и при 2–3 днях.",
  },
  {
    value: "half_split",
    label: "Полусплит",
    description: "Чередование верх / низ или большие группы — компромисс между объёмом и частотой.",
  },
  {
    value: "upper_lower",
    label: "Верх/Низ",
    description: "Классическое разделение для 4 дней: 2 верхних + 2 нижних дня.",
  },
  {
    value: "split",
    label: "Сплит",
    description: "Тяни/толкай/ноги или поагентному. Высокий объём, для 4–6 дней.",
  },
];

export const PERIODIZATION_OPTIONS: ReadonlyArray<{
  value: Periodization;
  label: string;
  description: string;
}> = [
  {
    value: "dup",
    label: "Волновая (DUP)",
    description: "Чередование тяжёлой / средней / лёгкой нагрузки внутри цикла. Хороший баланс.",
  },
  {
    value: "block",
    label: "Блоковая",
    description: "Накопление → интенсификация → пик → разгрузка. Управляемая прогрессия.",
  },
  {
    value: "linear",
    label: "Линейная (LP)",
    description: "Постепенный рост интенсивности и снижение объёма от недели к неделе.",
  },
  {
    value: "emergent",
    label: "Эмерджентная",
    description: "Авто-регуляция по тренду e1RM, RPE/RIR и плановым разгрузкам.",
  },
];

export const CYCLE_LENGTH_OPTIONS: ReadonlyArray<{
  value: number;
  label: string;
  subtitle: string;
  description: string;
}> = [
  {
    value: 4,
    label: "Короткий",
    subtitle: "Экспресс · ~4 недели",
    description: "Быстрая прогрессия, ранняя разгрузка, агрессивная адаптация.",
  },
  {
    value: 6,
    label: "Средний",
    subtitle: "Стандарт · 6–8 недель",
    description: "Лучший баланс объёма и интенсивности. Подходит большинству.",
  },
  {
    value: 10,
    label: "Длинный",
    subtitle: "Марафон · 9+ недель",
    description: "Длительное накопление, контроль и аккуратное планирование восстановления.",
  },
];

export const DAYS_PER_WEEK_OPTIONS: ReadonlyArray<{
  value: number;
  label: string;
  description: string;
}> = [
  { value: 2, label: "2", description: "Минимально для поддержания формы." },
  { value: 3, label: "3", description: "Оптимально для новичков и перезапуска." },
  { value: 4, label: "4", description: "Базовый сплит верх/низ или полусплит." },
  { value: 5, label: "5", description: "Высокий объём, продвинутый уровень." },
  { value: 6, label: "6", description: "Только для продвинутых, тщательное планирование." },
];
