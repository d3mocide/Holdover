"""Willamette-zone waterbody seed.

Alias strings are the exact labels used on the ODFW stocking schedule (fetched 2026-10-17).
The SEED coordinates are the original hand-entered values, APPROXIMATE and from general knowledge.
COORD_UPDATES (below) overrides them with positions cross-checked against named OpenStreetMap
features in the basemap (scripts/check_coords.py). Waterbodies with no coordinate at all are listed
under "needs coordinates" instead of being drawn. Rows not in COORD_UPDATES remain unverified.
"""
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Gauge, Waterbody, WaterbodyAlias, WaterbodyGauge
from app.normalize import normalize_alias

REGS_URL = "https://myodfw.com/fishing/regulations"
SOURCE = "odfw_stocking"
ZONE = "willamette"

# (canonical name, kind, lat, lon, [stocking-schedule labels])
SEED: list[tuple[str, str, float | None, float | None, list[str]]] = [
    ("Alton Baker Canal", "river", 44.0535, -123.0650, ["ALTON BAKER CANAL"]),
    ("Benson Lake", "lake", 45.594, -122.090, ["BENSON LK"]),
    ("Bethany Pond", "pond", 45.559, -122.845, ["BETHANY PD"]),
    ("Blue Lake", "lake", 45.540, -122.444, ["BLUE LK"]),
    ("Blue River", "river", 44.168, -122.330, ["BLUE R"]),
    ("Blue River Reservoir", "reservoir", 44.163, -122.240, ["BLUE RIVER RES"]),
    ("Breitenbush River", "river", 44.778, -122.145, ["BREITENBUSH R"]),
    ("Canby Pond", "pond", 45.263, -122.691, ["CANBY PD"]),
    ("Carmen Reservoir", "reservoir", 44.293, -122.030, ["CARMEN RES"]),
    ("Clear Lake (McKenzie)", "lake", 44.369, -121.992, ["CLEAR LK"]),
    ("Commonwealth Lake", "lake", 45.473, -122.817, ["COMMONWEALTH LK"]),
    ("Cottage Grove Reservoir", "reservoir", 43.715, -123.058, ["COTTAGE GROVE RES"]),
    ("Detroit Reservoir", "reservoir", 44.718, -122.150, ["DETROIT RES"]),
    ("Dexter Reservoir", "reservoir", 43.920, -122.810, ["DEXTER RES"]),
    ("Dorena Reservoir", "reservoir", 43.786, -122.950, ["DORENA RES"]),
    ("Dorman Pond", "pond", None, None, ["DORMAN PD"]),
    ("EE Wilson Pond", "pond", 44.720, -123.230, ["EE WILSON PD"]),
    ("Estacada Lake", "lake", 45.291, -122.330, ["ESTACADA LK"]),
    ("Fall Creek (Willamette R)", "creek", 43.970, -122.750, ["FALL CR (WILLAMETTE R)"]),
    ("Fall Creek Reservoir", "reservoir", 43.933, -122.620, ["FALL CR RES"]),
    ("Faraday Lake", "lake", 45.285, -122.320, ["FARADAY LK"]),
    ("Foster Reservoir", "reservoir", 44.414, -122.674, ["FOSTER RES"]),
    ("Freeway Lakes, East", "lake", None, None, ["FREEWAY LK, EAST"]),
    ("Green Peter Reservoir", "reservoir", 44.450, -122.530, ["GREEN PETER RES"]),
    ("Haldeman Pond", "pond", None, None, ["HALDEMAN PD"]),
    ("Harriet Lake", "lake", None, None, ["HARRIET LK"]),
    ("Hartman Pond (Wahkeena Lake)", "pond", None, None, ["HARTMAN PD (WAHKEENA LK)"]),
    ("Henry Hagg Lake", "lake", 45.470, -123.187, ["HENRY HAGG LK"]),
    ("Hills Creek Reservoir", "reservoir", 43.717, -122.430, ["HILLS CR RES"]),
    ("Huddleston Pond (Hampton Pond)", "pond", None, None, ["HUDDLESTON PD (FMR HAMPTON PD)"]),
    ("Junction City Pond", "pond", 44.220, -123.200, ["JUNCTION CITY PD"]),
    ("Leaburg Lake", "lake", 44.101, -122.682, ["LEABURG LK"]),
    ("McKenzie River (below Leaburg Dam)", "river", 44.068, -122.820, ["MCKENZIE R-1 (below Leaburg Dam)"]),
    ("McKenzie River (above Leaburg Dam)", "river", 44.150, -122.500, ["MCKENZIE R-2 (above Leaburg Dam)"]),
    ("Mt Hood Pond (MHCC campus)", "pond", 45.523, -122.443, ["MT HOOD PD (MHCC CAMPUS)"]),
    ("North Fork Reservoir", "reservoir", 45.276, -122.261, ["NORTH FORK RES"]),
    ("Progress Lake", "lake", 45.456, -122.795, ["PROGRESS LK"]),
    ("Quartzville Creek", "creek", 44.560, -122.450, ["QUARTZVILLE CR"]),
    ("Roaring River Park Pond", "pond", 44.593, -122.747, ["ROARING RVR PARK PD"]),
    ("Row River Nature Park (Cottage Grove Pond)", "pond", 43.790, -123.044, ["ROW R NATURE PK-Fmr Cott. Grv. Pd"]),
    ("Salish Pond, West", "pond", 45.529, -122.460, ["SALISH PD, W"]),
    ("Salmon Creek", "creek", 43.738, -122.390, ["SALMON CR"]),
    ("Salmonberry Lake", "lake", None, None, ["SALMONBERRY LK"]),
    ("Santiam River, North Fork", "river", 44.780, -122.610, ["SANTIAM R, N FK-2"]),
    ("Sheridan Pond", "pond", 45.099, -123.398, ["SHERIDAN PD"]),
    ("Silver Creek Reservoir", "reservoir", None, None, ["SILVER CR RES"]),
    ("Small Fry Lake", "lake", None, None, ["SMALL FRY LK"]),
    ("Smith River Reservoir", "reservoir", None, None, ["SMITH R RES"]),
    ("St Louis Ponds", "pond", 45.159, -122.986, ["ST LOUIS PD"]),
    ("Sunnyside Park Pond", "pond", None, None, ["SUNNYSIDE PARK PD"]),
    ("Timber Linn Lake", "lake", 44.623, -123.110, ["TIMBER LINN LK"]),
    ("Timothy Lake", "lake", 45.110, -121.750, ["TIMOTHY LK"]),
    ("Trillium Lake", "lake", 45.278, -121.742, ["TRILLIUM LK"]),
    ("Trojan Recreation Lake", "lake", 46.032, -122.887, ["TROJAN RECREATION LK"]),
    ("Turner Lake", "lake", None, None, ["TURNER LK"]),
    ("Walter Wirth Lake", "lake", None, None, ["WALTER WIRTH LK"]),
    ("Waverly Lake", "lake", 44.634, -123.078, ["WAVERLY LK"]),
    ("Willamette River, Coast Fork", "river", 43.810, -123.030, ["WILLAMETTE R, CST FK"]),
]


