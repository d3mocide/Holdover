from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ExtractedItem(BaseModel):
    waterbody_raw: str = Field(min_length=1)
    species: list[str] = []
    rating: Literal["excellent", "good", "fair", "slow", "unknown"] = "unknown"
    note: str = ""
    source_sentence: str = Field(min_length=1)

    @field_validator("species", mode="before")
    @classmethod
    def _one_species_as_text(cls, v):
        # Models that do not enforce the schema often send "coho" instead of ["coho"]. Wrap it; anything else is validated as is.
        return [v] if isinstance(v, str) else v


class ExtractionResult(BaseModel):
    items: list[ExtractedItem]


class DigestResult(BaseModel):
    digest: str = Field(min_length=1)


class TextResult(BaseModel):
    text: str = Field(min_length=1, max_length=600)
