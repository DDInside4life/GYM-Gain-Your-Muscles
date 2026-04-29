"use client";

type Point = { x: number; y: number };

type Props = {
  values: number[];
  width?: number;
  height?: number;
};

export function E1rmChart({ values, width = 320, height = 96 }: Props) {
  if (values.length === 0) {
    return <div className="text-xs text-muted">Нет данных e1RM</div>;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const stepX = values.length > 1 ? width / (values.length - 1) : width;
  const points: Point[] = values.map((v, i) => ({
    x: i * stepX,
    y: height - ((v - min) / range) * height,
  }));
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-24">
      <path d={path} fill="none" stroke="currentColor" strokeWidth={2} />
      {points.map((p, idx) => (
        <circle key={idx} cx={p.x} cy={p.y} r={2.5} />
      ))}
    </svg>
  );
}