# Verified or snapped 2026-10-18 with scripts/check_coords.py against the Protomaps/OSM basemap.
# name -> (lat, lon, how). "osm" = same-named lake/pond/reservoir feature, label point or centroid;
# "snap" = nearest vertex of the same-named river/creek line (rivers have no single true point);
# "likely" = the OSM name differs from ODFW's, so it is a judgement call worth a second look.
COORD_UPDATES: dict[str, tuple[float, float, str]] = {
    "Benson Lake": (45.5776, -122.1239, "osm"),
    "Bethany Pond": (45.5569, -122.8719, "likely"),  # OSM: Bethany Lake (Bethany Lake Park)
    "Blue Lake": (45.5539, -122.4478, "osm"),
    "Blue River": (44.1689, -122.3305, "snap"),
    "Blue River Reservoir": (44.1883, -122.2658, "osm"),  # OSM: Blue River Lake
    "Breitenbush River": (44.7582, -122.1183, "snap"),
    "Canby Pond": (45.2529, -122.7043, "osm"),
    "Carmen Reservoir": (44.3400, -122.0038, "osm"),
    "Commonwealth Lake": (45.5119, -122.8080, "osm"),
    "Cottage Grove Reservoir": (43.6971, -123.0708, "osm"),  # OSM: Cottage Grove Lake
    "Detroit Reservoir": (44.7113, -122.1819, "osm"),  # OSM: Detroit Lake
    "Dexter Reservoir": (43.9162, -122.7988, "osm"),
    "Dorena Reservoir": (43.7704, -122.9151, "osm"),  # OSM: Dorena Lake
    "Dorman Pond": (45.6128, -123.2457, "osm"),
    "Faraday Lake": (45.2627, -122.3068, "osm"),
    "Fall Creek (Willamette R)": (43.9459, -122.7583, "snap"),
    "Fall Creek Reservoir": (43.9499, -122.7422, "osm"),  # OSM: Fall Creek Lake
    "Foster Reservoir": (44.4185, -122.6388, "osm"),  # OSM: Foster Lake
    "Freeway Lakes, East": (44.5908, -123.0653, "likely"),  # OSM: Freeway Lakes (one point for the complex)
    "Green Peter Reservoir": (44.4897, -122.4155, "osm"),  # OSM: Green Peter Lake
    "Harriet Lake": (45.0738, -121.9619, "osm"),  # OSM: Lake Harriet
    "Henry Hagg Lake": (45.4865, -123.2208, "osm"),
    "Hills Creek Reservoir": (43.6882, -122.4521, "osm"),
    "Leaburg Lake": (44.1414, -122.5949, "osm"),
    "McKenzie River (above Leaburg Dam)": (44.1319, -122.4997, "snap"),
    "McKenzie River (below Leaburg Dam)": (44.0609, -122.8065, "snap"),
    "North Fork Reservoir": (45.2330, -122.2558, "osm"),
    "Quartzville Creek": (44.5480, -122.4311, "snap"),
    "Salish Pond, West": (45.5307, -122.4448, "likely"),  # OSM: Salish Ponds Park
    "Salmon Creek": (43.7524, -122.4016, "snap"),
    "Santiam River, North Fork": (44.7842, -122.6083, "snap"),
    "Smith River Reservoir": (44.3202, -122.0463, "likely"),  # OSM: Smith Reservoir (Smith River, McKenzie basin)
    "Timber Linn Lake": (44.6380, -123.0554, "osm"),
    "Timothy Lake": (45.1262, -121.7884, "osm"),
    "Trillium Lake": (45.2699, -121.7394, "osm"),
    "Turner Lake": (44.8584, -122.9559, "osm"),
    "Walter Wirth Lake": (44.9095, -122.9891, "osm"),  # OSM: Wirth Lake
    "Waverly Lake": (44.6405, -123.0697, "osm"),
    "Willamette River, Coast Fork": (43.8144, -123.0446, "snap"),
}


