from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session
from app.llm.explain import cached_text, explain_key
from app.llm.prompts import EXPLAIN_VERSION
from app.planner import FISHERIES, facts_text, rank

router = APIRouter()


@router.get("/spots")
def spots(date_: date | None = Query(None, alias="date"), fishery: str = "trout", session: Session = Depends(get_session)):
    if fishery not in FISHERIES:
        raise HTTPException(422, f"fishery must be one of {', '.join(FISHERIES)}")
    day = date_ or date.today()
    out = []
    for i, sp in enumerate(rank(session, day, fishery), 1):
        g = cached_text(session, "explain", explain_key(sp.wb.id, day.isoformat(), fishery, facts_text(sp.facts)), EXPLAIN_VERSION)
        out.append({
            "rank": i, "waterbody": {"id": sp.wb.id, "name": sp.wb.name, "kind": sp.wb.kind, "lat": sp.wb.lat, "lon": sp.wb.lon},
            "score": sp.score, "coverage": sp.coverage,
            "factors": [{"name": f.name, "value": f.value, "weight": f.weight, "points": f.contribution, "detail": f.detail,
                         "applicable": f.applicable}
                        for f in sp.factors],
            "explanation": {"text": g.text if g else sp.template, "source": "llm" if g else "template",
                            "as_of": g.generated_at if g else None, "model": g.model if g else None},
            "report_sentence": sp.facts["report_sentence"],
        })
    w = get_settings()
    return {"date": day.isoformat(), "fishery": fishery, "spots": out,
            "weights": {"stocking": w.w_stocking, "report": w.w_report, "flow": w.w_flow, "forecast": w.w_forecast,
                        "distance": w.w_distance},
            "note": "Scores are tunable starting points, not validated. Stocking is by week and may change; "
                    "check ODFW for regulations."}
