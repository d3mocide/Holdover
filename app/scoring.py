"""Spot scoring. Pure functions: no database, no network, no LLM.

score = 100 * sum(weight_i * factor_i) / sum(weight_i over applicable factors)

Each factor is in [0, 1]. A factor with no data (no gauge, no forecast cached, no report item...) counts
as NEUTRAL (0.5), so a spot is neither rewarded nor punished for what we don't know, and a score built on
little evidence stays near 50 instead of swinging on one input. A factor that does not apply at all
(stocking for a non-trout fishery, distance when no home location is set) is dropped and the remaining
weights renormalised. `coverage` is the share of applicable weight that had real data, so the UI can say
how much of the score is evidence. Weights and every curve are tunable starting points, not validated.
"""
import math
import statistics
from dataclasses import dataclass, field
from datetime import date, timedelta

RATING = {"excellent": 1.0, "good": 0.75, "fair": 0.5, "slow": 0.2}


@dataclass
class Factor:
    name: str
    value: float | None
    weight: float
    detail: str
    applicable: bool = True
    contribution: float = 0.0  # points out of 100, filled by combine()


NEUTRAL = 0.5


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def stocking_factor(weeks: list[tuple[str, int]], day: date, zone_p90: float, weight: float) -> Factor:
    """weeks: (week_of ISO Monday, total fish). Recency of the stocking relative to `day`'s week, scaled by
    size relative to the zone's recent range. A stocking scheduled in `day`'s own week counts as that week
    (the schedule gives a week, not a day, so it may land after `day`)."""
    this_mon = monday(day)
    best, best_desc = 0.0, ""
    for week_of, total in weeks:
        ago = (this_mon - date.fromisoformat(week_of)).days // 7
        if ago < 0 or total <= 0:
            continue  # later weeks, or nothing stocked
        recency = {0: 1.0, 1: 0.75, 2: 0.5}.get(ago, 0.25 if ago <= 4 else 0.0)
        size = clamp(total / zone_p90) if zone_p90 > 0 else 0.5
        f = recency * (0.5 + 0.5 * size)
        if f > best:
            wk = date.fromisoformat(week_of)
            best, best_desc = f, f"{total:,} fish, week of {wk:%b} {wk.day} ({'this week' if ago == 0 else f'{ago} wk before'})"
    if best == 0.0:
        return Factor("stocking", None, weight, "no stocking in the 4 weeks before this date")
    return Factor("stocking", round(best, 3), weight, best_desc)


def report_factor(rating: str | None, issued_on: str | None, day: date, weight: float) -> Factor:
    if rating not in RATING or not issued_on:
        return Factor("report", None, weight, "no accepted report item")
    age = (day - date.fromisoformat(issued_on)).days
    if age > 30:
        return Factor("report", None, weight, f"latest report item is {age} days old")
    decay = 1.0 if age <= 8 else 0.7 if age <= 15 else 0.4
    return Factor("report", round(RATING[rating] * decay, 3), weight, f"ODFW report {issued_on}: {rating}")


def flow_factor(current: float | None, history: list[float], weight: float, span_hours: float = 0.0) -> Factor:
    """Suitability = closeness to the gauge's own median over its recent history (a river near its usual
    flow is more fishable than one blown out or very low). Needs enough history to mean anything."""
    if current is None:
        return Factor("flow", None, weight, "no flow gauge")
    if len(history) < 24 or span_hours < 48:
        return Factor("flow", None, weight, "not enough gauge history yet (needs 2+ days)")
    med = statistics.median(history)
    if med <= 0:
        return Factor("flow", None, weight, "gauge history unusable")
    rel = (current - med) / med
    f = clamp(1 - abs(rel) / 0.75, 0.0, 1.0)
    return Factor("flow", round(f, 3), weight, f"{current:,.0f} cfs vs median {med:,.0f} ({rel:+.0%})")


def forecast_factor(temp_f: float | None, precip_pct: float | None, wind_mph: float | None, weight: float) -> Factor:
    parts = []
    if temp_f is not None:  # comfortable 50-75F, tapering to 0 at 25F / 100F
        parts.append(1.0 if 50 <= temp_f <= 75 else clamp((temp_f - 25) / 25) if temp_f < 50 else clamp((100 - temp_f) / 25))
    if precip_pct is not None:
        parts.append(1 - 0.7 * clamp(precip_pct / 100))
    if wind_mph is not None:  # calm up to 8 mph, 0.2 at 20+
        parts.append(1.0 if wind_mph <= 8 else clamp(1 - (wind_mph - 8) / 15, 0.2, 1.0))
    if not parts:
        return Factor("forecast", None, weight, "no forecast")
    bits = [f"{temp_f:.0f}F" if temp_f is not None else None,
            f"{precip_pct:.0f}% rain" if precip_pct is not None else None,
            f"wind {wind_mph:.0f} mph" if wind_mph is not None else None]
    return Factor("forecast", round(sum(parts) / len(parts), 3), weight, ", ".join(b for b in bits if b))


def distance_factor(km: float | None, weight: float) -> Factor:
    if km is None:
        return Factor("distance", None, weight, "home location not set", applicable=False)
    miles = km * 0.621371
    return Factor("distance", round(1 - clamp(km / 120), 3), weight, f"{miles:.0f} mi straight-line")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def combine(factors: list[Factor]) -> tuple[float, float]:
    """Returns (score 0-100, coverage 0-1) and fills each factor's `contribution` in points."""
    app = [f for f in factors if f.applicable and f.weight > 0]
    total = sum(f.weight for f in app)
    for f in factors:
        f.contribution = 0.0
    if not app or total <= 0:
        return 0.0, 0.0
    for f in app:
        f.contribution = round(100 * f.weight * (NEUTRAL if f.value is None else f.value) / total, 1)
    score = round(sum(100 * f.weight * (NEUTRAL if f.value is None else f.value) / total for f in app), 1)
    return score, round(sum(f.weight for f in app if f.value is not None) / total, 2)
