# src/service.py
"""Habit tracker service and domain operations."""

from datetime import date as Date
from datetime import datetime, timezone
from pathlib import Path
import re
from uuid import uuid4

from src import store, streaks
from src.errors import (
    DuplicateLogError,
    FutureDateError,
    HabitNotFoundError,
    InvalidDateError,
    InvalidFrequencyError,
    InvalidNameError,
    InvalidValueError,
)
from src.models import Habit, HabitSummary, LogEntry

_DOW_TOKENS = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
_DOW_WEEKDAYS = {
    "Sun": 6,
    "Mon": 0,
    "Tue": 1,
    "Wed": 2,
    "Thu": 3,
    "Fri": 4,
    "Sat": 5,
}
_DOW_FREQUENCY_PATTERN = re.compile(
    r"\[(?:Sun|Mon|Tue|Wed|Thu|Fri|Sat)"
    r"(?:,(?:Sun|Mon|Tue|Wed|Thu|Fri|Sat))*\]"
)


class HabitTracker:
    """Manage habits and their completion logs."""

    def __init__(self, data_path: Path | None = None) -> None:
        """Load tracker state from the selected data file."""
        self.data_path = (
            data_path if data_path is not None else Path("./data/habits.json")
        )
        self._habits, self._logs = store.load(self.data_path)

    def add_habit(self, name: str, frequency: str) -> Habit:
        """Validate and add a habit, or return its existing duplicate."""
        if not self._is_valid_frequency(frequency):
            raise InvalidFrequencyError("Frequency must be daily, weekly, or a valid day list.")
        if not isinstance(name, str) or not name.strip() or len(name) > 100:
            raise InvalidNameError("Name must contain 1 to 100 characters.")

        for habit in self._habits:
            if habit.name == name and habit.frequency == frequency:
                return habit

        habit = Habit(
            id=str(uuid4()),
            name=name,
            frequency=frequency,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._habits.append(habit)
        return habit

    def log(self, habit_id: str, date: str, value: int = 1) -> LogEntry:
        """Validate and add a completion log."""
        if not any(habit.id == habit_id for habit in self._habits):
            raise HabitNotFoundError(f"No habit found with id {habit_id!r}.")

        try:
            parsed_date = Date.fromisoformat(date)
        except (TypeError, ValueError) as error:
            raise InvalidDateError("Date must use the YYYY-MM-DD format.") from error
        if parsed_date.isoformat() != date:
            raise InvalidDateError("Date must use the YYYY-MM-DD format.")

        if parsed_date > datetime.now(timezone.utc).date():
            raise FutureDateError("A completion date cannot be in the future.")

        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise InvalidValueError("Value must be a positive integer.")

        if any(
            entry.habit_id == habit_id and entry.date == date
            for entry in self._logs
        ):
            raise DuplicateLogError(
                f"Habit {habit_id!r} already has a log for {date}."
            )

        entry = LogEntry(habit_id=habit_id, date=date, value=value)
        self._logs.append(entry)
        return entry

    def current_streak(self, habit_id: str) -> int:
        """Return the current streak for a habit."""
        habit = self._find_habit(habit_id)
        dates = [
            entry.date for entry in self._logs if entry.habit_id == habit_id
        ]
        today = datetime.now(timezone.utc).date().isoformat()

        if habit.frequency == "daily":
            return streaks.daily_streak(dates, today)
        if habit.frequency == "weekly":
            return streaks.weekly_streak(dates, today)
        scheduled_days = frozenset(
            _DOW_WEEKDAYS[token]
            for token in habit.frequency[1:-1].split(",")
        )
        return streaks.days_of_week_streak(dates, today, scheduled_days)

    def list_habits(self) -> list[HabitSummary]:
        """Return habit summaries sorted by name."""
        summaries = [
            HabitSummary(
                name=habit.name,
                frequency=habit.frequency,
                current_streak=self.current_streak(habit.id),
                last_logged_date=self._last_logged_date(habit.id),
            )
            for habit in self._habits
        ]
        return sorted(summaries, key=lambda summary: summary.name)

    def list_logs(self, habit_id: str) -> list[LogEntry]:
        """Return a habit's logs sorted by date in descending order."""
        self._find_habit(habit_id)
        return sorted(
            (entry for entry in self._logs if entry.habit_id == habit_id),
            key=lambda entry: entry.date,
            reverse=True,
        )

    def save(self, path: Path | None = None) -> None:
        """Persist tracker state atomically."""
        store.save(path if path is not None else self.data_path, self._habits, self._logs)

    def delete_habit(self, habit_id: str) -> None:
        """Delete a habit and all of its completion logs."""
        self._find_habit(habit_id)
        self._habits = [
            habit for habit in self._habits if habit.id != habit_id
        ]
        self._logs = [
            entry for entry in self._logs if entry.habit_id != habit_id
        ]

    @staticmethod
    def _is_valid_frequency(frequency: str) -> bool:
        """Check daily, weekly, and strictly ordered day-list frequencies."""
        if not isinstance(frequency, str):
            return False
        if frequency in {"daily", "weekly"}:
            return True
        if not _DOW_FREQUENCY_PATTERN.fullmatch(frequency):
            return False
        tokens = frequency[1:-1].split(",")
        positions = [_DOW_TOKENS.index(token) for token in tokens]
        return positions == sorted(set(positions))

    def _find_habit(self, habit_id: str) -> Habit:
        """Find a habit by id or raise the domain error."""
        for habit in self._habits:
            if habit.id == habit_id:
                return habit
        raise HabitNotFoundError(f"No habit found with id {habit_id!r}.")

    def _last_logged_date(self, habit_id: str) -> str | None:
        """Return the latest logged date for a habit, if present."""
        dates = [
            entry.date for entry in self._logs if entry.habit_id == habit_id
        ]
        return max(dates) if dates else None