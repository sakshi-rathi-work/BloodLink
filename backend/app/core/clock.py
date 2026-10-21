"""Centralized clock helper for deterministic time in business logic and tests."""
from datetime import date
from typing import Optional

_frozen_today: Optional[date] = None


def today() -> date:
    """Return today's date, or frozen date if set for testing."""
    if _frozen_today is not None:
        return _frozen_today
    return date.today()


def set_today(val: Optional[date]) -> None:
    """Freeze or unfreeze time for testing."""
    global _frozen_today
    _frozen_today = val
