"""Which waterbodies are fed by fish counted at a dam or fishway, and what to say about it.

Only the Tualatin so far (the pilot). The Tualatin joins the Willamette at West Linn, above Willamette Falls, so adult salmon and steelhead headed
for it pass the Willamette Falls fishway, which ODFW counts. Other upper-Willamette rivers can be added here the same way."""
from sqlalchemy.orm import Session

from app.sources import dart

BY_WATERBODY = {"Tualatin River": dart}


def for_waterbody(session: Session, name: str) -> dict | None:
    mod = BY_WATERBODY.get(name)
    if mod is None:
        return None
    s = mod.summary(session)
    if s is None:
        return None
    return {**s, "note": "Counted by ODFW at the Willamette Falls fishway (Oregon City), which fish heading for the Tualatin pass first. Counts run a few days behind, "
                         "are for the whole upper Willamette, and say nothing about how many reach this river or when you can fish for them. Check ODFW's regulations."}
