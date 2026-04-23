"use client";

import { useCallback, useEffect, useState } from "react";
import { aiApi } from "./api";
import type {
  AIExplanation,
  AIProgressionResponse,
  AIStatus,
  AIWorkoutResponse,
  GenerateInput,
} from "./types";

const RETRY_COUNT = 2;

async function withRetry<T>(fn: () => Promise<T>, retries = RETRY_COUNT): Promise<T> {
  let lastErr: unknown;
  for (let i = 0; i <= retries; i++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      if (i < retries) await new Promise((r) => setTimeout(r, 250 * (i + 1)));
    }
  }
  throw lastErr;
}

export function useAiStatus() {
  const [status, setStatus] = useState<AIStatus | null>(null);
  useEffect(() => {
    aiApi.status().then(setStatus).catch(() => setStatus({ enabled: false, provider: "", model: "" }));
  }, []);
  return status;
}

export function useAiWorkout() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<AIWorkoutResponse | null>(null);

  const generate = useCallback(async (payload: GenerateInput) => {
    setLoading(true);
    setError(null);
    try {
      const res = await withRetry(() => aiApi.generateWorkout(payload));
      setResponse(res);
      return res;
    } catch (err) {
      setError(err instanceof Error ? err.message : "AI generation failed");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const progress = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res: AIProgressionResponse = await withRetry(() => aiApi.progressWorkout());
      setResponse(res as unknown as AIWorkoutResponse);
      return res;
    } catch (err) {
      setError(err instanceof Error ? err.message : "AI progression failed");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, response, generate, progress, setResponse };
}

export function usePlanExplanation(planId: number | null) {
  const [explanation, setExplanation] = useState<AIExplanation | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!planId) {
      setExplanation(null);
      return;
    }
    setLoading(true);
    aiApi
      .planExplanation(planId)
      .then(setExplanation)
      .catch(() => setExplanation(null))
      .finally(() => setLoading(false));
  }, [planId]);

  return { explanation, loading };
}
