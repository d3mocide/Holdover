"""Writes the narrative paragraphs of the weekly briefing from the facts in app/briefing.py.

The model reads facts and writes prose; it decides nothing. Each paragraph is checked against the facts it was given (no number, name
or species that is not there), retried once with the offending terms named, and stored together with those facts, the time and the model.
A section whose paragraph fails the check simply has no paragraph and the page shows its facts."""
import json
import logging
from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.briefing import Section, build, monday
from app.http import now_iso
from app.llm.client import LLMClient, LLMUnavailable
from app.llm.explain import guard
from app.llm.prompts import BRIEFING_SYSTEM, BRIEFING_VERSION
from app.llm.schemas import ParagraphResult
from app.models import Generation

log = logging.getLogger("holdover.llm")


def key_for(week: date, zone: str, section: str) -> str:
    return f"{week.isoformat()}:{zone}:{section}"


def write(llm: LLMClient, section: Section) -> str:
    """A grounded paragraph for one section. Raises LLMUnavailable, or ValueError if it cannot be grounded after one retry."""
    facts = "\n".join(f"- {f}" for f in section.facts)
    user = f"Topic: {section.title}\n{section.hint}\nFacts:\n{facts}" if section.hint else f"Topic: {section.title}\nFacts:\n{facts}"
    text = llm.chat_json(BRIEFING_SYSTEM, user, ParagraphResult).text.strip()
    bad = guard(text, facts)
    if bad:
        text = llm.chat_json(BRIEFING_SYSTEM, f"{user}\n\nYour previous text used terms that are not in the facts: {', '.join(sorted(set(bad)))}. "
                             "Write it again using only what the facts say.", ParagraphResult).text.strip()
        bad = guard(text, facts)
    if bad:
        raise ValueError(f"ungrounded terms {sorted(set(bad))}")
    return text


def generate(session: Session, llm: LLMClient, today: date | None = None, zone: str = "willamette") -> dict:
    today = today or date.today()
    week = monday(today)
    out = {"written": 0, "rejected": 0, "llm": "ok"}
    if not llm.configured:
        out["llm"] = "not_configured"
        return out
    for sec in build(session, today, zone):
        if not sec.narrate:
            continue
        try:
            text = write(llm, sec)
        except LLMUnavailable as exc:
            log.warning("briefing: LLM unavailable: %s", exc)
            out["llm"] = "unreachable"
            break
        except ValueError as exc:
            log.warning("briefing: %s paragraph discarded: %s", sec.key, exc)
            out["rejected"] += 1
            continue
        key = key_for(week, zone, sec.key)
        session.execute(delete(Generation).where(Generation.kind == "briefing", Generation.key == key))
        session.add(Generation(kind="briefing", key=key, prompt_version=BRIEFING_VERSION, model=llm.model, generated_at=now_iso(),
                               text=json.dumps({"text": text, "facts": sec.facts})))
        session.commit()
        out["written"] += 1
    return out


def stored(session: Session, week: date, zone: str = "willamette") -> dict[str, dict]:
    """The paragraphs written for this week and zone, by section key, each with the facts it was written from."""
    out = {}
    for g in session.scalars(select(Generation).where(Generation.kind == "briefing", Generation.key.like(f"{week.isoformat()}:{zone}:%"),
                                                      Generation.prompt_version == BRIEFING_VERSION)):
        d = json.loads(g.text)
        out[g.key.split(":", 2)[2]] = {"text": d["text"], "facts": d["facts"], "as_of": g.generated_at, "model": g.model}
    return out
