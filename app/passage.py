"""Which waterbodies are fed by fish counted at a dam or fishway, and what to say about it.

The Tualatin joins the Willamette at West Linn, above Willamette Falls, so adult salmon and steelhead headed for it (and for the other upper-Willamette
rivers listed below) pass the Willamette Falls fishway, which ODFW counts."""
from sqlalchemy.orm import Session

from app.sources import dart

# Rivers above Willamette Falls, whose adult salmon and steelhead pass the fishway ODFW counts. The Clackamas and the Sandy enter below it (or the Columbia),
# so they are NOT here; the Columbia dams' counts would be the right ones for those, and are not added yet.
ABOVE_THE_FALLS = ("Tualatin River", "Willamette River", "Willamette River, Coast Fork", "Middle Fork Willamette River", "South Santiam River", "Molalla River",
                   "Calapooia River", "Santiam River, North Fork", "McKenzie River (above Leaburg Dam)", "McKenzie River (below Leaburg Dam)")
BY_WATERBODY = {name: dart for name in ABOVE_THE_FALLS}


def for_waterbody(session: Session, name: str) -> dict | None:
    mod = BY_WATERBODY.get(name)
    if mod is None:
        return None
    s = mod.summary(session)
    if s is None:
        return None
    return {**s, "note": f"Counted by ODFW at the Willamette Falls fishway (Oregon City), which fish heading for the {name} pass first. Counts run a few days behind, "
                         "are for the whole upper Willamette, and say nothing about how many reach this river or when you can fish for them. Check ODFW's regulations."}
