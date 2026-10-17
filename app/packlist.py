"""Template-driven pack list. Gear suggestions are generic; nothing here states a regulation.
The LLM may only reword the one-line intro (see app/llm/explain.py); the checklist is always the template."""
from datetime import date


def season(d: date) -> str:
    return {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
            6: "summer", 7: "summer", 8: "summer"}.get(d.month, "fall")


def _item(id_: str, label: str, group: str) -> dict:
    return {"id": id_, "label": label, "group": group}


def pack_list(day: date, fishery: str, temp_f: float | None, precip_pct: float | None, wind_mph: float | None,
              kind: str | None = None) -> dict:
    seas = season(day)
    items = [_item("license", "Fishing license and any required tags (confirm what you need on ODFW)", "Before you go"),
             _item("phone", "Charged phone and a way to pay for parking or day-use fees", "Before you go"),
             _item("water", "Water and snacks", "Comfort"),
             _item("first-aid", "Small first-aid kit, line clippers, pliers", "Safety")]
    gear = {
        "trout": [("rod-light", "Light spinning rod and reel (4-6 lb line)"), ("trout-lures", "Small spinners or spoons, hooks, split shot"),
                  ("bait", "Bait or dough bait, bobbers, a small net")],
        "steelhead": [("rod-drift", "Longer drift or spinning rod and reel (10-15 lb line)"),
                      ("steel-lures", "Spinners, drift gear, bobbers and baits, extra leader"),
                      ("net-gaff", "Large net and a fish bonker or release tools")],
        "warmwater": [("rod-med", "Medium spinning or baitcasting rod"), ("ww-lures", "Soft plastics, jigs, crankbaits, hooks and weights"),
                      ("pol", "Polarized sunglasses"), ("net-ww", "Net and fish grips")],
    }.get(fishery, [])
    items += [_item(i, l, "Gear") for i, l in gear]
    if kind == "river" or fishery == "steelhead":
        items.append(_item("waders", "Waders or wading boots with good traction, and a wading staff", "Gear"))
        items.append(_item("pfd", "Life jacket if you'll be near fast or deep water", "Safety"))
    cold = temp_f is not None and temp_f < 45 or seas == "winter"
    warm = temp_f is not None and temp_f >= 80
    if cold:
        items += [_item("layers", "Warm layers, hat and gloves", "Clothing"), _item("thermos", "Thermos of something hot", "Comfort")]
    else:
        items.append(_item("layers", "Layers you can add or shed", "Clothing"))
    if warm:
        items += [_item("sun", "Sunscreen, hat and sunglasses", "Comfort"), _item("water2", "Extra water", "Comfort")]
    if precip_pct is not None and precip_pct >= 30 or seas in ("fall", "winter", "spring") and precip_pct is None:
        items.append(_item("rain", "Rain jacket", "Clothing"))
    if wind_mph is not None and wind_mph >= 15:
        items.append(_item("wind", "Windbreaker; plan for casting into wind", "Clothing"))
    if seas in ("summer",):
        items.append(_item("bug", "Insect repellent", "Comfort"))
    bits = []
    if temp_f is not None:
        bits.append(f"{temp_f:.0f}F")
    if precip_pct is not None:
        bits.append(f"{precip_pct:.0f}% chance of rain")
    if wind_mph is not None:
        bits.append(f"wind {wind_mph:.0f} mph")
    intro = f"Pack for a {seas} day on the water" + (f": {', '.join(bits)}." if bits else ". No forecast is cached, so check conditions before you leave.")
    return {"intro": intro, "season": seas, "items": items}
