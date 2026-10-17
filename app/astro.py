"""Daylight and moon, computed locally (no feed)."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from astral import LocationInfo, moon
from astral.sun import sun

TZ = ZoneInfo("America/Los_Angeles")


def daylight(lat: float, lon: float, d: date) -> dict:
    s = sun(LocationInfo(latitude=lat, longitude=lon, timezone="America/Los_Angeles").observer, date=d, tzinfo=TZ)
    f = lambda dt: dt.astimezone(TZ).strftime("%H:%M")
    return {"first_light": f(s["dawn"]), "sunrise": f(s["sunrise"]), "sunset": f(s["sunset"]), "last_light": f(s["dusk"])}


def moon_phase(d: date) -> dict:
    p = moon.phase(d)  # 0..27.99 days into the cycle
    names = [(1.84, "New moon"), (5.53, "Waxing crescent"), (9.22, "First quarter"), (12.91, "Waxing gibbous"),
             (16.61, "Full moon"), (20.30, "Waning gibbous"), (23.99, "Last quarter"), (27.68, "Waning crescent")]
    name = next((n for lim, n in names if p < lim), "New moon")
    return {"phase": name, "age_days": round(p, 1)}
