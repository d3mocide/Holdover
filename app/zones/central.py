"""Central zone (ODFW field_zone_value=1): Deschutes, Crooked and Metolius country, the Cascade lakes and the Mt Hood east side.

Names and labels come from the zone's stocking schedule (fetched 2026-10-18; 36 labels, 35 waterbodies: LAVA LAKE B and LAVA LAKE L
are one water). Pins come from same-named features in the OpenStreetMap data inside the basemap (scripts/propose_zone.py), narrowed
to the label's ODFW district. Nothing here is from memory. PINS records how each was found; a waterbody with no pin is listed under
"needs coordinates" and is never drawn."""

ZONE = "central"
LABEL = "Central"
STOCKING_VALUE = 1
REPORT_KEY = "central"

# (canonical name, kind, lat, lon, [stocking-schedule labels])
SEED: list[tuple[str, str, float | None, float | None, list[str]]] = [
    ("Antelope Flat Reservoir", "reservoir", 44.00567, -120.37997, ["ANTELOPE FLAT RESERVOIR"]),
    ("Baker Pond", "pond", None, None, ["BAKER POND"]),
    ("Bikini Pond", "pond", None, None, ["BIKINI POND"]),
    ("Century Gravel Pond", "pond", None, None, ["CENTURY GRAVEL POND"]),
    ("Clear Lake (Wasco)", "lake", 45.18260, -121.70607, ["CLEAR LAKE"]),
    ("Cottonwood Pit", "pond", None, None, ["COTTONWOOD PIT"]),
    ("Cultus Lake", "lake", 43.83804, -121.86247, ["CULTUS LAKE B"]),
    ("Deer Lake", "lake", 43.81991, -121.89392, ["DEER LAKE"]),
    ("Devils Lake", "lake", 44.03486, -121.76220, ["DEVILS LAKE"]),
    ("East Lake", "lake", None, None, ["EAST LAKE"]),
    ("Fall River", "river", None, None, ["FALL RIVER"]),
    ("Frog Lake", "lake", 45.21868, -121.69476, ["FROG LAKE"]),
    ("Hosmer Lake", "lake", 43.96759, -121.78181, ["HOSMER LAKE"]),
    ("Kingsley Reservoir (Upper)", "reservoir", 45.63781, -121.67857, ["KINGSLEY RESERVOIR UPPER"]),
    ("Laurance Lake", "lake", 45.45931, -121.66591, ["LAURANCE LAKE"]),
    ("Lava Lake", "lake", 43.92112, -121.77301, ["LAVA LAKE B", "LAVA LAKE L"]),
    ("Lost Lake", "lake", 45.48934, -121.82362, ["LOST LAKE"]),
    ("Metolius Pond", "pond", None, None, ["METOLIUS POND"]),
    ("Middle Fork Pond (Hood River)", "pond", None, None, ["MIDDLE FORK POND HOOD RIVER"]),
    ("Ochoco Reservoir", "reservoir", 44.30373, -120.69674, ["OCHOCO RESERVOIR"]),
    ("Olallie Lake", "lake", 44.80693, -121.78740, ["OLALLIE LAKE"]),
    ("Paulina Lake", "lake", 43.71940, -121.25987, ["PAULINA LAKE"]),
    ("Pine Hollow Reservoir", "reservoir", 45.24772, -121.29441, ["PINE HOLLOW RESERVOIR"]),
    ("Pine Nursery Pond", "pond", 44.09113, -121.26812, ["PINE NURSERY POND"]),
    ("Prineville Fishing Pond", "pond", None, None, ["PRINEVILLE FISHING POND"]),
    ("Redmond Fireman South Pond", "pond", None, None, ["REDMOND FIREMAN SOUTH POND"]),
    ("Rock Creek Reservoir", "reservoir", None, None, ["ROCK CREEK RESERVOIR"]),
    ("Shevlin Pond", "pond", 44.08864, -121.36776, ["SHEVLIN POND"]),
    ("Smock Prairie Reservoir", "reservoir", 45.15030, -121.37647, ["SMOCK PRAIRIE RESERVOIR"]),
    ("Sprague Pit Pond", "pond", None, None, ["SPRAGUE PIT POND"]),
    ("Taylor Lake", "lake", 45.64269, -121.20711, ["TAYLOR LAKE"]),
    ("Three Creeks Lake", "lake", None, None, ["THREE CREEKS LAKE"]),
    ("Twin Lake, North", "lake", 43.72761, -121.76652, ["TWIN LAKE NORTH"]),
    ("Twin Lake, South", "lake", 43.71399, -121.76633, ["TWIN LAKE SOUTH"]),
    ("Walton Lake", "lake", 44.43555, -120.33555, ["WALTON LAKE"]),
]

