from __future__ import annotations

from app.core.metrics import ProductMetrics, RequestMetricTags, classify_request


def test_classify_request_for_core_workout_endpoints() -> None:
    assert classify_request(RequestMetricTags("POST", "/api/workouts/generate", 201)) == "generation"
    assert classify_request(RequestMetricTags("POST", "/api/workouts/12/finalize-test-week", 200)) == "finalize"
    assert classify_request(RequestMetricTags("POST", "/api/workouts/sets", 201)) == "set_log"


def test_metrics_snapshot_contains_success_rates_and_latency() -> None:
    metrics = ProductMetrics()
    metrics.record_generation(True)
    metrics.record_generation(False)
    metrics.record_finalize(True)
    metrics.record_set_log_latency(120.0)
    metrics.record_set_log_latency(80.0)
    snapshot = metrics.snapshot()
    assert snapshot["generation_success_rate"] == 0.5
    assert snapshot["finalize_success_rate"] == 1.0
    assert snapshot["set_log_latency_ms_avg"] == 100.0
