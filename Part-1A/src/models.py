# src/models.py
"""Immutable data models for the habit tracker."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Habit:
    """Represent a habit."""

    id: str
    name: str
    frequency: str
    created_at: str


@dataclass(frozen=True)
class LogEntry:
    """Represent a habit completion."""

    habit_id: str
    date: str
    value: int


@dataclass(frozen=True)
class HabitSummary:
    """Represent a habit and its current summary."""

    name: str
    frequency: str
    current_streak: int
    last_logged_date: str | None