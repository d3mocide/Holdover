import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.http import now_iso
from app.llm.client import LLMClient
from app.llm.prompts import EXTRACT_SYSTEM, EXTRACT_VERSION
from app.llm.schemas import ExtractionResult
from app.models import Generation, Report, ReportItem, Waterbody, WaterbodyAlias
from app.normalize import name_key as _key
from app.sources.odfw_report import report_text

def _ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def match_waterbody(session: Session, raw: str) -> int | None:
    """Exact match only, after dropping generic words (River, Lake, Fork...). 'North Santiam' matches
    'Santiam River, North Fork' but 'Willamette River' does not match the Coast Fork. Anything
    looser goes to the human review queue."""
    key = _key(raw)
    if not key:
        return None
    hits = set()
    for wb in session.scalars(select(Waterbody)):
        if _key(wb.name) == key:
            hits.add(wb.id)
    for a in session.scalars(select(WaterbodyAlias).where(WaterbodyAlias.confirmed == 1)):
        if a.waterbody_id and _key(a.alias_text) == key:
            hits.add(a.waterbody_id)
    return hits.pop() if len(hits) == 1 else None


def extracted(session: Session, report_id: int) -> bool:
    return session.scalar(select(Generation.id).where(
        Generation.kind == "extract", Generation.key == str(report_id), Generation.prompt_version == EXTRACT_VERSION
    )) is not None


def extract_report(session: Session, report: Report, llm: LLMClient) -> dict:
    """Idempotent. Raises LLMUnavailable (nothing written) or ValueError (bad model output)."""
    if extracted(session, report.id):
        return {"skipped": True}
    text = report_text(session, report)
    result = llm.chat_json(EXTRACT_SYSTEM, f"Zone: {report.zone}\n\nText:\n{text}", ExtractionResult)
    haystack = _ws(text)
    kept = rejected = 0
    for it in result.items:
        grounded = _ws(it.source_sentence) in haystack
        session.add(ReportItem(
            report_id=report.id, waterbody_id=match_waterbody(session, it.waterbody_raw) if grounded else None,
            waterbody_raw=it.waterbody_raw, species=", ".join(it.species), rating=it.rating, note=it.note,
            source_sentence=it.source_sentence,
            status="review" if grounded else "rejected",
        ))
        kept, rejected = kept + grounded, rejected + (not grounded)
    session.add(Generation(kind="extract", key=str(report.id), prompt_version=EXTRACT_VERSION, model=llm.model,
                           generated_at=now_iso(), text=json.dumps({"kept": kept, "rejected": rejected})))
    session.commit()
    return {"kept": kept, "rejected": rejected}
