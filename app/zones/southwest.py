"""Southwest zone (ODFW field_zone_value=5): the Rogue and Umpqua country and the southern coast lakes.

Names and labels come from the zone's stocking schedule (fetched 2026-10-18; 43 labels, 43 waterbodies; ODFW offices: Central Point, Roseburg, Charleston, Gold Beach, Coos Bay). Pins
come from same-named features in the OpenStreetMap data inside the basemap (scripts/propose_zone.py). Nothing here is from memory. PINS records how each was
found; a waterbody with no pin is listed under "needs coordinates" and is never drawn. Only unambiguous same-name matches were pinned: a name with several far-apart
candidates, or with no same-named feature, is left empty."""

ZONE = "southwest"
LABEL = "Southwest"
STOCKING_VALUE = 5
REPORT_KEY = "sw"

# (canonical name, kind, lat, lon, [stocking-schedule labels])
SEED: list[tuple[str, str, float | None, float | None, list[str]]] = [
    ("Applegate Reservoir", "reservoir", 42.03331, -123.14564, ["APPLEGATE RESERVOIR"]),
    ("Arizona Pond", "pond", 42.61659, -124.39533, ["ARIZONA POND"]),
    ("Ben Irving Reservoir", "reservoir", 43.04610, -123.57497, ["BEN IRVING RESERVOIR"]),
    ("Bluebill Lake", "lake", 43.44712, -124.26061, ["BLUEBILL LAKE"]),
    ("Bradley Lake", "lake", 43.06531, -124.42721, ["BRADLEY LAKE"]),
    ("Burma Pond (L)", "pond", None, None, ["BURMA POND L"]),
    ("Butterfield Lake", "lake", 43.52018, -124.22219, ["BUTTERFIELD LAKE"]),
    ("Clearwater Bay", "lake", None, None, ["CLEARWATER BAY"]),
    ("Cooper Creek Reservoir", "reservoir", None, None, ["COOPER CREEK RESERVOIR"]),
    ("Eel Lake", "lake", 43.61472, -124.17324, ["EEL LAKE"]),
    ("Emigrant Reservoir", "reservoir", 42.14791, -122.61546, ["EMIGRANT RESERVOIR"]),
    ("Empire Lake, Lower", "lake", None, None, ["EMPIRE LAKE LWR"]),
    ("Empire Lake, Upper", "lake", 43.39597, -124.25588, ["EMPIRE LAKE UPPER"]),
    ("Expo Pond 1 (Rogue)", "pond", None, None, ["EXPO POND 1 ROGUE"]),
    ("Fish Lake (Southwest)", "lake", 42.38581, -122.33495, ["FISH LAKE"]),
    ("Floras Lake", "lake", 42.89361, -124.50430, ["FLORAS LAKE"]),
    ("Galesville Reservoir", "reservoir", 42.83746, -123.15811, ["GALESVILLE RESERVOIR"]),
    ("Garrison Lake", "lake", 42.75337, -124.50521, ["GARRISON LAKE"]),
    ("Hemlock Lake (Hemlock Meadow Reservoir)", "reservoir", None, None, ["HEMLOCK LAKE HEMLOCK MEADOW RESERVOIR"]),
    ("Howard Prairie Reservoir", "reservoir", 42.23668, -122.40594, ["HOWARD PRAIRIE RESERVOIR"]),
    ("Hyatt Reservoir", "reservoir", 42.18596, -122.44877, ["HYATT RESERVOIR"]),
    ("Johnsons Mill Pond", "pond", None, None, ["JOHNSONS MILL POND"]),
    ("Laird Lake", "lake", None, None, ["LAIRD LAKE"]),
    ("Lake in the Woods", "lake", None, None, ["LAKE IN THE WOODS"]),
    ("Lake Marie", "lake", 43.65911, -124.19461, ["LAKE MARIE"]),
    ("Lemolo Reservoir", "reservoir", 43.31135, -122.18010, ["LEMOLO RESERVOIR"]),
    ("Libby Pond", "pond", None, None, ["LIBBY POND"]),
    ("Loon Lake", "lake", 43.58718, -123.83785, ["LOON LAKE"]),
    ("Lost Creek Reservoir", "reservoir", None, None, ["LOST CREEK RESERVOIR"]),
    ("Medco Pond", "pond", None, None, ["MEDCO POND"]),
    ("Plat I Reservoir", "reservoir", None, None, ["PLAT I RESERVOIR"]),
    ("Powers Pond", "pond", None, None, ["POWERS POND"]),
    ("Red Top Lake", "lake", None, None, ["RED TOP LAKE"]),
    ("Reinhart Park Pond", "pond", None, None, ["REINHART PARK POND"]),
    ("Rogue River (above Lost Creek)", "river", None, None, ["ROGUE RIVER ABOVE LOST CREEK"]),
    ("Saunders Lake", "lake", 43.53469, -124.21885, ["SAUNDERS LAKE"]),
    ("Lake Selmac", "lake", 42.26066, -123.57802, ["SELMAC LAKE"]),
    ("Spalding Pond", "pond", None, None, ["SPALDING POND"]),
    ("SRU Lake (formerly USFS Lake)", "lake", None, None, ["SRU LAKE FORMERLY USFS LAKE"]),
    ("Tenmile Lake, North", "lake", 43.59604, -124.11790, ["TENMILE LAKE NORTH"]),
    ("Tenmile Lake, South", "lake", 43.55959, -124.13618, ["TENMILE LAKE SOUTH"]),
    ("Weaver Road Pond", "pond", None, None, ["WEAVER ROAD POND"]),
    ("Willow Lake (formerly Willow Creek Reservoir)", "reservoir", None, None, ["WILLOW LAKE FORMER WILLOW CREEK RESERVOIR"]),
]

