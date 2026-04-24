export function sanitizeNonNegativeNumericInput(raw: string, allowDecimal = true): string | null {
  if (raw === "") return "";
  const pattern = allowDecimal ? /^\d*\.?\d*$/ : /^\d*$/;
  if (!pattern.test(raw)) return null;

  let next = raw;
  if (allowDecimal && next.startsWith(".")) next = `0${next}`;

  if (next.includes(".")) {
    const [intPart, decimalPart] = next.split(".");
    const normalizedInt = (intPart || "0").replace(/^0+(?=\d)/, "");
    return `${normalizedInt || "0"}.${decimalPart ?? ""}`;
  }
  return next.replace(/^0+(?=\d)/, "");
}

export function parseNonNegativeNumber(value: string): number | null {
  if (value === "") return null;
  const parsed = Number(value);
  if (Number.isNaN(parsed) || parsed < 0) return null;
  return parsed;
}

export function parsePositiveNumber(value: string): number | null {
  const parsed = parseNonNegativeNumber(value);
  if (parsed === null || parsed <= 0) return null;
  return parsed;
}
