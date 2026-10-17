from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Waterbody, WaterbodyAlias
from app.normalize import normalize_alias


def resolve_alias(session: Session, raw_label: str, source: str) -> WaterbodyAlias:
    """Find or create the alias row. New aliases are unconfirmed; a fuzzy *proposal* is stored for
    the admin queue, but only confirmed aliases ever produce map pins."""
    key = normalize_alias(raw_label)
    alias = session.scalar(
        select(WaterbodyAlias).where(WaterbodyAlias.alias_text == key, WaterbodyAlias.source == source)
    )
    if alias is not None:
        return alias
    alias = WaterbodyAlias(alias_text=key, source=source, confirmed=0)
    best, score = None, 0.0
    for wb in session.scalars(select(Waterbody)):
        s = SequenceMatcher(None, key, normalize_alias(wb.name)).ratio()
        if s > score:
            best, score = wb, s
    if best is not None and score >= 0.6:
        alias.waterbody_id = best.id  # proposal only: confirmed stays 0
        alias.proposed_confidence = round(score, 2)
    session.add(alias)
    session.flush()
    return alias
