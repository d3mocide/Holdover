"""Portable schema (section 3 of the handoff). Dates and times are ISO-8601 text."""
from sqlalchemy import ForeignKey, Integer, LargeBinary, Float, PrimaryKeyConstraint, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Waterbody(Base):
    __tablename__ = "waterbody"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)  # lake|pond|river|reservoir|creek
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    zone: Mapped[str | None] = mapped_column(Text)
    species_json: Mapped[str | None] = mapped_column(Text)
    regs_url: Mapped[str | None] = mapped_column(Text)
    starred: Mapped[int] = mapped_column(Integer, default=0, server_default="0")  # legacy: superseded by Favorite


class WaterbodyAlias(Base):
    __tablename__ = "waterbody_alias"
    __table_args__ = (UniqueConstraint("alias_text", "source"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    alias_text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    waterbody_id: Mapped[int | None] = mapped_column(ForeignKey("waterbody.id"))
    confirmed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    proposed_confidence: Mapped[float | None] = mapped_column(Float)


class RawFetch(Base):
    __tablename__ = "raw_fetch"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[str] = mapped_column(Text)
    status: Mapped[int | None] = mapped_column(Integer)
    content_hash: Mapped[str | None] = mapped_column(Text)
    body: Mapped[bytes | None] = mapped_column(LargeBinary)
    parse_ok: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)


class StockingSnapshot(Base):
    __tablename__ = "stocking_snapshot"
    id: Mapped[int] = mapped_column(primary_key=True)
    raw_fetch_id: Mapped[int | None] = mapped_column(ForeignKey("raw_fetch.id"))
    scraped_at: Mapped[str] = mapped_column(Text)
    week_of: Mapped[str] = mapped_column(Text)  # Monday, YYYY-MM-DD
    alias_id: Mapped[int | None] = mapped_column(ForeignKey("waterbody_alias.id"))
    zone_office: Mapped[str | None] = mapped_column(Text)
    legals: Mapped[int | None] = mapped_column(Integer)
    trophy: Mapped[int | None] = mapped_column(Integer)
    brood: Mapped[int | None] = mapped_column(Integer)
    fingerling: Mapped[int | None] = mapped_column(Integer)
    total: Mapped[int | None] = mapped_column(Integer)


class Report(Base):
    __tablename__ = "report"
    id: Mapped[int] = mapped_column(primary_key=True)
    raw_fetch_id: Mapped[int | None] = mapped_column(ForeignKey("raw_fetch.id"))
    zone: Mapped[str | None] = mapped_column(Text)
    issued_on: Mapped[str | None] = mapped_column(Text)
    summary_text: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    generated_at: Mapped[str | None] = mapped_column(Text)


class ReportItem(Base):
    __tablename__ = "report_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int | None] = mapped_column(ForeignKey("report.id"))
    waterbody_id: Mapped[int | None] = mapped_column(ForeignKey("waterbody.id"))
    waterbody_raw: Mapped[str | None] = mapped_column(Text)
    species: Mapped[str | None] = mapped_column(Text)
    rating: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    source_sentence: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="review", server_default="review")


class Gauge(Base):
    __tablename__ = "gauge"
    id: Mapped[int] = mapped_column(primary_key=True)
    site_no: Mapped[str] = mapped_column(Text)
    agency: Mapped[str] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)


class WaterbodyGauge(Base):
    __tablename__ = "waterbody_gauge"
    waterbody_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gauge_id: Mapped[int] = mapped_column(Integer, primary_key=True)


class GaugeReading(Base):
    __tablename__ = "gauge_reading"
    __table_args__ = (PrimaryKeyConstraint("gauge_id", "parameter", "observed_at"),)
    gauge_id: Mapped[int] = mapped_column(Integer)
    parameter: Mapped[str] = mapped_column(Text)
    value: Mapped[float | None] = mapped_column(Float)
    observed_at: Mapped[str] = mapped_column(Text)
    provisional: Mapped[int] = mapped_column(Integer, default=1, server_default="1")


class ReservoirReading(Base):
    __tablename__ = "reservoir_reading"
    __table_args__ = (PrimaryKeyConstraint("project", "observed_at"),)
    project: Mapped[str] = mapped_column(Text)  # Army Corps location code, e.g. DET
    observed_at: Mapped[str] = mapped_column(Text)  # UTC, minute precision
    elevation_ft: Mapped[float] = mapped_column(Float)
    raw_fetch_id: Mapped[int | None] = mapped_column(Integer)


class FireDanger(Base):
    __tablename__ = "fire_danger"
    id: Mapped[int] = mapped_column(primary_key=True)
    waterbody_id: Mapped[int] = mapped_column(Integer, index=True)
    level: Mapped[int] = mapped_column(Integer)  # ODF public fire danger, 1 Low to 4 Extreme
    area: Mapped[str] = mapped_column(Text)  # ODF regulated-use area code
    district: Mapped[int | None] = mapped_column(Integer)
    raw_fetch_id: Mapped[int | None] = mapped_column(Integer, index=True)


class FireNearby(Base):
    __tablename__ = "fire_nearby"
    id: Mapped[int] = mapped_column(primary_key=True)
    waterbody_id: Mapped[int] = mapped_column(Integer, index=True)
    incident: Mapped[str] = mapped_column(Text)
    acres: Mapped[float | None] = mapped_column(Float)
    percent_contained: Mapped[float | None] = mapped_column(Float)
    updated_at: Mapped[str | None] = mapped_column(Text)
    distance_km: Mapped[float] = mapped_column(Float)
    inside: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    raw_fetch_id: Mapped[int | None] = mapped_column(Integer, index=True)