# "osm" = a same-named water feature (polygon or labelled lake). "likely" = a same-named point of interest or a choice between candidates: check these.
PINS: dict[str, tuple[str, str]] = {
    "Applegate Reservoir": ("osm", "OSM water 'Applegate Lake'"),
    "Arizona Pond": ("likely", "OSM point 'Arizona Pond' (point of interest)"),
    "Ben Irving Reservoir": ("osm", "OSM water 'Ben Irving Reservoir'"),
    "Bluebill Lake": ("likely", "OSM point 'Bluebill Lake' (point of interest)"),
    "Bradley Lake": ("likely", "OSM point 'Bradley Lake' (point of interest)"),
    "Butterfield Lake": ("likely", "OSM point 'Butterfield Lake' (point of interest)"),
    "Eel Lake": ("osm", "OSM water 'Eel Lake'"),
    "Emigrant Reservoir": ("osm", "OSM water 'Emigrant Lake' (two points 1.4 km apart on the same lake; took the first)"),
    "Empire Lake, Upper": ("likely", "OSM point 'Upper Empire Lake' (point of interest)"),
    "Fish Lake (Southwest)": ("likely", "three OSM 'Fish Lake' features in the district; took the Jackson County one on the water layer"),
    "Floras Lake": ("osm", "OSM water 'Floras Lake'"),
    "Galesville Reservoir": ("osm", "OSM water 'Galesville Reservoir'"),
    "Garrison Lake": ("osm", "OSM water 'Garrison Lake'"),
    "Howard Prairie Reservoir": ("osm", "OSM water 'Howard Prairie Lake'"),
    "Hyatt Reservoir": ("osm", "OSM water 'Hyatt Reservoir'"),
    "Lake Marie": ("likely", "OSM point 'Lake Marie' (point of interest); another 'Marie Lake' exists in the Cascades"),
    "Lemolo Reservoir": ("osm", "OSM water 'Lemolo Lake'"),
    "Loon Lake": ("osm", "two OSM 'Loon Lake' features; took the water-layer one in the Umpqua basin"),
    "Saunders Lake": ("osm", "OSM water 'Saunders Lake'"),
    "Lake Selmac": ("osm", "OSM water 'Lake Selmac'"),
    "Tenmile Lake, North": ("osm", "OSM water 'North Tenmile Lake'"),
    "Tenmile Lake, South": ("osm", "OSM water 'South Tenmile Lake'"),
}

FISHERY_HINTS: dict[str, list[str]] = {}  # stocked trout until the owner says otherwise; the weekly report can add species

# USGS gauges (site, name, lat, lon) that reported discharge on the live Water Data API on 2026-10-19. None is clearly the same water as a stocked lake or pond.
GAUGES: list[tuple[str, str, float, float]] = [
    ("14372300", "Rogue River near Agness", 42.59278, -124.06200),
    ("14339000", "Rogue River at Dodge Bridge near Eagle Point", 42.52485, -122.84282),
    ("14361500", "Rogue River at Grants Pass", 42.43040, -123.31784),
    ("14369500", "Applegate River near Wilderville", 42.35401, -123.40673),
    ("14378200", "Illinois River near Agness", 42.54488, -124.05191),
    ("14400000", "Chetco River near Brookings", 42.12344, -124.18731),
    ("14321000", "Umpqua River near Elkton", 43.58595, -123.55537),
    ("14319500", "North Umpqua River at Winchester", 43.27097, -123.41154),
    ("14312330", "South Umpqua River at Melrose", 43.25176, -123.44770),
]
GAUGE_LINKS: dict[str, list[str]] = {}


# Popular rivers (see app/zones/rivers.py): name -> (USGS gauges on it, fishery hints). Every gauge reported flow on the live API on 2026-10-19.
from app.zones.rivers import add_rivers  # noqa: E402

add_rivers(globals(), {
    "Rogue River": (["14372300", "14339000", "14361500"], ["steelhead"]),
    "Umpqua River": (["14321000"], ["steelhead", "warmwater"]),
    "North Umpqua River": (["14319500"], ["steelhead"]),
    "South Umpqua River": (["14312330"], ["warmwater"]),
    "Applegate River": (["14369500"], ["steelhead"]),
    "Illinois River": (["14378200"], ["steelhead"]),
    "Chetco River": (["14400000"], ["steelhead"]),
})