# How each coordinate was found. "osm" = a same-named water feature inside the label's ODFW district (unique, or the only one of
# its kind there). "likely" = a judgement between candidates, or a park or town label standing in for a pond: check these.
# "none" = no same-named feature in that district, so no pin.
PINS: dict[str, tuple[str, str]] = {
    "Antelope Flat Reservoir": ("likely", "two same-named OSM points about 6 km apart; took the one on the water layer"),
    "Clear Lake (Wasco)": ("osm", "OSM 'Clear Lake', Mt Hood side"),
    "Cultus Lake": ("osm", "OSM 'Cultus Lake'"),
    "Deer Lake": ("osm", "OSM 'Deer Lake', Deschutes side"),
    "Devils Lake": ("osm", "two OSM 'Devils Lake' features; took the Deschutes one on the Cascade Lakes side"),
    "Frog Lake": ("likely", "three OSM 'Frog Lake' features in the district; took the one beside Clear Lake (Wasco)"),
    "Hosmer Lake": ("osm", "OSM 'Hosmer Lake'"),
    "Kingsley Reservoir (Upper)": ("osm", "OSM 'Kingsley Reservoir' (the label says Upper)"),
    "Laurance Lake": ("osm", "OSM 'Laurance Lake'"),
    "Lava Lake": ("likely", "two OSM 'Lava Lake' features; took the Cascade Lakes one (ODFW's Bend district)"),
    "Lost Lake": ("osm", "OSM 'Lost Lake', Hood River County"),
    "Ochoco Reservoir": ("osm", "OSM 'Ochoco Reservoir'"),
    "Olallie Lake": ("osm", "OSM 'Olallie Lake'"),
    "Paulina Lake": ("osm", "OSM 'Paulina Lake'"),
    "Pine Hollow Reservoir": ("osm", "OSM 'Pine Hollow Reservoir'"),
    "Pine Nursery Pond": ("likely", "OSM 'Pine Nursery Park' (the pond is in the park)"),
    "Shevlin Pond": ("likely", "OSM 'Shevlin Park' (the pond is in the park)"),
    "Smock Prairie Reservoir": ("likely", "OSM 'Smock Reservoir', 1 km from 'Smock Prairie'"),
    "Taylor Lake": ("osm", "OSM 'Taylor Lake'"),
    "Twin Lake, North": ("osm", "OSM 'North Twin Lake'"),
    "Twin Lake, South": ("osm", "OSM 'South Twin Lake'"),
    "Walton Lake": ("osm", "OSM 'Walton Lake'"),
}

FISHERY_HINTS: dict[str, list[str]] = {}  # stocked trout only until the owner says otherwise; the weekly report can add species

# USGS gauges (site, name, lat, lon). All eight were reporting discharge on the live Water Data API on 2026-10-19, which is how they
# were chosen: sensors whose last reading is from 1991 (the upper Deschutes at La Pine, Benham Falls and Bend) are left out, and so
# are the John Day (Northeast zone) and the Columbia.
GAUGES: list[tuple[str, str, float, float]] = [
    ("14076500", "Deschutes River near Culver", 44.49873, -121.32116),
    ("14087400", "Crooked River below Opal Springs near Culver", 44.49234, -121.29838),
    ("14091500", "Metolius River near Grandview", 44.62623, -121.48394),
    ("14092500", "Deschutes River near Madras", 44.72595, -121.24699),
    ("14097100", "Warm Springs River near Kahneeta Hot Springs", 44.85651, -121.14977),
    ("14101500", "White River below Tygh Valley", 45.24172, -121.09514),
    ("14103000", "Deschutes River at Moody near Biggs", 45.62207, -120.90562),
    ("14120000", "Hood River at Tucker Bridge near Hood River", 45.65450, -121.54880),
]
# None of them is clearly the same water as a stocked lake or pond in this zone's schedule, so no waterbody is linked (and no
# ranking depends on them). They appear on the Gauges page, the map and the briefing.
GAUGE_LINKS: dict[str, list[str]] = {}


# Popular rivers (see app/zones/rivers.py): name -> (USGS gauges on it, fishery hints). Every gauge reported flow on the live API on 2026-10-19.
from app.zones.rivers import add_rivers  # noqa: E402

add_rivers(globals(), {
    "Deschutes River": (["14076500", "14092500", "14103000"], ["steelhead"]),
    "Crooked River": (["14087400"], []),
    "Metolius River": (["14091500"], []),
    "Hood River": (["14120000"], ["steelhead"]),
})