def _same(a: float | None, b: float | None) -> bool:
    return (a is None and b is None) or (a is not None and b is not None and abs(a - b) < 1e-6)


# Which fisheries a water supports beyond stocked trout. Seed hints from general knowledge, NOT verified:
# the owner should correct them. Trout membership comes from the stocking schedule itself, and any
# water also joins a fishery when an accepted report item names a matching species.
FISHERY_HINTS = {
    "Santiam River, North Fork": ["steelhead"], "McKenzie River (below Leaburg Dam)": ["steelhead"],
    "McKenzie River (above Leaburg Dam)": ["steelhead"],
    "Henry Hagg Lake": ["warmwater"], "Dorena Reservoir": ["warmwater"], "Cottage Grove Reservoir": ["warmwater"],
    "Foster Reservoir": ["warmwater"], "Blue Lake": ["warmwater"],
}


def _seed_zone(session: Session, zone: str, seed, updates: dict, hints: dict) -> int:
    added = 0
    for name, kind, seed_lat, seed_lon, labels in seed:
        upd = updates.get(name)
        lat, lon = (upd[0], upd[1]) if upd else (seed_lat, seed_lon)
        wb = session.scalar(select(Waterbody).where(Waterbody.name == name))
        if wb is None:
            wb = Waterbody(name=name, kind=kind, lat=lat, lon=lon, zone=zone, regs_url=REGS_URL)
            session.add(wb)
            session.flush()
            added += 1
        elif upd and _same(wb.lat, seed_lat) and _same(wb.lon, seed_lon):
            # Still holds the original hand-entered value: safe to correct. Anything else was set deliberately.
            wb.lat, wb.lon = lat, lon
        if name in hints and wb.species_json is None:
            wb.species_json = json.dumps({"fisheries": hints[name], "source": "seed hint, unverified"})
        for label in labels:
            key = normalize_alias(label)
            if session.scalar(
                select(WaterbodyAlias.id).where(WaterbodyAlias.alias_text == key, WaterbodyAlias.source == SOURCE)
            ) is None:
                session.add(WaterbodyAlias(alias_text=key, source=SOURCE, waterbody_id=wb.id, confirmed=1))
    return added


