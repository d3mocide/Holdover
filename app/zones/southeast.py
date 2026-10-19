"""Southeast zone (ODFW field_zone_value=4): the Klamath, Lakeview, Harney and Baker country.

Names and labels come from the zone's stocking schedule (fetched 2026-10-18; 36 labels, 36 waterbodies; ODFW offices: Lakeview, Hines, La Grande, Klamath Falls). Pins
come from same-named features in the OpenStreetMap data inside the basemap (scripts/propose_zone.py). Nothing here is from memory. PINS records how each was
found; a waterbody with no pin is listed under "needs coordinates" and is never drawn. Only unambiguous same-name matches were pinned: a name with several far-apart
candidates, or with no same-named feature, is left empty."""

ZONE = "southeast"
LABEL = "Southeast"
STOCKING_VALUE = 4
REPORT_KEY = "se"

# (canonical name, kind, lat, lon, [stocking-schedule labels])
SEED: list[tuple[str, str, float | None, float | None, list[str]]] = [
    ("Ana Reservoir", "reservoir", 42.99725, -120.75747, ["ANA RESERVOIR"]),
    ("Ana River", "river", 42.93287, -120.77967, ["ANA RIVER"]),
    ("Anthony Lake", "lake", None, None, ["ANTHONY LAKE"]),
    ("Balm Creek Reservoir", "reservoir", None, None, ["BALM CREEK RESERVOIR"]),
    ("Becker Pond", "pond", None, None, ["BECKER POND"]),
    ("Bully Creek Reservoir", "reservoir", None, None, ["BULLY CREEK RESERVOIR"]),
    ("Burns Gravel Pond", "pond", None, None, ["BURNS GRAVEL POND"]),
    ("Campbell Lake", "lake", None, None, ["CAMPBELL LAKE"]),
    ("Chickahominy Reservoir", "reservoir", 43.56026, -119.63160, ["CHICKAHOMINY RESERVOIR"]),
    ("Deadhorse Lake", "lake", None, None, ["DEADHORSE LAKE"]),
    ("Delintment Lake", "lake", 43.89254, -119.62665, ["DELINTMENT LAKE"]),
    ("Drews Gap Pond", "pond", None, None, ["DREWS GAP POND"]),
    ("Duncan Reservoir", "reservoir", 43.06828, -120.94586, ["DUNCAN RESERVOIR"]),
    ("Fish Lake (Southeast)", "lake", None, None, ["FISH LAKE"]),
    ("Fourmile Lake", "lake", 42.46655, -122.25262, ["FOURMILE LAKE"]),
    ("Haines Pond", "pond", None, None, ["HAINES POND"]),
    ("Heart Lake", "lake", None, None, ["HEART LAKE"]),
    ("Highway 203 Pond", "pond", None, None, ["HIGHWAY 203 POND"]),
    ("Holbrook Reservoir", "reservoir", None, None, ["HOLBROOK RESERVOIR"]),
    ("Krumbo Reservoir", "reservoir", 42.95498, -118.80695, ["KRUMBO RESERVOIR"]),
    ("Lake of the Woods", "lake", 42.36609, -122.21460, ["LAKE OF THE WOODS"]),
    ("Lofton Reservoir", "reservoir", 42.26391, -120.81844, ["LOFTON RESERVOIR"]),
    ("Miller Lake", "lake", 43.22862, -121.95743, ["MILLER LAKE"]),
    ("Murray Reservoir (formerly Hardy Murray Reservoir)", "reservoir", None, None, ["MURRAY RESERVOIR FORMER HARDY MURRAY RESERVOIR"]),
    ("North Powder Pond", "pond", None, None, ["NORTH POWDER POND"]),
    ("Phillips Reservoir", "reservoir", 44.67761, -118.05045, ["PHILLIPS RESERVOIR"]),
    ("Poison Creek Reservoir", "reservoir", None, None, ["POISON CREEK RESERVOIR"]),
    ("Powder River", "river", 44.73577, -118.20401, ["POWDER RIVER"]),
    ("Priday Reservoir", "reservoir", 42.33885, -119.89605, ["PRIDAY RESERVOIR"]),
    ("Taylor Green Pond", "pond", None, None, ["TAYLOR GREEN POND"]),
    ("Thief Valley Reservoir", "reservoir", None, None, ["THIEF VALLEY RESERVOIR"]),
    ("Thompson Valley Reservoir", "reservoir", None, None, ["THOMPSON VALLEY RESERVOIR"]),
    ("Tipton Pond, North", "pond", None, None, ["TIPTON POND NORTH"]),
    ("Twin Lake (Southeast)", "lake", None, None, ["TWIN LAKE"]),
    ("Vee Lake", "lake", None, None, ["VEE LAKE"]),
    ("Yellow Jacket Lake", "lake", None, None, ["YELLOW JACKET LAKE"]),
]

# "osm" = a same-named water feature (polygon or labelled lake). "likely" = a same-named point of interest or a choice between candidates: check these.
PINS: dict[str, tuple[str, str]] = {
    "Ana Reservoir": ("osm", "OSM water 'Ana Reservoir'"),
    "Ana River": ("likely", "a point along the OSM line 'Ana River' (it is a short spring-fed river; check)"),
    "Chickahominy Reservoir": ("osm", "OSM water 'Chickahominy Reservoir'"),
    "Delintment Lake": ("osm", "OSM water 'Delintment Lake'"),
    "Duncan Reservoir": ("osm", "OSM water 'Duncan Reservoir'"),
    "Fourmile Lake": ("osm", "OSM water 'Fourmile Lake'"),
    "Krumbo Reservoir": ("osm", "OSM water 'Krumbo Reservoir'"),
    "Lake of the Woods": ("osm", "OSM water 'Lake of the Woods'"),
    "Lofton Reservoir": ("osm", "OSM water 'Lofton Reservoir'"),
    "Miller Lake": ("likely", "two OSM 'Miller Lake' features; took the Klamath County one on the water layer"),
    "Phillips Reservoir": ("osm", "OSM water 'Phillips Lake'"),
    "Powder River": ("likely", "a point along the OSM line 'Powder River' in the La Grande district"),
    "Priday Reservoir": ("osm", "OSM water 'Priday Reservoir'"),
}

FISHERY_HINTS: dict[str, list[str]] = {}  # stocked trout until the owner says otherwise; the weekly report can add species

# USGS gauges (site, name, lat, lon) that reported discharge on the live Water Data API on 2026-10-19. None is clearly the same water as a stocked lake or pond.
GAUGES: list[tuple[str, str, float, float]] = [
    ("11509500", "Klamath River at Keno", 42.13320, -121.96223),
    ("11507500", "Link River at Klamath Falls", 42.22348, -121.79417),
    ("11502500", "Williamson River below Sprague River near Chiloquin", 42.56437, -121.87971),
    ("11501000", "Sprague River near Chiloquin", 42.58431, -121.84833),
    ("11504115", "Wood River near Klamath Agency", 42.58156, -121.94170),
    ("13181000", "Owyhee River near Rome", 42.86639, -117.64917),
    ("13233300", "Malheur River below Nevada Dam near Vale", 43.98750, -117.21889),
    ("13213100", "Snake River at Nyssa", 43.87611, -116.98250),
]
GAUGE_LINKS: dict[str, list[str]] = {}
