"""Northwest zone (ODFW field_zone_value=3): the Coast Range lakes and dune lakes from Tillamook to Florence.

Names and labels come from the zone's stocking schedule (fetched 2026-10-18; 33 labels, 33 waterbodies). Pins come from same-named features in
the OpenStreetMap data inside the basemap (scripts/propose_zone.py), narrowed to each label's ODFW district (Newport or Tillamook). Nothing
here is from memory. PINS records how each was found; a waterbody with no pin is listed under "needs coordinates" and is never drawn."""

ZONE = "northwest"
LABEL = "Northwest"
STOCKING_VALUE = 3
REPORT_KEY = "nw"

# (canonical name, kind, lat, lon, [stocking-schedule labels])
SEED: list[tuple[str, str, float | None, float | None, list[str]]] = [
    ("Alder Lake", "lake", 44.07052, -124.10392, ["ALDER LAKE"]),
    ("Big Creek Reservoir", "reservoir", None, None, ["BIG CREEK RESERVOIR"]),
    ("Buck Lake", "lake", None, None, ["BUCK LAKE"]),
    ("Cape Meares Lake", "lake", 45.50872, -123.94813, ["CAPE MEARES LAKE"]),
    ("Carter Lake", "lake", 43.85266, -124.14718, ["CARTER LAKE"]),
    ("Cleawox Lake", "lake", 43.93904, -124.11845, ["CLEAWOX LAKE"]),
    ("Coffenbury Lake", "lake", 46.16960, -123.96018, ["COFFENBURY LAKE"]),
    ("Cullaby Lake", "lake", 46.08533, -123.90444, ["CULLABY LAKE"]),
    ("Devil South Lake", "lake", None, None, ["DEVIL SOUTH LAKE"]),
    ("Dune Lake", "lake", None, None, ["DUNE LAKE"]),
    ("Eckman Lake", "lake", 44.41213, -124.03460, ["ECKMAN LAKE"]),
    ("Elbow Lake", "lake", 43.78682, -124.14897, ["ELBOW LAKE"]),
    ("Hebo Lake", "lake", 45.23096, -123.79588, ["HEBO LAKE"]),
    ("Loren South Pond", "pond", None, None, ["LOREN SOUTH POND"]),
    ("Lost Lake (Northwest)", "lake", 45.82432, -123.57890, ["LOST LAKE"]),
    ("Lytle Lake", "lake", 45.62350, -123.94000, ["LYTLE LAKE"]),
    ("Mercer Lake", "lake", 44.05516, -124.05605, ["MERCER LAKE"]),
    ("Munsel Lake", "lake", 44.00862, -124.08120, ["MUNSEL LAKE"]),
    ("Nedonna Pond", "pond", None, None, ["NEDONNA POND"]),
    ("North Lake", "lake", 45.21566, -123.72036, ["NORTH LAKE"]),
    ("Olalla Creek Reservoir", "reservoir", 44.68665, -123.92287, ["OLALLA CREEK RESERVOIR"]),
    ("Perkins Lake", "lake", None, None, ["PERKINS LAKE"]),
    ("Scout Lake", "lake", None, None, ["SCOUT LAKE FMRLY SCOUT CAMP LAKE"]),
    ("Siltcoos Lake", "lake", 43.87235, -124.09381, ["SILTCOOS LAKE"]),
    ("South Lake", "lake", 45.20171, -123.72163, ["SOUTH LAKE"]),
    ("Spring Lake", "lake", None, None, ["SPRING LAKE"]),
    ("Sunset Lake (North Coast Range)", "lake", None, None, ["SUNSET LAKE NORTH COAST RANGE"]),
    ("Sutton Lake", "lake", 44.05913, -124.09007, ["SUTTON LAKE"]),
    ("Tahoe Lake", "lake", 45.34974, -123.60130, ["TAHOE LAKE"]),
    ("Thissel Pond", "pond", None, None, ["THISSEL POND"]),
    ("Town Lake", "lake", 45.22470, -123.95589, ["TOWN LAKE"]),
    ("Vernonia Lake", "lake", 45.85485, -123.17371, ["VERNONIA LAKE"]),
    ("Woahink Lake", "lake", 43.91827, -124.09555, ["WOAHINK LAKE"]),
]