def seed_waterbodies(session: Session) -> int:
    """Idempotent: adds missing waterbodies and their confirmed aliases, for Willamette and every zone module."""
    from app.zones import MODULES
    added = _seed_zone(session, ZONE, SEED, COORD_UPDATES, FISHERY_HINTS)
    for m in MODULES:
        added += _seed_zone(session, m.ZONE, m.SEED, {}, m.FISHERY_HINTS)  # a pin set here is only ever inserted, never re-applied over a person's edit
    session.commit()
    seed_gauges(session)
    return added


# USGS gauges. Site numbers, names and coordinates were verified against the live USGS IV service
# on 2026-10-17 (all report 00060 discharge unless noted). (site_no, name, lat, lon)
GAUGES = [
    ("14166000", "Willamette River at Harrisburg", 44.27040, -123.17370),
    ("14174000", "Willamette River at Albany", 44.63873, -123.10676),
    ("14191000", "Willamette River at Salem", 44.94429, -123.04287),
    ("14150000", "Middle Fork Willamette River near Dexter", 43.94568, -122.83730),
    ("14152000", "Middle Fork Willamette River at Jasper", 43.99818, -122.90591),
    ("14153500", "Coast Fork Willamette R below Cottage Grove Dam", 43.72068, -123.04980),
    ("14157500", "Coast Fork Willamette River near Goshen", 43.98040, -122.96647),
    ("14162500", "McKenzie River near Vida", 44.12485, -122.47062),
    ("14163150", "McKenzie River below Leaburg Dam", 44.12374, -122.62757),
    ("14165500", "McKenzie River near Coburg", 44.11306, -123.04697),
    ("14178000", "North Santiam R below Boulder Creek near Detroit", 44.70679, -122.10119),
    ("14179000", "Breitenbush River above French Creek near Detroit", 44.75262, -122.12896),
    ("14181500", "North Santiam River at Niagara", 44.75378, -122.29744),
    ("14183000", "North Santiam River at Mehama", 44.78925, -122.61881),
    ("14185900", "Quartzville Creek near Cascadia", 44.54012, -122.43592),
    ("14210000", "Clackamas River at Estacada", 45.29984, -122.35397),
]

# waterbody name -> gauge site numbers that represent it. Only links that are clearly the same water.
GAUGE_LINKS = {
    "Santiam River, North Fork": ["14183000", "14181500"],
    "Breitenbush River": ["14179000"],
    "McKenzie River (below Leaburg Dam)": ["14163150"],
    "McKenzie River (above Leaburg Dam)": ["14162500"],
    "Willamette River, Coast Fork": ["14157500", "14153500"],
    "Quartzville Creek": ["14185900"],
    "Dexter Reservoir": ["14150000"],
    # Tailwater gauges just below the dam on the same river, like Dexter's.
    "Leaburg Lake": ["14163150"],
    "Cottage Grove Reservoir": ["14153500"],
    "Estacada Lake": ["14210000"],
}


def seed_gauges(session: Session) -> int:
    from app.zones import MODULES
    added = 0
    groups = [(ZONE, GAUGES, GAUGE_LINKS)] + [(m.ZONE, m.GAUGES, m.GAUGE_LINKS) for m in MODULES]
    for zone, gauges, links in groups:
        for site, name, lat, lon in gauges:
            g = session.scalar(select(Gauge).where(Gauge.site_no == site, Gauge.agency == "USGS"))
            if g is None:
                session.add(Gauge(site_no=site, agency="USGS", name=name, lat=lat, lon=lon, zone=zone))
                added += 1
            elif g.zone is None:
                g.zone = zone
        session.flush()
        for wb_name, sites in links.items():
            wb = session.scalar(select(Waterbody).where(Waterbody.name == wb_name))
            if wb is None:
                continue
            for site in sites:
                g = session.scalar(select(Gauge).where(Gauge.site_no == site))
                if g and session.get(WaterbodyGauge, (wb.id, g.id)) is None:
                    session.add(WaterbodyGauge(waterbody_id=wb.id, gauge_id=g.id))
    session.commit()
    return added
