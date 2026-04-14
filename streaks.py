from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import models


def calculate_streak(client: "models.Client") -> int:
    if not client.checkins:
        return 0

    checkins = sorted(client.checkins, key=lambda c: (c.date, c.id), reverse=True)

    # Keep only the latest check-in per day so each calendar date is counted once.
    latest_status_by_day: dict[date, str] = {}
    for checkin in checkins:
        if checkin.date not in latest_status_by_day:
            latest_status_by_day[checkin.date] = checkin.status

    ordered_days = sorted(latest_status_by_day.keys(), reverse=True)
    streak = 0
    expected_day = ordered_days[0]

    for day in ordered_days:
        if day != expected_day:
            break

        if latest_status_by_day[day] != "yes":
            break

        streak += 1
        expected_day = day - timedelta(days=1)

    return streak
