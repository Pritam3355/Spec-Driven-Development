# src/cli.py
"""Command-line interface for the habit tracker."""

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from .errors import HabitError
from .service import HabitTracker


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Track daily and weekly habits.")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("./data/habits.json"),
        help="Path to the habit data file.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    add_parser = commands.add_parser("add", help="Add a habit.")
    add_parser.add_argument("name")
    add_parser.add_argument("frequency")

    log_parser = commands.add_parser("log", help="Log a habit completion.")
    log_parser.add_argument("habit_id")
    log_parser.add_argument("date")
    log_parser.add_argument("--value", type=int, default=1)

    streak_parser = commands.add_parser("streak", help="Show a habit's streak.")
    streak_parser.add_argument("habit_id")

    commands.add_parser("list", help="List all habits.")

    logs_parser = commands.add_parser("logs", help="List a habit's logs.")
    logs_parser.add_argument("habit_id")

    delete_parser = commands.add_parser("delete", help="Delete a habit.")
    delete_parser.add_argument("habit_id")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the habit tracker command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    tracker = HabitTracker(data_path=args.data)

    try:
        if args.command == "add":
            result = tracker.add_habit(args.name, args.frequency)
            tracker.save()
            print(json.dumps(asdict(result), indent=2))
        elif args.command == "log":
            result = tracker.log(args.habit_id, args.date, args.value)
            tracker.save()
            print(json.dumps(asdict(result), indent=2))
        elif args.command == "streak":
            print(tracker.current_streak(args.habit_id))
        elif args.command == "list":
            print(
                json.dumps(
                    [asdict(summary) for summary in tracker.list_habits()],
                    indent=2,
                )
            )
        elif args.command == "logs":
            print(
                json.dumps(
                    [asdict(entry) for entry in tracker.list_logs(args.habit_id)],
                    indent=2,
                )
            )
        elif args.command == "delete":
            tracker.delete_habit(args.habit_id)
            tracker.save()
            print(json.dumps({"deleted": args.habit_id}))
    except HabitError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())