"""Northeast zone (ODFW field_zone_value=2): the Blue Mountains, John Day basin and Wallowa country.

Names and labels come from the zone's stocking schedule (fetched 2026-10-18; 49 labels, 49 waterbodies; ODFW offices: John Day, La Grande, Enterprise). Pins
come from same-named features in the OpenStreetMap data inside the basemap (scripts/propose_zone.py). Nothing here is from memory. PINS records how each was
found; a waterbody with no pin is listed under "needs coordinates" and is never drawn. Only unambiguous same-name matches were pinned: a name with several far-apart
candidates, or with no same-named feature, is left empty."""

ZONE = "northeast"
LABEL = "Northeast"
STOCKING_VALUE = 2
REPORT_KEY = "ne"

# (canonical name, kind, lat, lon, [stocking-schedule labels])
SEED: list[tuple[str, str, float | None, float | None, list[str]]] = [
    ("Aldrich Ponds", "lake", None, None, ["ALDRICH PDS"]),
    ("Anson Wright Pond", "pond", None, None, ["ANSON WRIGHT POND"]),
    ("Brandon South Pond (JD Screen Shop Pond)", "pond", None, None, ["BRANDON SOUTH POND JD SCREEN SP POND"]),
    ("Bull Prairie Reservoir", "reservoir", 44.97437, -119.66316, ["BULL PRAIRIE RESERVOIR"]),
    ("Cutsforth Pond", "pond", None, None, ["CUTSFORTH POND"]),
    ("Fish Lake (Northeast)", "lake", 45.04677, -117.09240, ["FISH LAKE"]),
    ("Grande Ronde Lake", "lake", 44.97816, -118.24368, ["GRANDE RONDE LAKE"]),
    ("Hat Rock Pond", "pond", 45.91696, -119.17056, ["HAT ROCK POND"]),
    ("Hog Creek Pond", "pond", None, None, ["HOG CREEK POND"]),
    ("Holliday Park Pond", "pond", None, None, ["HOLLIDAY PARK POND"]),
    ("Honeymoon Pond", "pond", None, None, ["HONEYMOON POND"]),
    ("Hunter Pond (Starkey Forest Ponds)", "pond", None, None, ["HUNTER POND STARKEY FOREST PDS"]),
    ("Jubilee Lake", "lake", 45.83197, -117.96017, ["JUBILEE LAKE"]),
    ("Kinney Lake", "lake", None, None, ["KINNEY LAKE"]),
    ("Ladd Peach Pond", "pond", None, None, ["LADD PEACH POND"]),
    ("Long Creek Pond", "pond", None, None, ["LONG CREEK POND"]),
    ("Lost Lake (Northeast)", "lake", None, None, ["LOST LAKE"]),
    ("Luger Pond", "pond", None, None, ["LUGER POND"]),
    ("Magone Lake", "lake", 44.54886, -118.91197, ["MAGONE LAKE"]),
    ("Marr Pond", "pond", None, None, ["MARR POND"]),
    ("McGraw Pond", "pond", None, None, ["MCGRAW POND"]),
    ("McNary Channel Ponds", "lake", None, None, ["MCNARY CHANNEL PDS"]),
    ("Morgan Lake", "lake", 45.30152, -118.13625, ["MORGAN LAKE"]),
    ("Morrow County OHV Park Pond 1 (Trout Lake)", "pond", None, None, ["MORROW CO OHV PARK POND #1 TROUT LAKE"]),
    ("Morrow County OHV Park Pond 2 (Red Rock)", "pond", None, None, ["MORROW CO OHV PARK POND #2 RED ROCK"]),
    ("Morrow County OHV Park Pond 3 (OBrien)", "pond", None, None, ["MORROW CO OHV PARK POND #3 O BRIEN"]),
    ("Morrow County OHV Park Pond 4 (Wilson)", "pond", None, None, ["MORROW CO OHV PARK POND #4 WILSON"]),
    ("Olive Lake", "lake", 44.78195, -118.60287, ["OLIVE LAKE"]),
    ("Penland Lake", "lake", None, None, ["PENLAND LAKE"]),
    ("Roulet Pond", "pond", None, None, ["ROULET POND"]),
    ("Rowe Creek Reservoir", "reservoir", None, None, ["ROWE CREEK RESERVOIR"]),
    ("Salt Creek Summit Pond", "pond", None, None, ["SALT CREEK SUMMIT POND"]),
    ("Seventh Street Pond", "pond", None, None, ["SEVENTH ST POND"]),
    ("Tatone Pond", "pond", None, None, ["TATONE POND"]),
    ("Teepee Pond", "pond", None, None, ["TEEPEE POND"]),
    ("Trout Farm Pond", "pond", None, None, ["TROUT FARM POND"]),
    ("Twin Ponds", "lake", None, None, ["TWIN PDS"]),
    ("Umapine Pond", "pond", None, None, ["UMAPINE POND"]),
    ("Umatilla Forest Ponds, North", "lake", None, None, ["UMATILLA FOREST PDS NORTH"]),
    ("Umatilla Forest Ponds, South", "lake", None, None, ["UMATILLA FOREST PDS SOUTH"]),
    ("Victor Pond", "pond", None, None, ["VICTOR POND"]),
    ("Walla Walla Forest Ponds, North", "lake", None, None, ["WALLA WALLA FOREST PDS NORTH"]),
    ("Walla Walla Forest Ponds, South", "lake", None, None, ["WALLA WALLA FOREST PDS SOUTH"]),
    ("Wallowa Lake", "lake", 45.30805, -117.20753, ["WALLOWA LAKE"]),
    ("Wallowa Wildlife Pond (Weavers Pond)", "pond", None, None, ["WALLOWA WLDLIFE POND WEAVRS POND"]),
    ("Weston Highway Pond", "pond", None, None, ["WESTON HIGHWAY POND"]),
    ("Wildcat Pond", "pond", None, None, ["WILDCAT POND"]),
    ("Willow Creek", "river", None, None, ["WILLOW CREEK"]),
    ("Willow Creek Reservoir", "reservoir", None, None, ["WILLOW CREEK RESERVOIR"]),
]

