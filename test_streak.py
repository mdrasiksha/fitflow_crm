from datetime import date
from types import SimpleNamespace
import unittest

from streaks import calculate_streak


def checkin(checkin_id: int, day: date, status: str):
    return SimpleNamespace(id=checkin_id, date=day, status=status)


class CalculateStreakTests(unittest.TestCase):
    def test_empty_checkins_returns_zero(self):
        client = SimpleNamespace(checkins=[])
        self.assertEqual(calculate_streak(client), 0)

    def test_breaks_on_missing_day_gap(self):
        client = SimpleNamespace(
            checkins=[
                checkin(1, date(2026, 4, 14), "yes"),
                checkin(2, date(2026, 4, 12), "yes"),
            ]
        )
        self.assertEqual(calculate_streak(client), 1)

    def test_breaks_on_no_status(self):
        client = SimpleNamespace(
            checkins=[
                checkin(1, date(2026, 4, 14), "yes"),
                checkin(2, date(2026, 4, 13), "no"),
                checkin(3, date(2026, 4, 12), "yes"),
            ]
        )
        self.assertEqual(calculate_streak(client), 1)

    def test_uses_latest_checkin_for_same_day(self):
        client = SimpleNamespace(
            checkins=[
                checkin(1, date(2026, 4, 14), "yes"),
                checkin(2, date(2026, 4, 14), "no"),
                checkin(3, date(2026, 4, 13), "yes"),
            ]
        )
        self.assertEqual(calculate_streak(client), 0)


if __name__ == "__main__":
    unittest.main()
