import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.http import now_iso
from app.llm.client import LLMClient
from app.llm.prompts import DIGEST_SYSTEM, DIGEST_VERSION
from app.llm.schemas import DigestResult
from app.models import Generation, Report, ReportItem


def ungrounded_terms(digest: str, source: str) -> list[str]:
    """Numbers and capitalised words (other than sentence starts) in the digest that don't occur in
    the source items. A cheap guard, not a proof: a hit means the digest is discarded."""
    src = source.lower()
    bad = [n for n in re.findall(r"\d[\d,.\-]*", digest) if n.rstrip(".,-").lower() not in src]
    for sent in re.split(r"(?<=[.!?])\s+", digest):
        for w in re.findall(r"(?<!^)(?<![.!?] )\b[A-Z][a-z]{2,}\b", sent):
            if w.lower() not in src:
                bad.append(w)
    return bad


def digest_key(report: Report) -> str:
    return f"{report.zone}:{report.issued_on}"


def summarize_report(session: Session, report: Report, llm: LLMClient) -> str | None:
    items = session.scalars(select(ReportItem).where(ReportItem.report_id == report.id,
                                                      ReportItem.status != "rejected")).all()
    if not items:
        return None
    lines = [f"- {i.waterbody_raw} ({i.species or 'species not stated'}; rating {i.rating}): {i.note} "
             f"[{i.source_sentence}]" for i in items]
    source = "\n".join(lines)
    digest = llm.chat_json(DIGEST_SYSTEM, f"Zone: {report.zone}\nItems:\n{source}", DigestResult).digest.strip()
    if ungrounded_terms(digest, source):
        raise ValueError(f"digest contains terms not in the items: {ungrounded_terms(digest, source)}")
    now = now_iso()
    gen = session.scalar(select(Generation).where(Generation.kind == "digest", Generation.key == digest_key(report),
                                                  Generation.prompt_version == DIGEST_VERSION))
    if gen is None:
        gen = Generation(kind="digest", key=digest_key(report), prompt_version=DIGEST_VERSION)
        session.add(gen)
    gen.text, gen.model, gen.generated_at = digest, llm.model, now
    report.summary_text, report.model, report.prompt_version, report.generated_at = digest, llm.model, DIGEST_VERSION, now
    session.commit()
    return digest
