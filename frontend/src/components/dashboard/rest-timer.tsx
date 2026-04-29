"use client";

import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";

type Props = {
  initialSec: number;
};

export function RestTimer({ initialSec }: Props) {
  const [left, setLeft] = useState(initialSec);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => {
      setLeft((prev) => {
        if (prev <= 1) {
          setRunning(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [running]);

  const view = useMemo(() => {
    const mm = Math.floor(left / 60);
    const ss = left % 60;
    return `${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`;
  }, [left]);

  return (
    <div className="flex items-center gap-2">
      <div className="text-sm tabular-nums">{view}</div>
      <Button size="sm" variant="outline" onClick={() => setRunning((v) => !v)}>
        {running ? "Пауза" : "Старт"}
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => {
          setRunning(false);
          setLeft(initialSec);
        }}
      >
        Сброс
      </Button>
    </div>
  );
}
