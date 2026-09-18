"""Pure domain rules for classifying and prioritizing social interactions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import re


INTENTS = ("question", "complaint", "lead", "praise", "spam", "other")
STATUSES = ("open", "in_progress", "resolved", "ignored")


@dataclass(frozen=True)
class TriageResult:
    intent: str
    priority: str
    score: int
    sla_minutes: int
    reasons: tuple[str, ...]


def classify(text: str) -> str:
    value = text.lower().strip()
    if not value:
        return "other"
    if re.search(r"\b(buy|price|pricing|quote|demo|trial|interested|cost)\b", value):
        return "lead"
    if re.search(r"\b(refund|broken|angry|complaint|terrible|not working|issue|problem)\b", value):
        return "complaint"
    if re.search(r"\b(thanks|thank you|love|great|awesome|excellent)\b", value):
        return "praise"
    if re.search(r"\b(free money|click here|crypto|winner|giveaway|visit my)\b", value):
        return "spam"
    if "?" in value or re.search(r"\b(how|what|where|when|can you|does it)\b", value):
        return "question"
    return "other"


def triage(text: str, reach: int = 0, age_minutes: int = 0) -> TriageResult:
    intent = classify(text)
    score = 20
    reasons: list[str] = []
    if intent == "complaint":
        score += 45
        reasons.append("customer complaint")
    elif intent == "lead":
        score += 40
        reasons.append("commercial intent")
    elif intent == "question":
        score += 20
        reasons.append("customer question")
    elif intent == "spam":
        score -= 30
        reasons.append("spam indicators")
    if reach >= 1000:
        score += 20
        reasons.append("high reach")
    elif reach >= 100:
        score += 10
        reasons.append("meaningful reach")
    if age_minutes >= 60:
        score += 10
        reasons.append("aging interaction")
    score = max(0, min(100, score))
    priority = "urgent" if score >= 80 else "high" if score >= 60 else "normal" if score >= 30 else "low"
    sla = {"urgent": 30, "high": 120, "normal": 480, "low": 1440}[priority]
    return TriageResult(intent, priority, score, sla, tuple(reasons))


def deadline(minutes: int, now: datetime | None = None) -> datetime:
    current = now or datetime.now(UTC)
    return current + timedelta(minutes=minutes)


def validate_transition(current: str, target: str) -> None:
    allowed = {
        "open": {"in_progress", "resolved", "ignored"},
        "in_progress": {"open", "resolved", "ignored"},
        "resolved": set(),
        "ignored": {"open"},
    }
    if current not in STATUSES or target not in STATUSES or target not in allowed[current]:
        raise ValueError(f"invalid status transition: {current} -> {target}")
