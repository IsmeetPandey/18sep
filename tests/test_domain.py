from datetime import datetime, timezone

import pytest

from app.domain import classify, deadline, triage, validate_transition


def test_classifies_commercial_intent_before_generic_question() -> None:
    assert classify("What is the price? I want to buy") == "lead"


def test_complaint_gets_high_priority() -> None:
    result = triage("The product is broken and I need a refund", reach=1500)
    assert result.intent == "complaint"
    assert result.priority == "urgent"
    assert result.score == 85
    assert result.sla_minutes == 30


def test_spam_is_low_priority() -> None:
    result = triage("winner click here for free money")
    assert result.intent == "spam"
    assert result.priority == "low"
    assert result.score == 0


def test_deadline_is_deterministic() -> None:
    current = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert deadline(30, current).isoformat() == "2026-01-01T00:30:00+00:00"


def test_terminal_state_cannot_be_reopened() -> None:
    with pytest.raises(ValueError, match="invalid status transition"):
        validate_transition("resolved", "open")


def test_ignored_can_be_reopened() -> None:
    validate_transition("ignored", "open")
