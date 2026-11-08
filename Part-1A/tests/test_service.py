"""Tests derived from spec.md ACs. 11 tests targeting ~50% coverage (per constitution 2)."""
from datetime import datetime, timedelta, timezone

import pytest

from src.errors import (
    DuplicateLogError, FutureDateError, HabitNotFoundError, InvalidFrequencyError,
    InvalidNameError, InvalidValueError,
)
from src.service import HabitTracker

def _utc_date(offset_days: int) -> str:
    """ISO date offset from UTC today (spec clarify Q2/A2: today = UTC day)."""
    return (datetime.now(tz=timezone.utc).date()
            + timedelta(days=offset_days)).isoformat()

@pytest.fixture
def tracker(tmp_path):
    return HabitTracker(data_path=tmp_path / "habits.json")

def test_ac_1_1_uuidv4(tracker):
    h = tracker.add_habit("meditate", "daily")
    assert isinstance(h.id, str) and len(h.id) == 36
    assert h.id[14] == "4"

def test_ac_1_2_bad_frequency(tracker):
    with pytest.raises(InvalidFrequencyError):
        tracker.add_habit("x", "hourly")

def test_ac_1_3_bad_name(tracker):
    with pytest.raises(InvalidNameError):
        tracker.add_habit("   ", "daily")

def test_ac_1_4_idempotent_add(tracker):
    a = tracker.add_habit("run", "daily")
    b = tracker.add_habit("run", "daily")
    assert a.id == b.id

def test_ac_2_3_future_date(tracker):
    h = tracker.add_habit("run", "daily")
    with pytest.raises(FutureDateError):
        tracker.log(h.id, _utc_date(1))

def test_ac_2_4_duplicate_log(tracker):
    h = tracker.add_habit("read", "daily")
    tracker.log(h.id, _utc_date(-1))
    with pytest.raises(DuplicateLogError):
        tracker.log(h.id, _utc_date(-1))

def test_ac_2_5_invalid_value(tracker):
    h = tracker.add_habit("read", "daily")
    with pytest.raises(InvalidValueError):
        tracker.log(h.id, _utc_date(-1), value=0)

def test_ac_3_2_daily_streak(tracker):
    h = tracker.add_habit("stretch", "daily")
    for offset in [0, -1, -2]:
        tracker.log(h.id, _utc_date(offset))
    assert tracker.current_streak(h.id) == 3

def test_ac_3_2b_streak_zero_on_gap(tracker):
    h = tracker.add_habit("walk", "daily")
    tracker.log(h.id, _utc_date(-2))
    assert tracker.current_streak(h.id) == 0

def test_ac_3_4_unknown_habit(tracker):
    with pytest.raises(HabitNotFoundError):
        tracker.current_streak("nonexistent-id")

def test_ac_5_4_missing_file_ok(tmp_path):
    t = HabitTracker(data_path=tmp_path / "does-not-exist.json")
    assert t.list_habits() == []
