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
    starred: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


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
    updated_at: Mapped[str] = mapped_column(Text)
    deleted: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


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
    updated_at: Mapped[str] = mapped_column(Text)
    deleted: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class Pin(Base):
    __tablename__ = "pin"
    uuid: Mapped[str] = mapped_column(Text, primary_key=True)
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    label: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
