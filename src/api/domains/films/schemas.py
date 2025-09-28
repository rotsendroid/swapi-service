from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class FilmRelationSchema(BaseModel):
    id: int
    title: str
    episode_id: int
    opening_crawl: Optional[str] = None
    director: Optional[str] = None
    producer: Optional[str] = None
    release_date: date
    created: datetime
    edited: datetime
    url: str

    @field_validator("opening_crawl")
    @classmethod
    def truncate_opening_crawl(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            # Replace \r\n with spaces and clean up multiple spaces
            cleaned = v.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
            cleaned = " ".join(cleaned.split())  # Remove multiple spaces
            if len(cleaned) > 100:
                return cleaned[:100] + "..."
            return cleaned
        return v

    class Config:
        from_attributes = True


class FilmSchema(BaseModel):
    id: int
    title: str
    episode_id: int
    opening_crawl: Optional[str] = None
    director: Optional[str] = None
    producer: Optional[str] = None
    release_date: date
    created: datetime
    edited: datetime
    url: str
    characters: list[CharacterRelationSchema] = []
    starships: list[StarshipRelationSchema] = []

    @field_validator("opening_crawl")
    @classmethod
    def clean_opening_crawl(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            # Replace \r\n with spaces and clean up multiple spaces
            cleaned = v.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
            cleaned = " ".join(cleaned.split())  # Remove multiple spaces
            return cleaned
        return v

    class Config:
        from_attributes = True


# Import here to avoid circular imports
from api.domains.characters.schemas import CharacterRelationSchema  # noqa: E402
from api.domains.starships.schemas import StarshipRelationSchema  # noqa: E402

# Rebuild models after all schemas are imported
FilmSchema.model_rebuild()