# "osm" = a same-named water feature (polygon or labelled lake). "likely" = a same-named point of interest or a choice between candidates: check these.
PINS: dict[str, tuple[str, str]] = {
    "Bull Prairie Reservoir": ("likely", "OSM point 'Bull Prairie Lake' (point of interest)"),
    "Fish Lake (Northeast)": ("osm", "OSM water 'Fish Lake' in the La Grande district"),
    "Grande Ronde Lake": ("likely", "OSM point 'Grande Ronde Lake' (point of interest)"),
    "Hat Rock Pond": ("likely", "OSM point 'Hat Rock' (the state park holds the pond)"),
    "Jubilee Lake": ("osm", "OSM water 'Jubilee Lake'"),
    "Magone Lake": ("osm", "OSM water 'Magone Lake'"),
    "Morgan Lake": ("osm", "OSM water 'Morgan Lake'"),
    "Olive Lake": ("osm", "two OSM 'Olive Lake' features; took the Grant County one on the water layer"),
    "Wallowa Lake": ("osm", "OSM water 'Wallowa Lake'"),
}

FISHERY_HINTS: dict[str, list[str]] = {}  # stocked trout until the owner says otherwise; the weekly report can add species

# USGS gauges (site, name, lat, lon) that reported discharge on the live Water Data API on 2026-10-19. None is clearly the same water as a stocked lake or pond.
GAUGES: list[tuple[str, str, float, float]] = [
    ("13333000", "Grande Ronde River at Troy", 45.94570, -117.45101),
    ("13331500", "Minam River at Minam", 45.61987, -117.72659),
    ("14046000", "North Fork John Day River at Monument", 44.81492, -119.43200),
    ("14038530", "John Day River near John Day", 44.41849, -118.90634),
    ("14048000", "John Day River at McDonald Ferry", 45.58763, -120.40949),
    ("14033500", "Umatilla River near Umatilla", 45.90269, -119.32708),
]
GAUGE_LINKS: dict[str, list[str]] = {}
