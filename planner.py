from datetime import date
import math


def priority_score(topic, today=None):
    today = today or date.today()
    exam = date.fromisoformat(topic["exam_date"])
    days_left = max((exam - today).days, 0)

    urgency = 100 if days_left == 0 else min(100, 100 / (1 + days_left) * 10)
    difficulty = topic["difficulty"] / 5 * 100
    weakness = 100 - topic["confidence"]
    importance = topic["importance"] / 5 * 100
    remaining = max(topic["estimated_minutes"] - topic["completed_minutes"], 0)
    remaining_factor = min(100, remaining / max(topic["estimated_minutes"], 1) * 100)

    score = (
        urgency * 0.30
        + difficulty * 0.20
        + weakness * 0.25
        + importance * 0.15
        + remaining_factor * 0.10
    )
    return round(score, 1)


def add_scores(topics, today=None):
    result = []
    for t in topics:
        d = dict(t)
        d["priority"] = priority_score(d, today)
        d["remaining_minutes"] = max(d["estimated_minutes"] - d["completed_minutes"], 0)
        result.append(d)
    return result


def build_schedule(topics, daily_minutes, study_date=None):
    """Greedy adaptive scheduler: prioritizes high score topics and caps a session at 90 min."""
    study_date = study_date or date.today()
    candidates = [t for t in add_scores(topics, study_date) if t["status"] != "Completed" and t["remaining_minutes"] > 0]
    candidates.sort(key=lambda x: x["priority"], reverse=True)

    schedule = []
    remaining_day = daily_minutes
    for t in candidates:
        if remaining_day <= 0:
            break
        allocation = min(90, t["remaining_minutes"], remaining_day)
        if allocation >= 15:
            schedule.append({
                "topic_id": t["id"],
                "subject": t["subject_name"],
                "topic": t["name"],
                "minutes": int(allocation),
                "priority": t["priority"],
                "reason": explain_priority(t, study_date),
            })
            remaining_day -= allocation
    return schedule


def explain_priority(topic, today=None):
    today = today or date.today()
    days_left = max((date.fromisoformat(topic["exam_date"]) - today).days, 0)
    reasons = []
    if days_left <= 7:
        reasons.append("exam soon")
    if topic["confidence"] <= 50:
        reasons.append("low confidence")
    if topic["difficulty"] >= 4:
        reasons.append("high difficulty")
    if topic["importance"] >= 4:
        reasons.append("high importance")
    if not reasons:
        reasons.append("balanced priority")
    return ", ".join(reasons)
