from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True, slots=True)
class RequestMetricTags:
    method: str
    path: str
    status_code: int


class ProductMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._generation_total = 0
        self._generation_success = 0
        self._finalize_total = 0
        self._finalize_success = 0
        self._set_log_count = 0
        self._set_log_latency_sum_ms = 0.0

    def record_generation(self, success: bool) -> None:
        with self._lock:
            self._generation_total += 1
            self._generation_success += int(success)

    def record_finalize(self, success: bool) -> None:
        with self._lock:
            self._finalize_total += 1
            self._finalize_success += int(success)

    def record_set_log_latency(self, duration_ms: float) -> None:
        with self._lock:
            self._set_log_count += 1
            self._set_log_latency_sum_ms += max(0.0, duration_ms)

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            generation_rate = (
                self._generation_success / self._generation_total
                if self._generation_total
                else 0.0
            )
            finalize_rate = (
                self._finalize_success / self._finalize_total
                if self._finalize_total
                else 0.0
            )
            set_log_avg_latency = (
                self._set_log_latency_sum_ms / self._set_log_count
                if self._set_log_count
                else 0.0
            )
            return {
                "generation_success_rate": round(generation_rate, 4),
                "finalize_success_rate": round(finalize_rate, 4),
                "set_log_latency_ms_avg": round(set_log_avg_latency, 2),
            }


def classify_request(tags: RequestMetricTags) -> str | None:
    method = tags.method.upper()
    path = tags.path
    if method == "POST" and (
        path.endswith("/workouts/generate") or path.endswith("/workouts/generate-from-questionnaire")
    ):
        return "generation"
    if method == "POST" and path.endswith("/finalize-test-week"):
        return "finalize"
    if method == "POST" and path.endswith("/workouts/sets"):
        return "set_log"
    return None
