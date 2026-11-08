# src/errors.py
"""Domain errors for the habit tracker."""


class HabitError(Exception):
    """Base class for habit tracker domain errors."""


class InvalidFrequencyError(HabitError):
    """Raised when a habit frequency is invalid."""


class InvalidNameError(HabitError):
    """Raised when a habit name is invalid."""


class InvalidDateError(HabitError):
    """Raised when a log date is invalid."""


class FutureDateError(HabitError):
    """Raised when a log date is in the future."""


class DuplicateLogError(HabitError):
    """Raised when a completion is logged more than once for a date."""


class InvalidValueError(HabitError):
    """Raised when a log value is invalid."""


class HabitNotFoundError(HabitError):
    """Raised when a habit cannot be found."""


class CorruptDataError(HabitError):
    """Raised when persisted tracker data is invalid."""