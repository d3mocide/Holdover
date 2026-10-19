import json
import re

from sqlalchemy import delete, select
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


def match_waterbody(session: Session, raw: str, zone: str | None = None) -> int | None:
    """Exact match only, after dropping generic words (River, Lake, Fork...). 'North Santiam' matches
    'Santiam River, North Fork' but 'Willamette River' does not match the Coast Fork. Anything
    looser goes to the human review queue. With a zone, only that zone's waters are candidates: a Central-zone "Fall River"
    is neither Willamette's Fall Creek nor made ambiguous by it."""
    key = _key(raw)
    if not key:
        return None
    wbs = {wb.id: wb for wb in session.scalars(select(Waterbody).where(Waterbody.zone == zone) if zone else select(Waterbody))}
    hits = {wb_id for wb_id, wb in wbs.items() if _key(wb.name) == key}
    for a in session.scalars(select(WaterbodyAlias).where(WaterbodyAlias.confirmed == 1)):
        if a.waterbody_id in wbs and _key(a.alias_text) == key:
            hits.add(a.waterbody_id)
    return hits.pop() if len(hits) == 1 else None


def rematch_items(session: Session) -> int:
    """Re-run the zone-aware match. Unreviewed items are recomputed, so an old match across zones (a Northwest "Salmon River" matched to a
    Willamette creek) is corrected, and an item read before its waterbody existed gets matched. Accepted items are never touched: a
    person decided those. Rejected items are left alone. Returns how many changed."""
    n = 0
    for item, report in session.execute(select(ReportItem, Report).join(Report, Report.id == ReportItem.report_id)
                                        .where(ReportItem.status == "review")).all():
        wb_id = match_waterbody(session, item.waterbody_raw, report.zone)
        if wb_id != item.waterbody_id:
            item.waterbody_id = wb_id
            n += 1
    session.commit()
    return n


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
    # A re-extraction (a newer prompt version) replaces the model's earlier unreviewed reading of this report; what a person accepted or
    # rejected stays.
    session.execute(delete(ReportItem).where(ReportItem.report_id == report.id, ReportItem.status == "review"))
    kept = rejected = 0
    for it in result.items:
        grounded = _ws(it.source_sentence) in haystack
        session.add(ReportItem(
            report_id=report.id, waterbody_id=match_waterbody(session, it.waterbody_raw, report.zone) if grounded else None,
            waterbody_raw=it.waterbody_raw, species=", ".join(it.species), rating=it.rating, note=it.note,
            source_sentence=it.source_sentence,
            status="review" if grounded else "rejected",
        ))
        kept, rejected = kept + grounded, rejected + (not grounded)
    session.add(Generation(kind="extract", key=str(report.id), prompt_version=EXTRACT_VERSION, model=llm.model,
                           generated_at=now_iso(), text=json.dumps({"kept": kept, "rejected": rejected})))
    session.commit()
    return {"kept": kept, "rejected": rejected}
