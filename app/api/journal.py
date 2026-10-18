"""Journal sync. Rows carry client-generated UUIDs and updated_at; the server is a last-write-wins
mirror. Scrapers never touch these tables."""
import csv
import io
import json
import os
import re
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import csrf_guard, require_user
from app.config import get_settings
from app.db import get_session
from app.models import Catch, Pin, Trip, User

router = APIRouter(dependencies=[Depends(csrf_guard), Depends(require_user)])
_UUID = re.compile(r"^[0-9a-fA-F-]{8,64}$")


class _Row(BaseModel):
    uuid: str
    updated_at: str
    deleted: int = 0

    @field_validator("uuid")
    @classmethod
    def _uuid(cls, v):
        if not _UUID.match(v):
            raise ValueError("bad uuid")
        return v

    @field_validator("updated_at")
    @classmethod
    def _ts(cls, v):
        datetime.fromisoformat(v.replace("Z", "+00:00"))  # raises ValueError if not ISO
        return v


class TripIn(_Row):
    started_at: str | None = None
    ended_at: str | None = None
    waterbody_id: int | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    notes: str | None = None
    conditions_json: str | None = None
    conditions_source: str | None = None  # live|cached


class CatchIn(_Row):
    trip_uuid: str
    species: str | None = None
    count: int | None = Field(default=None, ge=0)
    length_in: float | None = None
    method: str | None = None
    kept: int | None = None
    photo_path: str | None = None


class PinIn(_Row):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    label: str | None = None
    notes: str | None = None


class Push(BaseModel):
    trips: list[TripIn] = []
    catches: list[CatchIn] = []
    pins: list[PinIn] = []


def _upsert(session: Session, model, row: BaseModel, user: User) -> str:
    """'applied' | 'stale' (existing row is as new or newer: ignore, which also makes a repeat push a no-op) |
    'foreign' (the uuid belongs to someone else: never touched)."""
    existing = session.get(model, row.uuid)
    data = row.model_dump()
    if existing is None:
        session.add(model(**data, owner_id=user.id))
        return "applied"
    if existing.owner_id != user.id:
        return "foreign"
    if _norm(existing.updated_at) >= _norm(row.updated_at):
        return "stale"
    for k, v in data.items():
        setattr(existing, k, v)
    return "applied"


def _norm(ts: str) -> datetime:
    d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


@router.post("/sync/push")
def push(body: Push, user: User = Depends(require_user), session: Session = Depends(get_session)):
    result = {"applied": 0, "stale": 0, "rejected": []}
    for group, model in ((body.trips, Trip), (body.pins, Pin), (body.catches, Catch)):  # trips before catches
        for row in group:
            if model is Catch:
                trip = session.get(Trip, row.trip_uuid)
                if trip is None:
                    result["rejected"].append({"uuid": row.uuid, "reason": "unknown trip_uuid"})
                    continue
                if trip.owner_id != user.id:
                    result["rejected"].append({"uuid": row.uuid, "reason": "trip belongs to another account"})
                    continue
                if row.photo_path and not row.photo_path.startswith(f"{user.id}-"):
                    result["rejected"].append({"uuid": row.uuid, "reason": "photo belongs to another account"})
                    continue
            outcome = _upsert(session, model, row, user)
            if outcome == "foreign":
                result["rejected"].append({"uuid": row.uuid, "reason": "belongs to another account"})
            else:
                result[outcome] += 1
        session.flush()
    session.commit()
    result["server_time"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    return result


def _dump(session: Session, user: User, since: str | None):
    """Only the signed-in user's own rows. owner_id is server-side bookkeeping and is never sent."""
    out = {}
    for key, model in (("trips", Trip), ("catches", Catch), ("pins", Pin)):
        q = select(model).where(model.owner_id == user.id)
        rows = [r for r in session.scalars(q)
                if since is None or _norm(r.updated_at) > _norm(since)]
        out[key] = [{c.name: getattr(r, c.name) for c in model.__table__.columns if c.name != "owner_id"} for r in rows]
    return out


@router.get("/sync/pull")
def pull(since: str | None = None, user: User = Depends(require_user), session: Session = Depends(get_session)):
    if since is not None:
        try:
            _norm(since)
        except ValueError:
            raise HTTPException(422, "since must be ISO-8601")
    d = _dump(session, user, since)
    d["server_time"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    return d


@router.get("/journal/export")
def export(format: str = "json", user: User = Depends(require_user), session: Session = Depends(get_session)):
    d = _dump(session, user, None)
    if format == "json":
        return JSONResponse(d, headers={"Content-Disposition": 'attachment; filename="holdover-journal.json"'})
    if format != "csv":
        raise HTTPException(422, "format must be json or csv")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["trip_uuid", "started_at", "ended_at", "waterbody_id", "lat", "lon", "species", "count",
                "length_in", "method", "kept", "trip_notes", "conditions_source"])
    catches: dict[str, list] = {}
    for c in d["catches"]:
        if not c["deleted"]:
            catches.setdefault(c["trip_uuid"], []).append(c)
    for t in d["trips"]:
        if t["deleted"]:
            continue
        base = [t["uuid"], t["started_at"], t["ended_at"], t["waterbody_id"], t["lat"], t["lon"]]
        tail = [t["notes"], t["conditions_source"]]
        for c in catches.get(t["uuid"]) or [None]:
            mid = [c["species"], c["count"], c["length_in"], c["method"], c["kept"]] if c else [None] * 5
            w.writerow(base + mid + tail)
    return PlainTextResponse(buf.getvalue(), media_type="text/csv",
                             headers={"Content-Disposition": 'attachment; filename="holdover-journal.csv"'})


def _photo_dir() -> str:
    d = os.path.join(get_settings().data_dir, "photos")
    os.makedirs(d, exist_ok=True)
    return d


@router.post("/journal/photo")
async def photo(file: UploadFile = File(...), user: User = Depends(require_user)):
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}.get(file.content_type or "")
    if ext is None:
        raise HTTPException(415, "jpeg, png or webp only")
    data = await file.read()
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(413, "photo over 15 MB")
    name = f"{user.id}-{secrets.token_hex(16)}{ext}"  # the prefix is the owner: only they can fetch or attach it
    with open(os.path.join(_photo_dir(), name), "wb") as f:
        f.write(data)
    return {"photo_path": name}


@router.get("/journal/photo/{name}")
def get_photo(name: str, user: User = Depends(require_user)):
    if not re.fullmatch(r"\d+-[0-9a-f]{32}\.(jpg|png|webp)", name) or not name.startswith(f"{user.id}-"):
        raise HTTPException(404)
    path = os.path.join(_photo_dir(), name)
    if not os.path.isfile(path):
        raise HTTPException(404)
    return FileResponse(path)
