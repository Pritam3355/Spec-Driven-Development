# src/streaks.py
"""Pure streak calculations for habit completion dates."""

from datetime import date, timedelta
from collections.abc import Iterable


def daily_streak(dates: Iterable[str], today: str) -> int:
    """Count consecutive logged ISO dates ending on today."""
    completed_dates = set(dates)
    current = date.fromisoformat(today)
    if current.isoformat() not in completed_dates:
        return 0

    streak = 0
    while current.isoformat() in completed_dates:
        streak += 1
        current -= timedelta(days=1)

    return streak


def weekly_streak(dates: Iterable[str], today: str) -> int:
    """Count consecutive logged ISO weeks ending in this week."""
    completed_weeks = {
        date.fromisoformat(log_date).isocalendar()[:2] for log_date in dates
    }
    current = date.fromisoformat(today)
    current_week = current.isocalendar()[:2]
    if current_week not in completed_weeks:
        return 0

    streak = 0
    while current_week in completed_weeks:
        streak += 1
        current -= timedelta(days=7)
        current_week = current.isocalendar()[:2]

    return streak