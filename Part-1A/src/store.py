# src/store.py
"""JSON persistence for habits and completion logs."""

import json
import os
from dataclasses import asdict
from pathlib import Path

from src.errors import CorruptDataError
from src.models import Habit, LogEntry


def _read_habit(record: object) -> Habit:
    """Reconstruct a habit from a JSON record."""
    if not isinstance(record, dict):
        raise CorruptDataError("Habit record must be an object.")

    habit_id = record.get("id")
    name = record.get("name")
    frequency = record.get("frequency")
    created_at = record.get("created_at")
    if not all(
        isinstance(value, str)
        for value in (habit_id, name, frequency, created_at)
    ):
        raise CorruptDataError("Habit record has invalid fields.")

    return Habit(
        id=habit_id,
        name=name,
        frequency=frequency,
        created_at=created_at,
    )


def _read_log(record: object) -> LogEntry:
    """Reconstruct a log entry from a JSON record."""
    if not isinstance(record, dict):
        raise CorruptDataError("Log record must be an object.")

    habit_id = record.get("habit_id")
    log_date = record.get("date")
    value = record.get("value")
    if (
        not isinstance(habit_id, str)
        or not isinstance(log_date, str)
        or not isinstance(value, int)
        or isinstance(value, bool)
    ):
        raise CorruptDataError("Log record has invalid fields.")

    return LogEntry(habit_id=habit_id, date=log_date, value=value)


def save(path: Path, habits: list[Habit], logs: list[LogEntry]) -> None:
    """Save tracker data as JSON using an atomic replacement."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    data = {
        "version": 1,
        "habits": [asdict(habit) for habit in habits],
        "logs": [asdict(log_entry) for log_entry in logs],
    }

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")

    os.replace(temporary_path, path)


def load(path: Path) -> tuple[list[Habit], list[LogEntry]]:
    """Load tracker data, returning empty lists when the file is missing."""
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return [], []
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise CorruptDataError("Tracker data is not valid JSON.") from error

    if not isinstance(data, dict):
        raise CorruptDataError("Tracker data must be a JSON object.")

    version = data.get("version")
    habits_data = data.get("habits")
    logs_data = data.get("logs")
    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version != 1
        or not isinstance(habits_data, list)
        or not isinstance(logs_data, list)
    ):
        raise CorruptDataError("Tracker data has an invalid structure.")

    return (
        [_read_habit(record) for record in habits_data],
        [_read_log(record) for record in logs_data],
    )