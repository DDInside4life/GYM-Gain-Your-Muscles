from __future__ import annotations

from app.services.workout.rules import decide_auto_deload


def test_auto_deload_triggers_when_two_signals_present() -> None:
    decision = decide_auto_deload(
        scheduled_deload=False,
        e1rm_drop_ratio=0.05,
        high_effort_ratio=0.55,
        missed_session_ratio=0.1,
    )
    assert decision.should_deload is True
    assert "drop_e1rm_trend" in decision.reasons
    assert "high_effort_trend" in decision.reasons


def test_auto_deload_keeps_scheduled_rule_backward_compatible() -> None:
    decision = decide_auto_deload(
        scheduled_deload=True,
        e1rm_drop_ratio=None,
        high_effort_ratio=None,
        missed_session_ratio=None,
    )
    assert decision.should_deload is True
    assert "scheduled_deload" in decision.reasons
