"""Rivers as waterbodies, declared once per zone: a name, the USGS gauges that are on it, and what anglers go there for.

A river has no schedule to take a name from, so each one here was chosen as a river many anglers fish (a judgement, listed in the owner's docs), and was
checked against the live USGS API: every gauge reports discharge now. A river's pin is the position of its first gauge (a river is long: move it with Settings,
Place pins). `fishery` is a seed hint, "from general knowledge, unverified", like the others in this app."""


def add_rivers(ns: dict, rivers: dict[str, tuple[list[str], list[str]]]) -> None:
    """ns is a zone module's globals (or app.seed's): it must have GAUGES, SEED and GAUGE_LINKS. `rivers`: name -> (gauge site numbers, fisheries)."""
    by_site = {g[0]: g for g in ns["GAUGES"]}
    for name, (sites, fisheries) in rivers.items():
        lead = by_site[sites[0]]  # a KeyError here means a river points at a gauge the zone does not define: fail loudly at import
        for s in sites:
            assert s in by_site, f"{name}: gauge {s} is not in this zone's GAUGES"
        ns["SEED"].append((name, "river", lead[2], lead[3], []))
        ns["GAUGE_LINKS"][name] = list(sites)
        if fisheries:
            ns["FISHERY_HINTS"][name] = list(fisheries)
        note = f"pinned at the USGS gauge '{lead[1]}'; a river is long, so move the pin to where you fish"
        if "PINS" in ns:
            ns["PINS"][name] = ("gauge", note)
        else:
            ns["COORD_UPDATES"][name] = (lead[2], lead[3], "gauge")
