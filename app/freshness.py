from datetime import date, timedelta


def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def freshness(week_of: str, today: date) -> str:
    """Stocking freshness bucket for the map. Weeks, never days.
    upcoming: scheduled for a later week; this_week; recent: 1-2 weeks back; older."""
    w = date.fromisoformat(week_of)
    this_mon = monday_of(today)
    if w > this_mon:
        return "upcoming"
    weeks_back = (this_mon - w).days // 7
    if weeks_back == 0:
        return "this_week"
    if weeks_back <= 2:
        return "recent"
    return "older"
