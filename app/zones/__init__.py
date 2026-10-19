"""Zones beyond the first. Each module here seeds one ODFW zone's waterbodies, gauges and gauge links; app/seed.py holds Willamette.

A zone module defines: ZONE (our key), LABEL, STOCKING_VALUE (ODFW's field_zone_value), REPORT_KEY (the key the weekly report parser
uses for it), SEED (name, kind, lat, lon, [stocking labels]), PINS (name -> how the coordinate was found), FISHERY_HINTS, GAUGES and
GAUGE_LINKS. A coordinate is never invented: it comes from a same-named OpenStreetMap feature (see PINS) or is left empty."""
from dataclasses import dataclass

from app.zones import central


@dataclass(frozen=True)
class ZoneInfo:
    key: str
    label: str
    stocking_value: int  # ODFW's field_zone_value on the stocking schedule
    report_key: str      # the zone key used by the weekly Recreation Report parser


WILLAMETTE = ZoneInfo("willamette", "Willamette", 6, "willamette")
MODULES = (central,)
ALL: tuple[ZoneInfo, ...] = (WILLAMETTE,) + tuple(ZoneInfo(m.ZONE, m.LABEL, m.STOCKING_VALUE, m.REPORT_KEY) for m in MODULES)
BY_KEY = {z.key: z for z in ALL}


def enabled(setting: str) -> list[ZoneInfo]:
    """The zones named in the ENABLED_ZONES setting (comma separated keys), in registry order. Unknown keys are ignored."""
    want = {k.strip().lower() for k in setting.split(",") if k.strip()}
    return [z for z in ALL if z.key in want]