class ForecastCache(Base):
    __tablename__ = "forecast_cache"
    __table_args__ = (PrimaryKeyConstraint("waterbody_id", "fetched_at"),)
    waterbody_id: Mapped[int] = mapped_column(Integer)
    fetched_at: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[str | None] = mapped_column(Text)


class Advisory(Base):
    __tablename__ = "advisory"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str | None] = mapped_column(Text)
    waterbody_id: Mapped[int | None] = mapped_column(Integer)
    text: Mapped[str | None] = mapped_column(Text)
    observed_at: Mapped[str | None] = mapped_column(Text)
    raw_fetch_id: Mapped[int | None] = mapped_column(Integer)


class Generation(Base):
    __tablename__ = "generation"
    __table_args__ = (UniqueConstraint("kind", "key", "prompt_version"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str | None] = mapped_column(Text)
    key: Mapped[str | None] = mapped_column(Text)
    text: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    generated_at: Mapped[str | None] = mapped_column(Text)


# Journal: client-generated UUIDs, never touched by scrapers
class Trip(Base):
    __tablename__ = "trip"
    uuid: Mapped[str] = mapped_column(Text, primary_key=True)
    started_at: Mapped[str | None] = mapped_column(Text)
    ended_at: Mapped[str | None] = mapped_column(Text)
    waterbody_id: Mapped[int | None] = mapped_column(Integer)
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    conditions_json: Mapped[str | None] = mapped_column(Text)
    conditions_source: Mapped[str | None] = mapped_column(Text)
    setup_uuid: Mapped[str | None] = mapped_column(Text)  # the named setup used, if any
    gear_json: Mapped[str | None] = mapped_column(Text)  # JSON list of gear_item uuids used on the trip
    updated_at: Mapped[str] = mapped_column(Text)
    deleted: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))  # NULL = pre-accounts row, adopted by the first admin


class Catch(Base):
    __tablename__ = "catch"
    uuid: Mapped[str] = mapped_column(Text, primary_key=True)
    trip_uuid: Mapped[str | None] = mapped_column(ForeignKey("trip.uuid"))
    species: Mapped[str | None] = mapped_column(Text)
    count: Mapped[int | None] = mapped_column(Integer)
    length_in: Mapped[float | None] = mapped_column(Float)
    method: Mapped[str | None] = mapped_column(Text)
    kept: Mapped[int | None] = mapped_column(Integer)
    photo_path: Mapped[str | None] = mapped_column(Text)
    gear_uuid: Mapped[str | None] = mapped_column(Text)  # the lure/fly this catch was caught on, if recorded
    updated_at: Mapped[str] = mapped_column(Text)
    deleted: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))


class Pin(Base):
    __tablename__ = "pin"
    uuid: Mapped[str] = mapped_column(Text, primary_key=True)
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    label: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(Text, unique=True)  # stored lower-case
    password_hash: Mapped[str] = mapped_column(Text)
    is_admin: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    disabled: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    home_lat: Mapped[float | None] = mapped_column(Float)
    home_lon: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[str] = mapped_column(Text)


class UserSession(Base):
    """Server-side session. Only a hash of the cookie token is stored, so a database leak is not a login."""
    __tablename__ = "user_session"
    token_hash: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    created_at: Mapped[str] = mapped_column(Text)
    last_used_at: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[str] = mapped_column(Text)
    device: Mapped[str | None] = mapped_column(Text)


class Invite(Base):
    __tablename__ = "invite"
    id: Mapped[int] = mapped_column(primary_key=True)
    code_hash: Mapped[str] = mapped_column(Text, unique=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created_at: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[str] = mapped_column(Text)
    used_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"))
    used_at: Mapped[str | None] = mapped_column(Text)


class Favorite(Base):
    __tablename__ = "favorite"
    __table_args__ = (PrimaryKeyConstraint("user_id", "waterbody_id"),)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    waterbody_id: Mapped[int] = mapped_column(ForeignKey("waterbody.id", ondelete="CASCADE"))


class GearItem(Base):
    """One thing in a person's tackle: a rod, a lure, a pair of waders. Private to its owner; syncs like a trip."""
    __tablename__ = "gear_item"
    uuid: Mapped[str] = mapped_column(Text, primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))
    kind: Mapped[str] = mapped_column(Text)  # rod|reel|line|lure|fly|terminal|net|wearable|electronics|other
    name: Mapped[str] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(Text)
    size: Mapped[str | None] = mapped_column(Text)  # free text: '6wt 9ft', '1/8 oz', '#12'
    color: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    fisheries_json: Mapped[str | None] = mapped_column(Text)  # JSON list of trout|steelhead|warmwater
    status: Mapped[str] = mapped_column(Text, default="active", server_default="active")  # active|retired|lost
    notes: Mapped[str | None] = mapped_column(Text)
    photo_path: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class GearSetup(Base):
    """A named combination ('6wt dry fly': rod + reel + line + leader) so a trip records one choice, not five."""
    __tablename__ = "gear_setup"
    uuid: Mapped[str] = mapped_column(Text, primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))
    name: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    item_uuids_json: Mapped[str] = mapped_column(Text, default="[]", server_default="[]")
    updated_at: Mapped[str] = mapped_column(Text)
    deleted: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