# "osm" = a same-named water feature (a polygon or a labelled lake) in the label's district. "likely" = a same-named point of interest or a choice
# between candidates: check these. Waters not listed here have no pin: no same-named feature in the district, or two far-apart candidates.
PINS: dict[str, tuple[str, str]] = {
    "Alder Lake": ("likely", "OSM point 'Alder Lake' (a point of interest, not a polygon), Newport district"),
    "Cape Meares Lake": ("osm", "OSM water 'Cape Meares Lake'"),
    "Carter Lake": ("likely", "OSM point 'Carter Lake' (point of interest), Newport district"),
    "Cleawox Lake": ("osm", "OSM water 'Cleawox Lake'"),
    "Coffenbury Lake": ("osm", "OSM water 'Coffenbury Lake'"),
    "Cullaby Lake": ("osm", "OSM water 'Cullaby Lake'"),
    "Eckman Lake": ("osm", "OSM water 'Eckman Lake'"),
    "Elbow Lake": ("likely", "OSM point 'Elbow Lake' (point of interest), Newport district"),
    "Hebo Lake": ("likely", "OSM point 'Hebo Lake' (the town 'Hebo' is 5 km away; took the lake)"),
    "Lost Lake (Northwest)": ("likely", "OSM point 'Lost Lake' in the Tillamook district; there is another Lost Lake in Central"),
    "Lytle Lake": ("osm", "OSM water 'Lake Lytle'"),
    "Mercer Lake": ("osm", "OSM water 'Mercer Lake'"),
    "Munsel Lake": ("osm", "OSM water 'Munsel Lake'"),
    "North Lake": ("likely", "OSM point 'North Lake'; the schedule gives no district, this one is beside South Lake and Hebo Lake"),
    "Olalla Creek Reservoir": ("osm", "OSM water 'Olalla Reservoir'"),
    "Siltcoos Lake": ("osm", "OSM water 'Siltcoos Lake'"),
    "South Lake": ("likely", "OSM point 'South Lake' beside North Lake and Hebo Lake (another 'South Lake' exists 45 km east)"),
    "Sutton Lake": ("osm", "OSM water 'Sutton Lake'"),
    "Tahoe Lake": ("likely", "OSM point 'Lake Tahoe' in the Tillamook district (the name matches the famous one, so check)"),
    "Town Lake": ("likely", "OSM point 'Town Lake', Tillamook district"),
    "Vernonia Lake": ("osm", "OSM water 'Vernonia Lake'"),
    "Woahink Lake": ("osm", "OSM water 'Woahink Lake'"),
}

FISHERY_HINTS: dict[str, list[str]] = {}  # stocked trout until the owner says otherwise; the weekly report can add species

# Coastal river gauges that reported discharge on the live USGS Water Data API on 2026-10-19 (the steelhead and salmon rivers the Northwest
# report talks about). Tidal and tiny-creek gauges were left out. None is clearly the same water as a stocked lake, so none is linked.
GAUGES: list[tuple[str, str, float, float]] = [
    ("14301000", "Nehalem River near Foss", 45.7040, -123.7554),
    ("14301500", "Wilson River near Tillamook", 45.4759, -123.7251),
    ("14302480", "Trask River above Cedar Creek near Tillamook", 45.4462, -123.7104),
    ("14303600", "Nestucca River near Beaver", 45.2665, -123.8471),
    ("14305500", "Siletz River at Siletz", 44.7151, -123.8873),
    ("14306500", "Alsea River near Tidewater", 44.3860, -123.8318),
    ("14307620", "Siuslaw River near Mapleton", 44.0623, -123.8832),
]
GAUGE_LINKS: dict[str, list[str]] = {}


# Popular rivers (see app/zones/rivers.py): name -> (USGS gauges on it, fishery hints). Every gauge reported flow on the live API on 2026-10-19.
from app.zones.rivers import add_rivers  # noqa: E402

add_rivers(globals(), {
    "Nehalem River": (["14301000"], ["steelhead"]),
    "Wilson River": (["14301500"], ["steelhead"]),
    "Trask River": (["14302480"], ["steelhead"]),
    "Nestucca River": (["14303600"], ["steelhead"]),
    "Siletz River": (["14305500"], ["steelhead"]),
    "Alsea River": (["14306500"], ["steelhead"]),
    "Siuslaw River": (["14307620"], ["steelhead"]),
})
