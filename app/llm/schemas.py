from typing import Literal

from pydantic import BaseModel, Field


class ExtractedItem(BaseModel):
    waterbody_raw: str = Field(min_length=1)
    species: list[str] = []
    rating: Literal["excellent", "good", "fair", "slow", "unknown"] = "unknown"
    note: str = ""
    source_sentence: str = Field(min_length=1)


class ExtractionResult(BaseModel):
    items: list[ExtractedItem]


class DigestResult(BaseModel):
    digest: str = Field(min_length=1)
