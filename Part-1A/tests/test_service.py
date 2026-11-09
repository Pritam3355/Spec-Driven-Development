"""Tests derived from spec.md ACs. 11 tests targeting ~50% coverage (per constitution 2)."""
import json
from datetime import datetime, timedelta, timezone

import pytest

from src.cli import build_parser
from src.errors import (
    DuplicateLogError, FutureDateError, HabitNotFoundError, InvalidFrequencyError,
    InvalidNameError, InvalidValueError,
)
from src.service import HabitTracker
from src.streaks import days_of_week_streak

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


# --------------------------------------------------------------------- v1.1
# PM enhancement round (spec.md v1.1): delete habit + days-of-week frequency.
# Fixed dates: 2026-01-05 Mon, 01-07 Wed, 01-09 Fri, 01-10 Sat, 01-12 Mon,
# 01-14 Wed (verified against datetime.date(2026, 1, d).weekday()).
_MWF = frozenset({0, 2, 4})  # Python weekdays: Mon=0, Wed=2, Fri=4


def test_ac_1_5_dow_add(tracker):
    h = tracker.add_habit("gym", "[Mon,Wed,Fri]")
    assert h.frequency == "[Mon,Wed,Fri]"          # stored verbatim (Q16)
    assert tracker.add_habit("gym", "[Mon,Wed,Fri]").id == h.id  # FR-1.4


def test_ac_1_6_dow_invalid(tracker):
    for bad in ("[Fri,Mon]", "[mon]", "[Monday]", "[Mon, Wed]", "[Mon,Mon]",
                "[]", "[Mon,", "Mon,Wed", "[Wed,Tue]"):
        with pytest.raises(InvalidFrequencyError):
            tracker.add_habit("bad " + bad, bad)


def test_ac_3_5_dow_streak():
    logs = ["2026-01-05", "2026-01-07", "2026-01-09", "2026-01-12", "2026-01-14"]
    # today = Wed 2026-01-14 (scheduled, logged): Wed14, Mon12, Fri09, Wed07,
    # Mon05 counted; previous scheduled Fri 2026-01-02 missing => 5.
    assert days_of_week_streak(logs, "2026-01-14", _MWF) == 5


def test_ac_3_5b_dow_today_unlogged():
    logs = ["2026-01-05", "2026-01-07", "2026-01-09"]
    # today = Mon 2026-01-12 is scheduled but has no log => 0 (FR-3.2 rule).
    assert days_of_week_streak(logs, "2026-01-12", _MWF) == 0


def test_ac_3_5c_dow_rest_today():
    logged = ["2026-01-05", "2026-01-07", "2026-01-09"]
    # Sat 01-10 / Sun 01-11 are rest days: neither count nor break (Q14).
    assert days_of_week_streak(logged, "2026-01-10", _MWF) == 3
    assert days_of_week_streak(logged, "2026-01-11", _MWF) == 3
    # but a missed scheduled day breaks the streak even on a rest day:
    assert days_of_week_streak(logged[:2], "2026-01-10", _MWF) == 0


def test_ac_3_5d_full_week(tracker):
    h = tracker.add_habit("allweek", "[Sun,Mon,Tue,Wed,Thu,Fri,Sat]")
    tracker.log(h.id, _utc_date(0))
    # deterministic for ANY real weekday: today scheduled+logged, yesterday not
    assert tracker.current_streak(h.id) == 1


def test_ac_6_1_delete(tracker):
    h = tracker.add_habit("temp", "daily")
    tracker.log(h.id, _utc_date(-1))
    tracker.delete_habit(h.id)
    assert all(s.name != "temp" for s in tracker.list_habits())
    with pytest.raises(HabitNotFoundError):
        tracker.log(h.id, _utc_date(-1))
    tracker.save()  # persisted cascade: inspect the store file directly —
    # list_logs() raises for an unknown habit, so read the JSON instead:
    data = json.loads(tracker.data_path.read_text(encoding="utf-8"))
    assert all(habit["id"] != h.id for habit in data["habits"])
    assert all(entry["habit_id"] != h.id for entry in data["logs"])  # no orphans
    reloaded = HabitTracker(data_path=tracker.data_path)
    with pytest.raises(HabitNotFoundError):
        reloaded.delete_habit(h.id)  # no tombstones (clarify Q11)


def test_ac_6_2_delete_unknown(tracker):
    with pytest.raises(HabitNotFoundError):
        tracker.delete_habit("nonexistent-id")


def test_ac_7_1_cli_parser():
    parser = build_parser()
    args = parser.parse_args(["delete", "abc-123"])
    assert args.command == "delete" and args.habit_id == "abc-123"
    args2 = parser.parse_args(["add", "gym", "[Mon,Wed,Fri]"])
    assert args2.command == "add" and args2.frequency == "[Mon,Wed,Fri]"

