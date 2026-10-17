"""LLM rewording of scored facts. Text is cached in `generation`; the API falls back to the template
whenever there is no cached text (LLM never configured, down, or its output failed the guard)."""
import hashlib
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.http import now_iso
from app.llm.client import LLMClient, LLMUnavailable
from app.llm.prompts import EXPLAIN_SYSTEM, EXPLAIN_VERSION, PACK_SYSTEM, PACK_VERSION
from app.llm.schemas import TextResult
from app.llm.summarize import ungrounded_terms
from app.models import Generation

log = logging.getLogger("holdover.llm")
SPECIES = ("trout", "steelhead", "salmon", "coho", "chinook", "bass", "walleye", "panfish", "crappie", "bluegill",
           "shad", "perch", "catfish", "kokanee", "rainbow", "cutthroat")


def guard(text: str, source: str) -> list[str]:
    """Numbers, proper nouns and species named in `text` that are not in `source` (empty = grounded)."""
    low = source.lower()
    bad = ungrounded_terms(text, source)
    bad += [w for w in SPECIES if w in text.lower() and w not in low]
    return bad


def _key(*parts: str, facts: str) -> str:
    return ":".join(parts) + ":" + hashlib.sha1(facts.encode()).hexdigest()[:12]


def cached_text(session: Session, kind: str, key: str, version: str) -> Generation | None:
    return session.scalar(select(Generation).where(Generation.kind == kind, Generation.key == key,
                                                   Generation.prompt_version == version))


def explain_key(wb_id: int, day: str, fishery: str, facts: str) -> str:
    return _key(str(wb_id), day, fishery, facts=facts)


def generate(session: Session, llm: LLMClient, kind: str, key: str, version: str, system: str, user: str,
             source: str) -> str | None:
    """One guarded generation. Returns the text, or None if rejected. Raises LLMUnavailable if down."""
    if cached_text(session, kind, key, version):
        return cached_text(session, kind, key, version).text
    try:
        out = llm.chat_json(system, user, TextResult).text.strip()
    except ValueError as exc:
        log.warning("%s rejected (invalid output): %s", kind, exc)
        return None
    bad = guard(out, source)
    if bad:
        log.warning("%s rejected, ungrounded terms %s", kind, bad)
        return None
    session.add(Generation(kind=kind, key=key, text=out, model=llm.model, prompt_version=version, generated_at=now_iso()))
    session.commit()
    return out


def generate_explanations(session: Session, llm: LLMClient, day, fishery: str, limit: int = 15) -> dict:
    from app.planner import facts_text, rank
    out = {"generated": 0, "rejected": 0, "llm": "ok"}
    if not llm.configured:
        return {**out, "llm": "not_configured"}
    for spot in rank(session, day, fishery)[:limit]:
        facts = facts_text(spot.facts)
        try:
            text = generate(session, llm, "explain", explain_key(spot.wb.id, day.isoformat(), fishery, facts),
                            EXPLAIN_VERSION, EXPLAIN_SYSTEM, f"Spot: {spot.wb.name}\nFacts:\n{facts}", f"{spot.wb.name}\n{facts}")
        except LLMUnavailable:
            out["llm"] = "unreachable"
            break
        out["generated" if text else "rejected"] += 1
    return out


def generate_pack_intros(session: Session, llm: LLMClient, day, fishery: str, limit: int = 10) -> dict:
    """LLM rewording of the pack-list intro only. The checklist itself is always the template."""
    from app.conditions import conditions
    from app.packlist import pack_list
    from app.planner import rank, wind_mph
    out = {"generated": 0, "rejected": 0}
    if not llm.configured:
        return out
    for spot in rank(session, day, fishery)[:limit]:
        w = (conditions(session, spot.wb, day)["weather"] or {}).get("day") or {}
        base = pack_list(day, fishery, w.get("temp_f"), w.get("precip_pct"), wind_mph(w.get("wind")), spot.wb.kind)["intro"]
        try:
            text = generate(session, llm, "pack", _key(str(spot.wb.id), day.isoformat(), fishery, facts=base), PACK_VERSION,
                            PACK_SYSTEM, f"Intro: {base}", base)
        except LLMUnavailable:
            break
        out["generated" if text else "rejected"] += 1
    return out
